import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Epilogue', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84",
    "graph2": "#ece8e1",
    "white": "#ffffff"
}

# Fonction pour éviter les erreurs de texte dans les chiffres
def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def load_data(file):
    # Lecture de l'onglet 'Dati report'
    df = pd.read_excel(file, sheet_name='Dati report', header=None)
    
    # Coordonnées basées sur ton fichier v2
    data = {
        "month": "Novembre 2025", 
        "ca_n": safe_float(df.iloc[8, 1]),
        "ca_n_1": safe_float(df.iloc[9, 1]),
        "diff_ca": round(safe_float(df.iloc[8, 2]) * 100, 1),
        "ric_cost_n": safe_float(df.iloc[12, 1]),
        "ric_cost_n_1": safe_float(df.iloc[13, 1]),
        "marg_n": round(safe_float(df.iloc[16, 1]) * 100, 1),
        "marg_n_1": round(safe_float(df.iloc[17, 1]) * 100, 1),
    }
    return data

def draw_page_1(d):
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    
    # Header
    ax.text(0.05, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=18, fontweight='bold')
    ax.text(0.5, 0.88, "A'RICCIONE - TERRAZZA", color=COLORS["white"], fontsize=22, ha='center', fontweight='bold')
    ax.text(0.5, 0.85, d["month"], color=COLORS["highlight"], fontsize=14, ha='center')

    # Bloc Fatturato
    ax.text(0.05, 0.78, "Fatturato", color=COLORS["accent"], fontsize=18, fontweight='bold')
    
    # Graphique CA
    ax_bar = fig.add_axes([0.1, 0.62, 0.35, 0.12], facecolor=COLORS["bg"])
    ax_bar.bar(["2024", "2025"], [d["ca_n_1"], d["ca_n"]], color=[COLORS["graph1"], COLORS["graph2"]], width=0.5)
    ax_bar.set_frame_on(False)
    ax_bar.tick_params(colors=COLORS["white"])
    ax_bar.get_yaxis().set_visible(False)

    # Chiffres CA
    ax.text(0.55, 0.72, f"{int(d['ca_n']):,} €".replace(',', ' '), color=COLORS["white"], fontsize=30, fontweight='bold')
    ax.text(0.55, 0.68, f"{d['diff_ca']}% vs 2024", color=COLORS["accent"], fontsize=16)

    # Bloc Ricavi - Costi
    ax.text(0.05, 0.50, "Ricavi - Costi", color=COLORS["accent"], fontsize=18, fontweight='bold')
    ax.text(0.05, 0.44, f"€ {int(d['ric_cost_n']):,}".replace(',', ' '), color=COLORS["white"], fontsize=24)
    ax.text(0.35, 0.44, f"€ {int(d['ric_cost_n_1']):,}".replace(',', ' '), color=COLORS["graph1"], fontsize=24)

    # Bloc Margine
    ax.text(0.05, 0.30, "Margine % su ricavi", color=COLORS["accent"], fontsize=18, fontweight='bold')
    ax.text(0.05, 0.22, f"{d['marg_n']}%", color=COLORS["white"], fontsize=45, fontweight='bold')
    ax.text(0.25, 0.22, f"{d['marg_n_1']}%", color=COLORS["graph1"], fontsize=45)

    plt.axis('off')
    return fig

# --- INTERFACE ---
st.title("FIZZY Automator 🥂")
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded:
    try:
        data_dict = load_data(uploaded)
        st.pyplot(draw_page_1(data_dict))
        
        # Petit bouton pour télécharger l'image
        fn = "rapport_p1.png"
        plt.savefig(fn, facecolor=COLORS["bg"])
        with open(fn, "rb") as img:
            st.download_button("Télécharger l'image du rapport", img, file_name=fn, mime="image/png")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
else:
    st.info("En attente du fichier Excel dans la barre latérale.")
