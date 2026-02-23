import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")

COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84",  # Gris 2025
    "graph2": "#ece8e1",  # Beige 2024
    "white": "#ffffff"
}

# --- 2. FONCTIONS DE TRAITEMENT ---
def clean_val(val):
    if pd.isna(val) or isinstance(val, str): return 0.0
    return float(val)

def load_data(file):
    df = pd.read_excel(file, sheet_name='Dati report', header=None)
    raw_month = df.iloc[4, 2]
    formatted_month = raw_month.strftime('%B %Y') if hasattr(raw_month, 'strftime') else str(raw_month)
    return {
        "month": formatted_month, 
        "fatturato_n": clean_val(df.iloc[8, 2]),
        "fatturato_n_1": clean_val(df.iloc[9, 2]),
        "diff_fatturato": round(clean_val(df.iloc[8, 3]) * 100, 1),
        "ric_cost_n": clean_val(df.iloc[12, 2]),
        "ric_cost_n_1": clean_val(df.iloc[13, 2]),
        "marg_n": round(clean_val(df.iloc[16, 2]) * 100, 1),
        "marg_n_1": round(clean_val(df.iloc[17, 2]) * 100, 1),
    }

# --- 3. FONCTION DE DESSIN DU RAPPORT (IMAGE FINALE) ---
def draw_full_report(d, restaurant_name, analysis_text):
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax_main = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax_main.axis('off')

    # Header
    ax_main.text(0.5, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=16, fontweight='bold', ha='center', linespacing=0.9)
    ax_main.text(0.5, 0.89, "Report Mensile", color=COLORS["white"], fontsize=32, ha='center', fontfamily='serif', fontstyle='italic')
    ax_main.text(0.5, 0.86, f"{restaurant_name.upper()}", color=COLORS["white"], fontsize=16, ha='center')
    ax_main.text(0.5, 0.84, d["month"].upper(), color=COLORS["highlight"], fontsize=12, ha='center')

    # Graphique (Moitié gauche)
    ax_bar = fig.add_axes([0.1, 0.58, 0.35, 0.20], facecolor=COLORS["bg"])
    vals = [d["fatturato_n"], d["fatturato_n_1"]]
    rects = ax_bar.bar([0, 1], vals, color=[COLORS["graph1"], COLORS["graph2"]], width=0.8, zorder=3)
    ax_bar.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))
    ax_bar.grid(axis='y', color=COLORS["white"], linestyle='-', linewidth=0.5, alpha=0.2, zorder=0)
    ax_bar.tick_params(axis='y', colors=COLORS["white"], labelsize=9)
    for s in ax_bar.spines.values(): s.set_visible(False)
    ax_bar.set_xticks([])

    # Chiffres Fatturato (À droite du graph)
    ax_main.text(0.52, 0.72, f"{d['fatturato_n']:,.0f} €".replace(',', ' '), color=COLORS["white"], fontsize=35, fontweight='bold')
    ax_main.text(0.52, 0.68, f"{d['diff_fatturato']}% vs 2024", color=COLORS["accent"], fontsize=18)
    
    # Intégration du texte personnalisé
    ax_main.text(0.52, 0.64, analysis_text, color=COLORS["white"], fontsize=10, linespacing=1.5, va='top')

    # Section Ricavi - Costi
    ax_main.text(0.1, 0.48, "RICAVI - COSTI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    ax_main.text(0.1, 0.42, f"€ {d['ric_cost_n']:,.0f}".replace(',', ' '), color=COLORS["white"], fontsize=28, fontweight='bold')
    ax_main.text(0.40, 0.42, f"€ {d['ric_cost_n_1']:,.0f}".replace(',', ' '), color=COLORS["graph1"], fontsize=28)

    # Section Margine
    ax_main.text(0.1, 0.28, "MARGINE % SU RICAVI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    ax_main.text(0.1, 0.18, f"{d['marg_n']}%", color=COLORS["white"], fontsize=55, fontweight='bold')
    ax_main.text(0.35, 0.18, f"{d['marg_n_1']}%", color=COLORS["graph1"], fontsize=55, alpha=0.7)
    
    return fig

# --- 4. INTERFACE UTILISATEUR ---
st.title("Rapport Fizzy Automatizzazione ⚡️")

# Sidebar
restaurant_input = st.sidebar.text_input("Nom du Restaurant *", value="A'RICCIONE - TERRAZZA")
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded and restaurant_input:
    data_dict = load_data(uploaded)
    
    # MÉTHODE HYBRIDE : 2 Colonnes pour travailler
    col_viz, col_edit = st.columns([1, 1])
    
    with col_viz:
        st.subheader("📊 Aperçu des données")
        # Petit graphique interactif rapide
        chart_df = pd.DataFrame({
            "Année": ["2025", "2024"],
            "Fatturato": [data_dict["fatturato_n"], data_dict["fatturato_n_1"]]
        })
        st.bar_chart(data=chart_df, x="Année", y="Fatturato")
        st.metric("Variation", f"{data_dict['diff_fatturato']}%")

    with col_edit:
        st.subheader("✍️ Analyse Narrative")
        # Le texte que l'utilisateur rédige sera envoyé dans l'image finale
        default_text = "Dal confronto con lo stesso periodo dell'anno precedente\nemerge che, il fatturato registra un incremento\nsignificativo rispetto al 2024."
        user_text = st.text_area("Rédigez ici (utilisez Entrée pour les sauts de ligne) :", value=default_text, height=200)

    st.divider()

    # Génération du rapport pro
    if st.button("🎨 Générer l'image finale pour le client"):
        fig = draw_full_report(data_dict, restaurant_input, user_text)
        st.pyplot(fig)
        
        # Préparation du téléchargement
        fn = f"Rapport_{restaurant_input.replace(' ', '_')}.png"
        fig.savefig(fn, facecolor=COLORS["bg"], bbox_inches='tight', dpi=200)
        with open(fn, "rb") as img:
            st.download_button("📥 Télécharger le rapport (.png)", img, file_name=fn, mime="image/png")

else:
    st.info("Veuillez configurer le nom du restaurant et charger un fichier Excel.")