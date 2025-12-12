import pandas as pd
import os
from scipy.stats import pearsonr
from datetime import datetime

def carica_dati(percorso_file):
    """Carica il csv e restituisce il DataFrame o None."""
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
    """Calcolo coefficiente di Pearson e P-value"""
    return pearsonr(df[col_x], df[col_y])


def focusVerde(df_efficienza_full):
    stagioni_focus = ['20/21', '21/22', '22/23'] 
    df_focus = df_efficienza_full[df_efficienza_full['Anno-Calcistico'].isin(stagioni_focus)].copy()
    df_focus['Anno-Calcistico'] = pd.Categorical(
        df_focus['Anno-Calcistico'], 
        categories=stagioni_focus, 
        ordered=True
    )
    return df_focus.sort_values('Anno-Calcistico')

def calcola_inflazione(df_raw, soglia_minima=1000000):
    print(f"[FIX] Ricalcolo dati inflazione (Soglia {soglia_minima/1e6}M)...")
    
    # 1. Filtro (uguale alla diagnostica)
    df = df_raw[df_raw['transfer_fee'] >= soglia_minima].copy()
    
    try:
        df['Anno_Sort'] = df['transfer_season'].str.slice(0, 2).astype(int) + 2000
    except:
        df['Anno_Sort'] = pd.to_numeric(df['transfer_season'].str.slice(0, 2), errors='coerce') + 2000
    df = df[df['Anno_Sort'].between(2010, 2023)]

    # 2. Indice basato su MEDIANA (Cruciale)
    paniere = df.groupby('transfer_season').agg(
        Prezzo_Mediano=('transfer_fee', 'median'),
        Anno_Sort=('Anno_Sort', 'min')
    ).reset_index().sort_values('Anno_Sort')

    valore_base = paniere.iloc[0]['Prezzo_Mediano']
    paniere['Indice_Inflazione'] = paniere['Prezzo_Mediano'] / valore_base

    # 3. Spesa Totale
    spesa = df.groupby('transfer_season')['transfer_fee'].sum().reset_index()
    spesa.rename(columns={'transfer_fee': 'Spesa_Nominale'}, inplace=True)

    # 4. Merge
    df_fin = pd.merge(spesa, paniere, on='transfer_season')
    
    # 5. Calcoli Miliardi
    df_fin['Spesa_Mld_EUR'] = df_fin['Spesa_Nominale'] / 1e9
    
    # CRUCIALE: Se l'indice è 1.26, la Reale deve essere vicina alla Nominale
    df_fin['Spesa_Reale_Mld_EUR'] = df_fin['Spesa_Mld_EUR'] / df_fin['Indice_Inflazione']
    
    df_fin.rename(columns={'transfer_season': 'Anno-Calcistico'}, inplace=True)
    
    return df_fin


# Inserisci in gestione_dati.py

# In gestione_dati.py

