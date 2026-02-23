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
    # Création de la figure avec la couleur de fond
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    # Axe principal invisible pour le fond
    ax_bg = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax_bg.axis('off')
    
    # --- HEADER GLOBAL ---
    ax_bg.text(0.05, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=18, fontweight='bold')
    ax_bg.text(0.5, 0.88, restaurant_name.upper(), color=COLORS["white"], fontsize=22, ha='center', fontweight='bold')
    ax_bg.text(0.5, 0.85, d["month"], color=COLORS["highlight"], fontsize=14, ha='center')

    # --- NOUVEAU GRAPHIQUE FATTURATO (Style Image Cible) ---
    # On crée un axe plus grand pour le graphique
    ax_bar = fig.add_axes([0.1, 0.55, 0.8, 0.25], facecolor=COLORS["bg"])
    
    # Données et Couleurs inversées pour coller à l'image cible :
    # Barre 1 (gauche) = 2025 (N) en GRIS
    # Barre 2 (droite) = 2024 (N-1) en BEIGE
    valores = [d["fatturato_n"], d["fatturato_n_1"]]
    couleurs = [COLORS["graph1"], COLORS["graph2"]]
    positions = [0, 1]
    labels_legende = ['Fatturato 2025 €', 'Fatturato 2024 €']

    # Création des barres (plus larges pour être proches)
    rects = ax_bar.bar(positions, valores, color=couleurs, width=0.9, edgecolor=COLORS["bg"], linewidth=1)

    # --- MISE EN FORME DU GRAPHIQUE ---
    
    # Titre du graphique
    ax_bar.set_title(f"Venduto {restaurant_name.split('-')[0].strip()} {d['month'].split(' ')[0]}\n2025 vs 2024", 
                     color=COLORS["white"], fontsize=18, fontweight='bold', pad=25)

    # Légende personnalisée au-dessus
    legend_elements = [
        Line2D([0], [0], color=COLORS["graph1"], lw=0, marker='o', markersize=12, label=labels_legende[0]),
        Line2D([0], [0], color=COLORS["graph2"], lw=0, marker='o', markersize=12, label=labels_legende[1])
    ]
    ax_bar.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 1.02), 
                  ncol=2, frameon=False, labelcolor=COLORS["white"], fontsize=12)

    # Axe Y : Visible, formaté et avec grille
    ax_bar.set_ylim(0, max(valores) * 1.2) # Marge au-dessus pour le texte
    ax_bar.yaxis.set_major_formatter(ticker.FuncFormatter(human_format))
    ax_bar.tick_params(axis='y', colors=COLORS["white"], labelsize=12)
    ax_bar.grid(axis='y', color=COLORS["white"], linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Retirer les épines (cadres) sauf celle du bas si on veut
    for spine in ax_bar.spines.values():
        spine.set_visible(False)
    # ax_bar.spines['bottom'].set_visible(True) # Optionnel : garder la ligne du bas

    # Axe X : Un seul label "Terrazza" (ou le nom du resto)
    ax_bar.set_xticks([]) # On cache les ticks par défaut
    # On ajoute le label centré sous le graphique
    ax_bar.text(0.5, -0.1, restaurant_name.split('-')[-1].strip() if '-' in restaurant_name else restaurant_name, 
                transform=ax_bar.transAxes, color=COLORS["white"], fontsize=16, ha='center')

    # --- VALEURS SUR LES BARRES ---
    for rect in rects:
        height = rect.get_height()
        ax_bar.text(rect.get_x() + rect.get_width()/2., height + (max(valores)*0.02),
                    f'{int(height):,}'.replace(',', ' '),
                    ha='center', va='bottom', color=COLORS["white"], fontsize=18, fontweight='bold')

    # --- AUTRES SECTIONS (Plus bas) ---
    # SECTION RICAVI - COSTI
    ax_bg.text(0.05, 0.40, "Ricavi - Costi", color=COLORS["accent"], fontsize=18, fontweight='bold')
    ax_bg.text(0.05, 0.34, f"€ {d['ric_cost_n']:,.0f}".replace(',', ' '), color=COLORS["white"], fontsize=24)
    ax_bg.text(0.35, 0.34, f"€ {d['ric_cost_n_1']:,.0f}".replace(',', ' '), color=COLORS["graph1"], fontsize=24)

    # SECTION MARGINE
    ax_bg.text(0.05, 0.22, "Margine % su ricavi", color=COLORS["accent"], fontsize=18, fontweight='bold')
    ax_bg.text(0.05, 0.14, f"{d['marg_n']}%", color=COLORS["white"], fontsize=45, fontweight='bold')
    ax_bg.text(0.25, 0.14, f"{d['marg_n_1']}%", color=COLORS["graph1"], fontsize=45)

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