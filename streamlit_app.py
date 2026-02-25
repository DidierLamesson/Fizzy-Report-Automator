import re
import textwrap
from io import BytesIO
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
from PIL import Image

# =========================
# 3) COULEURS (ta palette)
# =========================
COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84",
    "graph2": "#ece8e1",
    "white": "#ffffff",
}

# =========================
# 2) PATHS ASSETS (ton repo)
# =========================
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
IMG_DIR = ASSETS_DIR / "img"

# Fonts (d'après ton screenshot repo)
FONT_EPILOGUE_REG = FONTS_DIR / "Epilogue-Regular.otf"
FONT_EPILOGUE_ITALIC = FONTS_DIR / "Epilogue-Italic.otf"
FONT_EPILOGUE_SEMIBOLD = FONTS_DIR / "Epilogue-SemiBold.otf"
FONT_EPILOGUE_SEMIBOLD_ITALIC = FONTS_DIR / "Epilogue-SemiBoldItalic.otf"
FONT_IVY = FONTS_DIR / "fonnts.com-Ivy-Presto-Display-Light.otf"

# Images
LOGO_PATH = IMG_DIR / "Logo Fizzy.png"
ARROW_UP_PATH = IMG_DIR / "Arrow_up.png"
ARROW_DOWN_PATH = IMG_DIR / "Arrow_down.png"
ARROW_ROUND_PATH = IMG_DIR / "Arrow_round.png"


# =========================
# 4) FONTS MATPLOTLIB
# =========================
def _register_font(path: Path):
    if path.exists():
        fm.fontManager.addfont(str(path))


_register_font(FONT_EPILOGUE_REG)
_register_font(FONT_EPILOGUE_ITALIC)
_register_font(FONT_EPILOGUE_SEMIBOLD)
_register_font(FONT_EPILOGUE_SEMIBOLD_ITALIC)
_register_font(FONT_IVY)

epilogue_regular = fm.FontProperties(fname=str(FONT_EPILOGUE_REG))
epilogue_italic = fm.FontProperties(fname=str(FONT_EPILOGUE_ITALIC))
epilogue_semibold = fm.FontProperties(fname=str(FONT_EPILOGUE_SEMIBOLD))
epilogue_semibold_italic = fm.FontProperties(fname=str(FONT_EPILOGUE_SEMIBOLD_ITALIC))
ivy_title = fm.FontProperties(fname=str(FONT_IVY))

plt.rcParams["font.family"] = epilogue_regular.get_name()
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


# =========================
# 1) CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title="FIZZY Automator",
    page_icon="⚡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# 5) HELPERS (format + wrap)
# =========================
def clean_val(val):
    """Robuste: gère NaN, float/int, et strings '507 767' / '507.767' / '507,767'."""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        s = re.sub(r"[^\d,.\-]", "", s)
        if not s:
            return 0.0
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            if "," in s:
                s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return 0.0
    return 0.0


def fmt_eur_dot(x, decimals=0):
    # 507767 -> "507.767 €"
    if decimals == 0:
        s = f"{int(round(x)):,}".replace(",", ".")
    else:
        s = f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def fmt_pct_1(x):
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:.1f}%"


def wrap_for_box(text, width=44):
    lines = []
    for para in (text or "").split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=width))
        lines.append("")
    return "\n".join(lines).strip()


def month_labels_from_graph_dates(d):
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
    labels = []
    for dt in d["graph_cost_dates"]:
        if hasattr(dt, "month"):
            labels.append(months_it.get(dt.month, str(dt)))
        else:
            labels.append(str(dt))
    return labels


# =========================
# 6) LOAD DATA (TON ANCIEN COMPLET)
# =========================
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
        if fatturato > 0:
            pctg = (food_cost / fatturato) * 100
        else:
            pctg = 0.0
        food_cost_pctg_n.append(round(pctg, 2))

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
        fatturato = clean_val(df.iloc[36 + i, 2])
        beverage_cost = beverage_cost_monthly_n[i]
        if fatturato > 0:
            pctg = (beverage_cost / fatturato) * 100
        else:
            pctg = 0.0
        beverage_cost_pctg_n.append(round(pctg, 2))

    beverage_cost_pctg_n_1 = []
    for i in range(len(beverage_cost_monthly_n_1)):
        fatturato = clean_val(df.iloc[36 + i, 8])
        beverage_cost = beverage_cost_monthly_n_1[i]
        if fatturato > 0:
            pctg = (beverage_cost / fatturato) * 100
        else:
            pctg = 0.0
        beverage_cost_pctg_n_1.append(round(pctg, 2))

    # --- 8. Calcul des pourcentages de Staff Cost ---
    staff_cost_pctg_n = []
    for i in range(len(staff_monthly_n)):
        fatturato = clean_val(df.iloc[50 + i, 2])
        staff_cost = staff_monthly_n[i]
        if fatturato > 0:
            pctg = (staff_cost / fatturato) * 100
        else:
            pctg = 0.0
        staff_cost_pctg_n.append(round(pctg, 2))

    staff_cost_pctg_n_1 = []
    for i in range(len(staff_monthly_n_1)):
        fatturato = clean_val(df.iloc[50 + i, 8])
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


