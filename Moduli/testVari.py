# Importazione librerie
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from scipy.stats import pearsonr

# Periodo di visualizzazione del progetto - valutazione effettuata sull'anno civile (1 gennaio - 31 dicembre)
dataInizio = '2010-01-01'
primaStagione = "10/11"
dataFine = '2024-12-31'
ultimaStagione = "23/24"

# caricamento e manipolazione dei dati: provo a pulire e tenere i soli dati che mi servono
def caricaInfo(nome_file):
    '''
    carico il contenuto di un archivio .csv all'interno di un DataFrame
    para: nome_file
    ret: retDataFrame, con il contenuto o 'None' se ha presentato errori
    '''
    if os.path.exists(nome_file):
        print(f"File '{nome_file}' trovato. \nCaricamento in corso...")
        retDataFrame = pd.read_csv(nome_file)
        return retDataFrame
        # Continua con l'analisi...
    else:
        print(f"ERRORE: File '{nome_file}' non trovato.")
        return None

def pulisciTrasferimenti(trasferimenti):
    '''
    funzione specifica per pulire il dataframe trasferimenti:
        - tolgo i valori nulli e metto 0.0
    '''
    if trasferimenti is None:
        print("ERRORE: DataFrame trasferimenti vuoto")
        quit()
    else:
        trasferimenti['transfer_fee'] = trasferimenti['transfer_fee'].fillna(0.0)   # sistemo i NaN in "transfer_fee"
        trasferimenti['market_value_in_eur'] = trasferimenti['market_value_in_eur'].fillna(0.0) # sistemo i NaN in "market_value_in_eur"
        return trasferimenti

def calcoloAnnuali(trasferimenti_totale):
    """
    Calcolo annuali:
        - volume trasferimenti
        - spese effettuate agglomerate
        - valore totale teorico dei giocatori che hanno effettuato un trasferimento

    Parametri:
        - trasferimenti_totale: DataFrame contenente tutti i trasferimenti puliti precedentemente

    Restituisce:
        - df_spesa_annuale: DataFrame con colonne 'Anno', 'Spesa_Mld_EUR', 'Volume_Trasferimenti' e 'Valore_Totale_Mld_EURO'
    """
    df_lavoro = trasferimenti_totale.copy() # creo una copia per non toccare l'originale

    # Filtro tramite anno
    try:
        df_lavoro['Anno'] = df_lavoro['transfer_season'].str.slice(0, 2).astype(int) + 2000
    except Exception:
        df_lavoro['Anno'] = pd.to_numeric(df_lavoro['transfer_season'].str.slice(0, 2), errors='coerce') + 2000
    df_filtrato = df_lavoro[df_lavoro['Anno'].between(2010, 2023)].dropna(subset=['Anno']).copy()
    
    # Raggruppamento
    df_spesa_stagionale = df_filtrato.groupby('transfer_season').agg(
        Valore_Totale_EURO=('market_value_in_eur','sum'),
        Spesa_Totale_EUR=('transfer_fee', 'sum'),
        Volume_Trasferimenti=('player_id', 'count')
    ).reset_index()

    # Ricalcoli e normalizzazioni
    df_spesa_stagionale.rename(columns={'transfer_season': 'Anno-Calcistico'}, inplace=True) # rinonimo la colonna in "Anno-Calcistico"
    df_spesa_stagionale['Spesa_Mld_EUR'] = df_spesa_stagionale['Spesa_Totale_EUR'] / 1_000_000_000  # converto euro in miliardi
    df_spesa_stagionale['Valore_Totale_Mld_EURO'] = df_spesa_stagionale['Valore_Totale_EURO'] / 1_000_000_000  # converto euro in miliardi
    
    return df_spesa_stagionale[['Anno-Calcistico', 'Spesa_Mld_EUR', 'Volume_Trasferimenti', 'Valore_Totale_Mld_EURO']]

def correlazionePearson(trasferimentiAnnuali):
    return trasferimentiAnnuali['Spesa_Mld_EUR'].corr(trasferimentiAnnuali['Volume_Trasferimenti'])

def analisiCorrelazione(trasferimentiAnnuali):
    r_value, p_value = pearsonr(trasferimentiAnnuali['Spesa_Mld_EUR'], trasferimentiAnnuali['Volume_Trasferimenti'])
    return r_value, p_value

