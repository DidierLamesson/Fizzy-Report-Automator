import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import altair as alt

# --- 1. CONFIGURATION & DESIGN ---
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
    # Extraction du mois et année [cite: 8]
    formatted_month = raw_month.strftime('%B %Y') if hasattr(raw_month, 'strftime') else str(raw_month)
    return {
        "month": formatted_month, 
        "fatturato_n": clean_val(df.iloc[8, 2]), # [cite: 12, 23]
        "fatturato_n_1": clean_val(df.iloc[9, 2]), # [cite: 20]
        "diff_fatturato": round(clean_val(df.iloc[8, 3]) * 100, 1), # [cite: 24]
        "ric_cost_n": clean_val(df.iloc[12, 2]), # [cite: 29]
        "ric_cost_n_1": clean_val(df.iloc[13, 2]), # [cite: 29]
        "marg_n": round(clean_val(df.iloc[16, 2]) * 100, 1), # [cite: 34]
        "marg_n_1": round(clean_val(df.iloc[17, 2]) * 100, 1), # [cite: 35]
    }

# --- 3. FONCTION DE DESSIN DU RAPPORT (IMAGE FINALE) ---
def draw_full_report(d, restaurant_name, analysis_text):
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax_main = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax_main.axis('off')

    # Header [cite: 1, 2, 3, 4]
    ax_main.text(0.5, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=16, fontweight='bold', ha='center', linespacing=0.9)
    ax_main.text(0.5, 0.89, "Report Mensile", color=COLORS["white"], fontsize=32, ha='center', fontfamily='serif', fontstyle='italic')
    ax_main.text(0.5, 0.86, f"{restaurant_name.upper()}", color=COLORS["white"], fontsize=16, ha='center')
    ax_main.text(0.5, 0.84, d["month"].upper(), color=COLORS["highlight"], fontsize=12, ha='center')

    # Graphique (Moitié gauche) [cite: 6, 7]
    ax_bar = fig.add_axes([0.1, 0.58, 0.35, 0.20], facecolor=COLORS["bg"])
    vals = [d["fatturato_n"], d["fatturato_n_1"]]
    rects = ax_bar.bar([0, 1], vals, color=[COLORS["graph1"], COLORS["graph2"]], width=0.8, zorder=3)
    
    # Formatage Axe Y (Espaces milliers) [cite: 11, 13, 14]
    ax_bar.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))
    ax_bar.grid(axis='y', color=COLORS["white"], linestyle='-', linewidth=0.5, alpha=0.2, zorder=0)
    ax_bar.tick_params(axis='y', colors=COLORS["white"], labelsize=9)
    for s in ax_bar.spines.values(): s.set_visible(False)
    ax_bar.set_xticks([])

    # Chiffres Fatturato (À droite du graph) [cite: 23, 24]
    ax_main.text(0.52, 0.72, f"{int(d['fatturato_n']):,}".replace(',', ' ') + " €", color=COLORS["white"], fontsize=35, fontweight='bold')
    ax_main.text(0.52, 0.68, f"{d['diff_fatturato']}% vs 2024", color=COLORS["accent"], fontsize=18)
    
    # Texte d'analyse [cite: 25]
    ax_main.text(0.52, 0.64, analysis_text, color=COLORS["white"], fontsize=10, linespacing=1.5, va='top', wrap=True)

    # Section Ricavi - Costi [cite: 26, 29]
    ax_main.text(0.1, 0.48, "RICAVI - COSTI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    ax_main.text(0.1, 0.42, f"€ {int(d['ric_cost_n']):,}".replace(',', ' '), color=COLORS["white"], fontsize=28, fontweight='bold')
    ax_main.text(0.40, 0.42, f"€ {int(d['ric_cost_n_1']):,}".replace(',', ' '), color=COLORS["graph1"], fontsize=28)

    # Section Margine [cite: 31, 34, 35]
    ax_main.text(0.1, 0.28, "MARGINE % SU RICAVI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    ax_main.text(0.1, 0.18, f"{int(d['marg_n'])}%", color=COLORS["white"], fontsize=55, fontweight='bold')
    ax_main.text(0.35, 0.18, f"{int(d['marg_n_1'])}%", color=COLORS["graph1"], fontsize=55, alpha=0.7)
    
    return fig

# --- 4. INTERFACE UTILISATEUR ---
st.title("Rapport Fizzy Automatizzazione ⚡️")

# Sidebar
restaurant_input = st.sidebar.text_input("Nom du Restaurant *", value="A'RICCIONE - TERRAZZA")
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded and restaurant_input:
    data_dict = load_data(uploaded)
    
    # MÉTHODE HYBRIDE : 2 Colonnes
    col_viz, col_edit = st.columns([1, 1])
    
    with col_viz:
        st.subheader("📊 Aperçu des données")
        
        # --- PRÉPARATION DES LABELS DYNAMIQUES ---
        # Mois actuel (ex: Novembre 2025)
        label_n = data_dict['month'] 
        
        # Calcul du mois N-1 (ex: Novembre 2024)
        # On remplace simplement l'année dans la chaîne de caractères
        if "2025" in label_n:
            label_n_1 = label_n.replace("2025", "2024")
        else:
            # Sécurité si l'année n'est pas 2025
            label_n_1 = "Année Précédente (N-1)"

        # --- AFFICHAGE DE LA VARIATION AU-DESSUS ---
        variation_nominale = data_dict['fatturato_n'] - data_dict['fatturato_n_1']
        suffixe = "↗︎" if variation_nominale > 0 else "↘︎"
        
        # Style pour mettre en avant la variation nominale
        st.markdown(f"### Variation : **{int(variation_nominale):,} €** {suffixe}".replace(",", " "))

        # --- DONNÉES DU GRAPHIQUE ---
        chart_data = pd.DataFrame({
            "Mois": [label_n, label_n_1],
            "Fatturato (€)": [data_dict["fatturato_n"], data_dict["fatturato_n_1"]]
        }).set_index("Mois")

        # Affichage du graphique natif
        st.bar_chart(chart_data, color="#918d84") # Utilise votre gris FIZZY [cite: 5, 7]
        
        # Rappel des metrics en bas pour la précision
        c1, c2 = st.columns(2)
        c1.metric(label_n, f"{int(data_dict['fatturato_n']):,}".replace(",", " ") + " €")
        c2.metric("Variation %", f"{data_dict['diff_fatturato']}%")

    with col_edit:
        st.subheader("✍️ Analyse Narrative")
        # Texte dynamique automatique [cite: 25]
        auto_text = (
            f"Dal confronto con lo stesso periodo dell'anno precedente emerge che, "
            f"a {data_dict['month']}, il fatturato registra un "
            f"{'incremento' if data_dict['diff_fatturato'] > 0 else 'calo'} "
            f"del {abs(data_dict['diff_fatturato'])}% rispetto al 2024."
        )
        user_text = st.text_area("Personnalisez votre analyse ici :", value=auto_text, height=300)

    st.divider()

    if st.button("🎨 Générer l'image finale pour le client"):
        fig = draw_full_report(data_dict, restaurant_input, user_text)
        st.pyplot(fig)
        
        fn = f"Rapport_{restaurant_input.replace(' ', '_')}.png"
        fig.savefig(fn, facecolor=COLORS["bg"], bbox_inches='tight', dpi=200)
        with open(fn, "rb") as img:
            st.download_button("📥 Télécharger le rapport (.png)", img, file_name=fn, mime="image/png")

else:
    st.info("Veuillez configurer le nom du restaurant et charger un fichier Excel.")