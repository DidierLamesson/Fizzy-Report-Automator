import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import re

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="FIZZY Automator", layout="wide")

# --- LOAD EPILOGUE FONT (GitHub root) ---

font_path_regular = "Epilogue-Variable.ttf"
font_path_italic = "Epilogue-VariableItalic.ttf"

fm.fontManager.addfont(font_path_regular)
fm.fontManager.addfont(font_path_italic)

epilogue_font = fm.FontProperties(fname=font_path_regular)
epilogue_font_italic = fm.FontProperties(fname=font_path_italic)

# Appliquer globalement à Matplotlib
plt.rcParams["font.family"] = epilogue_font.get_name()

COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84",
    "graph2": "#ece8e1",
    "white": "#ffffff",
}


# --- 2. FONCTIONS DE TRAITEMENT ---
def clean_val(val):
    """Robuste: gère NaN, float/int, et strings '507 767' / '507.767' / '507,767'."""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        # garde chiffres + séparateurs
        s = re.sub(r"[^\d,.\-]", "", s)
        if not s:
            return 0.0
        # heuristique: si virgule et point, on suppose virgule décimale
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            # si seulement virgule -> décimale
            if "," in s:
                s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return 0.0
    return 0.0


def load_data(file):
    df = pd.read_excel(file, sheet_name="Dati report", header=None)

    # Dictionnaire de traduction des mois
    months_it = {
        1: "Gennaio",
        2: "Febbraio",
        3: "Marzo",
        4: "Aprile",
        5: "Maggio",
        6: "Giugno",
        7: "Luglio",
        8: "Agosto",
        9: "Settembre",
        10: "Ottobre",
        11: "Novembre",
        12: "Dicembre",
    }

    # --- 1. Extraction de la date ---
    raw_date = df.iloc[4, 2]  # Supposons que la date est en C5
    if hasattr(raw_date, "month"):
        mes_it = months_it[raw_date.month]
        anno_n = raw_date.year
    else:
        mes_it = "Mese"
        anno_n = 2026  # Valeur par défaut

    # --- 2. Extraction des données "Fatturato" ---
    fatturato_n = clean_val(df.iloc[8, 2])  # Fatturato N (ligne 9, colonne C)
    fatturato_n_1 = clean_val(df.iloc[9, 2])  # Fatturato N-1 (ligne 10, colonne C)
    diff_fatturato = round(
        clean_val(df.iloc[8, 3]) * 100, 1
    )  # % variation (ligne 9, colonne D)

    # Ricavi - Costi et Margine
    ric_cost_n = clean_val(df.iloc[11, 2])  # Ricavi - Costi N (ligne 12, colonne C)
    ric_cost_n_1 = clean_val(df.iloc[12, 2])  # Ricavi - Costi N-1 (ligne 13, colonne C)
    marg_n = round(
        clean_val(df.iloc[14, 2]) * 100, 1
    )  # Margine N (ligne 15, colonne C)
    marg_n_1 = round(
        clean_val(df.iloc[15, 2]) * 100, 1
    )  # Margine N-1 (ligne 16, colonne C)

    # --- 3. Extraction des dates pour les 6 mois glissants (mêmes pour Food, Beverage & Labour) ---

    graph_cost_dates = [df.iloc[i, 1] for i in range(24, 30)]  # Dates en colonne B
    graph_cost_dates_n_1 = [df.iloc[i, 7] for i in range(24, 30)]  # Dates en colonne H

    # --- 3. Extraction des dates et données "Food Cost" ---

    fatturato_mensile_n = [
        clean_val(df.iloc[i, 2]) for i in range(24, 30)
    ]  # Fatturato mensuel N en colonne C
    fatturato_mensile_n_1 = [
        clean_val(df.iloc[i, 8]) for i in range(24, 30)
    ]  # Fatturato mensuel N-1 en colonne I

    # Food Cost mensuel (N et N-1)
    food_cost_monthly_n = [
        clean_val(df.iloc[i, 3]) for i in range(24, 30)
    ]  # Colonne D (N)
    food_cost_monthly_n_1 = [
        clean_val(df.iloc[i, 9]) for i in range(24, 30)
    ]  # Colonne J (N-1)

    # --- 4. Extraction des données "Beverage Cost" ---
    beverage_cost_monthly_n = [
        clean_val(df.iloc[i, 3]) for i in range(36, 42)
    ]  # Colonne D (N)
    beverage_cost_monthly_n_1 = [
        clean_val(df.iloc[i, 9]) for i in range(36, 42)
    ]  # Colonne J (N-1)

    # --- 5. Extraction des données "Incidenza Staff" ---
    staff_monthly_n = [clean_val(df.iloc[i, 3]) for i in range(50, 55)]  # Colonne D (N)
    staff_monthly_n_1 = [
        clean_val(df.iloc[i, 9]) for i in range(50, 55)
    ]  # Colonne J (N-1)

    # --- 6. Calcul des pourcentages de Food Cost ---
    food_cost_pctg_n = []
    for i in range(len(food_cost_monthly_n)):
        fatturato = fatturato_mensile_n[i]
        food_cost = food_cost_monthly_n[i]
        if fatturato > 0:  # Évite la division par zéro
            pctg = (food_cost / fatturato) * 100
        else:
            pctg = 0.0
        food_cost_pctg_n.append(round(pctg, 2))

    # Même chose pour N-1
    food_cost_pctg_n_1 = []
    for i in range(len(food_cost_monthly_n_1)):
        fatturato = fatturato_mensile_n_1[i]
        food_cost = food_cost_monthly_n_1[i]
        if fatturato > 0:
            pctg = (food_cost / fatturato) * 100
        else:
            pctg = 0.0
        food_cost_pctg_n_1.append(round(pctg, 2))

    # --- 7. Calcul des pourcentages de Beverage Cost ---
    beverage_cost_pctg_n = []
    for i in range(len(beverage_cost_monthly_n)):
        fatturato = clean_val(df.iloc[36 + i, 2])  # Fatturato mensuel N en colonne C
        beverage_cost = beverage_cost_monthly_n[i]
        if fatturato > 0:
            pctg = (beverage_cost / fatturato) * 100
        else:
            pctg = 0.0
        beverage_cost_pctg_n.append(round(pctg, 2))

    # Même chose pour N-1
    beverage_cost_pctg_n_1 = []
    for i in range(len(beverage_cost_monthly_n_1)):
        fatturato = clean_val(df.iloc[36 + i, 8])  # Fatturato mensuel N-1 en colonne I
        beverage_cost = beverage_cost_monthly_n_1[i]
        if fatturato > 0:
            pctg = (beverage_cost / fatturato) * 100
        else:
            pctg = 0.0
        beverage_cost_pctg_n_1.append(round(pctg, 2))

    # --- 8. Calcul des pourcentages de Staff Cost ---
    staff_cost_pctg_n = []
    for i in range(len(staff_monthly_n)):
        fatturato = clean_val(df.iloc[50 + i, 2])  # Fatturato mensuel N en colonne C
        staff_cost = staff_monthly_n[i]
        if fatturato > 0:
            pctg = (staff_cost / fatturato) * 100
        else:
            pctg = 0.0
        staff_cost_pctg_n.append(round(pctg, 2))

    # Même chose pour N-1
    staff_cost_pctg_n_1 = []
    for i in range(len(staff_monthly_n_1)):
        fatturato = clean_val(df.iloc[50 + i, 8])  # Fatturato mensuel N-1 en colonne I
        staff_cost = staff_monthly_n_1[i]
        if fatturato > 0:
            pctg = (staff_cost / fatturato) * 100
        else:
            pctg = 0.0
        staff_cost_pctg_n_1.append(round(pctg, 2))

    # --- 9. Calcul des moyennes ---
    food_cost_avg_n = sum(food_cost_monthly_n) / len(food_cost_monthly_n)
    food_cost_avg_n_1 = sum(food_cost_monthly_n_1) / len(food_cost_monthly_n_1)
    beverage_cost_avg_n = sum(beverage_cost_monthly_n) / len(beverage_cost_monthly_n)
    beverage_cost_avg_n_1 = sum(beverage_cost_monthly_n_1) / len(
        beverage_cost_monthly_n_1
    )
    staff_cost_avg_n = sum(staff_monthly_n) / len(staff_monthly_n)
    staff_cost_avg_n_1 = sum(staff_monthly_n_1) / len(staff_monthly_n_1)

    # --- 10. Retour des données ---
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
        # Dates
        "graph_cost_dates": graph_cost_dates,
        "graph_cost_dates_n_1": graph_cost_dates_n_1,
        # Fatturato Mensile
        "fatturato_mensile_n": fatturato_mensile_n,
        "fatturato_mensile_n_1": fatturato_mensile_n_1,
        # Food Cost
        "food_cost_monthly_n": food_cost_monthly_n,
        "food_cost_monthly_n_1": food_cost_monthly_n_1,
        "food_cost_pctg_n": food_cost_pctg_n,
        "food_cost_pctg_n_1": food_cost_pctg_n_1,
        "food_cost_avg_n": food_cost_avg_n,
        "food_cost_avg_n_1": food_cost_avg_n_1,
        # Beverage Cost
        "beverage_cost_monthly_n": beverage_cost_monthly_n,
        "beverage_cost_monthly_n_1": beverage_cost_monthly_n_1,
        "beverage_cost_pctg_n": beverage_cost_pctg_n,
        "beverage_cost_pctg_n_1": beverage_cost_pctg_n_1,
        "beverage_cost_avg_n": beverage_cost_avg_n,
        "beverage_cost_avg_n_1": beverage_cost_avg_n_1,
        # Incidenza Staff
        "staff_monthly_n": staff_monthly_n,
        "staff_monthly_n_1": staff_monthly_n_1,
        "staff_cost_pctg_n": staff_cost_pctg_n,
        "staff_cost_pctg_n_1": staff_cost_pctg_n_1,
        "staff_cost_avg_n": staff_cost_avg_n,
        "staff_cost_avg_n_1": staff_cost_avg_n_1,
    }


