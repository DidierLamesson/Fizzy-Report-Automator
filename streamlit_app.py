import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")

# Correction de l'erreur : l'argument est unsafe_allow_html
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Epilogue', sans-serif !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e3a5f;
        border-radius: 4px 4px 0px 0px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84", # N-1
    "graph2": "#ece8e1", # N
    "white": "#ffffff"
}

# --- FONCTION DE LECTURE EXCEL ---
def load_data(file):
    # Lecture de l'onglet 'Dati report'
    df = pd.read_excel(file, sheet_name='Dati report', header=None)
    
    data = {
        "month": "Novembre 2025", 
        "ca_n": df.iloc[8, 1],
        "ca_n_1": df.iloc[9, 1],
        "diff_ca": round(float(df.iloc[8, 2]) * 100, 1),
        "ric_cost_n": df.iloc[12, 1],
        "ric_cost_n_1": df.iloc[13, 1],
        "marg_n": round(float(df.iloc[16, 1]) * 100, 1),
        "marg_n_1": round(float(df.iloc[17, 1]) * 100, 1),
    }
    
    # Historique Food Cost (Lignes 26 à 31)
    hist = df.iloc[26:32, [0, 4]].copy()
    hist.columns = ['Mese', 'FC']
    hist['FC'] = pd.to_numeric(hist['FC']) * 100
    data['history'] = hist
    data['fc_avg'] = round(float(df.iloc[22, 1]) * 100, 1)
    data['fc_bench'] = round(float(df.iloc[22, 2]) * 100, 1)
    
    return data

# --- FONCTION RENDU VISUEL ---
def draw_page(d, page_type="P1"):
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    
    # Header
    ax.text(0.05, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=18, fontweight='bold')
    
    if page_type == "P1":
        ax.text(0.5, 0.88, "FATTURATO & MARGINI", color=COLORS["white"], fontsize=22, ha='center', fontweight='bold')
        
        # Graphique CA
        ax_bar = fig.add_axes([0.1, 0.65, 0.3, 0.12], facecolor=COLORS["bg"])
        ax_bar.bar(["2024", "2025"], [d["ca_n_1"], d["ca_n"]], color=[COLORS["graph1"], COLORS["graph2"]], width=0.5)
        ax_bar.tick_params(colors=COLORS["white"])
        for s in ax_bar.spines.values(): s.set_visible(False)
        ax_bar.set_yticks([])

        # Chiffres
        ax.text(0.5, 0.72, f"{int(d['ca_n']):,} €".replace(',', ' '), color=COLORS["white"], fontsize=35, fontweight='bold')
        ax.text(0.5, 0.68, f"{d['diff_ca']}% vs 2024", color=COLORS["accent"], fontsize=18)
        
    else: # Page 2
        ax.text(0.5, 0.88, "FOOD & BEVERAGE COST", color=COLORS["white"], fontsize=22, ha='center', fontweight='bold')
        ax_plot = fig.add_axes([0.1, 0.65, 0.8, 0.15], facecolor=COLORS["bg"])
        ax_plot.plot(d['history']['Mese'].astype(str), d['history']['FC'], color=COLORS["graph2"], marker='o', linewidth=3)
        ax_plot.axhline(y=d['fc_bench'], color=COLORS["accent"], linestyle='--', alpha=0.5)
        ax_plot.tick_params(colors=COLORS["white"])
        for s in ax_plot.spines.values(): s.set_visible(False)

    plt.axis('off')
    return fig

# --- INTERFACE ---
st.title("FIZZY Automator 🥂")
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded:
    try:
        data_dict = load_data(uploaded)
        tab1, tab2 = st.tabs(["📊 Page 1: Fatturato", "🍴 Page 2: Food Cost"])
        
        with tab1:
            st.pyplot(draw_page(data_dict, "P1"))
        with tab2:
            st.pyplot(draw_page(data_dict, "P2"))
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
else:
    st.info("👋 Bienvenue ! Veuillez charger votre fichier Excel dans la barre latérale.")