def valutaPearson(r):
    """
    Valuta il coefficiente di correlazione di Pearson (r) e stampa
    la forza e la direzione della relazione lineare.
    """
    print(f"Coefficiente di Pearson ottenuto: {r}. Effettuo valutazione sul valore:")
    # 1. Valuta la Forza (|r|)
    r_abs = abs(r)
    
    if r_abs == 1.0:
        forza = "Perfetta"
    elif r_abs > 0.8:
        forza = "Molto Forte"
    elif r_abs > 0.6:
        forza = "Forte"
    elif r_abs > 0.4:
        forza = "Moderata"
    elif r_abs > 0.2:
        forza = "Debole"
    elif r_abs > 0.0:
        forza = "Molto Debole / Trascurabile"
    else:
        print(f"Coefficiente di Pearson (r): {r:.4f}")
        print("Valutazione: Nessuna correlazione lineare significativa (r ≈ 0).")
        return

    # 2. Valuta la Direzione (Segno)
    if r > 0:
        direzione = "Positiva (all'aumentare di una variabile, aumenta l'altra)"
    else: # r < 0
        direzione = "Negativa (all'aumentare di una variabile, diminuisce l'altra)"
        
    # 3. Stampa il Risultato
    print("=" * 50)
    print(f"Coefficiente di Pearson (r): {r:.4f}")
    print("-" * 50)
    print(f"Forza: Correlazione {forza}.")
    print(f"Direzione: Correlazione {direzione}.")
    print("=" * 50)

def valutaP(p):
    print(f"P-value ottenuto: {p}")
    if p < 0.001:
        print("Interpretazione: Correlazione ALTAMENTE significativa (p < 0.001)")
    elif p < 0.05:
        print("Interpretazione: Correlazione significativa (p < 0.05)")
    else:
        print("Interpretazione: Correlazione NON significativa (p >= 0.05)")

def graficoCorrelazioneVolumeSpesa(df_aggregato):
    """
    Genera uno scatter plot (con regressione) che mostra la correlazione tra il Volume dei trasferimenti e la Spesa in Mld.

    - Usa 'Volume_Trasferimenti' (X)
    - Usa 'Spesa_Mld_EUR' (Y)
    - Usa 'Anno-Calcistico' (Etichette)
    - Visualizza il coefficiente di Pearson (r) e il p-value (p).
    """
    
    if df_aggregato is None or df_aggregato.empty:
        print("DataFrame aggregato non valido. Impossibile creare il grafico.")
        return None

    r, p = analisiCorrelazione(df_aggregato)
    valutaPearson(r)    # valutazione coefficiente di Pearson
    valutaP(p)  # valutazione p-value

    # --- Nomi delle colonne FISSATI (in base al tuo DataFrame) ---
    colonna_x = 'Volume_Trasferimenti'
    colonna_y = 'Spesa_Mld_EUR'
    colonna_label = 'Anno-Calcistico'
    # ---

    # Controllo di sicurezza
    colonne_necessarie = [colonna_x, colonna_y, colonna_label]
    if not all(col in df_aggregato.columns for col in colonne_necessarie):
        print(f"Errore: La funzione si aspettava le colonne {colonne_necessarie}.")
        print(f"Colonne trovate nel DataFrame: {df_aggregato.columns.tolist()}")
        return None
    # --- Fine controllo ---

    plt.figure(figsize=(10, 6))

    # Usa regplot con i nomi corretti
    sns.regplot(
        data=df_aggregato,
        x=colonna_x,
        y=colonna_y,   # <-- CORRETTO
        scatter_kws={'s': 80, 'alpha': 0.7, 'edgecolor': 'k'}, 
        line_kws={'color': 'red', 'linestyle': '--'} 
    )

    # --- Posizionamento Etichette (Anni) ---
    for i in range(df_aggregato.shape[0]):
        # Offset dinamico per evitare sovrapposizioni
        y_range = df_aggregato[colonna_y].max() - df_aggregato[colonna_y].min()
        offset = y_range * 0.015 # 1.5% dell'intervallo Y
        
        plt.text(
            x=df_aggregato[colonna_x].iloc[i],
            y=df_aggregato[colonna_y].iloc[i] - offset, # <-- CORRETTO
            s=str(df_aggregato[colonna_label].iloc[i]), # <-- CORRETTO
            ha='center',
            va='top',
            fontdict=dict(color='black', size=9)
        )

    # --- Box con Statistiche (r e p) ---
    stats_text = f"Pearson $r$: {r:.3f}\n$p$-value: {p:.3f}"
    plt.text(
        0.05, 0.95,
        stats_text,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='left',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.8, edgecolor='gray')
    )
    
    # --- Titoli e Assi (Aggiornati) ---
    plt.title('Correlazione tra Volume dei Trasferimenti e Spesa Totale', fontsize=14)
    plt.xlabel('Volume Trasferimenti (Numero Totale di Acquisti)', fontsize=12)
    plt.ylabel('Spesa Totale (Miliardi di €)', fontsize=12) # <-- CORRETTO
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    
    nomeFile = 'scatterplot_correlazione_VolumeTrasferimenti_SpesaAnnuale_conCoefficienti.png'
    plt.savefig(nomeFile)
    plt.show()
    plt.close()

    print(f"Grafico con statistiche salvato come '{nomeFile}'")
    return