def fmt_eur_it(x, decimals=0):
    # 507767 -> "507 767 €"
    if decimals == 0:
        s = f"{int(round(x)):,}".replace(",", " ")
    else:
        # 507767.89 -> "507 767,89"
        s = f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", " ")
    return f"{s} €"


def fmt_pct(x, decimals=1, signed=True):
    sign = "+" if (signed and x >= 0) else ""
    return f"{sign}{x:.{decimals}f}%"


def build_page1_suggestions(d):
    fatt_n = d["fatturato_n"]
    fatt_p = d["fatturato_n_1"]
    delta = fatt_n - fatt_p
    pct_calc = (delta / fatt_p * 100) if fatt_p else 0.0
    pct = d.get("diff_fatturato", pct_calc)

    ric_n = d["ric_cost_n"]
    ric_p = d["ric_cost_n_1"]
    ric_delta = ric_n - ric_p

    marg_n = d["marg_n"]
    marg_p = d["marg_n_1"]
    marg_delta = marg_n - marg_p  # points %

    trend_word = "incremento" if pct >= 0 else "calo"
    ric_word = "miglioramento" if ric_delta >= 0 else "peggioramento"
    marg_word = "miglioramento" if marg_delta >= 0 else "contrazione"

    p1 = (
        f"Dal confronto con lo stesso periodo dell’anno precedente emerge che, a "
        f"{d['month_name']} {d['year_n']}, il fatturato registra un {trend_word} "
        f"del {abs(pct):.1f}% rispetto a {d['month_name']} {d['year_n_1']} "
        f"({fmt_eur_it(fatt_n)} vs {fmt_eur_it(fatt_p)})."
    )

    p2 = (
        f"Oltre alla dinamica dei ricavi, si evidenzia un {ric_word} del risultato economico: "
        f"Ricavi - Costi pari a {fmt_eur_it(ric_n)} "
        f"(vs {fmt_eur_it(ric_p)}), con un {marg_word} dei margini "
        f"({marg_n:.1f}% vs {marg_p:.1f}%)."
    )

    # Varianti più corte
    p1_short = (
        f"A {d['month_name']} {d['year_n']} il fatturato è {fmt_eur_it(fatt_n)}, "
        f"{fmt_pct(pct, 1, True)} vs {d['year_n_1']}."
    )
    p2_short = (
        f"Ricavi - Costi: {fmt_eur_it(ric_n)} (vs {fmt_eur_it(ric_p)}); "
        f"Margine: {marg_n:.1f}% (vs {marg_p:.1f}%)."
    )

    return {
        "long": (p1, p2),
        "short": (p1_short, p2_short),
    }


