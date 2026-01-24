import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from matplotlib.ticker import FuncFormatter

# --- 1. CARICAMENTO E PREPARAZIONE (Solo Attaccanti) ---
print("1. Caricamento dati e filtro Attaccanti...")

try:
    # Carichiamo anche market_value_in_eur dai trasferimenti
    transfers = pd.read_csv('..//Dataset//transfers.csv', 
                            usecols=['player_id', 'transfer_season', 'transfer_fee', 'market_value_in_eur', 'player_name', 'to_club_name'])
    appearances = pd.read_csv('..//Dataset//appearances.csv', usecols=['game_id', 'player_id', 'goals', 'assists', 'minutes_played'])
    games = pd.read_csv('..//Dataset//games.csv', usecols=['game_id', 'season'])
    players = pd.read_csv('..//Dataset//players.csv', usecols=['player_id', 'date_of_birth', 'position'])
except FileNotFoundError:
    print("Errore: File non trovati.")
    exit()

# Unione Performance
perf_merged = appearances.merge(games, on='game_id', how='inner')
perf_23_24 = perf_merged[perf_merged['season'] == 2023] # Stagione 23/24

player_stats = perf_23_24.groupby('player_id').agg({
    'goals': 'sum', 'assists': 'sum', 'minutes_played': 'sum'
}).reset_index()

# Filtro Trasferimenti (Stagione 23/24, Fee > 500k, Market Value esistente)
df_transfers = transfers[
    (transfers['transfer_season'] == '23/24') & 
    (transfers['transfer_fee'] > 500000) &
    (transfers['market_value_in_eur'].notna()) &
    (transfers['market_value_in_eur'] > 0)
].copy()

df_transfers = df_transfers.merge(players, on='player_id', how='left')

# FILTRO ATTACCANTI
df_attackers = df_transfers[df_transfers['position'] == 'Attack'].copy()

# Età
df_attackers['date_of_birth'] = pd.to_datetime(df_attackers['date_of_birth'], errors='coerce')
df_attackers['age'] = 2023 - df_attackers['date_of_birth'].dt.year

# Merge Finale
df_full = df_attackers.merge(player_stats, on='player_id', how='inner')

# --- 2. CALCOLO PREZZO FAIR VALUE (IL TUO MODELLO) ---
features = ['goals', 'assists', 'minutes_played', 'age']
target = 'transfer_fee'

model_data = df_full.dropna(subset=features + [target, 'market_value_in_eur'])
model_data = model_data[model_data['minutes_played'] > 500] 

# Regressione
X = model_data[features]
y = np.log(model_data[target])
reg = LinearRegression()
reg.fit(X, y)

model_data['predicted_fair_value'] = np.exp(reg.predict(X))

# --- 3. ANALISI DI CORRELAZIONE (Statistica Pura) ---
print("\n--- MATRICE DI CORRELAZIONE (PEARSON) ---")
corr_matrix = model_data[['transfer_fee', 'market_value_in_eur', 'predicted_fair_value']].corr()
print(corr_matrix)

# Heatmap della correlazione (Opzionale, utile per il report)
plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", vmin=0, vmax=1)
plt.title('Correlazione: Prezzo Reale vs Hype vs Performance')
plt.tight_layout()
plt.show()

# --- 4. GRAFICO "TRIPLA VERITÀ" ---
# X: Transfermarkt (Hype)
# Y: Prezzo Reale (Realtà)
# Colore: Fair Value (Sostanza Tecnica)

plt.figure(figsize=(12, 8))
sns.set_style("whitegrid")

# Scatterplot
points = plt.scatter(
    x=model_data['market_value_in_eur'],
    y=model_data['transfer_fee'],
    c=np.log(model_data['predicted_fair_value']), # Colore basato sul valore tecnico (log per scala)
    cmap='viridis',
    s=80,
    alpha=0.7,
    edgecolors='k'
)

# Linea x=y (Dove Prezzo Reale = Prezzo Transfermarkt)
max_val = max(model_data['market_value_in_eur'].max(), model_data['transfer_fee'].max())
plt.plot([0, max_val], [0, max_val], 'r--', label='Prezzo = Transfermarkt Est.')

plt.xscale('log')
plt.yscale('log')
plt.xlabel('Valore Stimato da Transfermarkt (€)', fontsize=11)
plt.ylabel('Prezzo Reale di Acquisto (€)', fontsize=11)
plt.title('Il Triangolo della Verità: Hype (X) vs Prezzo (Y) vs Performance (Colore)', fontsize=14, fontweight='bold')

# Colorbar
cbar = plt.colorbar(points)
cbar.set_label('Intensità Fair Value (Performance Tecnica)', rotation=270, labelpad=15)

# Formattazione Assi
def millions(x, pos):
    return '€%1.0fM' % (x * 1e-6)
plt.gca().xaxis.set_major_formatter(FuncFormatter(millions))
plt.gca().yaxis.set_major_formatter(FuncFormatter(millions))

plt.legend()
plt.tight_layout()
pth_save = "..//Grafici//correlazione_triangolare"
plt.savefig(pth_save)
print(f"[GRAFICO - SALVATAGGIO] Salvato in: {pth_save}")
plt.show()