# =========================
# 7) SUGGESTIONS TEXT (page 1)
# =========================
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
    marg_delta = marg_n - marg_p

    trend_word = "incremento" if pct >= 0 else "calo"
    ric_word = "miglioramento" if ric_delta >= 0 else "peggioramento"
    marg_word = "miglioramento" if marg_delta >= 0 else "contrazione"

    p1 = (
        f"Dal confronto con lo stesso periodo dell’anno precedente emerge che, a "
        f"{d['month_name']} {d['year_n']}, il fatturato registra un {trend_word} "
        f"del {abs(pct):.1f}% rispetto a {d['month_name']} {d['year_n_1']} "
        f"({fmt_eur_dot(fatt_n)} vs {fmt_eur_dot(fatt_p)})."
    )

    p2 = (
        f"Oltre alla dinamica dei ricavi, si osserva una variazione del risultato economico: "
        f"Ricavi - Costi pari a {fmt_eur_dot(ric_n)} "
        f"(vs {fmt_eur_dot(ric_p)}), con un {marg_word} dei margini "
        f"({marg_n:.1f}% vs {marg_p:.1f}%)."
    )

    return p1, p2


# =========================
# 8) PREVIEW GRAPHIQUE (FIG) (simple)
# =========================
def make_fatturato_fig(d, label):
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    values = [d["fatturato_n"], d["fatturato_n_1"]]
    x = [0, 1]

    ax.bar(x, values, width=0.95, color=[COLORS["graph1"], COLORS["graph2"]], zorder=3)
    ax.set_xlim(-0.55, 1.55)

    for i, v in enumerate(values):
        ax.text(
            i,
            v + max(values) * 0.02,
            f"{int(round(v)):,}".replace(",", "."),
            ha="center",
            va="bottom",
            fontsize=16,
            color=COLORS["white"],
            fontproperties=epilogue_semibold,
        )

    ax.set_xticks([0.5])
    ax.set_xticklabels(
        [label], color=COLORS["white"], fontsize=11, fontproperties=epilogue_regular
    )

    ax.tick_params(axis="y", colors=COLORS["white"], labelsize=11, length=0)
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, p: f"{int(y):,}".replace(",", "."))
    )
    ax.set_ylim(0, max(values) * 1.2)

    ax.grid(axis="y", linestyle="-", alpha=0.15, color=COLORS["white"], zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)

    legend_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS["graph1"],
            markersize=10,
            label=f"Fatturato {d['year_n']} €",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS["graph2"],
            markersize=10,
            label=f"Fatturato {d['year_n_1']} €",
        ),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        ncol=2,
        frameon=False,
        fontsize=10,
        labelcolor=COLORS["white"],
    )

    plt.tight_layout()
    return fig


def make_food_cost_fig(d, label):
    fig, ax = plt.subplots(figsize=(6, 3.6))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    x_labels = month_labels_from_graph_dates(d)
    y = d["food_cost_pctg_n"]  # année en cours (déjà en %)

    ax.plot(
        range(len(y)),
        y,
        marker="o",
        linewidth=3,
        markersize=10,
        color=COLORS["graph1"],
        zorder=3,
    )

    ax.set_title(
        f"Andamento Food Cost Mensile {d['year_n']}",
        color=COLORS["white"],
        fontsize=16,
        fontproperties=epilogue_semibold,
        loc="left",
        pad=10,
    )

    # Legend style "• Terrazza"
    ax.plot([], [], marker="o", linestyle="None", color=COLORS["graph1"], label=label)
    leg = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        frameon=False,
        fontsize=10,
        labelcolor=COLORS["white"],
        handlelength=0,
    )
    for t in leg.get_texts():
        t.set_fontproperties(epilogue_regular)

    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(
        x_labels,
        rotation=45,
        ha="right",
        color=COLORS["white"],
        fontsize=9,
        fontproperties=epilogue_regular,
    )
    ax.tick_params(axis="x", colors=COLORS["white"], labelsize=9, length=0)

    ax.tick_params(axis="y", colors=COLORS["white"], labelsize=9, length=0)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, p: f"{v:.0f}%"))
    ax.set_ylim(0, max(25, (max(y) if y else 0) + 5))

    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)

    plt.tight_layout()
    return fig


