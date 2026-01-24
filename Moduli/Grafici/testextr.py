import os
import pandas as pd

def profile_datasets(folder_path="..//Dataset"):
    """
    Apre tutti i file CSV nella cartella specificata e genera un report di profilazione.
    
    Args:
        folder_path (str): Il percorso della cartella contenente i file CSV.
        
    Returns:
        str: Il report di profilazione completo come singola stringa.
    """
    
    # Inizializza una lista per costruire il report in modo strutturato
    report_lines = []

    # Validazione del percorso
    if not os.path.isdir(folder_path):
        return f"ERRORE: La cartella '{folder_path}' non è stata trovata."

    report_lines.append(f"--- ANALISI DELLA CARTELLA: '{folder_path}' ---")
    
    csv_files_found = False
    
    for filename in os.listdir(folder_path):
        
        if filename.lower().endswith('.csv') and os.path.isfile(os.path.join(folder_path, filename)):
            
            csv_files_found = True
            file_path = os.path.join(folder_path, filename)
            
            # --- Inizio del Blocco di Profilazione (STRUTTURA PULITA) ---
            report_lines.append(f"\n==========================================")
            report_lines.append(f"FILE: {filename}")
            report_lines.append(f"==========================================")
            
            try:
                # Lettura del file
                df = pd.read_csv(file_path)
                
                # Profilazione: 1. Dimensioni
                report_lines.append(f"DIMENSIONI: {df.shape[0]} righe, {df.shape[1]} colonne.")
                
                # Profilazione: 2. Colonne
                report_lines.append(f"COLONNE: {', '.join(df.columns)}")

                # Profilazione: 3. Head (Catturare l'output di head come stringa)
                report_lines.append("\nPRIME 5 RIGHE:")
                report_lines.append(df.head().to_string()) # to_string() converte il DataFrame in un formato di testo pulito
                
                # Profilazione: 4. Info (Catturare l'output di info come stringa)
                report_lines.append("\nPROFILAZIONE DETTAGLIATA (df.info()):")
                
                # df.info() scrive direttamente su stderr. Dobbiamo catturarlo.
                import io
                buffer = io.StringIO()
                df.info(buf=buffer)
                report_lines.append(buffer.getvalue())
                
            except pd.errors.EmptyDataError:
                report_lines.append("ATTENZIONE: Il file è vuoto.")
            except Exception as e:
                report_lines.append(f"ERRORE inatteso durante la lettura del file: {e}")
            
            report_lines.append(f"==========================================")
            # --- Fine del Blocco di Profilazione ---
                
    if not csv_files_found:
        report_lines.append("\nNESSUN file CSV trovato nella cartella specificata.")

    # Unisce tutte le linee in una singola stringa e la restituisce
    return "\n".join(report_lines)

# --- NUOVO BLOCCO DI ESECUZIONE E SCRITTURA ---

# 1. Chiama la funzione per ottenere il report strutturato
report_output = profile_datasets()

# 2. Definisci il percorso del file di output (nella cartella Dataset)
output_folder = "..//Dataset"
output_filename = "dataset_report.txt"
output_path = os.path.join(output_folder, output_filename)

# 3. Assicura che la cartella di output esista
if not os.path.isdir(output_folder):
    # Se la cartella Dataset non esiste, non possiamo scrivere al suo interno.
    print(f"\nIMPOSSIBILE SCRIVERE IL REPORT: La cartella '{output_folder}' non esiste.")
else:
    # 4. Scrive il report sul file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_output)
        
        # 5. Output a console per conferma (Azione Eseguita)
        print("\n" + report_output)
        print(f"\n\n✅ SUCCESSO: Il report di profilazione è stato scritto in: {output_path}")
    except Exception as e:
        print(f"\nERRORE CRITICO DI SCRITTURA: Impossibile scrivere il file di output. Dettaglio: {e}")