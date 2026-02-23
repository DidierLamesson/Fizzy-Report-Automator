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
    "graph1": "#918d84",  # Gris (pour 2025 selon l'image cible)
    "graph2": "#ece8e1",  # Beige (pour 2024 selon l'image cible)
    "white": "#ffffff"
}

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Epilogue', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# Fonction de nettoyage ultra-sécurisée
def clean_val(val):
    if pd.isna(val) or isinstance(val, str):
        return 0.0
    return float(val)

def load_data(file):
    # Lecture de l'onglet 'Dati report'
    df = pd.read_excel(file, sheet_name='Dati report', header=None)
    
    # Récupération du mois en C5 (index 4, 2)
    raw_month = df.iloc[4, 2]
    
    # Formate le mois si c'est une date, sinon prend le texte
    if hasattr(raw_month, 'strftime'):
        formatted_month = raw_month.strftime('%B %Y')
    else:
        formatted_month = str(raw_month)

    # On va chercher les autres valeurs
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

# Fonction pour formater les grands nombres avec des espaces (ex: 500 000)
def human_format(num, pos):
    return f'{int(num):,}'.replace(',', ' ')

def draw_page_1(d, restaurant_name):
    # Création de la figure 10x14 (format vertical type PDF)
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax_bg = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax_bg.axis('off')
    
    # --- HEADER ---
    ax_bg.text(0.05, 0.95, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=18, fontweight='bold')
    ax_bg.text(0.5, 0.90, restaurant_name.upper(), color=COLORS["white"], fontsize=22, ha='center', fontweight='bold')
    ax_bg.text(0.5, 0.87, d["month"], color=COLORS["highlight"], fontsize=14, ha='center')

    # --- GRAPHIQUE FATTURATO (Occupe la moitié haute : de 0.55 à 0.80) ---
    ax_bar = fig.add_axes([0.15, 0.58, 0.7, 0.22], facecolor=COLORS["bg"])
    
    valores = [d["fatturato_n"], d["fatturato_n_1"]]
    couleurs = [COLORS["graph1"], COLORS["graph2"]]
    positions = [0, 1]

    # zorder=3 pour que les barres soient devant la grille (zorder=1 ou 2)
    rects = ax_bar.bar(positions, valores, color=couleurs, width=0.8, zorder=3)

    # Grille horizontale discrète derrière les barres
    ax_bar.yaxis.set_major_formatter(ticker.FuncFormatter(human_format))
    ax_bar.grid(axis='y', color=COLORS["white"], linestyle='-', linewidth=0.5, alpha=0.2, zorder=0)
    
    # Masquer les bordures
    for spine in ax_bar.spines.values():
        spine.set_visible(False)
    
    # Titre et Légende du graphique
    ax_bar.set_title(f"Venduto {restaurant_name.split('-')[0].strip()} {d['month'].split(' ')[0]}\n2025 vs 2024", 
                     color=COLORS["white"], fontsize=16, fontweight='bold', pad=35)
    
    # Valeurs au-dessus des barres
    for rect in rects:
        height = rect.get_height()
        ax_bar.text(rect.get_x() + rect.get_width()/2., height + (max(valores)*0.02),
                    f'{int(height):,}'.replace(',', ' '),
                    ha='center', va='bottom', color=COLORS["white"], fontsize=14, fontweight='bold', zorder=4)

    # --- SECTIONS DU BAS (Alignées sous le graphique) ---
    
    # Section RICAVI - COSTI (Positionnée à 0.40)
    ax_bg.text(0.15, 0.45, "RICAVI - COSTI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    ax_bg.text(0.15, 0.40, f"€ {d['ric_cost_n']:,.0f}".replace(',', ' '), color=COLORS["white"], fontsize=28, fontweight='bold')
    ax_bg.text(0.50, 0.40, f"€ {d['ric_cost_n_1']:,.0f}".replace(',', ' '), color=COLORS["graph1"], fontsize=28, alpha=0.8)

    # Section MARGINE (Positionnée à 0.25)
    ax_bg.text(0.15, 0.28, "MARGINE % SU RICAVI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    ax_bg.text(0.15, 0.20, f"{d['marg_n']}%", color=COLORS["white"], fontsize=50, fontweight='bold')
    ax_bg.text(0.45, 0.20, f"{d['marg_n_1']}%", color=COLORS["graph1"], fontsize=50, alpha=0.8)

    return fig

# --- INTERFACE STREAMLIT ---
st.title("Report mensile Fizzy 📊")

# 1. Barre de saisie du nom (obligatoire)
restaurant_input = st.sidebar.text_input("Nom du Restaurant *", value="", placeholder="Ex: A'RICCIONE - TERRAZZA")

# 2. Upload du fichier
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

# Vérification du nom
if not restaurant_input:
    st.warning("⚠️ Veuillez saisir le nom du restaurant dans la barre latérale pour continuer.")
    st.stop()

if uploaded:
    try:
        data_dict = load_data(uploaded)
        
        # On passe le nom saisi à la fonction de dessin
        fig = draw_page_1(data_dict, restaurant_input)
        st.pyplot(fig)
        
        # Option de téléchargement
        fn = f"rapport_{restaurant_input.replace(' ', '_')}_p1.png"
        fig.savefig(fn, facecolor=COLORS["bg"], bbox_inches='tight', dpi=150)
        with open(fn, "rb") as img:
            st.download_button("📥 Télécharger la Page 1 (Image)", img, file_name=fn, mime="image/png")
            
    except Exception as e:
        st.error(f"Oups ! Une erreur est survenue : {e}")
else:
    st.info(f"✅ Nom configuré : **{restaurant_input}**. Dépose maintenant ton fichier Excel pour générer le rapport.")