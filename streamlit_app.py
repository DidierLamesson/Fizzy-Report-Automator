import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")


COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84",
    "graph2": "#ece8e1",
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
    
    # Si c'est une date Python/Excel, on la formate, sinon on prend le texte tel quel
    if hasattr(raw_month, 'strftime'):
        formatted_month = raw_month.strftime('%B %Y')
    else:
        formatted_month = str(raw_month)

    # On va chercher les autres valeurs
    data = {
        "month": formatted_month, 
        "fatturato_n": clean_val(df.iloc[8, 2]),
        "fatturato_n_1": clean_val(df.iloc[9, 2]),
        "diff_fatturato": round(clean_val(df.iloc[8, 3]) * 100, 1),
        "ric_cost_n": clean_val(df.iloc[12, 2]),
        "ric_cost_n_1": clean_val(df.iloc[13, 2]),
        "marg_n": round(clean_val(df.iloc[16, 2]) * 100, 1),
        "marg_n_1": round(clean_val(df.iloc[17, 2]) * 100, 1),
    }
    return data

def draw_page_1(d):
    # Création de la figure avec la couleur de fond
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    
    # Header
    ax.text(0.05, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=18, fontweight='bold')
    ax.text(0.5, 0.88, "A'RICCIONE - TERRAZZA", color=COLORS["white"], fontsize=22, ha='center', fontweight='bold')
    ax.text(0.5, 0.85, d["month"], color=COLORS["highlight"], fontsize=14, ha='center')

    # --- SECTION FATTURATO ---
    ax.text(0.05, 0.78, "Fatturato", color=COLORS["accent"], fontsize=18, fontweight='bold')
    
    # Graphique CA (Histogramme)
    ax_bar = fig.add_axes([0.1, 0.62, 0.35, 0.12], facecolor=COLORS["bg"])
    ax_bar.bar(["2024", "2025"], [d["ca_n_1"], d["ca_n"]], color=[COLORS["graph1"], COLORS["graph2"]], width=0.5)
    ax_bar.set_frame_on(False)
    ax_bar.tick_params(colors=COLORS["white"], labelsize=10)
    ax_bar.get_yaxis().set_visible(False)

    # Chiffres CA à droite du graphique
    # On utilise :.0f pour éviter les erreurs d'entiers si c'est un NaN
    ax.text(0.55, 0.72, f"{d['fatturato_n']:,.0f} €".replace(',', ' '), color=COLORS["white"], fontsize=30, fontweight='bold')
    ax.text(0.55, 0.68, f"{d['diff_fatturato']}% vs 2024", color=COLORS["accent"], fontsize=16)

    # --- SECTION RICAVI - COSTI ---
    ax.text(0.05, 0.50, "Ricavi - Costi", color=COLORS["accent"], fontsize=18, fontweight='bold')
    ax.text(0.05, 0.44, f"€ {d['ric_cost_n']:,.0f}".replace(',', ' '), color=COLORS["white"], fontsize=24)
    ax.text(0.35, 0.44, f"€ {d['ric_cost_n_1']:,.0f}".replace(',', ' '), color=COLORS["graph1"], fontsize=24)

    # --- SECTION MARGINE ---
    ax.text(0.05, 0.30, "Margine % su ricavi", color=COLORS["accent"], fontsize=18, fontweight='bold')
    ax.text(0.05, 0.22, f"{d['marg_n']}%", color=COLORS["white"], fontsize=45, fontweight='bold')
    ax.text(0.25, 0.22, f"{d['marg_n_1']}%", color=COLORS["graph1"], fontsize=45)

    plt.axis('off')
    return fig

# --- INTERFACE STREAMLIT ---
st.title("FIZZY Automator 🥂")
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded:
    try:
        data_dict = load_data(uploaded)
        fig = draw_page_1(data_dict)
        st.pyplot(fig)
        
        # Option de téléchargement
        fn = "rapport_fizzy_p1.png"
        fig.savefig(fn, facecolor=COLORS["bg"], bbox_inches='tight', dpi=150)
        with open(fn, "rb") as img:
            st.download_button("📥 Télécharger la Page 1 (Image)", img, file_name=fn, mime="image/png")
            
    except Exception as e:
        st.error(f"Oups ! Une erreur est survenue : {e}")
else:
    st.info("👋 Bonjour ! Dépose ton fichier Excel dans la barre de gauche pour générer le rapport.")
