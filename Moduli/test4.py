import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Caricamento Dati
try:
    df_transfers = pd.read_csv('..//Dataset//transfers.csv')
    df_clubs = pd.read_csv('..//Dataset//clubs.csv')
except FileNotFoundError as e:
    print(f"Errore critico: {e}. Verifica i percorsi.")
    exit()

# 2. Configurazione
top5_leagues = ['GB1', 'ES1', 'IT1', 'L1', 'FR1']
target_season = '23/24'

league_names = {
    'GB1': 'Premier',
    'ES1': 'Liga',
    'IT1': 'Serie A',
    'L1': 'Bundes',
    'FR1': 'Ligue 1'
}

# --- DEFINIZIONE PALETTE ---
league_colors = {
    'Premier': ('#2c3e50', '#3498db'),   # Blu Notte (Out) vs Blu Elettrico (In)
    'Liga':    ('#e67e22', '#f1c40f'),   # Arancio (Out) vs Giallo (In)
    'Serie A': ('#196f3d', '#2ecc71'),   # Verde Scuro (Out) vs Verde Neon (In)
    'Bundes':  ('#922b21', '#e74c3c'),   # Granata (Out) vs Rosso (In)
    'Ligue 1': ('#4a235a', '#af7ac5')    # Viola Scuro (Out) vs Lilla (In)
}

# 3. Pre-processing
df_transfers = df_transfers[df_transfers['transfer_season'] == target_season].copy()
df_transfers['transfer_fee'] = df_transfers['transfer_fee'].fillna(0)
club_to_league = df_clubs.set_index('club_id')['domestic_competition_id'].to_dict()
df_transfers['league_from'] = df_transfers['from_club_id'].map(club_to_league)
df_transfers['league_to'] = df_transfers['to_club_id'].map(club_to_league)

# 4. Aggregazione Dati
data_points = []

for league_code in top5_leagues:
    league_name = league_names.get(league_code, league_code)
    
    # ACQUISTI
    purchases = df_transfers[df_transfers['league_to'] == league_code]
    data_points.append({
        'League': league_name, 'Type': 'Acquisti',
        'Amount': purchases['transfer_fee'].sum(),
        'Count': len(purchases), 'Color': league_colors[league_name][0]
    })
    
    # CESSIONI
    sales = df_transfers[df_transfers['league_from'] == league_code]
    data_points.append({
        'League': league_name, 'Type': 'Vendite',
        'Amount': sales['transfer_fee'].sum(),
        'Count': len(sales), 'Color': league_colors[league_name][1]
    })

df_plot = pd.DataFrame(data_points)
df_plot['Amount_M'] = df_plot['Amount'] / 1_000_000

# 5. Visualizzazione
plt.figure(figsize=(16, 9)) 
sns.set_style("whitegrid")

# Normalizzazione dimensione bolle
min_c = df_plot['Count'].min()
max_c = df_plot['Count'].max()
def get_size(val):
    return 300 + (val - min_c) / (max_c - min_c) * 1200

# Plotting Loop
for idx, row in df_plot.iterrows():
    plt.scatter(
        x=row['Count'],
        y=row['Amount_M'],
        s=get_size(row['Count']),
        color=row['Color'],
        alpha=0.85, # Leggermente più opaco per contrasto
        edgecolor='white',
        linewidth=1
    )

# Formatting assi
plt.title(f'Top 5 Leghe {target_season}: Volume vs Intensità', fontsize=18, weight='bold', pad=20)
plt.ylabel('Valore Totale (Milioni di €)', fontsize=13)
plt.xlabel('Numero di Movimenti', fontsize=13)
plt.xlim(df_plot['Count'].min() * 0.9, df_plot['Count'].max() * 1.1)
plt.ylim(0, df_plot['Amount_M'].max() * 1.1)

# --- TABELLA LEGENDA A DESTRA ---
cell_text = []
cell_colours = []
row_labels = []

for league in league_names.values():
    row_labels.append(league)
    c_buy = league_colors[league][0]
    c_sell = league_colors[league][1]
    cell_colours.append([c_buy, c_sell])
    cell_text.append(['', ''])

# MODIFICA CHIAVE 1: Aumentiamo lo spazio a destra restringendo il grafico
plt.subplots_adjust(right=0.75) 

# MODIFICA CHIAVE 2: Spostiamo la bounding box più a destra (x=1.3)
the_table = plt.table(
    cellText=cell_text,
    cellColours=cell_colours,
    rowLabels=row_labels,
    colLabels=['Acquisti\n(Spese)', 'Vendite\n(Incassi)'],
    loc='right',
    bbox=[1.1, 0.25, 0.2, 0.6] # [x, y, width, height] -> x aumentato a 1.3
)

the_table.auto_set_font_size(False)
the_table.set_fontsize(11)
the_table.scale(1, 2)

pth_save = "..//Grafici//bolle_final_separated.png"
plt.savefig(pth_save, bbox_inches='tight')
print(f"[CONSULENTE] Grafico corretto e spaziato salvato in: {pth_save}")
plt.show()