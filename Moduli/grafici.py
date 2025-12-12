import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
import numpy as np
import geopandas as gpd
import urllib.request

# Configurazione stile globale
sns.set_theme(style="darkgrid")
asseX_stagioneCalcistica = "Stagione Calcistica (AA/AA)"
asseY_prezzoMld = "Prezzo (Mld €)"

def visualizza_salva_grafico(fig, path_completo):
    """
    Funzione helper: evito di scrivere sempre lo stesso codice nelle varie funzioni di grafico
    """
    try:
        # tight_layout spesso aiuta a non tagliare etichette
        plt.tight_layout()
        fig.savefig(path_completo)
        print(f"[GRAFICO - SALVATAGGIO] Salvato in: {path_completo}")
        plt.show()
    except Exception as e:
        print(f"[GRAFICO - ERROR] Impossibile salvare il grafico: {e}")

def plot_confronto_nominale_reale(df, cartella_output):
    """
    Funzione:
    - confronto tra spesa reale e spesa inflazionata
    - Area rossa di riempimento (inflazione)
    """
    plt.figure(figsize=(12, 7))
    
    # Linea 1: Spesa Nominale
    sns.lineplot(
        data=df, 
        x='Anno-Calcistico', 
        y='Spesa_Mld_EUR', 
        label='Spesa Nominale (Cifre Ufficiali)', 
        marker='o', color='gray', linestyle='--', alpha=0.6, linewidth=2
    )

    # Linea 2: Spesa Reale
    sns.lineplot(
        data=df, 
        x='Anno-Calcistico', 
        y='Spesa_Reale_Mld_EUR', 
        label='Spesa Reale (Al netto inflazione mercato)', 
        marker='o', color='#ff3333', linewidth=3
    )

    # Area tra le due curve
    plt.fill_between(
        df['Anno-Calcistico'], 
        df['Spesa_Mld_EUR'], 
        df['Spesa_Reale_Mld_EUR'], 
        color='red', alpha=0.1
    )

    # plt.title("L'Illusione della Spesa: Nominale vs Reale (Base 2024)", fontsize=16, fontweight='bold', color='#333') ==> tolgo il titolo (lo metto nelle slide)
    plt.ylabel(asseY_prezzoMld, fontsize=12, fontweight='bold')
    plt.xlabel(asseX_stagioneCalcistica, fontsize=12, fontweight='bold')
    plt.xticks(rotation=45)
    plt.legend()
    
    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'confronto_spesa_nominale_reale.png'))

def correlazione_volume_spesa(df, r, p, cartella_output):
    """
    Funzione:
    - scatterplot correlazione volume trasferimenti - costo annuale
    - identifico valori sfasati e li cerchio
    """
    colonna_x = 'Volume_Trasferimenti'
    colonna_y = 'Spesa_Mld_EUR'
    colonna_label = 'Anno-Calcistico'

    plt.figure(figsize=(12, 7))
    sns.set_style("whitegrid")

    # 1. DISEGNA TUTTO (Base visibile)
    sns.regplot(
        data=df,
        x=colonna_x,
        y=colonna_y,
        scatter_kws={'s': 200, 'alpha': 0.9, 'edgecolor': 'white', 'linewidths': 1.5, 'color': '#2c7bb6'}, 
        line_kws={'color': '#d62728', 'linestyle': '--', 'linewidth': 2.5, 'label': f'Trend Lineare ($R={r:.2f}$)'}
    )

    # 2. EVIDENZIAZIONE SELETTIVA E ETICHETTE
    # anni_covid = ['20/21', '21/22']
    
    # Calcolo offset dinamico basato sul range dei dati
    y_range = df[colonna_y].max() - df[colonna_y].min()
    offset = y_range * 0.035 

    for i in range(df.shape[0]):
        anno = df[colonna_label].iloc[i]
        x_val = df[colonna_x].iloc[i]
        y_val = df[colonna_y].iloc[i]
        plt.text(x_val, y_val - offset, "", color='black', fontsize=10, fontweight='bold', ha='center', va='top', alpha=0.8)

    # plt.title('Correlazione Volume vs Spesa', fontsize=16, fontweight='bold', pad=20) ==> tolgo il titolo (mettere nelle slides)
    plt.xlabel('Volume Trasferimenti (n acquisti)', fontsize=13, fontweight='bold')
    plt.ylabel('Spesa Totale (Mld €)', fontsize=13, fontweight='bold')
    plt.legend(loc='lower right', frameon=True, fontsize=12, facecolor='white', framealpha=1)
    
    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'scatterplot_finale_clean.png'))

