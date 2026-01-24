import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from matplotlib.ticker import FuncFormatter

# --- 1. CARICAMENTO DATI ---
print("1. Caricamento dati...")
try:
    transfers = pd.read_csv('..//Dataset//transfers.csv', usecols=['player_id', 'transfer_season', 'transfer_fee', 'player_name', 'to_club_name'])
    appearances = pd.read_csv('..//Dataset//appearances.csv', usecols=['game_id', 'player_id', 'goals', 'assists', 'minutes_played'])
    games = pd.read_csv('..//Dataset//games.csv', usecols=['game_id', 'season'])
    players = pd.read_csv('..//Dataset//players.csv', usecols=['player_id', 'date_of_birth', 'position']) 
except FileNotFoundError:
    print("Errore: File non trovati.")
    exit()

# --- 2. ELABORAZIONE E FILTRAGGIO ---
print("2. Elaborazione...")

# Unione Performance + Stagione
perf_merged = appearances.merge(games, on='game_id', how='inner')
perf_23_24 = perf_merged[perf_merged['season'] == 2023] # Stagione 23/24

# Aggregazione Stats
player_stats = perf_23_24.groupby('player_id').agg({
    'goals': 'sum',
    'assists': 'sum',
    'minutes_played': 'sum'
}).reset_index()

# Preparazione Trasferimenti
df_transfers = transfers[
    (transfers['transfer_season'] == '23/24') & 
    (transfers['transfer_fee'] > 500000)
].copy()

# Merge con Anagrafica e Filtro ATTACCANTI
df_transfers = df_transfers.merge(players, on='player_id', how='left')

# --- IL FILTRO MAGICO ---
# Teniamo solo chi è classificato come 'Attack'
# (Verifica nel csv se usa 'Attack' o 'Forward', in base al report sembra 'Attack' )
df_attackers = df_transfers[df_transfers['position'] == 'Attack'].copy()

# Calcolo Età
df_attackers['date_of_birth'] = pd.to_datetime(df_attackers['date_of_birth'], errors='coerce')
df_attackers['age'] = 2023 - df_attackers['date_of_birth'].dt.year

# Merge Finale
df_full = df_attackers.merge(player_stats, on='player_id', how='inner')
print(f"   -> Analisi focalizzata su {len(df_full)} attaccanti.")

# --- 3. MODELLO FAIR VALUE (SOLO ATTACCANTI) ---
features = ['goals', 'assists', 'minutes_played', 'age']
target = 'transfer_fee'

model_data = df_full.dropna(subset=features + [target])
model_data = model_data[model_data['minutes_played'] > 500] 

# Log-Transformation
X = model_data[features]
y = np.log(model_data[target])

reg = LinearRegression()
reg.fit(X, y)

model_data['log_predicted_fee'] = reg.predict(X)
model_data['predicted_fee'] = np.exp(model_data['log_predicted_fee'])
model_data['residual'] = model_data['transfer_fee'] - model_data['predicted_fee']
model_data['status'] = np.where(model_data['residual'] > 0, 'Overpaid (Inefficient)', 'Underpaid (Bargain)')

# --- 4. PLOTTING PULITO ---
plt.figure(figsize=(12, 8))
sns.set_style("whitegrid")

sns.scatterplot(
    data=model_data,
    x='predicted_fee',
    y='transfer_fee',
    hue='status', 
    palette={'Overpaid (Inefficient)': '#d64541', 'Underpaid (Bargain)': '#27ae60'},
    alpha=0.6,
    s=70,
    edgecolor=None,
    legend=False # Niente legenda, grafico muto
)

# Linea Fair Value
max_val = max(model_data['predicted_fee'].max(), model_data['transfer_fee'].max())
plt.plot([0, max_val], [0, max_val], color='#34495e', linestyle='--', linewidth=1.5, alpha=0.8)

plt.xscale('log')
plt.yscale('log')

plt.xlabel('Fair Value Stimato (Basato su Gol/Assist/Età)', fontsize=11)
plt.ylabel('Prezzo Reale di Acquisto', fontsize=11)
plt.title('Anatomia del Bomber: Efficienza Mercato Attaccanti 23/24', fontsize=14, fontweight='bold')

def millions(x, pos):
    return '€%1.0fM' % (x * 1e-6)
plt.gca().xaxis.set_major_formatter(FuncFormatter(millions))
plt.gca().yaxis.set_major_formatter(FuncFormatter(millions))

plt.tight_layout()
pth_save = "..//Grafici//reale_vs_fairvalue_FORWARDS"
plt.savefig(pth_save)
print(f"[GRAFICO - SALVATAGGIO] Salvato in: {pth_save}")
plt.show()

# Stampa di controllo per te
print("\n--- TOP 3 OVERPAID (ATTACCANTI) ---")
print(model_data.nlargest(3, 'residual')[['player_name', 'transfer_fee', 'predicted_fee']])
print("\n--- TOP 3 UNDERPAID (ATTACCANTI) ---")
print(model_data.nsmallest(3, 'residual')[['player_name', 'transfer_fee', 'predicted_fee']])