def make_fatturato_fig(d, label=""):
    fig, ax = plt.subplots(figsize=(6, 6))

    # Background
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    # Données
    values = [d["fatturato_n"], d["fatturato_n_1"]]
    x = [0, 1]

    ax.bar(
        x,
        values,
        width=0.95,
        color=[COLORS["graph1"], COLORS["graph2"]],
        alpha=1.0,
        zorder=3,
    )
    ax.set_xlim(-0.475 - 0.05, 1.475)

    # Labels au-dessus
    for i, v in enumerate(values):
        ax.text(
            i,
            v + max(values) * 0.02,
            f"{v:,.0f}".replace(",", " "),
            ha="center",
            va="bottom",
            fontproperties=epilogue_font,
            fontsize=18,
            color=COLORS["white"],
            fontweight=900,
        )

    # Axe X
    ax.set_xticks([0.5])
    ax.set_xticklabels([label] if label else [])

    # Axe Y
    ax.tick_params(axis="y", colors=COLORS["white"], labelsize=14)
    ax.tick_params(axis="y", length=0)
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", " "))
    )
    ax.set_ylim(0, max(values) * 1.2)

    # Grille
    ax.grid(axis="y", linestyle="-", alpha=0.15, color=COLORS["white"], zorder=0)

    # Supprimer bordures
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Légende
    legend_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS["graph1"],
            markeredgecolor="none",
            markeredgewidth=0,
            markersize=12,
            label=f"Fatturato {d['year_n']} €",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS["graph2"],
            markeredgecolor="none",
            markeredgewidth=0,
            markersize=12,
            label=f"Fatturato {d['year_n_1']} €",
        ),
    ]

    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        ncol=2,
        frameon=False,
        fontsize=14,
        labelcolor=COLORS["white"],
    )

    plt.tight_layout()
    return fig


