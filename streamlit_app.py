import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
import numpy as np

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")

COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84",  # Gris (2025)
    "graph2": "#ece8e1",  # Beige (2024)
    "white": "#ffffff"
}

# Injection de la police Epilogue
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Epilogue', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS DATA (Gardées selon votre demande) ---
def clean_val(val):
    if pd.isna(val) or isinstance(val, str):
        return 0.0
    return float(val)

def load_data(file):
    df = pd.read_excel(file, sheet_name='Dati report', header=None)
    raw_month = df.iloc[4, 2]
    if hasattr(raw_month, 'strftime'):
        formatted_month = raw_month.strftime('%B %Y')
    else:
        formatted_month = str(raw_month)

    data = {
        "month": formatted_month, 
        "fatturato_n": clean_val(df.iloc[8, 2]),    # N = 2025
        "fatturato_n_1": clean_val(df.iloc[9, 2]),  # N-1 = 2024
        "diff_fatturato": round(clean_val(df.iloc[8, 3]) * 100, 1),
        "ric_cost_n": clean_val(df.iloc[12, 2]),
        "ric_cost_n_1": clean_val(df.iloc[13, 2]),
        "marg_n": round(clean_val(df.iloc[16, 2]) * 100, 1),
        "marg_n_1": round(clean_val(df.iloc[17, 2]) * 100, 1),
    }
    return data

def human_format(num, pos):
    return f'{int(num):,}'.replace(',', ' ')

# --- FONCTION DE DESSIN (Structure Zones A, B, C, D) ---
def draw_full_report(d, restaurant_name):
    # Création du Canva A4 vertical
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax_main = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax_main.axis('off')

    # --- ZONE A : HEADER ---
    # Logo textuel
    ax_main.text(0.5, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=16, fontweight='bold', ha='center', linespacing=0.9)
    
    # Titre principal 
    ax_main.text(0.5, 0.89, "Report Mensile", color=COLORS["white"], fontsize=32, ha='center', fontfamily='serif', fontstyle='italic')
    
    # Sous-titre dynamique
    ax_main.text(0.5, 0.86, f"{restaurant_name.upper()}", color=COLORS["white"], fontsize=16, ha='center', fontweight='light')
    
    # Date du rapport
    ax_main.text(0.5, 0.84, d["month"].upper(), color=COLORS["highlight"], fontsize=12, ha='center')

    # --- ZONE B : GRAPHIQUE COMPARATIF (y: 0.55 à 0.80) ---
    # Placement précis du graphique dans sa boîte
    ax_bar = fig.add_axes([0.1, 0.4, 0.35, 0.20], facecolor=COLORS["bg"])
    
    valores = [d["fatturato_n"], d["fatturato_n_1"]]
    positions = [0, 1]
    
    # Dessin des barres (zorder=3 pour couvrir la grille)
    rects = ax_bar.bar(positions, valores, color=[COLORS["graph1"], COLORS["graph2"]], width=0.8, zorder=3)

    # Grille et formatage Axe Y
    ax_bar.yaxis.set_major_formatter(ticker.FuncFormatter(human_format))
    ax_bar.grid(axis='y', color=COLORS["white"], linestyle='-', linewidth=0.5, alpha=0.2, zorder=0)
    ax_bar.tick_params(axis='y', colors=COLORS["white"], labelsize=10)
    
    # Nettoyage des bordures
    for spine in ax_bar.spines.values():
        spine.set_visible(False)
    ax_bar.set_xticks([]) # On enlève les graduations X

    # Titre interne au graph
    nom_court = restaurant_name.split('-')[0].strip()
    mois_court = d['month'].split(' ')[0]
    ax_bar.text(0.5, 1.25, f"Venduto {nom_court} {mois_court}", transform=ax_bar.transAxes, 
                color=COLORS["white"], fontsize=18, fontweight='bold', ha='center')
    ax_bar.text(0.5, 1.15, "2025 vs 2024", transform=ax_bar.transAxes, 
                color=COLORS["white"], fontsize=14, ha='center')

    # Valeurs au-dessus des barres
    for rect in rects:
        h = rect.get_height()
        ax_bar.text(rect.get_x() + rect.get_width()/2., h + (max(valores)*0.02),
                    f'{int(h):,}'.replace(',', ' '),
                    ha='center', va='bottom', color=COLORS["white"], fontsize=14, fontweight='bold', zorder=4)

    # Label sous le graphique
    label_x = restaurant_name.split('-')[-1].strip() if '-' in restaurant_name else "Totale"
    ax_bar.text(0.5, -0.1, label_x, transform=ax_bar.transAxes, color=COLORS["white"], fontsize=12, ha='center')

    # --- ZONE C : PERFORMANCE FINANCIÈRE (y: 0.35 à 0.50) ---
    ax_main.text(0.1, 0.48, "RICAVI - COSTI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    
    # Chiffres côte à côte
    ax_main.text(0.1, 0.42, f"€ {d['ric_cost_n']:,.0f}".replace(',', ' '), color=COLORS["white"], fontsize=28, fontweight='bold')
    ax_main.text(0.40, 0.42, f"€ {d['ric_cost_n_1']:,.0f}".replace(',', ' '), color=COLORS["graph1"], fontsize=28)
    
    # Bloc texte (Analyse narrative)
    analysis = "Oltre alla crescita dei ricavi, si osserva una marcata variazione del\nrisultato economico: con un conseguente miglioramento significativo dei margini."
    ax_main.text(0.1, 0.36, analysis, color=COLORS["white"], fontsize=10, linespacing=1.6, alpha=0.9)

    # --- ZONE D : ANALYSE DES MARGES (y: 0.10 à 0.30) ---
    ax_main.text(0.1, 0.28, "MARGINE % SU RICAVI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    
    # Pourcentages impactants
    ax_main.text(0.1, 0.18, f"{d['marg_n']}%", color=COLORS["white"], fontsize=55, fontweight='bold')
    ax_main.text(0.35, 0.18, f"{d['marg_n_1']}%", color=COLORS["graph1"], fontsize=55, alpha=0.7)
    
    ax_main.text(0.35, 0.14, "vs 2024", color=COLORS["highlight"], fontsize=10)

    return fig

# --- INTERFACE STREAMLIT ---
st.title("FIZZY Automator 🥂")

restaurant_input = st.sidebar.text_input("Nom du Restaurant *", value="", placeholder="Ex: A'RICCIONE - TERRAZZA")
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if not restaurant_input:
    st.warning("⚠️ Veuillez saisir le nom du restaurant dans la barre latérale.")
    st.stop()

if uploaded:
    try:
        data_dict = load_data(uploaded)
        fig = draw_full_report(data_dict, restaurant_input)
        st.pyplot(fig)
        
        # Téléchargement
        fn = f"Rapport_{restaurant_input.replace(' ', '_')}.png"
        fig.savefig(fn, facecolor=COLORS["bg"], bbox_inches='tight', dpi=200)
        with open(fn, "rb") as img:
            st.sidebar.download_button("📥 Télécharger le Rapport", img, file_name=fn, mime="image/png")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
else:
    st.info("👋 En attente du fichier Excel.")