def prepara_dati_geografici(df_transfers, df_clubs):
    """
    Unisce i trasferimenti ai club per ottenere la nazione di provenienza.
    Analisi LATO VENDITORE (Chi incassa?).
    """
    print("[GEO] Join tra Transfers e Clubs in corso...")
    
    # 1. Pulizia e Preparazione Clubs
    # Prendiamo solo quello che ci serve: ID e Competizione
    clubs_light = df_clubs[['club_id', 'domestic_competition_id']].copy()
    
    # 2. MERGE (Join)
    # Vogliamo sapere dove si trova il club che HA VENDUTO (from_club_id)
    # Left join: teniamo tutti i trasferimenti, se non troviamo il club pazienza
    df_merged = df_transfers.merge(
        clubs_light, 
        left_on='from_club_id', 
        right_on='club_id', 
        how='left'
    )
    
    # 3. Mappatura Codici Competizione -> Nazioni
    # Questi sono i codici standard di Transfermarkt. 
    # Se il tuo CSV ha codici diversi, dovrai aggiornare questo dizionario.
    comp_to_country = {
        'GB1': 'United Kingdom', 'ES1': 'Spain', 'IT1': 'Italy', 'L1': 'Germany', 'FR1': 'France',
        'PO1': 'Portugal', 'NL1': 'Netherlands', 'TR1': 'Turkey', 'BE1': 'Belgium', 'RU1': 'Russia',
        'BRA1': 'Brazil', 'AR1N': 'Argentina', 'MLS1': 'United States of America', 
        'UKR1': 'Ukraine', 'GR1': 'Greece', 'SC1': 'United Kingdom', # Scozia -> UK per semplicità mappa
        'DK1': 'Denmark', 'SE1': 'Sweden', 'NO1': 'Norway', 'CH1': 'Switzerland',
        'A1': 'Austria', 'PL1': 'Poland', 'CZ1': 'Czechia', 'HR1': 'Croatia',
        'RO1': 'Romania', 'SER1': 'Serbia'
    }

    # Applichiamo la mappa
    df_merged['Country'] = df_merged['domestic_competition_id'].map(comp_to_country)
    
    # 4. Diagnostica rapida (per vedere se stiamo perdendo troppi dati)
    missing = df_merged['Country'].isna().sum()
    total = len(df_merged)
    print(f"[GEO] Trasferimenti mappati: {total - missing}/{total}. (Mancanti: {missing})")
    
    if (total - missing) < 100:
        print("[ERROR] Troppi pochi dati mappati. Controlla i codici in 'domestic_competition_id' nel file clubs.csv")
        # Stampa i codici univoci per debug
        print("Codici trovati:", df_merged['domestic_competition_id'].unique()[:20])
        return pd.DataFrame()

    # 5. Aggregazione per Nazione (Strategia Miniera vs EuroSpin)
    df_agg = df_merged.dropna(subset=['Country']).groupby('Country').agg(
        Total_Spend=('transfer_fee', 'sum'),
        Transfer_Count=('transfer_fee', 'count')
    ).reset_index()

    # Calcolo Prezzo Medio (Valore della merce)
    df_agg['Avg_Price'] = df_agg['Total_Spend'] / df_agg['Transfer_Count']
    df_agg['Avg_Price_Mln'] = df_agg['Avg_Price'] / 1e6
    
    return df_agg

def prepara_dati_eta_valore(df_raw):
    """
    Prepara il dataset giocatori per l'analisi Età vs Valore.
    Target: Stagione 23/24.
    Filtri: Età 18-36, Valore > 1Mln.
    Include DIAGNOSTICA per valori mancanti.
    """
    print("\n[ETÀ-VALORE] --- INIZIO DIAGNOSTICA ---")
    
    if df_raw is None:
        return pd.DataFrame()

    df = df_raw.copy()

    # 1. Filtro Stagione (2023)
    # Assicuriamoci che last_season sia gestita correttamente
    df['last_season'] = pd.to_numeric(df['last_season'], errors='coerce')
    df = df[df['last_season'] == 2023].copy()
    print(f" -> Giocatori attivi nella stagione 2023: {len(df)}")

    # 2. Pulizia Valore di Mercato (CRUCIALE)
    # Rimuoviamo eventuali virgole o punti se sono stringhe, prima di convertire
    if df['market_value_in_eur'].dtype == object:
        df['market_value_in_eur'] = df['market_value_in_eur'].astype(str).str.replace(',', '', regex=False)

    df['market_value_in_eur'] = pd.to_numeric(df['market_value_in_eur'], errors='coerce')
    
    # DEBUG: Vediamo se abbiamo perso qualcuno di grosso
    top_raw = df.sort_values('market_value_in_eur', ascending=False).head(3)
    print(f" -> Top 3 Valori grezzi trovati: {top_raw['market_value_in_eur'].tolist()}")

    df = df.dropna(subset=['market_value_in_eur'])
    
    # Filtro > 1Mln
    df = df[df['market_value_in_eur'] >= 1000000]
    
    # Convertiamo in Milioni
    df['Valore_Mln'] = df['market_value_in_eur'] / 1e6

    # 3. Pulizia Data e Calcolo Età
    df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')
    df = df.dropna(subset=['date_of_birth'])
    
    target_date = pd.to_datetime('2024-01-01')
    df['age'] = (target_date - df['date_of_birth']).dt.days // 365

    # 4. Filtro Età "Prime" (18-36)
    df = df[df['age'].between(18, 36)]

    # --- DIAGNOSTICA FINALE ---
    print(f" -> Dataset finale pronto: {len(df)} giocatori.")
    print(" -> I 5 GIOCATORI PIÙ COSTOSI NEL DATASET FILTRATO:")
    top_players = df.sort_values('Valore_Mln', ascending=False).head(5)
    for idx, row in top_players.iterrows():
        print(f"    * {row['name']} ({row['age']} anni): {row['Valore_Mln']} Mln €")
    print("------------------------------------------\n")
    
    return df
#==== FINE FILE ===#