def plot_istogramma_spese(df, cartella_output):
    """
    Funzione:
        - istogramma spese annuali: agglomerato spese (considerati tutti i trasferimenti)
    """
    anni = df['Anno-Calcistico']
    spese = df['Spesa_Mld_EUR']

    plt.figure(figsize=(12, 7)) 
    bars = plt.bar(anni, spese, color='skyblue', label='Spesa (Mld EUR)')

    plt.xlabel(asseX_stagioneCalcistica, fontsize=12, fontweight='bold')
    plt.ylabel(asseY_prezzoMld, fontsize=12, fontweight='bold')
    # plt.title('Spesa Annuale per Trasferimenti Calcistici', fontsize=14, fontweight='bold') ==> tolgo il titolo (lo metto nelle slide)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Etichette sopra le barre
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + (spese.max() * 0.01),
            "",
            ha='center', va='bottom', fontsize=9
        )

    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'spese_annuali_istogramma.png'))

def plot_trend_efficienza(df_plot, cartella_output):
    """
    Ripristinato:
    - Doppia fill_between (Rosso per overspending, Verde per underspending)
    - Colori specifici e stili di linea
    """
    plt.figure(figsize=(14, 7))
    
    # Linea Spesa
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Spesa_Mld_EUR', 
                 marker='o', label='Spesa Effettiva (Prezzo)', color='#E63946', linewidth=3)
    
    # Linea Valore
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Valore_Totale_Mld_EURO', 
                 marker='o', label='Valore Stimato (Fair Value)', color='#1D3557', linestyle='--', linewidth=3)
    
    # RIEMPIMENTO AREE (Fondamentale per vedere l'efficienza)
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

    # plt.title("Prezzo Pagato vs Valore Stimato: L'Evoluzione della Bolla", fontsize=16, fontweight='bold', pad=20) ==> tolgo il titolo (mettere nelle slides)
    plt.ylabel(asseY_prezzoMld, fontsize=12, fontweight='bold')
    plt.xlabel(asseX_stagioneCalcistica, fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.legend(fontsize=11, loc='upper left', frameon=True, framealpha=0.9)
    plt.xticks(rotation=45)
    
    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'trend_spesa_valore.png'))

def plot_premium_percentuale(df_plot, cartella_output):
    """
    Funzione:
    - genero istogramma con percentuali di sovrapprezzo/sottoprezzo (caso 21/22)
    """
    media_premium = df_plot['Premium_Percentuale'].mean()
    
    plt.figure(figsize=(14, 7))
    
    # Logica colori
    colors = []
    for val in df_plot['Premium_Percentuale']:
        if val >= 25: colors.append('#D62828')    # Rosso Scuro
        elif val > 0: colors.append('#F77F00')    # Arancione
        else:         colors.append('#2A9D8F')    # Verde

    sns.barplot(data=df_plot, x='Anno-Calcistico', y='Premium_Percentuale', 
                hue='Anno-Calcistico', palette=colors, legend=False)
    
    plt.axhline(0, color='black', linewidth=1.5, linestyle='-')
    
    # Etichette sui valori con offset condizionale
    # for i, v in enumerate(df_plot['Premium_Percentuale']):
    #    offset = 1.5 if v >= 0 else -3.5
    #    txt_color = 'black' 
    #    plt.text(i, v + offset, f"{v:.1f}%", ha='center', va='center', fontweight='bold', fontsize=11, color=txt_color)

    # plt.title("Il 'Premium' di Mercato: Quanto si paga in più rispetto al valore reale?", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("% Sovrapprezzo / Sottoprezzo", fontsize=12, fontweight='bold')
    plt.xlabel(asseX_stagioneCalcistica, fontsize=12, fontweight='bold')
    plt.xticks(rotation=45)
    
    # media 21,5 % di overspending
    print("[NOTA: mettere nelle slides?] Media del 21.5 % di overspending \\ Definizione colori: \\- valori superiori a 21.5%: rosso\\- valori tra 0 e 21.5%: giallo\\-valori sotto lo 0: verde")


    # plt.axhline(media_premium, color='gray', linestyle='--', alpha=0.7, label=f'Media Periodo: {media_premium:.1f}%')
    #plt.legend(loc='upper right')

    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'percentuali_differenza.png'))

