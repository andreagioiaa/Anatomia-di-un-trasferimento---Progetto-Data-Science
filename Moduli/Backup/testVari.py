# Importazione librerie
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from scipy.stats import pearsonr, spearmanr

cartGrafici = "..\\Grafici\\"
cartDati = "..\\Dataset\\"

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

def aggiungiSpesaReale(df_spesa_stagionale):
    """
    Aggiunge la colonna 'Spesa_Reale_Mld_EUR' normalizzando i prezzi
    basandosi sul costo medio di un trasferimento nell'anno base (ultima stagione).
    """
    # FIX: Ricostruisco i valori in Euro partendo dai Miliardi che hai già
    # Spesa_Mld_EUR è in miliardi, quindi moltiplico per 1 miliardo per avere gli euro
    spesa_in_euro = df_spesa_stagionale['Spesa_Mld_EUR'] * 1_000_000_000
    
    # 1. Calcolo il costo medio per singolo trasferimento
    df_spesa_stagionale['Costo_Medio_Unitario'] = spesa_in_euro / df_spesa_stagionale['Volume_Trasferimenti']

    # 2. Definisco l'anno base (prendo l'ultima stagione disponibile)
    costo_base = df_spesa_stagionale.iloc[-1]['Costo_Medio_Unitario']
    anno_base = df_spesa_stagionale.iloc[-1]['Anno-Calcistico']
    
    print(f"--- NORMALIZZAZIONE INFLAZIONE ---")
    print(f"Anno Base per i prezzi: {anno_base} (Costo medio: {costo_base/1_000_000:.2f} Mln €)")

    # 3. Calcolo la Spesa Reale
    # Formula: SpesaNominale * (CostoBase / CostoAnnoCorrente)
    df_spesa_stagionale['Spesa_Reale_Mld_EUR'] = df_spesa_stagionale['Spesa_Mld_EUR'] * (costo_base / df_spesa_stagionale['Costo_Medio_Unitario'])
    
    return df_spesa_stagionale

def graficoConfrontoNominaleReale(df_aggregato):
    plt.figure(figsize=(12, 7))
    sns.set_theme(style="darkgrid") # O usa lo stile scuro che preferisci

    # Linea 1: Spesa Nominale (Quello che si legge sui giornali)
    sns.lineplot(
        data=df_aggregato, 
        x='Anno-Calcistico', 
        y='Spesa_Mld_EUR', 
        label='Spesa Nominale (Cifre Ufficiali)', 
        marker='o', color='gray', linestyle='--', alpha=0.6, linewidth=2
    )

    # Linea 2: Spesa Reale (Il potere d'acquisto effettivo)
    sns.lineplot(
        data=df_aggregato, 
        x='Anno-Calcistico', 
        y='Spesa_Reale_Mld_EUR', 
        label='Spesa Reale (Al netto inflazione mercato)', 
        marker='o', color='#ff3333', linewidth=3
    )

    # Area tra le due curve per evidenziare l'inflazione
    plt.fill_between(
        df_aggregato['Anno-Calcistico'], 
        df_aggregato['Spesa_Mld_EUR'], 
        df_aggregato['Spesa_Reale_Mld_EUR'], 
        color='red', alpha=0.1
    )

    plt.title("L'Illusione della Spesa: Nominale vs Reale (Base 2024)", fontsize=16, fontweight='bold', color='#333')
    plt.ylabel("Miliardi di € (Valuta 2024)", fontsize=12)
    plt.xlabel("Stagione", fontsize=12)
    plt.xticks(rotation=45)
    plt.legend()
    
    nomeFile = cartGrafici + 'confronto_spesa_nominale_reale.png'
    plt.savefig(nomeFile)
    plt.show()
    print(f"Grafico confronto salvato in {nomeFile}")

