import pandas as pd
import os
from scipy.stats import pearsonr

def carica_dati(percorso_file):
    """Carica il csv e restituisce il DF o None."""
    if os.path.exists(percorso_file):
        print(f"[INFO] Caricamento: {percorso_file}...")
        return pd.read_csv(percorso_file)
    else:
        print(f"[ERROR] File non trovato: {percorso_file}")
        return None

def pulisci_trasferimenti(df):
    """Pulisce i NaN e prepara i tipi di dato."""
    if df is None:
        raise ValueError("DataFrame vuoto passato a pulisci_trasferimenti")
    
    df_clean = df.copy()
    df_clean['transfer_fee'] = df_clean['transfer_fee'].fillna(0.0)
    df_clean['market_value_in_eur'] = df_clean['market_value_in_eur'].fillna(0.0)
    return df_clean

def calcola_metriche_annuali(df):
    """Aggrega i dati per stagione."""
    df_work = df.copy()
    
    # Gestione anno sicura
    try:
        df_work['Anno'] = df_work['transfer_season'].str.slice(0, 2).astype(int) + 2000
    except Exception:
        df_work['Anno'] = pd.to_numeric(df_work['transfer_season'].str.slice(0, 2), errors='coerce') + 2000
        
    df_filt = df_work[df_work['Anno'].between(2010, 2023)].dropna(subset=['Anno']).copy()
    
    df_agg = df_filt.groupby('transfer_season').agg(
        Valore_Totale_EURO=('market_value_in_eur','sum'),
        Spesa_Totale_EUR=('transfer_fee', 'sum'),
        Volume_Trasferimenti=('player_id', 'count')
    ).reset_index()

    df_agg.rename(columns={'transfer_season': 'Anno-Calcistico'}, inplace=True)
    df_agg['Spesa_Mld_EUR'] = df_agg['Spesa_Totale_EUR'] / 1e9
    df_agg['Valore_Totale_Mld_EURO'] = df_agg['Valore_Totale_EURO'] / 1e9
    
    return df_agg

def aggiungi_spesa_reale(df_agg):
    """Calcola l'inflazione interna del mercato."""
    df = df_agg.copy()
    spesa_euro = df['Spesa_Mld_EUR'] * 1e9
    df['Costo_Medio_Unitario'] = spesa_euro / df['Volume_Trasferimenti']
    
    # Anno base: ultima entry
    costo_base = df.iloc[-1]['Costo_Medio_Unitario']
    df['Spesa_Reale_Mld_EUR'] = df['Spesa_Mld_EUR'] * (costo_base / df['Costo_Medio_Unitario'])
    return df

def analizza_efficienza(df_raw, stagioni_target):
    """Analisi avanzata efficienza mercato (delta valore/prezzo)."""
    df = df_raw[df_raw['transfer_season'].isin(stagioni_target)].copy()
    df = df[df['transfer_fee'] > 0] # Solo onerosi
    
    df_agg = df.groupby('transfer_season').agg(
        Valore_Totale_EURO=('market_value_in_eur', 'sum'),
        Spesa_Totale_EUR=('transfer_fee', 'sum')
    ).reset_index()
    
    df_agg.rename(columns={'transfer_season': 'Anno-Calcistico'}, inplace=True)
    df_agg['Spesa_Mld_EUR'] = df_agg['Spesa_Totale_EUR'] / 1e9
    df_agg['Valore_Totale_Mld_EURO'] = df_agg['Valore_Totale_EURO'] / 1e9
    
    df_agg['Delta_Assoluto'] = df_agg['Spesa_Mld_EUR'] - df_agg['Valore_Totale_Mld_EURO']
    df_agg['Premium_Percentuale'] = (df_agg['Delta_Assoluto'] / df_agg['Valore_Totale_Mld_EURO']) * 100
    
    # Sorting logico
    df_agg['Anno-Calcistico'] = pd.Categorical(df_agg['Anno-Calcistico'], categories=stagioni_target, ordered=True)
    return df_agg.sort_values('Anno-Calcistico')

def calcola_correlazione(df, col_x, col_y):
    """Wrapper per Pearson puro."""
    return pearsonr(df[col_x], df[col_y])