def make_beverage_cost_fig(d, label):
    fig, ax = plt.subplots(figsize=(6, 3.6))
    fig.patch.set_facecolor(COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    x_labels = month_labels_from_graph_dates(d)
    y = d["beverage_cost_pctg_n"]  # année en cours (déjà en %)

    # On garde un rouge proche de ton exemple, sinon dis-moi si tu veux une autre teinte.
    BEV_COLOR = "#e74c3c"

    ax.plot(
        range(len(y)),
        y,
        marker="o",
        linewidth=3,
        markersize=10,
        color=BEV_COLOR,
        zorder=3,
    )

    ax.set_title(
        f"Andamento Beverage Cost Mensile {d['year_n']}",
        color=COLORS["white"],
        fontsize=16,
        fontproperties=epilogue_semibold,
        loc="left",
        pad=10,
    )

    ax.plot([], [], marker="o", linestyle="None", color=BEV_COLOR, label=label)
    leg = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        frameon=False,
        fontsize=10,
        labelcolor=COLORS["white"],
        handlelength=0,
    )
    for t in leg.get_texts():
        t.set_fontproperties(epilogue_regular)

    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(
        x_labels,
        rotation=45,
        ha="right",
        color=COLORS["white"],
        fontsize=9,
        fontproperties=epilogue_regular,
    )
    ax.tick_params(axis="x", colors=COLORS["white"], labelsize=9, length=0)

    ax.tick_params(axis="y", colors=COLORS["white"], labelsize=9, length=0)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, p: f"{v:.0f}%"))
    ax.set_ylim(0, max(12, (max(y) if y else 0) + 2))

    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)

    plt.tight_layout()
    return fig


# =========================
# 9) PDF PAGE 1 (layout)
# =========================

from matplotlib.patches import Rectangle, FancyBboxPatch
from PIL import Image


def _px_to_pt(px, dpi):
    # Matplotlib taille les fonts/linewidths en points.
    # 1 pt = 1/72 inch ; px -> pt dépend du dpi.
    return px * 72.0 / dpi


def _img_rgba(path):
    return Image.open(path).convert("RGBA")