def graficoCorrelazioneVolumeSpesa(df_aggregato):
    """
    Versione PULITA per presentazione orale (FIXED: linewidths error).
    """
    if df_aggregato is None or df_aggregato.empty:
        return None

    r, p = analisiCorrelazione(df_aggregato)
    
    colonna_x = 'Volume_Trasferimenti'
    colonna_y = 'Spesa_Mld_EUR'
    colonna_label = 'Anno-Calcistico'

    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")

    # 1. DISEGNA TUTTO (Base visibile)
    sns.regplot(
        data=df_aggregato,
        x=colonna_x,
        y=colonna_y,
        # CORREZIONE QUI: cambiato 'linewidth' in 'linewidths'
        scatter_kws={'s': 200, 'alpha': 0.9, 'edgecolor': 'white', 'linewidths': 1.5, 'color': '#2c7bb6'}, 
        line_kws={'color': '#d62728', 'linestyle': '--', 'linewidth': 2.5, 'label': f'Trend Lineare ($R={r:.2f}$)'}
    )

    # 2. EVIDENZIAZIONE SELETTIVA (Solo cerchi rossi)
    anni_covid = ['20/21', '21/22']
    
    # Calcolo offset dinamico
    y_range = df_aggregato[colonna_y].max() - df_aggregato[colonna_y].min()
    offset = y_range * 0.035 

    for i in range(df_aggregato.shape[0]):
        anno = df_aggregato[colonna_label].iloc[i]
        x_val = df_aggregato[colonna_x].iloc[i]
        y_val = df_aggregato[colonna_y].iloc[i]
        
        if anno in anni_covid:
            # --- SOLO CERCHIO ROSSO ---
            # Anche qui usiamo linewidths per sicurezza
            plt.scatter([x_val], [y_val], s=350, facecolors='none', edgecolors='red', linewidths=3.5, zorder=10)
            # Etichetta Rossa
            plt.text(x_val, y_val - (offset), anno, color='#d62728', fontweight='bold', fontsize=12, ha='center', va='top', zorder=11)
        else:
            # --- NORMALITÀ ---
            plt.text(x_val, y_val - offset, anno, color='black', fontsize=10, fontweight='bold', ha='center', va='top', alpha=0.8)

    # Box statistiche
    stats_text = f"Pearson $r$: {r:.3f}\n$p$-value: {p:.3f}"
    plt.text(0.02, 0.95, stats_text, transform=plt.gca().transAxes, fontsize=11,
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.95, edgecolor='#cccccc'))

    # Titoli e Label
    plt.title('Correlazione Volume vs Spesa', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Volume Trasferimenti (Numero Acquisti)', fontsize=13)
    plt.ylabel('Spesa Totale (Miliardi €)', fontsize=13)
    
    # Legenda in basso a destra
    plt.legend(loc='lower right', frameon=True, fontsize=12, facecolor='white', framealpha=1)
    
    plt.tight_layout()
    nomeFile = cartGrafici + 'scatterplot_finale_clean.png'
    plt.savefig(nomeFile)
    plt.show()
    print(f"Grafico salvato: {nomeFile}")

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
    file_name = cartGrafici + 'spese_annuali_istogramma.png'
    plt.savefig(file_name)
    plt.show()
    
    print(f"Grafico salvato con successo come '{file_name}'")

def analizza_efficienza_mercato_clean(df_input):
    """
    Pulisce il dataset, applica i filtri temporali (10/11 - 23/24) 
    e calcola le metriche di efficienza.
    """
    
    # 1. COPIA DI SICUREZZA
    # Qui usiamo df_input che è quello passato alla funzione
    df = df_input.copy()

    # 2. FILTRO TEMPORALE (Range: 10/11 - 23/24)
    stagioni_target = [
        '10/11', '11/12', '12/13', '13/14', '14/15', '15/16', 
        '16/17', '17/18', '18/19', '19/20', '20/21', '21/22', 
        '22/23', '23/24'
    ]
    
    df_periodo = df[df['transfer_season'].isin(stagioni_target)].copy()

    # 3. FILTRO QUALITATIVO (No Parametri Zero)
    n_iniziali = len(df_periodo)
    df_clean = df_periodo[df_periodo['transfer_fee'] > 0].copy()
    n_rimossi = n_iniziali - len(df_clean)
    
    print(f"--- DATA CLEANING REPORT ---")
    print(f"Periodo analizzato: 10/11 -> 23/24")
    print(f"Transazioni totali nel periodo: {n_iniziali}")
    print(f"Rimossi {n_rimossi} trasferimenti a costo zero (Free/Prestiti gratuiti).")
    print(f"Dataset finale: {len(df_clean)} transazioni onerose.")

    # 4. RAGGRUPPAMENTO
    df_agg = df_clean.groupby('transfer_season').agg(
        Valore_Totale_EURO=('market_value_in_eur', 'sum'),
        Spesa_Totale_EUR=('transfer_fee', 'sum'),
        Volume_Trasferimenti=('player_id', 'count')
    ).reset_index()

    # 5. RICALCOLI E METRICHE FINALI
    df_agg.rename(columns={'transfer_season': 'Anno-Calcistico'}, inplace=True)
    
    df_agg['Spesa_Mld_EUR'] = df_agg['Spesa_Totale_EUR'] / 1_000_000_000
    df_agg['Valore_Totale_Mld_EURO'] = df_agg['Valore_Totale_EURO'] / 1_000_000_000
    
    df_agg['Delta_Assoluto'] = df_agg['Spesa_Mld_EUR'] - df_agg['Valore_Totale_Mld_EURO']
    df_agg['Premium_Percentuale'] = (df_agg['Delta_Assoluto'] / df_agg['Valore_Totale_Mld_EURO']) * 100

    # Ordino cronologicamente
    df_agg['Anno-Calcistico'] = pd.Categorical(df_agg['Anno-Calcistico'], categories=stagioni_target, ordered=True)
    df_agg = df_agg.sort_values('Anno-Calcistico')

    return df_agg

# Quando usi la funzione di plottaggio che ti ho dato prima, 
# passagli il risultato di QUESTA funzione qui.

def grafico_trend_spesa_valore(df_spesa):
    """
    GRAFICO 1: Mostra l'andamento temporale di Spesa vs Valore.
    Stampa anche le correlazioni statistiche.
    """
    # Assicuriamoci che i dati siano ordinati
    df_plot = df_spesa.sort_values('Anno-Calcistico').copy()
    
    # Calcolo statistiche "al volo" per stamparle in console
    corr_p, _ = pearsonr(df_plot['Valore_Totale_Mld_EURO'], df_plot['Spesa_Mld_EUR'])
    print(f"--- INSIGHT STATISTICI (GRAFICO TREND) ---")
    print(f"Correlazione Pearson (Prezzo/Valore): {corr_p:.2f}")
    
    # SETUP GRAFICO
    plt.figure(figsize=(14, 7)) # Un bel 16:9 pieno
    
    # Linea Spesa (Effettiva)
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Spesa_Mld_EUR', 
                 marker='o', label='Spesa Effettiva (Prezzo)', color='#E63946', linewidth=3)
    
    # Linea Valore (Teorica)
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Valore_Totale_Mld_EURO', 
                 marker='o', label='Valore Stimato (Fair Value)', color='#1D3557', linestyle='--', linewidth=3)
    
    # RIEMPIMENTO AREE (Inefficienza)
    plt.fill_between(df_plot['Anno-Calcistico'], 
                     df_plot['Valore_Totale_Mld_EURO'], 
                     df_plot['Spesa_Mld_EUR'], 
                     where=(df_plot['Spesa_Mld_EUR'] > df_plot['Valore_Totale_Mld_EURO']),
                     interpolate=True, color='#E63946', alpha=0.15, label='Overspending (Inefficienza)')
    
    plt.fill_between(df_plot['Anno-Calcistico'], 
                     df_plot['Valore_Totale_Mld_EURO'], 
                     df_plot['Spesa_Mld_EUR'], 
                     where=(df_plot['Spesa_Mld_EUR'] <= df_plot['Valore_Totale_Mld_EURO']),
                     interpolate=True, color='#2A9D8F', alpha=0.15, label='Underspending (Risparmio)')

    # Styling Consultant-Level
    plt.title("Prezzo Pagato vs Valore Stimato: L'Evoluzione della Bolla", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("Miliardi di €", fontsize=12, fontweight='bold')
    plt.xlabel("Stagione", fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(fontsize=11, loc='upper left', frameon=True, framealpha=0.9)
    plt.xticks(rotation=45)
    
    plt.tight_layout()

    # Salva il grafico in un file immagine
    file_name = cartGrafici + 'trend_spesa_valore.png'
    plt.savefig(file_name)
    plt.show()
    
    print(f"Grafico salvato con successo come '{file_name}'")

def grafico_premium_inefficienza(df_spesa):
    """
    GRAFICO 2: Focus specifico sulla % di sovrapprezzo (Markup).
    """
    df_plot = df_spesa.sort_values('Anno-Calcistico').copy()
    
    # Calcolo se non esiste
    if 'Premium_Percentuale' not in df_plot.columns:
         df_plot['Delta_Assoluto'] = df_plot['Spesa_Mld_EUR'] - df_plot['Valore_Totale_Mld_EURO']
         df_plot['Premium_Percentuale'] = (df_plot['Delta_Assoluto'] / df_plot['Valore_Totale_Mld_EURO']) * 100

    media_premium = df_plot['Premium_Percentuale'].mean()
    print(f"--- INSIGHT STATISTICI (GRAFICO PREMIUM) ---")
    print(f"Markup Medio applicato dal mercato: {media_premium:.2f}%")
    print("-" * 40)

    # SETUP GRAFICO
    plt.figure(figsize=(14, 7))
    
    # Logica colori semaforica
    colors = []
    for val in df_plot['Premium_Percentuale']:
        if val >= 25: colors.append('#D62828')    # Rosso Scuro (Danger Zone)
        elif val > 0: colors.append('#F77F00')    # Arancione (Inflazione standard)
        else:         colors.append('#2A9D8F')    # Verde (Sottovalutazione)

    # --- FIX CRITICO PER SEABORN ---
    # Ho aggiunto hue='Anno-Calcistico' e legend=False come richiesto dal warning
    # Il resto è identico alla tua logica
    sns.barplot(data=df_plot, x='Anno-Calcistico', y='Premium_Percentuale', 
                hue='Anno-Calcistico', palette=colors, legend=False)
    
    # Linea dello zero (Equilibrio)
    plt.axhline(0, color='black', linewidth=1.5, linestyle='-')
    
    # Etichette sui valori
    for i, v in enumerate(df_plot['Premium_Percentuale']):
        offset = 1.5 if v >= 0 else -3.5
        txt_color = 'black' if abs(v) < 20 else 'black' 
        plt.text(i, v + offset, f"{v:.1f}%", ha='center', va='center', fontweight='bold', fontsize=11, color=txt_color)

    plt.title("Il 'Premium' di Mercato: Quanto si paga in più rispetto al valore reale?", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("% Sovrapprezzo / Sottoprezzo", fontsize=12, fontweight='bold')
    plt.xlabel("Stagione", fontsize=12, fontweight='bold')
    plt.xticks(rotation=45)
    
    # Aggiungo una linea media tratteggiata per dare contesto
    plt.axhline(media_premium, color='gray', linestyle='--', alpha=0.7, label=f'Media Periodo: {media_premium:.1f}%')
    plt.legend(loc='upper right')

    plt.tight_layout()

    # --- IL TUO SALVATAGGIO ---
    # Uso la variabile globale cartGrafici come da tua impostazione
    file_name = cartGrafici + 'percentuali_differenza.png'
    plt.savefig(file_name)
    
    # Mostro il grafico DOPO averlo salvato (ordine corretto per evitare bug grafici)
    plt.show()
    
    print(f"Grafico salvato con successo come '{file_name}'")

# Chiamate varie
trasferimenti_totale = pulisciTrasferimenti(caricaInfo(cartDati + 'transfers.csv'))
# print(trasferimenti_totale.head()) # stampa la testa del DataFrame (testa: prime 5 righe)
# print(trasferimenti_totale.tail()) # stampa la coda del DataFrame (coda: ultime 5 righe)

# PRE: Sistemo i dati
trasferimentiAnnuali = calcoloAnnuali(trasferimenti_totale)
print(trasferimentiAnnuali)
trasferimentiAnnuali = aggiungiSpesaReale(trasferimentiAnnuali)


# GRAFICI
# 1: Istogramma Spese Annuali
istogrammaSpeseAnnuali(trasferimentiAnnuali)

# 2. Grafico Comparativo - Spesa Annuale/Spesa Inflazionata
graficoConfrontoNominaleReale(trasferimentiAnnuali)

# 3. Scatterplot (Analisi Correlazione con Focus COVID)
graficoCorrelazioneVolumeSpesa(trasferimentiAnnuali)

# considerazioni tra Valore effettivo (costo acquisto) e Valore statistico
# VECCHIA: df_analizzato = analizza_efficienza_mercato(analizza_efficienza_mercato_clean(trasferimenti_totale))
transfer_vir_eff = analizza_efficienza_mercato_clean(trasferimenti_totale)
grafico_trend_spesa_valore(transfer_vir_eff)    
grafico_premium_inefficienza(transfer_vir_eff)