import os
import sys
import pandas as pd
# Importiamo i nostri moduli personalizzati
import gestione_dati as gd
import grafici as gr

# --- CONFIGURAZIONE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CART_DATI = os.path.join(BASE_DIR, "..", "Dataset")
CART_GRAFICI = os.path.join(BASE_DIR, "..", "Grafici")
FILE_INPUT = os.path.join(CART_DATI, "transfers.csv")
FILE_CLUBS = os.path.join(CART_DATI, "clubs.csv")
FILE_GIOCATORI = os.path.join(CART_DATI, "players.csv")


# Carica il dataset
df_transfers = gd.carica_dati(FILE_INPUT)

# Unisco le colonne 'from' e 'to' per trovare tutti i club menzionati
all_clubs = pd.concat([df_transfers['from_club_name'], df_transfers['to_club_name']])

# Conto quante volte appare ogni club (proxy per l'importanza/attività)
club_counts = all_clubs.value_counts().reset_index()
club_counts.columns = ['club_name', 'activity_volume']

# Salvo il nuovo file "anagrafico"
output_filename = 'clubs_detected_from_transfers.csv'
club_counts.to_csv(output_filename, index=False)

STAGIONI_TARGET = [
    '10/11', '11/12', '12/13', '13/14', '14/15', '15/16', 
    '16/17', '17/18', '18/19', '19/20', '20/21', '21/22', 
    '22/23', '23/24'
]

if not os.path.exists(CART_GRAFICI):
    os.makedirs(CART_GRAFICI)
    print(f"[SETUP] Creata cartella grafici: {CART_GRAFICI}")

df_raw = gd.carica_dati(FILE_INPUT)
df_clubs = gd.carica_dati(FILE_CLUBS)
if df_raw is None or df_clubs is None:
    sys.exit("Impossibile procedere senza dati.")
    

df_clean = gd.pulisci_trasferimenti(df_raw)

# 3. ELABORAZIONE METRICHE GENERALI
print("--- Elaborazione Metriche Annuali ---")
df_annuale = gd.calcola_metriche_annuali(df_clean)
df_annuale = gd.aggiungi_spesa_reale(df_annuale)

# Calcolo Statistiche
r_pearson, p_value = gd.calcola_correlazione(df_annuale, 'Spesa_Mld_EUR', 'Volume_Trasferimenti')
print(f"[RISULTATI] Correlazione Volume/Spesa -> r: {r_pearson:.2f}, p: {p_value:.4f}")

# 4. ELABORAZIONE EFFICIENZA (PREZZO VS VALORE)
print("--- Elaborazione Efficienza Mercato ---")
# Calcolo su tutto il periodo storico
df_efficienza_full = gd.analizza_efficienza(df_clean, STAGIONI_TARGET)

# === NUOVO STEP: PREPARAZIONE DATI PER IL FOCUS COVID ===
print("--- Preparazione Focus COVID ---")
stagioni_focus = ['18/19', '19/20', '20/21', '21/22', '22/23'] # Finestra 5 anni

# Filtriamo il dataframe completo tenendo solo le righe che sono "isin" (dentro) la nostra lista target
df_focus = df_efficienza_full[df_efficienza_full['Anno-Calcistico'].isin(stagioni_focus)].copy()

# Importante: Ridefiniamo l'ordine categorico solo per queste 5 stagioni
# Altrimenti il grafico potrebbe lasciare spazi vuoti per gli anni mancanti
df_focus['Anno-Calcistico'] = pd.Categorical(
    df_focus['Anno-Calcistico'], 
    categories=stagioni_focus, 
    ordered=True
)
df_focus = df_focus.sort_values('Anno-Calcistico')


# PER GRAFICO INFLAZIONE
df_clean = gd.pulisci_trasferimenti(df_raw)

print("\n--- DEBUG COLONNE ---")
print(df_clean.columns.tolist())
print("---------------------\n")


df_inflazione_fix = gd.calcola_inflazione(df_clean, soglia_minima=1000000)
print("\n[VERIFICA DATI PRIMA DEL PLOT - 23/24]")
print(df_inflazione_fix[['Anno-Calcistico', 'Indice_Inflazione', 'Spesa_Mld_EUR', 'Spesa_Reale_Mld_EUR']].tail(1))
# ========================================================
print("--- [GENERAZIONE GRAFICI] ---")

