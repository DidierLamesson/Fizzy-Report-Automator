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
# 1) CONFIG STREAMLIT
# =========================
st.set_page_config(page_title="FIZZY Automator", layout="wide")


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
# 8) PREVIEW FIG (simple)
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


# =========================
# 9) PDF PAGE 1 (layout)
# =========================
def _img_rgba(path: Path):
    return Image.open(path).convert("RGBA")


def _place_img(ax, img: Image.Image, x, y, w, z=5):
    """Place image with center at (x,y) in ax coords (0..1), width=w in ax coords."""
    aspect = img.width / img.height
    h = w / aspect
    x0, x1 = x - w / 2, x + w / 2
    y0, y1 = y - h / 2, y + h / 2
    ax.imshow(img, extent=[x0, x1, y0, y1], zorder=z)


def _pill(ax, x, y, w, h, text, fill=False):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.008,rounding_size=0.02",
        linewidth=1.2,
        edgecolor=COLORS["white"],
        facecolor=(0, 0, 0, 0) if not fill else (0, 0, 0, 0.65),
        alpha=0.9,
        zorder=10,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=12,
        fontproperties=epilogue_regular,
        zorder=11,
    )


def render_page1_fig(d, restaurant_name, analysis_text):
    dpi = 100
    fig = plt.figure(figsize=(1200 / dpi, 1500 / dpi), dpi=dpi, facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # --- DEBUG GRID (mettre True pour caler la mise en page) ---
    DEBUG_GRID = True
    if DEBUG_GRID:
        for gx in [i / 10 for i in range(1, 10)]:
            ax.plot([gx, gx], [0, 1], color="white", alpha=0.08, lw=1, zorder=1)
        for gy in [i / 10 for i in range(1, 10)]:
            ax.plot([0, 1], [gy, gy], color="white", alpha=0.08, lw=1, zorder=1)

    # Images
    logo = _img_rgba(LOGO_PATH)
    arrow_up = _img_rgba(ARROW_UP_PATH)
    arrow_down = _img_rgba(ARROW_DOWN_PATH)
    arrow_round = _img_rgba(ARROW_ROUND_PATH)

    # Header
    _place_img(ax, logo, x=0.50, y=0.955, w=0.22, z=10)
    _pill(
        ax,
        x=0.72,
        y=0.92,
        w=0.22,
        h=0.050,
        text=f"{d['month_name']} {d['year_n']}",
        fill=False,
    )

    ax.text(
        0.5,
        0.865,
        "Report Mensile",
        ha="center",
        va="center",
        color=COLORS["highlight"],
        fontsize=58,
        fontproperties=ivy_title,
        style="italic",
    )

    ax.text(
        0.5,
        0.815,
        restaurant_name.upper(),
        ha="center",
        va="center",
        color=COLORS["accent"],
        fontsize=20,
        fontproperties=epilogue_semibold,
    )

    ax.plot([0.10, 0.90], [0.785, 0.785], color=COLORS["white"], alpha=0.65, lw=1)

    # Section title
    ax.text(
        0.5,
        0.715,
        "Fatturato",
        ha="center",
        va="center",
        color=COLORS["accent"],
        fontsize=26,
        fontproperties=epilogue_semibold,
    )

    # Left block title
    ax.text(
        0.26,
        0.665,
        f"Venduto {restaurant_name} {d['month_name']}",
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=15,
        fontproperties=epilogue_semibold,
    )
    ax.text(
        0.26,
        0.642,
        f"{d['year_n']} vs {d['year_n_1']}",
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=12,
        fontproperties=epilogue_regular,
    )

    # Bar chart
    ax_bar = fig.add_axes([0.13, 0.36, 0.36, 0.25], facecolor=COLORS["bg"])
    vals = [d["fatturato_n"], d["fatturato_n_1"]]
    ax_bar.bar(
        [0, 1], vals, color=[COLORS["graph1"], COLORS["graph2"]], width=0.90, zorder=3
    )

    for i, v in enumerate(vals):
        ax_bar.text(
            i,
            v + max(vals) * 0.02,
            f"{int(round(v)):,}".replace(",", "."),
            ha="center",
            va="bottom",
            fontsize=10,
            color=COLORS["white"],
            fontproperties=epilogue_semibold,
        )

    ax_bar.set_xticks([0.5])
    ax_bar.set_xticklabels(
        [restaurant_name],
        color=COLORS["white"],
        fontsize=9,
        fontproperties=epilogue_regular,
    )
    ax_bar.tick_params(axis="y", colors=COLORS["white"], labelsize=9, length=0)
    ax_bar.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda y, p: f"{int(y):,}".replace(",", "."))
    )
    ax_bar.set_ylim(0, max(vals) * 1.25)
    ax_bar.grid(
        axis="y",
        color=COLORS["white"],
        linestyle="-",
        linewidth=0.6,
        alpha=0.18,
        zorder=0,
    )
    for s in ax_bar.spines.values():
        s.set_visible(False)

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
    ax_bar.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.10),
        ncol=2,
        frameon=False,
        fontsize=8,
        labelcolor=COLORS["white"],
    )

    # Right KPI block
    ax.text(
        0.62,
        0.64,
        f"Fatturato {d['month_name']} {d['year_n']} €",
        ha="left",
        va="center",
        color=COLORS["white"],
        fontsize=11,
        fontproperties=epilogue_semibold,
    )

    ax.text(
        0.62,
        0.605,
        fmt_eur_dot(d["fatturato_n"]),
        ha="left",
        va="center",
        color=COLORS["highlight"],
        fontsize=26,
        fontproperties=epilogue_semibold,
    )

    arrow_img = arrow_up if d["diff_fatturato"] >= 0 else arrow_down
    _place_img(ax, arrow_img, x=0.60, y=0.605, w=0.035, z=12)

    ax.text(
        0.62,
        0.565,
        f"vs {d['year_n_1']}",
        ha="left",
        va="center",
        color=COLORS["white"],
        fontsize=11,
        fontproperties=epilogue_regular,
    )

    ax.text(
        0.62,
        0.535,
        fmt_pct_1(d["diff_fatturato"]),
        ha="left",
        va="center",
        color=COLORS["accent"],
        fontsize=20,
        fontproperties=epilogue_semibold,
    )
    _place_img(ax, arrow_img, x=0.60, y=0.535, w=0.035, z=12)

    ax.plot([0.60, 0.90], [0.505, 0.505], color=COLORS["white"], alpha=0.25, lw=1)

    # Analysis text (user)
    wrapped = wrap_for_box(analysis_text, width=44)
    ax.text(
        0.62,
        0.485,
        wrapped,
        ha="left",
        va="top",
        color=COLORS["white"],
        fontsize=12,
        fontproperties=epilogue_regular,
        linespacing=1.6,
    )

    # Bottom separator
    ax.plot([0.10, 0.90], [0.18, 0.18], color=COLORS["white"], alpha=0.35, lw=1)

    # Bottom titles
    ax.text(
        0.26,
        0.14,
        "Ricavi - Costi",
        ha="center",
        va="center",
        color=COLORS["accent"],
        fontsize=16,
        fontproperties=epilogue_semibold,
    )
    ax.text(
        0.74,
        0.14,
        "Margine % su ricavi",
        ha="center",
        va="center",
        color=COLORS["accent"],
        fontsize=16,
        fontproperties=epilogue_semibold,
    )

    # Bottom values (Ricavi - Costi)
    ax.text(
        0.16,
        0.095,
        f"{d['month_name']} {d['year_n']}",
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
    )
    ax.text(
        0.16,
        0.065,
        fmt_eur_dot(d["ric_cost_n"]),
        ha="center",
        va="center",
        color=COLORS["highlight"],
        fontsize=18,
        fontproperties=epilogue_semibold,
    )

    ax.text(
        0.36,
        0.095,
        f"vs {d['year_n_1']}",
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
    )
    ax.text(
        0.36,
        0.065,
        fmt_eur_dot(d["ric_cost_n_1"]),
        ha="center",
        va="center",
        color=COLORS["highlight"],
        fontsize=18,
        fontproperties=epilogue_semibold,
    )

    # Divider
    ax.plot(
        [0.50, 0.50],
        [0.05, 0.11],
        color=COLORS["white"],
        alpha=0.45,
        lw=2,
        linestyle="--",
    )

    # Bottom values (Margine) - 1 décimale
    ax.text(
        0.66,
        0.095,
        f"{d['month_name']} {d['year_n']}",
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
    )
    ax.text(
        0.66,
        0.065,
        f"{d['marg_n']:.1f}%",
        ha="center",
        va="center",
        color=COLORS["highlight"],
        fontsize=18,
        fontproperties=epilogue_semibold,
    )

    ax.text(
        0.82,
        0.095,
        f"vs {d['year_n_1']}",
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
    )
    ax.text(
        0.82,
        0.065,
        f"{d['marg_n_1']:.1f}%",
        ha="center",
        va="center",
        color=COLORS["highlight"],
        fontsize=18,
        fontproperties=epilogue_semibold,
    )

    # Round arrow bottom right
    _place_img(ax, arrow_round, x=0.92, y=0.09, w=0.07, z=20)

    return fig


