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

def main():
    # 1. SETUP AMBIENTE
    if not os.path.exists(CART_GRAFICI):
        os.makedirs(CART_GRAFICI)
        print(f"[SETUP] Creata cartella grafici: {CART_GRAFICI}")

    # 2. CARICAMENTO E PULIZIA
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
    print(f"Correlazione Volume/Spesa -> r: {r_pearson:.2f}, p: {p_value:.4f}")

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


    # 5. GENERAZIONE GRAFICI
    print("--- Generazione Grafici ---")
    
    # Grafici Generali
    gr.plot_istogramma_spese(df_annuale, CART_GRAFICI)
    gr.plot_confronto_nominale_reale(df_annuale, CART_GRAFICI)
    gr.plot_scatter_volume_spesa(df_annuale, r_pearson, p_value, CART_GRAFICI)
    
    # Grafici Efficienza Storici
    gr.plot_trend_efficienza(df_efficienza_full, CART_GRAFICI)
    gr.plot_premium_percentuale(df_efficienza_full, CART_GRAFICI)
    
    # === NUOVA CHIAMATA AL GRAFICO DI FOCUS ===
    # === AGGIORNAMENTO NEL MAIN ===
    print("--- Preparazione Focus COVID (Macro-Zoom 3 Anni) ---")
    
    # STRINGIAMO I DENTI: Solo il triennio della verità
    stagioni_focus = ['20/21', '21/22', '22/23'] 
    
    # Filtro dati
    df_focus = df_efficienza_full[df_efficienza_full['Anno-Calcistico'].isin(stagioni_focus)].copy()
    
    # Ordine categorico per evitare buchi
    df_focus['Anno-Calcistico'] = pd.Categorical(
        df_focus['Anno-Calcistico'], 
        categories=stagioni_focus, 
        ordered=True
    )
    df_focus = df_focus.sort_values('Anno-Calcistico')
    gr.plot_focus_covid(df_focus, CART_GRAFICI)
    # ==========================================

    # === NUOVA CHIAMATA: FOCUS SINGOLA STAGIONE ===
    print("--- Generazione Focus Singolo 21/22 ---")
    
    # Non serve ricreare tutto, basta filtrare df_focus o df_efficienza_full
    df_2122 = df_efficienza_full[df_efficienza_full['Anno-Calcistico'] == '21/22']
    
    if not df_2122.empty:
        gr.plot_focus_2122_head_to_head(df_2122, CART_GRAFICI)
    else:
        print("[WARN] Dati 21/22 non trovati per il focus singolo.")

    # === NUOVA CHIAMATA: GRAFICO PURO ===
    print("--- Generazione Grafico Area Verde Pura ---")
    gr.plot_pure_green_area(df_focus, CART_GRAFICI) # Usa df_focus (il triennio)

    print("[DONE] Analisi completata.")

if __name__ == "__main__":
    main()