print("[GRAFICO 1]:\\Istogramma Spese Annuali")
gr.plot_istogramma_spese(df_annuale, CART_GRAFICI)
print("[GRAFICO 2]:\\Confronto valori reali e valore ipotetico inflazione -- \"L'ESPANSIONE INDUSTRIALE DEL CALCIO\"")
gr.plot_confronto_nominale_reale(df_inflazione_fix, CART_GRAFICI)
print("[GRAFICO 3]:\\Grafico correlazione volume - spesa")
gr.correlazione_volume_spesa(df_annuale, r_pearson, p_value, CART_GRAFICI)
print("[GRAFICO 4]:\\Grafico efficienza.")
gr.plot_trend_efficienza(df_efficienza_full, CART_GRAFICI)
print("[GRAFICO 5]:\\Analisi su cosa succede precisamente nel 21/22")
gr.focus_AreaVerde(gd.focusVerde(df_focus), CART_GRAFICI)
print("[GRAFICO 6]:\\Grafico percentuali sovrapprezzo-sottoprezzo")
gr.plot_premium_percentuale(df_efficienza_full, CART_GRAFICI)

print("[GRAFICO 7]:\\Mappa Mondiale Efficienza (Miniera vs Euro Spin)")
# 1. Prepariamo i dati geo
df_geo = gd.prepara_dati_geografici(df_clean, df_clubs)
# 2. Generiamo il grafico (se ci sono dati)
if not df_geo.empty:
    gr.plot_mappa_efficienza(df_geo, CART_GRAFICI)
else:
    print("[WARN] Mappa saltata: controlla la colonna 'league_name' nel CSV.")

print("[DONE] Analisi completata - progetto terminato.")
#==== FINE FILE ===#

def verifica_volumi_mercato(df_raw, soglia_minima=1000000):
    """
    Diagnostica per capire se la linea rossa piatta è corretta.
    Confronta Volume (Quanti giocatori) vs Prezzi (Quanto costano).
    """
    print(f"\n[DIAGNOSTICA] Analisi Mercato sopra {soglia_minima/1e6}M €")
    
    # 1. Filtro base
    df = df_raw[df_raw['transfer_fee'] >= soglia_minima].copy()
    
    # Gestione Anno
    try:
        df['Anno'] = df['transfer_season'].str.slice(0, 2).astype(int) + 2000
    except:
        df['Anno'] = pd.to_numeric(df['transfer_season'].str.slice(0, 2), errors='coerce') + 2000
        
    df = df[df['Anno'].between(2010, 2023)]

    # 2. Aggregazione per capire i driver
    report = df.groupby('transfer_season').agg(
        N_Trasferimenti=('transfer_fee', 'count'),          # VOLUME
        Prezzo_Mediano=('transfer_fee', 'median'),          # PREZZO (Driver Inflazione)
        Spesa_Totale=('transfer_fee', 'sum')                # SPESA NOMINALE
    ).reset_index()
    
    # 3. Calcolo Variazioni rispetto al 2010 (Base 100)
    base_vol = report.iloc[0]['N_Trasferimenti']
    base_price = report.iloc[0]['Prezzo_Mediano']
    base_spend = report.iloc[0]['Spesa_Totale']
    
    report['Crescita_Volume_x'] = report['N_Trasferimenti'] / base_vol
    report['Crescita_Prezzi_x'] = report['Prezzo_Mediano'] / base_price
    report['Crescita_Spesa_x'] = report['Spesa_Totale'] / base_spend
    
    # Formattazione per lettura umana
    report['Spesa_Totale_Mld'] = report['Spesa_Totale'] / 1e9
    report['Prezzo_Mediano_Mln'] = report['Prezzo_Mediano'] / 1e6
    
    # Mostriamo le colonne chiave
    cols = ['transfer_season', 'N_Trasferimenti', 'Crescita_Volume_x', 
            'Prezzo_Mediano_Mln', 'Crescita_Prezzi_x', 
            'Spesa_Totale_Mld', 'Crescita_Spesa_x']
    
    print(report[cols].to_string(index=False))
    return report

# --- ESEGUI QUESTO ---
# Assicurati di passare il df_clean (quello con tutti i dati, non raggruppato)
report_debug = verifica_volumi_mercato(df_clean, soglia_minima=1000000)



# --- INCOLLA QUESTO BLOCCO ALLA FINE DEL FILE ---

print("\n========================================")
print("[EXTRA] ANALISI VALORE GIOCATORI 23/24")
print("========================================")

# 1. Caricamento Dataset Giocatori
df_players = gd.carica_dati(FILE_GIOCATORI)

if df_players is not None:
    # 2. Preparazione Dati (Calcolo età e filtro 2023)
    df_age_clean = gd.prepara_dati_eta_valore(df_players)
    
    # 3. Generazione Grafico
    print(f"[GRAFICO 8]:\\Distribuzione Valore per Età")
    gr.plot_distribuzione_eta_valore(df_age_clean, CART_GRAFICI)
else:
    print("[ERROR] File players.csv non trovato o illeggibile.")