def build_page1_pdf_bytes(d, restaurant_name, analysis_text):
    fig = render_page1_fig(d, restaurant_name, analysis_text)
    buf = BytesIO()
    fig.savefig(buf, format="pdf", facecolor=COLORS["bg"])
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def build_page1_png_bytes(d, restaurant_name, analysis_text):
    fig = render_page1_fig(d, restaurant_name, analysis_text)
    buf = BytesIO()
    fig.savefig(buf, format="png", facecolor=COLORS["bg"], dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# =========================
# 10) UI
# =========================
st.title("Report Fizzy Automatizzazione ⚡️")

restaurant_input = st.sidebar.text_input(
    "Nome clienti *", value="A'RICCIONE - TERRAZZA"
)
uploaded = st.sidebar.file_uploader("Charger le fichier Excel", type="xlsx")

if uploaded and restaurant_input:
    data = load_data(uploaded)

    col_viz, col_edit = st.columns([1, 1])

    with col_viz:
        st.subheader("📊 Fatturato Mensile (preview)")
        preview_fig = make_fatturato_fig(data, label=restaurant_input)
        st.pyplot(preview_fig)

    with col_edit:
        st.subheader("✍️ Analyse Narrative")

        p1_default, p2_default = build_page1_suggestions(data)

        p1 = st.text_area("Paragrafo 1", value=p1_default, height=160)
        p2 = st.text_area("Paragrafo 2", value=p2_default, height=160)

        analysis_text = f"{p1}\n\n{p2}"

        st.divider()

        st.subheader("👀 Aperçu Page 1 (live)")

        png_bytes = build_page1_png_bytes(data, restaurant_input, analysis_text)
        st.image(png_bytes, use_container_width=False)

        # Optionnel : garder un download PDF (sans bouton, calculé à la volée)
        pdf_bytes = build_page1_pdf_bytes(data, restaurant_input, analysis_text)
        file_name = f"Report_{restaurant_input}_{data['month_name']}_{data['year_n']}_page1.pdf".replace(
            " ", "_"
        )

        st.download_button(
            "⬇️ Télécharger le PDF (Page 1)",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
        )
