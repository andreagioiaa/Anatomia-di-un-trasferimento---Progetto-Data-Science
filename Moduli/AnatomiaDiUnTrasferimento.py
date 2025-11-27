# Progetto DataScience: Anatomia di un trasferimento

# Studio dei trasferimenti di calciomercato dal 2010 ad oggi (31 settembre 2024).

# Importazione librerie
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Periodo di visualizzazione del progetto - valutazione effettuata sull'anno civile (1 gennaio - 31 dicembre)
data_inizio = '2010-01-01'
data_fine = '2024-12-31'

# 5 migliori campionati
campionati_migliori = {
    'Bundesliga': ['bundesliga', 'germany', 'deutschland', 'de1'],
    'Premier League': ['premier league', 'england', 'gb1'],
    'Serie A': ['serie a', 'italy', 'italia', 'it1'],
    'LaLiga': ['la liga', 'laliga', 'spain', 'españa', 'es1'],
    'Ligue 1': ['ligue 1', 'france', 'fr1']
}
# codici 5 migliori campionati: 'competition.csv'
campionati_migliori_codici = ['DE1', 'GB1', 'IT1', 'ES1', 'FR1']

def caricaInfo(nome_file):
    if os.path.exists(nome_file):
        print(f"File '{nome_file}' trovato. Caricamento in corso...")
        df_transfers = pd.read_csv(nome_file)
        return df_transfers
        # Continua con l'analisi...
    else:
        print(f"ERRORE: File '{nome_file}' non trovato.")
        return None

# Caricamento dati
# print("Caricamento dati...")
# trasferimenti = caricaInfo('archive\\transfers.csv')
# squadre = caricaInfo('archive\\clubs.csv')
# competizioni = caricaInfo('archive\\competitions.csv')

def stampaRigaSingola():
    print("-" * 70)
    return

def stampaRigaDoppia():
    print("=" * 70)
    return

# percentuale crescita dal 2010 ad oggi (senza parametro)
def calcola_aumento_spesa_globale():
    """
    Carica i dati dei trasferimenti, calcola la spesa totale per le stagioni
    '10/11' e '23/24' e restituisce l'aumento percentuale.
    """
    
    # Dati di Riferimento
    ANNO_INIZIALE = '10/11'
    ANNO_FINALE = '23/24'
    
    df_transfers = caricaInfo('archive\\transfers.csv')

    # 2. Pulizia Dati: I NaN in 'transfer_fee' sono considerati 0
    df_transfers['transfer_fee'] = df_transfers['transfer_fee'].fillna(0.0)

    # 3. Aggregazione Spesa Totale per Stagione
    spesa_per_stagione = df_transfers.groupby('transfer_season')['transfer_fee'].sum()

    # 4. Estrazione Valori (con gestione degli errori)
    try:
        S_2010 = spesa_per_stagione.loc[ANNO_INIZIALE]
    except KeyError:
        S_2010 = 0.0
        
    try:
        S_2024 = spesa_per_stagione.loc[ANNO_FINALE]
    except KeyError:
        S_2024 = 0.0

    # 5. Logica di Calcolo della Crescita
    delta_S = S_2024 - S_2010
    
    if S_2010 == 0:
        aumento_P = np.inf if S_2024 > 0 else 0.0
    else:
        # Formula: ((S_finale - S_iniziale) / S_iniziale) * 100
        aumento_P = (delta_S / S_2010) * 100

    # Stampa dei risultati dettagliati (per verifica)
    print("\n" + "="*70)
    print("1) Risultati dell'Analisi di Crescita della Spesa Globale")
    print("="*70)
    print(f"Spesa Totale {ANNO_INIZIALE} (2010): €{S_2010:,.2f}")
    print(f"Spesa Totale {ANNO_FINALE} (2024): €{S_2024:,.2f}")
    print("-" * 70)
    print(f"Aumento Assoluto (Delta S): €{delta_S:,.2f}")
    print(f"Aumento Percentuale: {aumento_P:.2f} %")
    print("="*70)
    
    # 6. Ritorno della percentuale di aumento
    return aumento_P