def _trim_transparent(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[-1]
    bbox = alpha.getbbox()
    return img.crop(bbox) if bbox else img


from matplotlib.patches import Rectangle, FancyBboxPatch
from PIL import Image

# =========================
# HEADER 1 — MODULAIRE (px-accurate, imshow-safe)
# =========================
# Dépendances attendues (déjà chez toi) :
# - COLORS, LOGO_PATH
# - epilogue_regular, epilogue_semibold (ou epilogue_regular), ivy_title
# - _px_to_pt(px, dpi), _img_rgba(path), _trim_transparent(img)

HEADER1_CFG = {
    # --- Bordure page ---
    "draw_border": True,
    "border_width_px": 2,
    # --- Ligne du haut (logo + pill) ---
    "logo_enabled": True,
    "logo_w_px": 100,  # largeur logo
    "logo_top_px": 10,  # distance depuis le haut
    "pill_enabled": True,
    "pill_top_px": 80,  # distance depuis le haut
    "pill_right_margin_px": 80,  # marge droite
    "pill_font_px": 14,
    "pill_pad_x_px": 6,
    "pill_pad_y_px": 6,
    "pill_border_width_px": 2,
    # --- Espacements verticaux (le layout “suit” automatiquement) ---
    "gap_after_toprow_px": 20,  # espace après la ligne logo/pill avant le titre
    "gap_title_to_restaurant_px": 10,  # espace titre -> restaurant
    "gap_restaurant_to_line_px": 15,  # espace restaurant -> ligne
    # --- Titre ---
    "title_text": "Report Mensile",
    "title_font_px": 80,
    "title_color": "highlight",  # clé dans COLORS
    "title_fontprops": "ivy_title",
    "title_fontstyle": "italic",
    # --- Restaurant ---
    "restaurant_font_px": 20,
    "restaurant_color": "accent",  # clé dans COLORS
    "restaurant_fontprops": "epilogue_regular",  # ou "epilogue_semibold"
    # --- Ligne ---
    "line_side_margin_px": 80,  # marge gauche/droite
    "line_width_px": 2,
    "line_color": "highlight",  # clé dans COLORS
}


def _measure_text_px(ax, s, font_px, fontprops, dpi, fontstyle=None):
    """Mesure (w_px, h_px) réels du texte rendu, en pixels (ne modifie pas le layout)."""
    t = ax.text(
        0,
        0,
        s,
        transform=ax.transAxes,
        fontsize=_px_to_pt(font_px, dpi),
        fontproperties=fontprops,
        fontstyle=fontstyle,
        alpha=0.0,
    )
    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    bb = t.get_window_extent(renderer=r)
    t.remove()
    return bb.width, bb.height


def _draw_text_top_px(
    ax, y_from_top, top_px, s, font_px, fontprops, dpi, color, z=10, fontstyle=None
):
    """Dessine un texte aligné sur le haut (top_px depuis le haut). Retourne la hauteur px du texte."""
    t = ax.text(
        0.5,
        y_from_top(top_px),
        s,
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=_px_to_pt(font_px, dpi),
        fontproperties=fontprops,
        fontstyle=fontstyle,
        color=color,
        zorder=z,
    )
    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    bb = t.get_window_extent(renderer=r)
    return bb.height


def _draw_header1(
    ax, W_PX, H_PX, month_label: str, restaurant_name: str, dpi: int, cfg=None
):
    cfg = {**HEADER1_CFG, **(cfg or {})}

    # ✅ imshow-safe : on verrouille le repère “page” et on empêche le letterboxing
    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # px -> axes
    def x(px):
        return px / W_PX

    def y_from_top(top_px):
        return 1.0 - (top_px / H_PX)

    def rect_from_top(left_px, top_px, w_px, h_px):
        x0 = x(left_px)
        y1 = y_from_top(top_px)
        y0 = y_from_top(top_px + h_px)
        return x0, y0, (w_px / W_PX), (h_px / H_PX)

    # 1) Logo (haut centre) — pixel perfect
    logo_bottom_px = 0
    if cfg["logo_enabled"] and LOGO_PATH.exists():
        logo = _trim_transparent(_img_rgba(LOGO_PATH))

        LOGO_W_PX = cfg["logo_w_px"]
        LOGO_TOP_PX = cfg["logo_top_px"]

        aspect = logo.width / logo.height
        logo_h_px = LOGO_W_PX / aspect

        left_px = (W_PX - LOGO_W_PX) / 2
        x0_px, x1_px = left_px, left_px + LOGO_W_PX
        y1_px = H_PX - LOGO_TOP_PX
        y0_px = y1_px - logo_h_px

        ax.imshow(
            logo,
            extent=[x(x0_px), x(x1_px), (y0_px / H_PX), (y1_px / H_PX)],
            zorder=1000,
            aspect="auto",  # ✅ crucial : ne pas laisser imshow imposer un aspect
        )

        logo_bottom_px = LOGO_TOP_PX + logo_h_px

    # 2) Pill (date à droite) — largeur/hauteur mesurées (modulaire)
    pill_bottom_px = 0
    if cfg["pill_enabled"]:
        pill_text = month_label

        PILL_TOP_PX = cfg["pill_top_px"]
        PILL_RIGHT_MARGIN_PX = cfg["pill_right_margin_px"]
        pill_font_px = cfg["pill_font_px"]
        pad_x_px = cfg["pill_pad_x_px"]
        pad_y_px = cfg["pill_pad_y_px"]

        text_w_px, text_h_px = _measure_text_px(
            ax, pill_text, pill_font_px, epilogue_regular, dpi
        )
        PILL_W_PX = int(text_w_px + 2 * pad_x_px)
        PILL_H_PX = int(text_h_px + 2 * pad_y_px)

        pill_left_px = W_PX - PILL_RIGHT_MARGIN_PX - PILL_W_PX
        x0, y0, w_ax, h_ax = rect_from_top(
            pill_left_px, PILL_TOP_PX, PILL_W_PX, PILL_H_PX
        )

        ax.add_patch(
            FancyBboxPatch(
                (x0, y0),
                w_ax,
                h_ax,
                boxstyle=f"round,pad=0.0,rounding_size={min(h_ax/2, w_ax/2)}",
                transform=ax.transAxes,
                facecolor=COLORS["bg"],
                edgecolor=COLORS["highlight"],
                linewidth=_px_to_pt(cfg["pill_border_width_px"], dpi),
                zorder=900,
            )
        )
        ax.text(
            x0 + w_ax / 2,
            y0 + h_ax / 2,
            pill_text,
            transform=ax.transAxes,
            ha="center",
            va="center",
            color=COLORS["white"],
            fontsize=_px_to_pt(pill_font_px, dpi),
            fontproperties=epilogue_regular,
            zorder=901,
        )

        pill_bottom_px = PILL_TOP_PX + PILL_H_PX

    # 3) Curseur vertical : démarre sous la “top row” (logo/pill) de façon modulaire
    toprow_bottom_px = max(logo_bottom_px, pill_bottom_px)
    y_cursor_px = toprow_bottom_px + cfg["gap_after_toprow_px"]

    # 4) Titre (centre) — hauteur mesurée -> y_cursor avance tout seul
    title_text = cfg["title_text"]
    title_font_px = cfg["title_font_px"]
    title_color = COLORS[cfg["title_color"]]
    title_fontprops = globals()[cfg["title_fontprops"]]  # ivy_title
    title_fontstyle = cfg["title_fontstyle"]

    h_title_px = _draw_text_top_px(
        ax,
        y_from_top,
        y_cursor_px,
        title_text,
        title_font_px,
        title_fontprops,
        dpi,
        title_color,
        z=850,
        fontstyle=title_fontstyle,
    )
    y_cursor_px += h_title_px + cfg["gap_title_to_restaurant_px"]

    # 5) Restaurant (centre) — hauteur mesurée -> y_cursor avance tout seul
    resto_text = (restaurant_name or "").upper()
    resto_font_px = cfg["restaurant_font_px"]
    resto_color = COLORS[cfg["restaurant_color"]]
    resto_fontprops = globals()[
        cfg["restaurant_fontprops"]
    ]  # epilogue_regular/semibold

    h_resto_px = _draw_text_top_px(
        ax,
        y_from_top,
        y_cursor_px,
        resto_text,
        resto_font_px,
        resto_fontprops,
        dpi,
        resto_color,
        z=850,
    )
    y_cursor_px += h_resto_px + cfg["gap_restaurant_to_line_px"]

    # 6) Ligne (sous le restaurant)
    SIDE_MARGIN_PX = cfg["line_side_margin_px"]
    ax.hlines(
        y=y_from_top(y_cursor_px),
        xmin=x(SIDE_MARGIN_PX),
        xmax=x(W_PX - SIDE_MARGIN_PX),
        colors=COLORS[cfg["line_color"]],
        linewidth=_px_to_pt(cfg["line_width_px"], dpi),
        zorder=800,
    )
    return y_cursor_px  # ✅ position de la ligne en px depuis le haut


# =========================
# BODY 1 — FATTURATO (px-accurate, "modulaire", imshow-safe)
# =========================
# Dépendances attendues (déjà chez toi) :
# - COLORS, ARROW_UP_PATH, ARROW_DOWN_PATH
# - epilogue_regular, epilogue_semibold, ivy_title
# - _px_to_pt(px, dpi), _img_rgba(path), _trim_transparent(img)
# - fmt_eur_dot(x), (optionnel) fmt_pct_1(x)
# - matplotlib.ticker as ticker

import textwrap
import matplotlib.ticker as ticker

BODY1_CFG = {
    # --- Marges / colonnes ---
    "side_margin_px": 80,  # marge gauche/droite globale
    "col_gap_px": 40,  # espace entre colonne gauche et droite
    "left_col_ratio": 0.56,  # % de largeur pour la colonne gauche (graph)
    # --- Zone de départ du body (depuis le haut de la page) ---
    "gap_after_header_px": 20,  # espace entre la ligne du header et le début du body
    # --- Kicker (nom resto en haut du body) + ligne ---
    "kicker_enabled": False,
    "kicker_font_px": 18,
    "kicker_gap_after_px": 10,
    "kicker_line_enabled": False,
    "kicker_line_width_px": 2,
    "kicker_line_gap_after_px": 18,
    # --- Titre section (fixe) ---
    "section_title_text": "Fatturato",
    "section_title_font_px": 36,
    "section_title_gap_after_px": 16,
    # --- Sous-titres colonne gauche ---
    "left_title_font_px": 20,  # "Venduto ..."
    "left_subtitle_font_px": 16,  # "2025 vs 2024"
    "left_titles_gap_px": 8,
    "left_titles_to_chart_gap_px": 18,
    # --- Chart (barres) ---
    "chart_h_px": 250,  # hauteur chart dans la page
    "chart_value_font_px": 14,  # valeurs au dessus des barres
    "chart_tick_font_px": 12,
    "chart_label_font_px": 12,
    "chart_legend_font_px": 12,
    "chart_top_extra_px": 36,  # espace interne pour loger la légende
    # --- Bloc stats colonne droite ---
    "stats_title_font_px": 14,  # "Fatturato Dicembre 2025 €"
    "stats_value_font_px": 26,  # "565.048 €"
    "stats_vs_font_px": 14,  # "vs 2024"
    "stats_pct_font_px": 20,  # "+3.1%"
    "stats_gap_1_px": 10,
    "stats_gap_2_px": 18,
    "stats_gap_3_px": 16,
    # --- Flèche variation ---
    "arrow_w_px": 24,  # taille icône flèche
    "arrow_gap_right_px": 10,  # espace entre flèche et %
    # --- Ligne sous stats ---
    "stats_line_enabled": True,
    "stats_line_width_px": 2,
    "stats_line_gap_after_px": 18,
    "stats_line_left_inset_px": 0,  # décale le début de la ligne dans la colonne droite (0 = align à gauche)
    # La fin de la ligne est alignée à droite avec la même marge que "side_margin_px"
    # --- Paragraphe (texte) ---
    "para_font_px": 14,
    "para_linespacing": 1.6,
    "para_wrap_factor": 0.55,  # approx largeur caractère = font_px*0.55
}


def _draw_text_top_left_px(
    ax,
    x_px,
    y_from_top,
    top_px,
    s,
    font_px,
    fontprops,
    dpi,
    color,
    z=10,
    fontstyle=None,
):
    """Texte aligné left/top à une position pixel (x_px, top_px). Retourne hauteur px."""
    t = ax.text(
        x_px / ax._W_PX,  # injecté plus bas
        y_from_top(top_px),
        s,
        ha="left",
        va="top",
        transform=ax.transAxes,
        fontsize=_px_to_pt(font_px, dpi),
        fontproperties=fontprops,
        fontstyle=fontstyle,
        color=color,
        zorder=z,
    )
    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    bb = t.get_window_extent(renderer=r)
    return bb.height


def _draw_text_top_center_px(
    ax, y_from_top, top_px, s, font_px, fontprops, dpi, color, z=10, fontstyle=None
):
    """Texte aligné center/top. Retourne hauteur px."""
    t = ax.text(
        0.5,
        y_from_top(top_px),
        s,
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=_px_to_pt(font_px, dpi),
        fontproperties=fontprops,
        fontstyle=fontstyle,
        color=color,
        zorder=z,
    )
    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    bb = t.get_window_extent(renderer=r)
    return bb.height


def _place_img_px(ax, img, W_PX, H_PX, left_px, top_px, width_px, z=1000):
    """Place une image RGBA au pixel près (top-left)."""
    aspect = img.width / img.height
    height_px = width_px / aspect

    x0_px, x1_px = left_px, left_px + width_px
    y1_px = H_PX - top_px
    y0_px = y1_px - height_px

    ax.imshow(
        img,
        extent=[x0_px / W_PX, x1_px / W_PX, y0_px / H_PX, y1_px / H_PX],
        zorder=z,
        aspect="auto",  # ✅ imshow-safe
    )
    return height_px


def _draw_fatturato_chart_in_page(fig, left, bottom, width, height, d, label, cfg, dpi):
    """
    Reproduit ton make_fatturato_fig mais directement dans la page (vector, pas raster).
    left/bottom/width/height sont en coords figure (0..1).
    """
    axc = fig.add_axes([left, bottom, width, height], facecolor=COLORS["bg"])
    axc.set_facecolor(COLORS["bg"])

    values = [d["fatturato_n"], d["fatturato_n_1"]]
    x = [0, 1]

    axc.bar(x, values, width=0.95, color=[COLORS["graph1"], COLORS["graph2"]], zorder=3)
    axc.set_xlim(-0.55, 1.55)

    for i, v in enumerate(values):
        axc.text(
            i,
            v + max(values) * 0.02,
            f"{int(round(v)):,}".replace(",", "."),
            ha="center",
            va="bottom",
            fontsize=_px_to_pt(cfg["chart_value_font_px"], dpi),
            color=COLORS["white"],
            fontproperties=epilogue_semibold,
        )

    axc.set_xticks([0.5])
    axc.set_xticklabels(
        [label],
        color=COLORS["white"],
        fontsize=_px_to_pt(cfg["chart_label_font_px"], dpi),
        fontproperties=epilogue_regular,
    )

    axc.tick_params(
        axis="y",
        colors=COLORS["white"],
        labelsize=_px_to_pt(cfg["chart_tick_font_px"], dpi),
        length=0,
    )
    axc.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, p: f"{int(y):,}".replace(",", "."))
    )
    axc.set_ylim(0, max(values) * 1.2)

    axc.grid(axis="y", linestyle="-", alpha=0.15, color=COLORS["white"], zorder=0)
    for s in axc.spines.values():
        s.set_visible(False)

    # Légende (on la place dans le haut de la zone chart, sans sortir)
    legend_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS["graph1"],
            markersize=8,
            label=f"Fatturato {d['year_n']} €",
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS["graph2"],
            markersize=8,
            label=f"Fatturato {d['year_n_1']} €",
        ),
    ]
    axc.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.0),  # reste dans le cadre
        ncol=2,
        frameon=False,
        fontsize=_px_to_pt(cfg["chart_legend_font_px"], dpi),
        labelcolor=COLORS["white"],
    )
    return axc


