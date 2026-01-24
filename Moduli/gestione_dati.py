import pandas as pd
import os
from scipy.stats import pearsonr
from datetime import datetime
import numpy as np

# PREZZO MINIMO DI CONFRONTO
PREZZO_MINIMO = 5000000

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
    Prepara il dataset giocatori per l'analisi Età vs Valore, 
    filtrando per giocatori attivi e con valore > 1M€.
    """
    print("\n[ETÀ-VALORE] --- INIZIO DIAGNOSTICA ---")
    
    if df_raw is None:
        print("[ERROR] DataFrame iniziale vuoto.")
        return pd.DataFrame()

    df = df_raw.copy()

    # --- 1. Pulizia Valore di Mercato (CRUCIALE) ---
    
    # Rimuoviamo eventuali formattazioni non numeriche prima di convertire
    if df['market_value_in_eur'].dtype == object:
        df['market_value_in_eur'] = df['market_value_in_eur'].astype(str).str.replace(',', '', regex=False)

    df['market_value_in_eur'] = pd.to_numeric(df['market_value_in_eur'], errors='coerce')
    df = df.dropna(subset=['market_value_in_eur'])
    
    # --- 2. Filtro Attività/Pertinenza (La mossa per includere Mbappé ed escludere Klose) ---
    
    df['contract_expiration_date'] = pd.to_datetime(df['contract_expiration_date'], errors='coerce')
    df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')
    
    # Parametri per l'analisi 2023
    Data_Limite_Attivita = pd.to_datetime('2023-06-30')
    Soglia_Top_Player = 50000000 # 50 Milioni

    # Filtro: Contratto valido DOPO Giu 2023 OPPURE Valore di mercato > 50M (Top Player)
    df = df[
        (df['contract_expiration_date'] > Data_Limite_Attivita) | 
        (df['market_value_in_eur'] > Soglia_Top_Player)
    ].copy()

    print(f" -> Giocatori ritenuti attivi (con contratto o Top Player): {len(df)}")
    
    # --- 3. Calcolo Età e Filtri Finali ---
    
    target_date = pd.to_datetime('2024-01-01') # Età calcolata al 1 Gennaio 2024 (per l'analisi 2023/24)
    df['age'] = (target_date - df['date_of_birth']).dt.days // 365
    
    # Filtro valore > 1Mln
    df = df[df['market_value_in_eur'] >= 1000000]
    
    # Filtro Età "Prime" (18-36)
    df = df[df['age'].between(18, 36)]
    
    # Convertiamo in Milioni per il grafico
    df['Valore_Mln'] = df['market_value_in_eur'] / 1e6

    # --- DIAGNOSTICA FINALE ---
    print(f" -> Dataset finale pronto: {len(df)} giocatori.")
    print(f" -> TOP 5 VALORI RITROVATI (dovrebbe includere Top Player):")
    top_players = df.sort_values('market_value_in_eur', ascending=False).head(5)
    for idx, row in top_players.iterrows():
        print(f"    * {row['name']} ({row['age']} anni): {row['Valore_Mln']:.2f} Mln €")
    print("------------------------------------------\n")
    
    return df[['player_id', 'age', 'Valore_Mln', 'market_value_in_eur', 'current_club_domestic_competition_id']]



def prepara_dati_efficienza_scout(df_transfers, df_players, df_clubs):
    """
    Unisce i dati di trasferimenti (transfer_fee, transfer_date), 
    giocatori (date_of_birth) e club (competizione) per calcolare le features 
    necessarie per il modello di Efficienza degli Scout.
    """
    import pandas as pd
    
    print("\n[EFFICIENZA SCOUT] --- PREPARAZIONE MODELLO ---")
    
    # 1. Pulizia e Conversione Iniziale
    df_transfers = df_transfers.copy()
    
    # Rimuoviamo i trasferimenti a costo zero (spesso sono fine prestito o giovanili)
    df_transfers = df_transfers.dropna(subset=['transfer_fee'])
    df_transfers = df_transfers[df_transfers['transfer_fee'] > 0].copy()
    
    # Conversione date e pulizia ID
    df_transfers['transfer_date'] = pd.to_datetime(df_transfers['transfer_date'], errors='coerce')
    df_players['date_of_birth'] = pd.to_datetime(df_players['date_of_birth'], errors='coerce')
    
    # Assicuriamo che gli ID siano trattati come numeri interi per il merge
    df_transfers['player_id'] = pd.to_numeric(df_transfers['player_id'], errors='coerce').astype('Int64')
    df_players['player_id'] = pd.to_numeric(df_players['player_id'], errors='coerce').astype('Int64')
    
    # 2. Unione Trasferimenti e Giocatori (per l'età)
    df_merged = df_transfers.merge(
        df_players[['player_id', 'date_of_birth']], 
        on='player_id', 
        how='left'
    )
    
    # 3. Calcolo Età al Trasferimento
    df_merged['age_at_transfer'] = (df_merged['transfer_date'] - df_merged['date_of_birth']).dt.days // 365
    
    # Filtra trasferimenti con età ragionevole (16-40) e dove l'età è nota
    df_merged = df_merged[df_merged['age_at_transfer'].between(16, 40)].dropna(subset=['age_at_transfer']).copy()
    
    print(f" -> Trasferimenti validi dopo età/fee e pulizia: {len(df_merged)}")

    # 4. Aggiunta delle Leghe (Club di PROVENIENZA e DESTINAZIONE)
    
    df_clubs_small = df_clubs[['club_id', 'domestic_competition_id']].copy()
    
    # Merge per la lega di PROVENIENZA
    df_clubs_small.columns = ['from_club_id', 'league_from'] 
    df_final = df_merged.merge(
        df_clubs_small, 
        on='from_club_id', 
        how='left'
    )

    # Merge per la lega di DESTINAZIONE
    df_clubs_small.columns = ['to_club_id', 'league_to'] 
    df_final = df_final.merge(
        df_clubs_small, 
        on='to_club_id', 
        how='left'
    ).dropna(subset=['league_from', 'league_to']) # Rimuovi trasferimenti in leghe sconosciute
    
    print(f" -> Trasferimenti con lega di provenienza e destinazione nota: {len(df_final)}")
    
    # 5. Preparazione Feature Finali per il Modello
    df_model = df_final[[
        'transfer_fee', 
        'age_at_transfer', 
        'league_from', 
        'league_to', 
        'transfer_season'
    ]].copy()
    
    # 6. Encoding della Variabile Target (Log Transformation)
    # Per stabilizzare la varianza e migliorare le performance del modello di regressione
    df_model['log_transfer_fee'] = np.log1p(df_model['transfer_fee'])
    
    print(f" -> DataFrame per il modello pronto: {len(df_model)} righe.")
    print("------------------------------------------\n")
    
    return df_model


#==== FINE FILE ===#