# --- 3. INTERFACE UTILISATEUR ---
st.title("Report Fizzy Automatizzazione ⚡️")

restaurant_input = st.sidebar.text_input(
    "Nome clienti *", value="A'RICCIONE - TERRAZZA"
)
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded and restaurant_input:

    data_dict = load_data(uploaded)

    # Colonnes
    col_viz, col_edit = st.columns([1, 1])

    # =========================
    # 📊 COLONNE GRAPH
    # =========================
    with col_viz:

        st.subheader("📊 Fatturato Mensile")

        fig = make_fatturato_fig(data_dict, label="")
        st.pyplot(fig)

    # =========================
    # ✍️ COLONNE ANALYSE
    # =========================
    with col_edit:

        st.subheader("✍️ Analyse Narrative")

        suggest = build_page1_suggestions(data_dict)

        mode = st.radio("Style", ["long", "short"], horizontal=True, index=0)

        p1_default, p2_default = suggest[mode]

        p1 = st.text_area("Paragrafo 1", value=p1_default, height=160)
        p2 = st.text_area("Paragrafo 2", value=p2_default, height=160)

        analysis_text = f"{p1}\n\n{p2}"

    st.divider()


# --- 4. FONCTION DE DESSIN DU RAPPORT (IMAGE FINALE) ---
def draw_full_report(d, restaurant_name, analysis_text):
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax_main = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax_main.axis("off")

    # Header
    ax_main.text(
        0.5,
        0.94,
        "We\nare_\nFIZZY",
        color=COLORS["white"],
        fontsize=16,
        fontweight="bold",
        ha="center",
        linespacing=0.9,
    )
    ax_main.text(
        0.5,
        0.89,
        "Report Mensile",
        color=COLORS["white"],
        fontsize=32,
        ha="center",
        fontfamily="serif",
        fontstyle="italic",
    )
    ax_main.text(
        0.5,
        0.86,
        f"{restaurant_name.upper()}",
        color=COLORS["white"],
        fontsize=16,
        ha="center",
    )
    ax_main.text(
        0.5,
        0.84,
        d["full_date_n"].upper(),
        color=COLORS["highlight"],
        fontsize=12,
        ha="center",
    )

    # Graphique Fatturato
    ax_bar = fig.add_axes([0.15, 0.58, 0.35, 0.20], facecolor=COLORS["bg"])
    vals = [d["fatturato_n"], d["fatturato_n_1"]]
    rects = ax_bar.bar(
        [0, 1], vals, color=[COLORS["graph1"], COLORS["graph2"]], width=0.8, zorder=3
    )

    # Formatage Axe Y
    ax_bar.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", " "))
    )
    ax_bar.grid(
        axis="y",
        color=COLORS["white"],
        linestyle="-",
        linewidth=0.5,
        alpha=0.2,
        zorder=0,
    )
    ax_bar.tick_params(axis="y", colors=COLORS["white"], labelsize=9)
    for s in ax_bar.spines.values():
        s.set_visible(False)
    ax_bar.set_xticks([])

    # Chiffres Fatturato
    val_txt = f"{int(d['fatturato_n']):,}".replace(",", " ") + " €"
    ax_main.text(
        0.55, 0.72, val_txt, color=COLORS["white"], fontsize=35, fontweight="bold"
    )
    ax_main.text(
        0.55,
        0.68,
        f"{d['diff_fatturato']}% vs {d['year_n_1']}",
        color=COLORS["accent"],
        fontsize=18,
    )

    # Texte d'analyse
    ax_main.text(
        0.55,
        0.64,
        analysis_text,
        color=COLORS["white"],
        fontsize=10,
        linespacing=1.5,
        va="top",
        wrap=True,
    )

    # Section Ricavi - Costi
    ax_main.text(
        0.1,
        0.48,
        "RICAVI - COSTI",
        color=COLORS["accent"],
        fontsize=14,
        fontweight="bold",
    )
    ax_main.text(
        0.1,
        0.42,
        f"€ {int(d['ric_cost_n']):,}".replace(",", " "),
        color=COLORS["white"],
        fontsize=28,
        fontweight="bold",
    )
    ax_main.text(
        0.40,
        0.42,
        f"€ {int(d['ric_cost_n_1']):,}".replace(",", " "),
        color=COLORS["graph1"],
        fontsize=28,
    )

    # Section Margine
    ax_main.text(
        0.1,
        0.28,
        "MARGINE % SU RICAVI",
        color=COLORS["accent"],
        fontsize=14,
        fontweight="bold",
    )
    ax_main.text(
        0.1,
        0.18,
        f"{int(d['marg_n'])}%",
        color=COLORS["white"],
        fontsize=55,
        fontweight="bold",
    )
    ax_main.text(
        0.35,
        0.18,
        f"{int(d['marg_n_1'])}%",
        color=COLORS["graph1"],
        fontsize=55,
        alpha=0.7,
    )

    return fig
