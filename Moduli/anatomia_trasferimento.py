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

STAGIONI_TARGET = [
    '10/11', '11/12', '12/13', '13/14', '14/15', '15/16', 
    '16/17', '17/18', '18/19', '19/20', '20/21', '21/22', 
    '22/23', '23/24'
]

if not os.path.exists(CART_GRAFICI):
    os.makedirs(CART_GRAFICI)
    print(f"[SETUP] Creata cartella grafici: {CART_GRAFICI}")

df_raw = gd.carica_dati(FILE_INPUT)
if df_raw is None:
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

# ========================================================
print("--- Generazione Grafici ---")
print("[GRAFICO]: Istogramma Spese Annuali")
gr.plot_istogramma_spese(df_annuale, CART_GRAFICI)
print("[GRAFICO]: Confronto valori reali e valore ipotetico inflazione")
gr.plot_confronto_nominale_reale(df_annuale, CART_GRAFICI)
print("[GRAFICO]: Grafico correlazione volume - spesa")
gr.plot_scatter_volume_spesa(df_annuale, r_pearson, p_value, CART_GRAFICI)
print("[GRAFICO]: Grafico efficienza.")
gr.plot_trend_efficienza(df_efficienza_full, CART_GRAFICI)
print("[GRAFICO]: Grafico Area Verde Pura per anno calcistico 21/22.")
gr.focus_AreaVerde(gd.focusVerde(df_focus), CART_GRAFICI)
print("[GRAFICO]: Grafico efficienza con percentuali.")
gr.plot_premium_percentuale(df_efficienza_full, CART_GRAFICI)

print("[DONE] Analisi completata.")
#==== FINE FILE ===#