# percentuale crescita dal 2010 ad oggi (con parametro)
def calcola_aumento_spesa_da_df(df_spesa, anno_inizio=2010, anno_fine=2024):
    """
    Calcola l'aumento percentuale della spesa tra due anni specifici
    utilizzando un DataFrame pre-aggregato.
    """
    
    # 1. Estrazione dei valori (usando la colonna 'Spesa_Mld_EUR')
    # Nota: Usiamo .loc per trovare l'anno esatto nella colonna 'Anno'
    
    # Trova il valore dell'anno iniziale
    try:
        S_iniziale = df_spesa[df_spesa['Anno'] == anno_inizio]['Spesa_Mld_EUR'].iloc[0]
    except IndexError:
        print(f"AVVISO: Spesa per l'anno {anno_inizio} non trovata.")
        S_iniziale = 0.0

    # Trova il valore dell'anno finale
    try:
        S_finale = df_spesa[df_spesa['Anno'] == anno_fine]['Spesa_Mld_EUR'].iloc[0]
    except IndexError:
        print(f"AVVISO: Spesa per l'anno {anno_fine} non trovata.")
        S_finale = 0.0
        
    # 2. Calcolo della Crescita
    delta_S = S_finale - S_iniziale
    
    if S_iniziale == 0:
        aumento_P = np.inf if S_finale > 0 else 0.0
    else:
        aumento_P = (delta_S / S_iniziale) * 100

    # Stampa i risultati e restituisce la percentuale
    print(f"\nAnalisi tra {anno_inizio} e {anno_fine}:")
    print(f"Aumento Assoluto: €{delta_S:.2f} miliardi")
    print(f"Aumento Percentuale: {aumento_P:.2f} %")
    
    return aumento_P

def calcola_spesa_annuale_completa(file_name='archive\\transfers.csv'):
    """
    Carica i dati dei trasferimenti, pulisce il costo, aggrega la spesa totale
    per ogni anno di inizio stagione dal 2010 al 2024 e restituisce il DataFrame
    della spesa annuale (in Miliardi di Euro).
    """
    
    # 1. Caricamento dati e pulizia
    try:
        df_transfers = pd.read_csv(file_name)
    except FileNotFoundError:
        return pd.DataFrame()

    df_transfers['transfer_fee'] = df_transfers['transfer_fee'].fillna(0.0)

    # 2. Creazione della Colonna Anno Numerico
    try:
        df_transfers['start_year'] = df_transfers['transfer_season'].str.slice(0, 2).astype(int) + 2000
    except Exception:
        df_transfers['start_year'] = pd.to_numeric(df_transfers['transfer_season'].str.slice(0, 2), errors='coerce') + 2000
    
    # Filtra per l'intervallo richiesto [2010, 2024]
    df_transfers = df_transfers[df_transfers['start_year'].between(2010, 2024)].dropna(subset=['start_year']).copy()
    df_transfers['start_year'] = df_transfers['start_year'].astype(int)

    # 3. Aggregazione Spesa Totale per Anno
    spesa_annua = df_transfers.groupby('start_year')['transfer_fee'].sum().reset_index()
    spesa_annua.columns = ['Anno', 'Spesa_Totale_EUR']

    # 4. Normalizzazione per la leggibilità (Miliardi di Euro)
    spesa_annua['Spesa_Mld_EUR'] = spesa_annua['Spesa_Totale_EUR'] / 1_000_000_000
    
    return spesa_annua