# --- AGGIUNGI QUESTA FUNZIONE ALLA FINE DI grafici.py ---
def plot_focus_covid(df_focus, cartella_output):
    """
    Grafico "Microscopio": Zoom estremo con barra di connessione visiva (pulita).
    Rimosse annotazioni testuali per massima chiarezza.
    """
    df_plot = df_focus.sort_values('Anno-Calcistico').copy()

    plt.figure(figsize=(10, 7))

    # --- CALCOLO LIMITI ASSE Y (Zoom Aggressivo) ---
    all_values = pd.concat([df_plot['Spesa_Mld_EUR'], df_plot['Valore_Totale_Mld_EURO']])
    y_min = all_values.min()
    y_max = all_values.max()
    
    # Margine ridotto (2%)
    margin = (y_max - y_min) * 0.02 
    plt.ylim(y_min - margin, y_max + margin)

    # --- LINEE ---
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Spesa_Mld_EUR', 
                 marker='o', markersize=9, 
                 label='Spesa Effettiva', color='#E63946', linewidth=3, zorder=3)
    
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Valore_Totale_Mld_EURO', 
                 marker='D', markersize=7, 
                 label='Valore Stimato', color='#1D3557', linestyle='--', linewidth=2.5, zorder=2)

    # --- RIEMPIMENTO AREE ---
    # Area Rossa
    plt.fill_between(df_plot['Anno-Calcistico'], 
                     df_plot['Valore_Totale_Mld_EURO'], 
                     df_plot['Spesa_Mld_EUR'], 
                     where=(df_plot['Spesa_Mld_EUR'] > df_plot['Valore_Totale_Mld_EURO']),
                     interpolate=True, color='#E63946', alpha=0.15)
    
    # Area VERDE
    plt.fill_between(df_plot['Anno-Calcistico'], 
                     df_plot['Valore_Totale_Mld_EURO'], 
                     df_plot['Spesa_Mld_EUR'], 
                     where=(df_plot['Spesa_Mld_EUR'] <= df_plot['Valore_Totale_Mld_EURO']),
                     interpolate=True, color='#2A9D8F', alpha=0.3, hatch='//')

    # --- BARRA DI CONNESSIONE (SOLO VISIVA) ---
    target_season = '21/22'
    try:
        row_target = df_plot[df_plot['Anno-Calcistico'] == target_season].iloc[0]
        spesa_target = row_target['Spesa_Mld_EUR']
        valore_target = row_target['Valore_Totale_Mld_EURO']
        gap = spesa_target - valore_target

        # Disegniamo la barra solo se c'è un gap visibile, colorandola in base al segno
        if gap < 0:
            colore_barra = '#2A9D8F' # Verde (Underspending)
            label_barra = 'Gap (Risparmio)'
        else:
            colore_barra = '#E63946' # Rosso (Overspending)
            label_barra = 'Gap (Spreco)'

        # Linea verticale pulita senza testo
        plt.vlines(x=target_season, ymin=spesa_target, ymax=valore_target, 
                   colors=colore_barra, linewidth=4, label=label_barra, zorder=4)
                     
    except IndexError:
        pass

    plt.title("MICRO-ANALISI: 21/22 Stagione di Correzione", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Miliardi di € (Zoom Max)", fontsize=11, fontweight='bold')
    plt.xlabel(asseX_stagioneCalcistica, fontsize=11, fontweight='bold')
    plt.grid(True, alpha=0.4, linestyle='--')
    plt.legend(loc='upper left')
    
    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'focus_trend_covid.png'))

