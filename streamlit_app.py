import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION & STYLE ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")

# Injection CSS pour les polices et le centrage
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@300;400;700&family=Playfair+Display:ital,wght@0,700;1,700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Epilogue', sans-serif; 
        background-color: #172e4d;
    }
    
    /* Style pour simuler Ivy Presto (Serif élégant) */
    .report-title {
        font-family: 'Playfair Display', serif;
        font-size: 42px;
        color: #ffffff;
        text-align: center;
        margin-top: -20px;
    }
    
    .logo-container {
        text-align: center;
        color: #ffffff;
        font-family: 'Epilogue', sans-serif;
        font-weight: bold;
        line-height: 0.9;
        margin-bottom: 10px;
    }
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

def clean_val(val):
    if pd.isna(val) or isinstance(val, str): return 0.0
    return float(val)

def load_data(file):
    df = pd.read_excel(file, sheet_name='Dati report', header=None)
    data = {
        "month": "Novembre 2025", 
        "ca_n": clean_val(df.iloc[8, 1]),
        "ca_n_1": clean_val(df.iloc[9, 1]),
        "diff_ca": round(clean_val(df.iloc[8, 2]) * 100, 1),
        "ric_cost_n": clean_val(df.iloc[12, 1]),
        "ric_cost_n_1": clean_val(df.iloc[13, 1]),
        "marg_n": round(clean_val(df.iloc[16, 1]) * 100, 1),
        "marg_n_1": round(clean_val(df.iloc[17, 1]) * 100, 1),
    }
    return data

def draw_page_1(d):
    # Format 10x14 pour un aspect PDF vertical
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    
    # --- LOGO ET TITRE (Centrés graphiquement) ---
    ax.text(0.5, 0.93, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=22, fontweight='bold', ha='center', linespacing=0.9)
    ax.text(0.5, 0.88, "Report Mensile", color=COLORS["white"], fontsize=32, ha='center', fontfamily='serif', fontstyle='italic')
    
    # Ligne de séparation élégante
    ax.plot([0.3, 0.7], [0.86, 0.86], color=COLORS["accent"], linewidth=1, alpha=0.5)
    
    ax.text(0.5, 0.83, "A'RICCIONE - TERRAZZA", color=COLORS["white"], fontsize=18, ha='center', fontweight='light')
    ax.text(0.5, 0.81, d["month"].upper(), color=COLORS["highlight"], fontsize=12, ha='center', letterspacing=2)

    # --- SECTION FATTURATO ---
    ax.text(0.1, 0.74, "FATTURATO", color=COLORS["accent"], fontsize=16, fontweight='bold')
    
    # Graphique CA décalé à gauche
    ax_bar = fig.add_axes([0.1, 0.58, 0.3, 0.12], facecolor=COLORS["bg"])
    ax_bar.bar(["2024", "2025"], [d["ca_n_1"], d["ca_n"]], color=[COLORS["graph1"], COLORS["graph2"]], width=0.5)
    ax_bar.set_frame_on(False)
    ax_bar.tick_params(colors=COLORS["white"], labelsize=10)
    ax_bar.get_yaxis().set_visible(False)

    # Valeur CA à droite
    ax.text(0.5, 0.68, f"{d['ca_n']:,.0f} €".replace(',', '.'), color=COLORS["white"], fontsize=38, fontweight='bold')
    ax.text(0.5, 0.64, f"{d['diff_ca']}% vs 2024", color=COLORS["accent"], fontsize=18)

    # --- SECTION RICAVI - COSTI ---
    ax.text(0.1, 0.48, "RICAVI - COSTI", color=COLORS["accent"], fontsize=16, fontweight='bold')
    ax.text(0.1, 0.42, f"€ {d['ric_cost_n']:,.0f}".replace(',', '.'), color=COLORS["white"], fontsize=28)
    ax.text(0.45, 0.42, f"€ {d['ric_cost_n_1']:,.0f}".replace(',', '.'), color=COLORS["graph1"], fontsize=28, alpha=0.7)

    # --- SECTION MARGINE ---
    ax.text(0.1, 0.30, "MARGINE % SU RICAVI", color=COLORS["accent"], fontsize=16, fontweight='bold')
    ax.text(0.1, 0.22, f"{d['marg_n']}%", color=COLORS["white"], fontsize=55, fontweight='bold')
    ax.text(0.35, 0.22, f"{d['marg_n_1']}%", color=COLORS["graph1"], fontsize=55, alpha=0.7)

    plt.axis('off')
    return fig

# --- INTERFACE ---
st.markdown('<div class="logo-container">We<br>are_<br>FIZZY</div>', unsafe_allow_html=True)
st.markdown('<div class="report-title">Report Mensile</div>', unsafe_allow_html=True)

uploaded = st.sidebar.file_uploader("Fichier Excel", type="xlsx")

if uploaded:
    data_dict = load_data(uploaded)
    fig = draw_page_1(data_dict)
    st.pyplot(fig)
    
    # Bouton de téléchargement propre
    fn = "Fizzy_Report_P1.png"
    fig.savefig(fn, facecolor=COLORS["bg"], bbox_inches='tight', dpi=200)
    with open(fn, "rb") as img:
        st.sidebar.download_button("📥 Télécharger le rapport", img, file_name=fn)