def istogrammaSpeseAnnuali(trasferimentiAgglomerati):
    """
    Crea un istogramma (grafico a barre) delle spese annuali per stagione calcistica,
    mostrando il valore esatto sopra ogni barra.

    Args:
        trasferimentiAgglomerati (pd.DataFrame): DataFrame contenente almeno
                                                le colonne 'Anno-Calcistico'
                                                e 'Spesa_Mld_EUR'.
    """
    
    # Controllo preliminare sulla validità del DataFrame
    if trasferimentiAgglomerati.empty:
        print("Il DataFrame fornito è vuoto.")
        return
    
    required_cols = ['Anno-Calcistico', 'Spesa_Mld_EUR']
    if not all(col in trasferimentiAgglomerati.columns for col in required_cols):
        print(f"Il DataFrame deve contenere le colonne: {', '.join(required_cols)}")
        print(f"Colonne disponibili: {trasferimentiAgglomerati.columns.tolist()}")
        return

    # Estrazione dei dati per il grafico
    anni = trasferimentiAgglomerati['Anno-Calcistico']
    spese = trasferimentiAgglomerati['Spesa_Mld_EUR']

    # Creazione della figura e degli assi per il grafico
    # Impostiamo una dimensione adatta per la leggibilità delle etichette
    plt.figure(figsize=(12, 7)) 
    
    # Creazione delle barre
    bars = plt.bar(anni, spese, color='skyblue', label='Spesa (Mld EUR)')

    # Aggiunta di etichette, titolo e griglia
    plt.xlabel('Stagione Calcistica', fontsize=12)
    plt.ylabel('Spesa (Miliardi EUR)', fontsize=12)
    plt.title('Spesa Annuale per Trasferimenti Calcistici', fontsize=14, fontweight='bold')
    
    # Rotazione delle etichette sull'asse X per evitare sovrapposizioni
    plt.xticks(rotation=45, ha='right', fontsize=10)
    
    # Aggiunta di una griglia sull'asse Y per facilitare la lettura
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Aggiunta delle etichette con il valore sopra ogni barra
    for bar in bars:
        yval = bar.get_height()
        
        # plt.text() posiziona il testo
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,  # Posizione X (centro della barra)
            yval + (spese.max() * 0.01),          # Posizione Y (leggermente sopra la barra)
            f'{yval:.2f}',                        # Testo da visualizzare (formattato a 2 decimali)
            ha='center',                          # Allineamento orizzontale
            va='bottom',                          # Allineamento verticale
            fontsize=9
        )

    # Ottimizza il layout per assicurarsi che tutto sia visibile
    plt.tight_layout() 

    # Salva il grafico in un file immagine
    file_name = 'spese_annuali_istogramma.png'
    plt.savefig(file_name)
    plt.show()
    
    print(f"Grafico salvato con successo come '{file_name}'")

# Chiamate varie
trasferimenti_totale = pulisciTrasferimenti(caricaInfo('archive\\transfers.csv'))
# print(trasferimenti_totale.head()) # stampa la testa del DataFrame (testa: prime 5 righe)
# print(trasferimenti_totale.tail()) # stampa la coda del DataFrame (coda: ultime 5 righe)

trasferimentiAnnuali = calcoloAnnuali(trasferimenti_totale)
print(trasferimentiAnnuali)

# Analisi e grafico correlazione tra "volume trasferimenti" e "spesa annuale"
graficoCorrelazioneVolumeSpesa(trasferimentiAnnuali)

# Istogramma con spese annuali
istogrammaSpeseAnnuali(trasferimentiAnnuali)