import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")

# Injection de la police Epilogue
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

# --- 2. FONCTIONS DE TRAITEMENT ---
def clean_val(val):
    if pd.isna(val) or isinstance(val, str):
        return 0.0
    return float(val)

def load_data(file):
    df = pd.read_excel(file, sheet_name='Dati report', header=None)

    # Dictionnaire de traduction des mois
    months_it = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }

    # --- 1. Extraction de la date (ex: "Dicembre 2025") ---
    raw_date = df.iloc[4, 2]  # Supposons que la date est en C5
    if hasattr(raw_date, 'month'):
        mes_it = months_it[raw_date.month]
        anno_n = raw_date.year
    else:
        mes_it = "Mese"
        anno_n = 2026  # Valeur par défaut

    # --- 2. Extraction dynamique des données "Fatturato" ---
    # Chercher les lignes contenant "Fatturato 2025" et "Fatturato 2024"
    fatturato_n_row = df[df.apply(lambda row: row.astype(str).str.contains("Fatturato.*2025", na=False, regex=True).any(), axis=1)].index[0]
    fatturato_n_1_row = df[df.apply(lambda row: row.astype(str).str.contains("Fatturato.*2024", na=False, regex=True).any(), axis=1)].index[0]

    fatturato_n = clean_val(df.iloc[fatturato_n_row, 2])
    fatturato_n_1 = clean_val(df.iloc[fatturato_n_1_row, 2])
    diff_fatturato = round(clean_val(df.iloc[fatturato_n_row, 3]) * 100, 1)

    # Ricavi - Costi et Margine (offsets relatifs)
    ric_cost_n = clean_val(df.iloc[fatturato_n_row + 4, 2])
    ric_cost_n_1 = clean_val(df.iloc[fatturato_n_row + 5, 2])
    marg_n = round(clean_val(df.iloc[fatturato_n_row + 8, 2]) * 100, 1)
    marg_n_1 = round(clean_val(df.iloc[fatturato_n_row + 9, 2]) * 100, 1)

    # --- 3. Extraction dynamique des données "Food & Beverage Cost" ---
    # Chercher les titres "Food Cost" et "Beverage Cost"
    food_cost_title_row = df[df.apply(lambda row: row.astype(str).str.contains("Food Cost", na=False).any(), axis=1)].index[0]
    beverage_cost_title_row = df[df.apply(lambda row: row.astype(str).str.contains("Beverage Cost", na=False).any(), axis=1)].index[0]

    # Extraire les valeurs mensuelles (6 prochaines lignes)
    food_cost_monthly = [clean_val(df.iloc[food_cost_title_row + i, 2]) for i in range(1, 7)]
    beverage_cost_monthly = [clean_val(df.iloc[beverage_cost_title_row + i, 2]) for i in range(1, 7)]

    # Moyennes (1 ligne après les valeurs mensuelles)
    food_cost_avg = clean_val(df.iloc[food_cost_title_row + 7, 2])
    beverage_cost_avg = clean_val(df.iloc[beverage_cost_title_row + 7, 2])

    # --- 4. Extraction dynamique des données "Incidenza Staff" ---
    # Chercher le titre "Incidenza Staff" ou "Labour Cost"
    staff_cost_title_row = df[df.apply(lambda row: row.astype(str).str.contains("Incidenza Staff|Labour Cost", na=False).any(), axis=1)].index[0]

    # Extraire les pourcentages (3 prochaines lignes)
    staff_cost_dec = clean_val(df.iloc[staff_cost_title_row + 1, 2])
    staff_cost_nov = clean_val(df.iloc[staff_cost_title_row + 2, 2])
    staff_cost_dec_2024 = clean_val(df.iloc[staff_cost_title_row + 3, 2])
    staff_benchmark = clean_val(df.iloc[staff_cost_title_row + 4, 2])

    # --- 5. Retour des données ---
    return {
        # Fatturato
        "month_name": mes_it,
        "year_n": anno_n,
        "year_n_1": anno_n - 1,
        "full_date_n": f"{mes_it} {anno_n}",
        "full_date_n_1": f"{mes_it} {anno_n - 1}",
        "fatturato_n": fatturato_n,
        "fatturato_n_1": fatturato_n_1,
        "diff_fatturato": diff_fatturato,
        "ric_cost_n": ric_cost_n,
        "ric_cost_n_1": ric_cost_n_1,
        "marg_n": marg_n,
        "marg_n_1": marg_n_1,

        # Food & Beverage Cost
        "food_cost_monthly": food_cost_monthly,
        "beverage_cost_monthly": beverage_cost_monthly,
        "food_cost_avg": food_cost_avg,
        "beverage_cost_avg": beverage_cost_avg,

        # Incidenza Staff
        "staff_cost_dec": staff_cost_dec,
        "staff_cost_nov": staff_cost_nov,
        "staff_cost_dec_2024": staff_cost_dec_2024,
        "staff_benchmark": staff_benchmark,
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
    ax_main.text(0.5, 0.84, d["full_date_n"].upper(), color=COLORS["highlight"], fontsize=12, ha='center')

    # Graphique Fatturato
    ax_bar = fig.add_axes([0.15, 0.58, 0.35, 0.20], facecolor=COLORS["bg"])
    vals = [d["fatturato_n"], d["fatturato_n_1"]]
    rects = ax_bar.bar([0, 1], vals, color=[COLORS["graph1"], COLORS["graph2"]], width=0.8, zorder=3)

    # Formatage Axe Y
    ax_bar.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))
    ax_bar.grid(axis='y', color=COLORS["white"], linestyle='-', linewidth=0.5, alpha=0.2, zorder=0)
    ax_bar.tick_params(axis='y', colors=COLORS["white"], labelsize=9)
    for s in ax_bar.spines.values():
        s.set_visible(False)
    ax_bar.set_xticks([])

    # Chiffres Fatturato
    val_txt = f"{int(d['fatturato_n']):,}".replace(',', ' ') + " €"
    ax_main.text(0.55, 0.72, val_txt, color=COLORS["white"], fontsize=35, fontweight='bold')
    ax_main.text(0.55, 0.68, f"{d['diff_fatturato']}% vs {d['year_n_1']}", color=COLORS["accent"], fontsize=18)

    # Texte d'analyse
    ax_main.text(0.55, 0.64, analysis_text, color=COLORS["white"], fontsize=10, linespacing=1.5, va='top', wrap=True)

    # Section Ricavi - Costi
    ax_main.text(0.1, 0.48, "RICAVI - COSTI", color=COLORS["accent"], fontsize=14, fontweight='bold')
    ax_main.text(0.1, 0.42, f"€ {int(d['ric_cost_n']):,}".replace(',', ' '), color=COLORS["white"], fontsize=28, fontweight='bold')
    ax_main.text(0.40, 0.42, f"€ {int(d['ric_cost_n_1']):,}".replace(',', ' '), color=COLORS["graph1"], fontsize=28)

    # Section Margine
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

    # Affichage des données extraites (pour vérification)
    st.subheader("🔍 Données extraites")
    st.json(data_dict)

    col_viz, col_edit = st.columns([1, 1])

    with col_viz:
        st.subheader("📊 Aperçu des données")

        label_n = data_dict['full_date_n']
        label_n_1 = data_dict['full_date_n_1']

        # Variation nominale
        diff_euro = data_dict['fatturato_n'] - data_dict['fatturato_n_1']
        suffixe = "↗︎" if diff_euro > 0 else "↘︎"
        st.markdown(f"### Variation : **{int(diff_euro):,} €** {suffixe}".replace(",", " "))

        # Graphique Fatturato
        chart_data = pd.DataFrame({
            "Fatturato (€)": [data_dict["fatturato_n"], data_dict["fatturato_n_1"]]
        }, index=[label_n, label_n_1])
        st.bar_chart(chart_data, color=COLORS["graph1"])

        # Metrics
        c1, c2 = st.columns(2)
        val_n = f"{int(data_dict['fatturato_n']):,}".replace(",", " ")
        c1.metric(label_n, f"{val_n} €")
        c2.metric(f"vs {data_dict['year_n_1']}", f"{data_dict['diff_fatturato']}%")

    with col_edit:
        st.subheader("✍️ Analyse Narrative")
        auto_text = (
            f"Dal confronto con lo stesso periodo dell'anno precedente emerge che, "
            f"a {data_dict['month_name']} {data_dict['year_n']}, il fatturato registra un "
            f"{'incremento' if data_dict['diff_fatturato'] > 0 else 'calo'} "
            f"del {abs(data_dict['diff_fatturato'])}% rispetto al {data_dict['year_n_1']}."
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
    st.info("Benvenuto! Carica un file Excel per iniziare.")