def focus_AreaVerde(df_focus, cartella_output):
    """
    grafico:
    - concentrazione riferimento area (spesa < valore) del 21/22
    """
    df_plot = df_focus.sort_values('Anno-Calcistico').copy()

    plt.figure(figsize=(10, 7))

    # --- SETUP ZOOM CHIRURGICO SUL 21/22 ---
    try:
        row_2122 = df_plot[df_plot['Anno-Calcistico'] == '21/22'].iloc[0]
        val_spesa = row_2122['Spesa_Mld_EUR']
        val_valore = row_2122['Valore_Totale_Mld_EURO']
        
        mid_point = (val_spesa + val_valore) / 2
        # Zoom 50x
        plt.ylim(mid_point - 0.15, mid_point + 0.15)
        
    except IndexError:
        print("[ERR] Dati 21/22 non trovati per lo zoom.")
        return

    # --- DISEGNO LINEE PURE ---
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Spesa_Mld_EUR', 
                 marker=None, 
                 label='Spesa (Prezzo)', color='#E63946', linewidth=4, zorder=3)
    
    sns.lineplot(data=df_plot, x='Anno-Calcistico', y='Valore_Totale_Mld_EURO', 
                 marker=None,
                 label='Valore (Fair Value)', color='#1D3557', linestyle='--', linewidth=3, zorder=2)

    # --- AREA VERDE (Con ETICHETTA per la Legenda) ---
    plt.fill_between(df_plot['Anno-Calcistico'], 
                     df_plot['Valore_Totale_Mld_EURO'], 
                     df_plot['Spesa_Mld_EUR'], 
                     where=(df_plot['Spesa_Mld_EUR'] <= df_plot['Valore_Totale_Mld_EURO']),
                     interpolate=True, 
                     color='#2A9D8F', 
                     alpha=0.6, 
                     hatch='////',
                     label='Area di Risparmio (Underspending)') # <--- QUI STA LA MODIFICA

    # Riempimento rosso (Senza etichetta per non affollare, o aggiungila se vuoi)
    plt.fill_between(df_plot['Anno-Calcistico'], 
                     df_plot['Valore_Totale_Mld_EURO'], 
                     df_plot['Spesa_Mld_EUR'], 
                     where=(df_plot['Spesa_Mld_EUR'] > df_plot['Valore_Totale_Mld_EURO']),
                     interpolate=True, color='#E63946', alpha=0.1)

    # plt.title("Focus 'Pura Geometria' 21/22", fontsize=14, fontweight='bold', pad=15) ==> tolgo il titolo (mettere nelle slides)
    plt.xlabel(asseX_stagioneCalcistica, fontsize=12, fontweight='bold')
    plt.ylabel(asseY_prezzoMld, fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # La legenda ora includerà automaticamente l'area verde grazie al parametro 'label' sopra
    plt.legend(loc='upper left', frameon=True, framealpha=0.95)

    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'focus_area_verde_pure.png'))


# Inserisci in grafici.py
# Aggiungi 'import geopandas as gpd' all'inizio del file