def graficoSpeseAnnuali(df_spesa_annuale):
    """
    Genera e salva un grafico a barre (istogramma) della spesa totale annuale.

    Il grafico mostra la Spesa Totale (in Miliardi di Euro) per l'anno di
    inizio stagione (2010-2024).

    Parametri:
    df_spesa_annuale (pd.DataFrame): DataFrame pre-aggregato con colonne
                                     'Anno' e 'Spesa_Mld_EUR'.
    """
    
    df = df_spesa_annuale.copy()

    # Crea la figura e gli assi
    fig, ax = plt.subplots(figsize=(12, 6))

    # Crea il grafico a barre
    ax.bar(df['Anno'], df['Spesa_Mld_EUR'], color='forestgreen', alpha=0.8, edgecolor='black', linewidth=0.7)

    # Etichette e Titolo
    ax.set_xlabel('Anno', fontsize=12)
    ax.set_ylabel('Spesa Totale (Miliardi di €)', fontsize=12)
    ax.set_title('Spesa Totale Annuale nel Calciomercato (2010 - 2024)', fontsize=14)

    # Formattazione Asse X (mostra ogni anno)
    ax.set_xticks(df['Anno'])
    ax.set_xticklabels(df['Anno'].astype(int), rotation=45, ha='right')

    # Aggiungi una griglia per una migliore lettura
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    # Aggiungi etichette dei dati in cima alle barre
    for i in range(len(df)):
        ax.text(df['Anno'].iloc[i], df['Spesa_Mld_EUR'].iloc[i] + 0.2, 
                f'{df["Spesa_Mld_EUR"].iloc[i]:.2f}', 
                ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    
    nomeFile = 'istogrammaSpesaAnnuale.png'
    plt.savefig(nomeFile)
    plt.show()
    plt.close(fig)
    
    print(f"Grafico salvato come '{nomeFile}'")
    return nomeFile

def datiCorrelazione(file_name='archive\\transfers.csv'):
    """
    Carica i dati dei trasferimenti e aggrega Volume, Spesa Totale 
    e Prezzo Medio per anno (2010-2024).
    """
    
    # 1. Caricamento dati e pulizia
    try:
        # Nota: uso 'transfers.csv' perché è il file caricato.
        # Nel tuo script locale, usa 'archive/transfers.csv'
        df_transfers = pd.read_csv(file_name) 
    except FileNotFoundError:
        print(f"ERRORE: File '{file_name}' non trovato.")
        return None

    df_transfers['transfer_fee'] = df_transfers['transfer_fee'].fillna(0.0)

    # 2. Creazione della Colonna Anno Numerico
    try:
        df_transfers['start_year'] = df_transfers['transfer_season'].str.slice(0, 2).astype(int) + 2000
    except Exception:
        df_transfers['start_year'] = pd.to_numeric(df_transfers['transfer_season'].str.slice(0, 2), errors='coerce') + 2000
    
    df_transfers = df_transfers[df_transfers['start_year'].between(2010, 2024)].dropna(subset=['start_year']).copy()
    df_transfers['start_year'] = df_transfers['start_year'].astype(int)

    # 3. Aggregazione per Anno
    df_agg = df_transfers.groupby('start_year').agg(
        Spesa_Totale_Mld=('transfer_fee', 'sum'),
        Volume_Trasferimenti=('player_id', 'count')
    ).reset_index()

    # 4. Calcolo Metriche
    df_agg['Spesa_Totale_Mld'] = df_agg['Spesa_Totale_Mld'] / 1_000_000_000
    df_agg['Prezzo_Medio_Mln'] = (df_agg['Spesa_Totale_Mld'] * 1000) / df_agg['Volume_Trasferimenti']
    
    return df_agg

def analizza_correlazione_volume_prezzi(df_aggregato):
    """
    Calcola la correlazione tra spesa, volume e prezzo medio
    partendo da un DataFrame aggregato.
    """
    
    if df_aggregato is None or df_aggregato.empty:
        print("DataFrame vuoto o nullo. Impossibile analizzare la correlazione.")
        return None
        
    print("--- Dati Aggregati per Analisi di Correlazione ---")
    print(df_aggregato.to_markdown(index=False, floatfmt=".2f", numalign="left", stralign="left"))

    # Calcolo della Matrice di Correlazione
    df_corr_data = df_aggregato[['Spesa_Totale_Mld', 'Volume_Trasferimenti', 'Prezzo_Medio_Mln']]
    
    corr_matrix = df_corr_data.corr()
    
    print("\n--- Matrice di Correlazione di Pearson (r) ---")
    print(corr_matrix.to_markdown(floatfmt=".4f", numalign="left", stralign="left"))
    
    return corr_matrix

def graficoCorrelazioneVolumePrezzo(df_aggregato):
    """
    Genera uno scatter plot (con regressione) che mostra la 
    correlazione tra il Volume dei trasferimenti e il Prezzo Medio.
    
    VERSIONE MODIFICATA:
    - Posizionamento etichette corretto (per visibilità 2024).
    - Rimozione di plt.show() e ordine corretto di savefig/close.
    """
    
    if df_aggregato is None or df_aggregato.empty:
        print("DataFrame aggregato non valido. Impossibile creare il grafico.")
        return None

    plt.figure(figsize=(10, 6))

    # Usa regplot di seaborn per creare lo scatter plot E la linea di regressione
    sns.regplot(
        data=df_aggregato,
        x='Volume_Trasferimenti',
        y='Prezzo_Medio_Mln',
        scatter_kws={'s': 80, 'alpha': 0.7, 'edgecolor': 'k'}, # Stile dei punti
        line_kws={'color': 'red', 'linestyle': '--'} # Stile della linea
    )

    # --- MODIFICA CHIAVE: Posizionamento Etichette ---
    # Aggiungi etichette (l'anno) per ogni punto
    for i in range(df_aggregato.shape[0]):
        plt.text(
            x=df_aggregato['Volume_Trasferimenti'].iloc[i],     # Centrato su X
            y=df_aggregato['Prezzo_Medio_Mln'].iloc[i] - 0.02,  # Leggero offset verso il basso
            s=str(df_aggregato['start_year'].iloc[i]), # Testo (anno)
            ha='center', # Allineamento orizzontale centrato
            va='top',    # Allineamento verticale (il testo sta sotto la coordinata)
            fontdict=dict(color='black', size=9)
        )

    # Titoli e Assi (aggiunto intervallo di anni per chiarezza)
    plt.title('Correlazione tra Volume dei Trasferimenti e Prezzo Medio (2010-2024)', fontsize=14)
    plt.xlabel('Volume Trasferimenti (Numero Totale di Acquisti)', fontsize=12)
    plt.ylabel('Prezzo Medio per Trasferimento (Milioni di €)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    
    nomeFile = 'scatterplot_correlazioneVolumePrezzo_corretto.png'
    plt.savefig(nomeFile)
    plt.show()
    plt.close()

    print(f"Grafico corretto salvato come '{nomeFile}'")
    return nomeFile

# --- CHIAMATA ALLE FUNZIONI ---
# 1. Esegui la funzione di calcolo annuale (che abbiamo già)
df_spesa_annuale = calcola_spesa_annuale_completa() 
print(df_spesa_annuale.to_markdown(index=False, floatfmt=".2f", numalign="left", stralign="left"))

stampaRigaSingola()
stampaRigaSingola()
# 2. Chiama la nuova funzione passando il DataFrame come parametro
percentuale_crescita = calcola_aumento_spesa_da_df(df_spesa_annuale, anno_inizio=2010, anno_fine=2024)

stampaRigaSingola()
stampaRigaSingola()
# 3. Chiamata alla funzione per la creazione dell'Istogramma
graficoSpeseAnnuali(df_spesa_annuale)

stampaRigaSingola()
stampaRigaSingola()
# 4. Chiamate per analisi correlazione "Volume - Prezzi"
df_dati_correlazione = datiCorrelazione()
if df_dati_correlazione is not None:
    matrice_correlazione = analizza_correlazione_volume_prezzi(df_dati_correlazione)
    stampaRigaSingola()
    stampaRigaSingola()
    graficoCorrelazioneVolumePrezzo(df_dati_correlazione)