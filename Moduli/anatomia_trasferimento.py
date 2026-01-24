import os
import sys
import pandas as pd
import numpy as np 
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import gestione_dati as gd
import grafici as gr 

# --- CONFIGURAZIONE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CART_DATI = os.path.join(BASE_DIR, "..", "Dataset")
CART_GRAFICI = os.path.join(BASE_DIR, "..", "Grafici")
FILE_TRASFERIMENTI = os.path.join(CART_DATI, "transfers.csv")
FILE_CLUBS = os.path.join(CART_DATI, "clubs.csv")
FILE_GIOCATORI = os.path.join(CART_DATI, "players.csv")

# ARCO TEMPORALE PROGETTO
STAGIONI_TARGET = [
    '10/11', '11/12', '12/13', '13/14', '14/15', '15/16', 
    '16/17', '17/18', '18/19', '19/20', '20/21', '21/22', 
    '22/23', '23/24'
]

# PREZZI PER CONFRONTO (sia per parametro zero che per valore)
PREZZO_MINIMO = 10000000 # 10 milioni

if not os.path.exists(CART_GRAFICI):
    os.makedirs(CART_GRAFICI)
    print(f"[SETUP] Creata cartella grafici: {CART_GRAFICI}")

# --- CARICAMENTO DATI BASE ---
# Uso nomi più chiari per i DataFrame che saranno passati alle funzioni
df_raw_transfers = gd.carica_dati(FILE_TRASFERIMENTI)
df_clubs = gd.carica_dati(FILE_CLUBS)
df_players = gd.carica_dati(FILE_GIOCATORI)

if df_raw_transfers is None or df_clubs is None or df_players is None:
    sys.exit("Impossibile procedere senza tutti i dati (transfers, clubs, players).")

# --- SEZIONE 1: ANALISI DESCRITTIVA BASE ---

df_clean = gd.pulisci_trasferimenti(df_raw_transfers)

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
df_focus['Anno-Calcistico'] = pd.Categorical(
    df_focus['Anno-Calcistico'], 
    categories=stagioni_focus, 
    ordered=True
)
df_focus = df_focus.sort_values('Anno-Calcistico')


# PER GRAFICO INFLAZIONE
df_inflazione_fix = gd.calcola_inflazione(df_clean, soglia_minima=1000000)
print("\n[VERIFICA DATI PRIMA DEL PLOT - 23/24]")
print(df_inflazione_fix[['Anno-Calcistico', 'Indice_Inflazione', 'Spesa_Mld_EUR', 'Spesa_Reale_Mld_EUR']].tail(1))

# ========================================================
print("--- [GENERAZIONE GRAFICI DESCRITTIVI] ---")

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


print("\n========================================")
print("[EXTRA] ANALISI VALORE GIOCATORI 23/24")
print("========================================")

df_age_clean = gd.prepara_dati_eta_valore(df_players) 
print(f"[GRAFICO 8]:\\Distribuzione Valore per Età")
gr.plot_distribuzione_eta_valore(df_age_clean, CART_GRAFICI) 


# --- FASE 4: Classifica e Grafico Strategico (Correzione per Efficienza Relativa) ---

# 1. Calcolo del Risparmio e Spesa Totale per Lega (Necessario per la Percentuale)
df_risultati = df_modello.copy()

# Colonna che cattura l'underpay (Risparmio) come valore positivo
df_risultati['Risparmio'] = np.where(
    df_risultati['Epsilon_Residuale'] < 0, 
    abs(df_risultati['Epsilon_Residuale']), 
    0
)

# Raggruppa per Lega e calcola le metriche
df_metriche = df_risultati.groupby('league_to').agg(
    Spesa_Totale_Reale=('transfer_fee', 'sum'),
    Risparmio_Totale=('Risparmio', 'sum'),
)

# Calcola l'Efficienza RELATIVA (in percentuale)
# Efficienza Percentuale = (Risparmio Totale / Spesa Totale) * 100
df_metriche['Efficienza_Percentuale'] = (
    df_metriche['Risparmio_Totale'] / df_metriche['Spesa_Totale_Reale']
) * 100


# 2. Classifica Assoluta (Quella che stavi generando)
top_5_assoluti = df_metriche['Risparmio_Totale'].sort_values(ascending=False).head(5)

print("\n--- CLASSIFICA TOP 5 LEGHE PER EFFICIENZA SCOUTING (Risparmio Totale) ---")
print(top_5_assoluti)
print("------------------------------------------")


# 3. Classifica Percentuale (Il vero insight strategico)
top_5_percentuali = df_metriche['Efficienza_Percentuale'].sort_values(ascending=False).head(5)

print("\n--- CLASSIFICA TOP 5 LEGHE PER EFFICIENZA SCOUTING (Percentuale sulla Spesa) ---")
print(top_5_percentuali)
print("------------------------------------------")


# 4. Generazione Grafico (Usiamo la classifica Percentuale)
print("[GRAFICO 9]:\\Classifica Efficienza Scouting (Bar Plot - Percentuale)")
gr.plot_efficienza_scout(top_5_percentuali, CART_GRAFICI)

print("[DONE] Analisi completata - progetto terminato.")