def plot_mappa_efficienza(df_geo, cartella_output):
    """
    Genera una Choropleth Map mondiale.
    STILE: PRO (Sfondo scuro/oceano, colori accesi).
    """
    if df_geo.empty:
        return

    # Percorso locale mappa
    map_file_path = os.path.join(cartella_output, "world_map_data.json")
    url_map = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"

    try:
        # Download se manca
        if not os.path.exists(map_file_path):
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url_map, map_file_path)

        # Caricamento
        world = gpd.read_file(map_file_path)
        
        # Merge
        world_data = world.merge(df_geo, how="left", left_on="name", right_on="Country")
        
        # --- STYLING AGGRESSIVO ---
        fig, ax = plt.subplots(1, 1, figsize=(20, 12)) # Formato panoramico
        
        # 1. Colore del Mare (Background dell'asse)
        ax.set_facecolor('#aadaff') # Azzurro tenue professionale
        
        # 2. Disegno i paesi SENZA dati (Grigio scuro per contrasto o Bianco sporco)
        world.plot(ax=ax, color='#f2f4f7', edgecolor='#999999', linewidth=0.5)
        
        # 3. Disegno i dati (Heatmap)
        # cmap='plasma' o 'inferno' sono molto meglio per vedere le differenze
        plot = world_data.dropna(subset=['Avg_Price_Mln']).plot(
            column='Avg_Price_Mln',
            cmap='inferno_r', # Invertito: Scuro = Caro (Miniera), Chiaro = Economico
            linewidth=0.5,
            ax=ax,
            edgecolor='white', # Bordo bianco per far risaltare i paesi colorati
            legend=False # La facciamo a mano che viene meglio
        )
        
        # 4. Colorbar Personalizzata (In basso orizzontale)
        sm = plt.cm.ScalarMappable(cmap='inferno_r', norm=plt.Normalize(
            vmin=world_data['Avg_Price_Mln'].min(), 
            vmax=world_data['Avg_Price_Mln'].max()))
        sm._A = []
        cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.04, aspect=30, orientation='horizontal')
        cbar.set_label('Prezzo Medio Giocatore (Mln €) - [Più scuro = Più Costoso]', fontsize=12, fontweight='bold')

        # 5. Titoli e Annotazioni Pulite
        plt.title("GLOBAL TRANSFER EFFICIENCY\nDove si paga la qualità?", fontsize=24, fontweight='bold', fontfamily='sans-serif', pad=20)
        ax.axis('off') 
        
        # Annotazione "Miniera vs Eurospin" elegante
        plt.figtext(0.15, 0.20, 
            "⚫ SCURO = MINIERA D'ORO (Boutique)\n"
            "🟡 CHIARO = SUPERMERCATO (Volume)", 
            fontsize=14, fontweight='bold', color='#333333',
            bbox={"facecolor":"white", "alpha":0.7, "edgecolor":"none", "pad":10}
        )

        visualizza_salva_grafico(plt, os.path.join(cartella_output, 'mappa_efficienza_globale_v2.png'))
        
    except Exception as e:
        print(f"[GRAFICO - ERROR] {e}")

def plot_distribuzione_eta_valore(df, cartella_output):
    """
    Boxplot: Distribuzione Valore di Mercato per Età (Segmento > 1M€).
    """
    if df.empty:
        print("[WARN] Dataset vuoto dopo i filtri. Impossibile generare grafico.")
        return

    plt.figure(figsize=(16, 9))
    
    # Boxplot
    # Usiamo 'mako' o 'viridis' per un look professionale
    sns.boxplot(
        data=df, 
        x='age', 
        y='Valore_Mln', 
        palette='mako',        
        linewidth=1.2,
        showfliers=True,
        flierprops={"marker": "d", "markerfacecolor": "#555", "markersize": 3, "alpha": 0.5}
    )

    # Titolo parlante: spieghiamo subito cosa stiamo guardando
    plt.title("Valore di Mercato per Età: Il 'Prime' Calcistico (Giocatori > 1M€)", 
              fontsize=20, fontweight='bold', pad=20, color='#333')
    
    plt.xlabel("Età (Anni)", fontsize=14, fontweight='bold')
    plt.ylabel("Valore di Mercato Stimato (Mln €)", fontsize=14, fontweight='bold')
    
    # Griglia per facilitare la lettura dei livelli mediani
    plt.grid(axis='y', linestyle='--', alpha=0.5, which='both')
    
    # Annotazione Strategica (Opzionale, se vuoi fare bella figura)
    # Calcoliamo l'età con la mediana più alta
    peak_age = df.groupby('age')['Valore_Mln'].median().idxmax()
    peak_val = df.groupby('age')['Valore_Mln'].median().max()
    
    print(f"[INSIGHT] L'età di picco per valore mediano è: {peak_age} anni ({peak_val:.2f} Mln €)")

    visualizza_salva_grafico(plt, os.path.join(cartella_output, 'boxplot_eta_valore_elite.png'))
#==== FINE FILE ===#