def _draw_body1_fatturato(
    ax, W_PX, H_PX, d, restaurant_name: str, analysis_text: str, dpi: int, cfg=None
):
    """
    Corps page 1 "Fatturato" (à appeler après le header).
    IMPORTANT: ne touche pas l'aspect/limits en dehors => imshow-safe.
    """
    cfg = {**BODY1_CFG, **(cfg or {})}

    # ✅ imshow-safe : on verrouille le repère “page”
    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # petit hack interne pour helper left/top
    ax._W_PX = W_PX

    def x(px):
        return px / W_PX

    def y_from_top(top_px):
        return 1.0 - (top_px / H_PX)

    side = cfg["side_margin_px"]
    gap = cfg["col_gap_px"]

    usable_w = W_PX - 2 * side - gap
    left_w = int(usable_w * cfg["left_col_ratio"])
    right_w = usable_w - left_w

    left_x0 = side
    right_x0 = side + left_w + gap
    right_x1 = W_PX - side

    header_line_y_px = cfg.get("header_line_y_px", 0)
    y = int(header_line_y_px + cfg["gap_after_header_px"])

    # --- Kicker + ligne ---
    if cfg["kicker_enabled"]:
        h = _draw_text_top_center_px(
            ax,
            y_from_top,
            y,
            (restaurant_name or "").upper(),
            cfg["kicker_font_px"],
            epilogue_semibold,
            dpi,
            COLORS["accent"],
            z=850,
        )
        y += h + cfg["kicker_gap_after_px"]

    if cfg["kicker_line_enabled"]:
        ax.hlines(
            y=y_from_top(y),
            xmin=x(side),
            xmax=x(W_PX - side),
            colors=COLORS["highlight"],
            linewidth=_px_to_pt(cfg["kicker_line_width_px"], dpi),
            zorder=800,
        )
        y += cfg["kicker_line_gap_after_px"]

    # --- Section title (fixe) ---
    h_sec = _draw_text_top_center_px(
        ax,
        y_from_top,
        y,
        cfg["section_title_text"],
        cfg["section_title_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["accent"],
        z=850,
    )
    y += h_sec + cfg["section_title_gap_after_px"]

    # --- Colonne gauche : titres (variables) ---
    left_title = f"Venduto {restaurant_name} {d['month_name']}"
    left_sub = f"{d['year_n']} vs {d['year_n_1']}"

    h1 = _draw_text_top_left_px(
        ax,
        left_x0,
        y_from_top,
        y,
        left_title,
        cfg["left_title_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["white"],
        z=850,
    )
    y_left = y + h1 + cfg["left_titles_gap_px"]

    h2 = _draw_text_top_left_px(
        ax,
        left_x0,
        y_from_top,
        y_left,
        left_sub,
        cfg["left_subtitle_font_px"],
        epilogue_regular,
        dpi,
        COLORS["white"],
        z=850,
    )
    y_left = y_left + h2 + cfg["left_titles_to_chart_gap_px"]

    # --- Colonne gauche : chart ---
    chart_top = y_left
    chart_h = cfg["chart_h_px"]
    chart_w = left_w

    # coords figure pour add_axes
    fig = ax.figure
    chart_left_ax = x(left_x0)
    chart_bottom_ax = y_from_top(chart_top + chart_h)
    chart_w_ax = chart_w / W_PX
    chart_h_ax = chart_h / H_PX

    _draw_fatturato_chart_in_page(
        fig,
        left=chart_left_ax,
        bottom=chart_bottom_ax,
        width=chart_w_ax,
        height=chart_h_ax,
        d=d,
        label=restaurant_name,
        cfg=cfg,
        dpi=dpi,
    )

    # --- Colonne droite : bloc stats aligné au chart_top ---
    yR = chart_top

    stats_title = f"Fatturato {d['month_name']} {d['year_n']} €"
    hst = _draw_text_top_left_px(
        ax,
        right_x0,
        y_from_top,
        yR,
        stats_title,
        cfg["stats_title_font_px"],
        epilogue_regular,
        dpi,
        COLORS["white"],
        z=850,
    )
    yR += hst + cfg["stats_gap_1_px"]

    # valeur
    value_txt = fmt_eur_dot(d["fatturato_n"])
    hv = _draw_text_top_left_px(
        ax,
        right_x0,
        y_from_top,
        yR,
        value_txt,
        cfg["stats_value_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["highlight"],
        z=850,
    )
    yR += hv + cfg["stats_gap_2_px"]

    # vs N-1
    vs_txt = f"vs {d['year_n_1']}"
    hvs = _draw_text_top_left_px(
        ax,
        right_x0,
        y_from_top,
        yR,
        vs_txt,
        cfg["stats_vs_font_px"],
        epilogue_regular,
        dpi,
        COLORS["white"],
        z=850,
    )
    yR += hvs + cfg["stats_gap_1_px"]

    # flèche + %
    pct = d.get("diff_fatturato", 0.0)
    try:
        pct_txt = fmt_pct_1(pct)
    except NameError:
        pct_txt = f"{'+' if pct >= 0 else ''}{pct:.1f}%"

    arrow_path = ARROW_UP_PATH if pct >= 0 else ARROW_DOWN_PATH
    arrow_w = cfg["arrow_w_px"]

    # place flèche
    if arrow_path.exists():
        arrow_img = _trim_transparent(_img_rgba(arrow_path))
        _place_img_px(
            ax,
            arrow_img,
            W_PX,
            H_PX,
            left_px=right_x0,
            top_px=yR,
            width_px=arrow_w,
            z=900,
        )

    # place % à côté
    _draw_text_top_left_px(
        ax,
        right_x0 + arrow_w + cfg["arrow_gap_right_px"],
        y_from_top,
        yR + 2,  # micro-ajustement visuel
        pct_txt,
        cfg["stats_pct_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["highlight"],
        z=850,
    )
    yR += (
        cfg["stats_pct_font_px"] * 2 + cfg["stats_gap_3_px"]
    )  # avance “assez” (simple & stable)

    # --- ligne sous stats (align droite avec la marge side) ---
    if cfg["stats_line_enabled"]:
        ax.hlines(
            y=y_from_top(yR),
            xmin=x(right_x0 + cfg["stats_line_left_inset_px"]),
            xmax=x(right_x1),
            colors=COLORS["highlight"],
            linewidth=_px_to_pt(cfg["stats_line_width_px"], dpi),
            zorder=800,
        )
        yR += cfg["stats_line_gap_after_px"]

    # --- paragraphe (à droite) ---
    col_px = right_x1 - right_x0
    wrap_chars = max(20, int(col_px / (cfg["para_font_px"] * cfg["para_wrap_factor"])))
    text_wrapped = textwrap.fill((analysis_text or "").strip(), width=wrap_chars)

    ax.text(
        x(right_x0),
        y_from_top(yR),
        text_wrapped,
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=COLORS["white"],
        fontsize=_px_to_pt(cfg["para_font_px"], dpi),
        fontproperties=epilogue_regular,
        linespacing=cfg["para_linespacing"],
        zorder=850,
    )


def _draw_a4_page(ax, W_PX, H_PX, d, restaurant_name: str):
    # Repère "page" 0..1 (aspect auto pour éviter que imshow dérègle l’axe)
    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    dpi = int(ax.figure.dpi)

    # Header 1 : logo + pill date + titre + restaurant + ligne
    header_line_y_px = (
        _draw_header1(
            ax,
            W_PX=W_PX,
            H_PX=H_PX,
            month_label=d["full_date_n"],
            restaurant_name=restaurant_name,
            dpi=dpi,
        )
        or 0
    )

    # Texte d’analyse (généré automatiquement)
    p1, p2 = build_page1_suggestions(d)
    analysis_text = f"{p1}\n\n{p2}"

    # Body 1 : section Fatturato (titres + chart + stats + paragraphe)
    _draw_body1_fatturato(
        ax,
        W_PX,
        H_PX,
        d,
        restaurant_name,
        analysis_text,
        dpi,
        cfg={"header_line_y_px": header_line_y_px},
    )


# ✅ Taille cible en pixels (ton nouveau "format")
PAGE_W_PX = 800
PAGE_H_PX = 1000

# ✅ DPI de référence : fixe la taille physique du PDF
BASE_DPI = 100

# ✅ Taille “physique” (inches) qui correspond à 800x1000 px à BASE_DPI
PAGE_SIZE_INCH = (PAGE_W_PX / BASE_DPI, PAGE_H_PX / BASE_DPI)


def build_a4_pdf_bytes(d, restaurant_name: str, dpi=300) -> bytes:
    """
    PDF: on verrouille le format à 800x1000 via PAGE_SIZE_INCH + BASE_DPI.
    Le param `dpi` n'est plus utilisé ici pour éviter de changer la taille physique.
    (garde la signature pour ne rien casser ailleurs)
    """
    fig = plt.figure(figsize=PAGE_SIZE_INCH, dpi=BASE_DPI, facecolor=COLORS["bg"])
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])

    # ✅ layout basé sur la "grille" 800x1000
    W_PX, H_PX = PAGE_W_PX, PAGE_H_PX
    _draw_a4_page(ax, W_PX, H_PX, d, restaurant_name)

    buf = BytesIO()
    fig.savefig(
        buf,
        format="pdf",
        bbox_inches=None,
        pad_inches=0,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def build_a4_png_preview_bytes(d, restaurant_name: str, dpi=150) -> bytes:
    """
    PNG: on peut utiliser `dpi` uniquement pour la netteté de l'aperçu,
    MAIS le layout reste basé sur 800x1000.
    """
    fig = plt.figure(figsize=PAGE_SIZE_INCH, dpi=dpi, facecolor=COLORS["bg"])
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])

    # ✅ layout basé sur la "grille" 800x1000 (indépendant du dpi de rendu)
    W_PX, H_PX = PAGE_W_PX, PAGE_H_PX
    _draw_a4_page(ax, W_PX, H_PX, d, restaurant_name)

    buf = BytesIO()
    fig.savefig(
        buf,
        format="png",
        bbox_inches=None,
        pad_inches=0,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# =========================
# 10) UI
# =========================
st.title("Report Fizzy Automatizzazione ⚡️")

restaurant_input = st.sidebar.text_input("Nome clienti *", value="LEITAO")
uploaded = st.sidebar.file_uploader("Caricare il Report (.xslx))", type="xlsx")

if uploaded and restaurant_input:
    data = load_data(uploaded)

    col_viz, col_edit = st.columns([1, 1])

    with col_viz:
        st.subheader("📊 Fatturato Mensile (preview)")
        preview_fig = make_fatturato_fig(data, label=restaurant_input)
        st.pyplot(preview_fig)

    with col_edit:
        st.subheader("✍️ Analisa scritta (modificabile)")

        p1_default, p2_default = build_page1_suggestions(data)

        p1 = st.text_area("Paragrafo 1", value=p1_default, height=160)
        p2 = st.text_area("Paragrafo 2", value=p2_default, height=160)

        analysis_text = f"{p1}\n\n{p2}"

    # --- Section graphs pleine largeur ---
    st.divider()

    # =========================
    # FOOD COST
    # =========================
    st.subheader("📈 Food Cost (mensile)")
    food_col_graph, food_col_text = st.columns([1.2, 1], gap="large")

    with food_col_graph:
        food_fig = make_food_cost_fig(data, label=restaurant_input)
        st.pyplot(food_fig)

    with food_col_text:
        st.text_area("📝 Commento Food Cost", value="", height=280, key="food_comment")

    # =========================
    # BEVERAGE COST
    # =========================
    st.subheader("📈 Beverage Cost (mensile)")
    bev_col_graph, bev_col_text = st.columns([1.2, 1], gap="large")

    with bev_col_graph:
        bev_fig = make_beverage_cost_fig(data, label=restaurant_input)
        st.pyplot(bev_fig)

    with bev_col_text:
        st.text_area(
            "📝 Commento Beverage Cost", value="", height=280, key="beverage_comment"
        )
# --- UI : Download PDF ---
st.divider()

# (assure-toi que png_bytes est généré avant)
png_bytes = build_a4_png_preview_bytes(data, restaurant_input, dpi=150)

c1, c2 = st.columns([1.5, 1], gap="large")

with c1:
    st.image(png_bytes, caption="Aperçu (PNG)", use_container_width=True)

with c2:
    st.subheader("📄 Export PDF")

    pdf_bytes = build_a4_pdf_bytes(data, restaurant_input, dpi=300)

    st.download_button(
        label="⬇️ Scarica PDF",
        data=pdf_bytes,
        file_name=f"Report_{restaurant_input}.pdf",
        mime="application/pdf",
    )
