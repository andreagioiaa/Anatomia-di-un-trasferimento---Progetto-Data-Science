import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from matplotlib.ticker import FuncFormatter

# --- 1. CARICAMENTO DATI ---
print("1. Caricamento dati...")

try:
    transfers = pd.read_csv(
        '..//Dataset//transfers.csv',
        usecols=['player_id', 'transfer_season', 'transfer_fee', 'player_name', 'to_club_name', 'transfer_date']
    )

    appearances = pd.read_csv(
        '..//Dataset//appearances.csv',
        usecols=['game_id', 'player_id', 'goals', 'assists', 'minutes_played']
    )

    games = pd.read_csv(
        '..//Dataset//games.csv',
        usecols=['game_id', 'season']
    )

    players = pd.read_csv(
        '..//Dataset//players.csv',
        usecols=['player_id', 'date_of_birth', 'position']
    )
except FileNotFoundError as e:
    print(f"ERRORE CRITICO: Non trovo i file. Controlla il percorso.\nDettaglio: {e}")
    exit()

# --- 2. ELABORAZIONE PERFORMANCE ---
print("2. Elaborazione statistiche giocatori (Stagione 2023)...")

perf_merged = appearances.merge(games, on='game_id', how='inner')
perf_23_24 = perf_merged[perf_merged['season'] == 2023]

player_stats = perf_23_24.groupby('player_id').agg({
    'goals': 'sum',
    'assists': 'sum',
    'minutes_played': 'sum'
}).reset_index()

print(f"   -> Stats calcolate per {len(player_stats)} giocatori totali.")

# --- 3. PREPARAZIONE DATASET TRASFERIMENTI & FILTRO RUOLO ---
print("3. Preparazione dataset e FILTRO ATTACCANTI...")

df_transfers = transfers[
    (transfers['transfer_season'] == '23/24') & 
    (transfers['transfer_fee'] > 500000)
].copy()

# Aggiungiamo dati anagrafici (incluso il ruolo 'position')
df_transfers = df_transfers.merge(players, on='player_id', how='left')

# --- MODIFICA CHIAVE: FILTRO SOLO ATTACCANTI ---
# Definiamo i ruoli che consideriamo "Attaccanti". 
# Se nel tuo CSV c'è solo la macro-categoria 'Attack', il codice funzionerà comunque.
ruoli_attacco = ['Attack', 'Centre-Forward', 'Second Striker', 'Left Winger', 'Right Winger']

# Filtriamo: teniamo solo se la colonna 'position' è in quella lista
df_transfers = df_transfers[df_transfers['position'].isin(ruoli_attacco)]

print(f"   -> Giocatori filtrati (Solo Attaccanti): {len(df_transfers)}")
# -----------------------------------------------

# Calcolo Età approssimata nel 2023
df_transfers['date_of_birth'] = pd.to_datetime(df_transfers['date_of_birth'], errors='coerce')
df_transfers['age'] = 2023 - df_transfers['date_of_birth'].dt.year

# --- 4. MERGE FINALE ---
print("4. Creazione Master Dataset (Moneyball - Attackers Only)...")

df_full = df_transfers.merge(player_stats, on='player_id', how='inner')
print(f"   -> Righe totali da analizzare: {len(df_full)}")

# --- 5. MODELLO FAIR VALUE ---
print("5. Training Modello di Regressione (Specifico per Attaccanti)...")

features = ['goals', 'assists', 'minutes_played', 'age']
target = 'transfer_fee'

model_data = df_full.dropna(subset=features + [target])
model_data = model_data[model_data['minutes_played'] > 500] 

if len(model_data) < 5:
    print("ERRORE: Troppi pochi attaccanti trovati per l'analisi.")
    exit()

X = model_data[features]
y = np.log(model_data[target])

reg = LinearRegression()
reg.fit(X, y)

model_data['log_predicted_fee'] = reg.predict(X)
model_data['predicted_fee'] = np.exp(model_data['log_predicted_fee']) 
model_data['residual'] = model_data['transfer_fee'] - model_data['predicted_fee']
model_data['status'] = np.where(model_data['residual'] > 0, 'Overpaid', 'Value Deal') # Semplificato le label

# --- 6. PLOTTING ---
print("6. Generazione Grafico Attaccanti...")

plt.figure(figsize=(12, 8))
sns.set_style("whitegrid")

# Scatterplot
sns.scatterplot(
    data=model_data,
    x='predicted_fee',
    y='transfer_fee',
    hue='status', 
    palette={'Overpaid': '#d64541', 'Value Deal': '#27ae60'}, # Rosso vs Verde
    alpha=0.7, 
    s=80,      
    edgecolor='w', # Ho aggiunto un bordino bianco per far risaltare i punti
    linewidth=0.5,
    legend=True # Ho riattivato la legenda perché per un case study specifico è utile vedere cosa è cosa
)

# Linea Fair Value
max_val = max(model_data['predicted_fee'].max(), model_data['transfer_fee'].max())
plt.plot([0, max_val], [0, max_val], color='black', linestyle='--', linewidth=1.5, alpha=0.8, label='Fair Value')

# Assi Logaritmici
plt.xscale('log')
plt.yscale('log')

# Titolo esplicito per il Case Study
plt.title('Attaccanti 23/24: Reale vs Fair Value (Basato su Gol/Assist)', fontsize=14, fontweight='bold')

plt.xlabel('Valore Stimato (Performance Statistica)', fontsize=11)
plt.ylabel('Prezzo Reale di Trasferimento', fontsize=11)

def millions(x, pos):
    return '€%1.0fM' % (x * 1e-6)
plt.gca().xaxis.set_major_formatter(FuncFormatter(millions))
plt.gca().yaxis.set_major_formatter(FuncFormatter(millions))

plt.legend(title='Status Trasferimento')
plt.tight_layout()

# Salvataggio con nome specifico
pth_save = "..//Grafici//attaccanti_fair_value.png"
plt.savefig(pth_save)
print(f"[GRAFICO - SALVATAGGIO] Salvato in: {pth_save}")
plt.show()