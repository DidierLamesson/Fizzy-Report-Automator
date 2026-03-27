import re
from io import BytesIO
from pathlib import Path

import fitz  # pip install pymupdf
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import base64
import streamlit as st
from matplotlib.patches import Arc, FancyBboxPatch
from PIL import Image

# =========================
# 1) CONSTANTES VISUELLES (couleurs + mois)
# =========================
COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph1": "#918d84",
    "graph2": "#ece8e1",
    "white": "#ffffff",
}

MONTHS_IT = {
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

# =========================
# 2) CHEMINS DES ASSETS
# =========================
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
IMG_DIR = ASSETS_DIR / "img"

# Polices
FONT_EPILOGUE_REG = FONTS_DIR / "Epilogue-Regular.otf"
FONT_EPILOGUE_ITALIC = FONTS_DIR / "Epilogue-Italic.otf"
FONT_EPILOGUE_SEMIBOLD = FONTS_DIR / "Epilogue-SemiBold.otf"
FONT_EPILOGUE_SEMIBOLD_ITALIC = FONTS_DIR / "Epilogue-SemiBoldItalic.otf"
FONT_IVY = FONTS_DIR / "fonnts.com-Ivy-Presto-Display-Light.otf"

# Images
LOGO_PATH = IMG_DIR / "Logo Fizzy.png"
ARROW_UP_PATH = IMG_DIR / "Arrow_up.png"
ARROW_DOWN_PATH = IMG_DIR / "Arrow_down.png"


# =========================
# 3) CONFIGURATION DES POLICES MATPLOTLIB
# =========================
def _register_font(path: Path):
    if path.exists():
        fm.fontManager.addfont(str(path))


for font_path in (
    FONT_EPILOGUE_REG,
    FONT_EPILOGUE_ITALIC,
    FONT_EPILOGUE_SEMIBOLD,
    FONT_EPILOGUE_SEMIBOLD_ITALIC,
    FONT_IVY,
):
    _register_font(font_path)

epilogue_regular = fm.FontProperties(fname=str(FONT_EPILOGUE_REG))
epilogue_italic = fm.FontProperties(fname=str(FONT_EPILOGUE_ITALIC))
epilogue_semibold = fm.FontProperties(fname=str(FONT_EPILOGUE_SEMIBOLD))
epilogue_semibold_italic = fm.FontProperties(fname=str(FONT_EPILOGUE_SEMIBOLD_ITALIC))
ivy_title = fm.FontProperties(fname=str(FONT_IVY))

plt.rcParams["font.family"] = epilogue_regular.get_name()
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

# =========================
# 4) CONFIGURATION STREAMLIT
# =========================
st.set_page_config(
    page_title="FIZZY Automator",
    page_icon="⚡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _img_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def inject_brand_logo():
    soda_logo_uri = _img_to_data_uri(LOGO_PATH)
    if not soda_logo_uri:
        return

    st.html(
        f"""
        <div class="soda-header-logo">
            <img src="{soda_logo_uri}" alt="We are Soda" />
        </div>
        """
    )


# --- State langue ---
if "lang" not in st.session_state:
    st.session_state["lang"] = "it"


def _t(it_text, fr_text):
    """Retourne le texte selon la langue active."""
    return fr_text if st.session_state["lang"] == "fr" else it_text


def inject_brand_css():
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@400;500;600;700;800&display=swap');

        /* =========================
           1) TOKENS
        ========================= */
        :root {
            --soda-blue: #11324F;
            --soda-blue-dark: #28504D;
            --soda-green: #758D5A;
            --soda-acid: #F0FF6E;
            --soda-text: #1B252E;
            --soda-text-soft: #2C3E50;
            --soda-bg: #F5F3EE;
            --soda-white: #FFFFFF;
            --soda-border: rgba(17, 50, 79, 0.16);
            --soda-border-soft: rgba(17, 50, 79, 0.10);
            --soda-sidebar-grad: linear-gradient(180deg, var(--soda-blue) 0%, var(--soda-blue-dark) 100%);
            --soda-main-grad:
                radial-gradient(circle at top left, rgba(17, 50, 79, 0.07) 0%, transparent 32%),
                radial-gradient(circle at bottom right, rgba(117, 141, 90, 0.10) 0%, transparent 36%),
                linear-gradient(180deg, #F7F5F0 0%, #EEF1E8 100%);
        }

        /* =========================
           2) BASE GLOBALE
        ========================= */
        html, body, [class*="css"] {
            font-family: "Epilogue", sans-serif;
        }

        .stApp {
            background: #F4F3EE !important;
            color: var(--soda-text) !important;
        }

        hr {
            border-color: rgba(17, 50, 79, 0.12) !important;
        }

        h1, h2, h3 {
            font-family: "Epilogue", sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em;
            color: var(--soda-blue);
        }

        p, label, .stMarkdown {
            color: var(--soda-text) !important;
        }

        /* Boutons globaux */
        .stButton > button,
        .stDownloadButton > button {
            background: var(--soda-acid) !important;
            color: var(--soda-blue) !important;
            border: none !important;
            border-radius: 999px !important;
            font-family: "Epilogue", sans-serif !important;
            font-weight: 700 !important;
            padding: 0.72rem 1.1rem !important;
            box-shadow: none !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            filter: brightness(0.98);
        }

        /* =========================
           3) HEADER
        ========================= */
        header[data-testid="stHeader"] {
            background: var(--soda-blue) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        }

        header[data-testid="stHeader"] > div {
            background: transparent !important;
        }

        header[data-testid="stHeader"] *,
        header[data-testid="stHeader"] [data-testid="stIconMaterial"] {
            color: #FFFFFF !important;
        }

        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] button:hover,
        header[data-testid="stHeader"] button:focus,
        header[data-testid="stHeader"] button:focus-visible,
        header[data-testid="stHeader"] button:active {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }

        /* =========================
           4) SIDEBAR
        ========================= */
        section[data-testid="stSidebar"] {
            background: var(--soda-sidebar-grad);
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] small {
            color: #FFFFFF !important;
        }

        /* Flèche collapse / expand */
        [data-testid="stSidebarCollapsedControl"] [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] [data-testid="stIconMaterial"] {
            color: #FFFFFF !important;
        }

        [data-testid="stSidebarCollapsedControl"] button,
        section[data-testid="stSidebar"] button[kind="header"],
        [data-testid="stSidebarCollapsedControl"] button:hover,
        [data-testid="stSidebarCollapsedControl"] button:focus,
        [data-testid="stSidebarCollapsedControl"] button:focus-visible,
        [data-testid="stSidebarCollapsedControl"] button:active,
        section[data-testid="stSidebar"] button[kind="header"]:hover,
        section[data-testid="stSidebar"] button[kind="header"]:focus,
        section[data-testid="stSidebar"] button[kind="header"]:focus-visible,
        section[data-testid="stSidebar"] button[kind="header"]:active {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
        }

        /* =========================
           5) SIDEBAR - INPUT CLIENT
        ========================= */
        section[data-testid="stSidebar"] .stTextInput > div {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="input"],
        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="base-input"] {
            background: var(--soda-white) !important;
            border: 1px solid rgba(17, 50, 79, 0.18) !important;
            border-radius: 22px !important;
            min-height: 56px !important;
            padding: 0 0.9rem !important;
            box-shadow: none !important;
            display: flex !important;
            align-items: center !important;
        }

        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="input"] > div,
        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="base-input"] > div {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            padding: 0 !important;
        }

        /* Neutralise les wrappers imbriqués parasites */
        section[data-testid="stSidebar"] .stTextInput [data-baseweb="input"] [data-baseweb="input"],
        section[data-testid="stSidebar"] .stTextInput [data-baseweb="input"] [data-baseweb="base-input"],
        section[data-testid="stSidebar"] .stTextInput [data-baseweb="base-input"] [data-baseweb="input"],
        section[data-testid="stSidebar"] .stTextInput [data-baseweb="base-input"] [data-baseweb="base-input"] {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            min-height: 0 !important;
            padding: 0 !important;
        }

        section[data-testid="stSidebar"] .stTextInput [data-baseweb="input"] [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] .stTextInput [data-baseweb="input"] [data-baseweb="base-input"] > div,
        section[data-testid="stSidebar"] .stTextInput [data-baseweb="base-input"] [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] .stTextInput [data-baseweb="base-input"] [data-baseweb="base-input"] > div {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        section[data-testid="stSidebar"] .stTextInput input,
        section[data-testid="stSidebar"] .stTextInput input:hover,
        section[data-testid="stSidebar"] .stTextInput input:focus,
        section[data-testid="stSidebar"] .stTextInput input:focus-visible,
        section[data-testid="stSidebar"] .stTextInput input:active {
            position: relative;
            z-index: 2;
            background: transparent !important;
            color: var(--soda-blue) !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            font-family: "Epilogue", sans-serif !important;
            font-weight: 500 !important;
            -webkit-appearance: none !important;
            appearance: none !important;
        }

        section[data-testid="stSidebar"] .stTextInput *:focus,
        section[data-testid="stSidebar"] .stTextInput *:focus-visible {
            outline: none !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="input"]:focus-within,
        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="base-input"]:focus-within {
            border: 1px solid rgba(17, 50, 79, 0.18) !important;
            box-shadow: none !important;
            outline: none !important;
        }

        /* =========================
           6) SIDEBAR - FILE UPLOADER
        ========================= */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
        }

        /* Par défaut le widget hérite du blanc */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"],
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] * {
            color: #FFFFFF !important;
        }

        /* Dropzone */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
            background: var(--soda-white) !important;
            border: 1px dashed rgba(17, 50, 79, 0.20) !important;
            border-radius: 24px !important;
            padding: 1.25rem !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] [data-testid="stFileUploader"] section,
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] section * {
            color: var(--soda-blue) !important;
        }

        /* Bouton Browse files */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] section button {
            background: var(--soda-white) !important;
            color: var(--soda-blue) !important;
            border: 1px solid rgba(17, 50, 79, 0.18) !important;
            border-radius: 16px !important;
            box-shadow: none !important;
            padding: 0.5rem 0.9rem !important;
        }

        /* Ligne du fichier uploadé */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
            background: transparent !important;
            box-shadow: none !important;
        }

        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button:not(section button) {
            border: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
            min-width: 0 !important;
            width: auto !important;
            height: auto !important;
        }

        section[data-testid="stSidebar"] [data-testid="stFileUploader"] svg {
            color: currentColor !important;
        }

        /* =========================
           7) ZONE PRINCIPALE
        ========================= */
        [data-testid="stAppViewContainer"] > .main {
            background: var(--soda-main-grad) !important;
        }

        .main .block-container {
            max-width: 1400px;
            padding: 2rem 2.2rem 2.4rem 2.2rem !important;
            background: rgba(255, 255, 255, 0.24);
            border: 1px solid rgba(17, 50, 79, 0.07);
            border-radius: 28px;
        }

        [data-testid="stAppViewContainer"] > .main h1,
        [data-testid="stAppViewContainer"] > .main h2,
        [data-testid="stAppViewContainer"] > .main h3 {
            color: var(--soda-blue) !important;
        }

        [data-testid="stAppViewContainer"] > .main p,
        [data-testid="stAppViewContainer"] > .main label,
        [data-testid="stAppViewContainer"] > .main .stMarkdown,
        [data-testid="stAppViewContainer"] > .main span,
        [data-testid="stAppViewContainer"] > .main li {
            color: var(--soda-text-soft) !important;
        }

        [data-testid="stAppViewContainer"] > .main small {
            color: rgba(44, 62, 80, 0.78) !important;
        }

        /* =========================
           8) CHAMPS ZONE PRINCIPALE
        ========================= */
        [data-testid="stAppViewContainer"] > .main .stTextArea textarea,
        [data-testid="stAppViewContainer"] > .main .stTextArea textarea:disabled,
        [data-testid="stAppViewContainer"] > .main .stTextArea textarea[disabled],
        [data-testid="stAppViewContainer"] > .main .stTextInput input,
        [data-testid="stAppViewContainer"] > .main div[data-baseweb="textarea"] textarea,
        [data-testid="stAppViewContainer"] > .main div[data-baseweb="textarea"] textarea:disabled,
        [data-testid="stAppViewContainer"] > .main div[data-baseweb="textarea"] textarea[disabled],
        [data-testid="stAppViewContainer"] > .main div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.88) !important;
            color: var(--soda-blue) !important;
            -webkit-text-fill-color: var(--soda-blue) !important;
            caret-color: var(--soda-blue) !important;
            border: 1px solid var(--soda-border-soft) !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }

        /* Patch placeholder réel */
        [data-testid="stAppViewContainer"] > .main textarea::placeholder,
        [data-testid="stAppViewContainer"] > .main input::placeholder {
            color: rgba(17, 50, 79, 0.55) !important;
            -webkit-text-fill-color: rgba(17, 50, 79, 0.55) !important;
            opacity: 1 !important;
        }

        /* Patch contenu disabled : ce n'est pas un placeholder, mais la vraie valeur */
        [data-testid="stAppViewContainer"] > .main textarea:disabled,
        [data-testid="stAppViewContainer"] > .main textarea[disabled],
        [data-testid="stAppViewContainer"] > .main textarea[aria-disabled="true"] {
            color: var(--soda-blue) !important;
            -webkit-text-fill-color: var(--soda-blue) !important;
            opacity: 1 !important;
        }

        [data-testid="stAppViewContainer"] > .main [data-testid="stAlert"] {
            background: rgba(255, 255, 255, 0.72) !important;
            border: 1px solid rgba(17, 50, 79, 0.08) !important;
        }
        
        /* ===== LOGO SODA ===== */

        /* Logo dans le header, à gauche de la zone Deploy */
        .soda-header-logo {
            position: fixed;
            top: 0.72rem;
            right: 8.5rem;
            z-index: 99999;
            height: 34px;
            display: flex;
            align-items: center;
            pointer-events: none;
        }

        .soda-header-logo img {
            height: 100%;
            width: auto;
            display: block;
            object-fit: contain;
        }

        /* Logo en haut de sidebar */
        .soda-sidebar-logo {
            margin-top: 0.2rem;
            margin-bottom: 1.2rem;
            display: flex;
            justify-content: flex-start;
        }

        .soda-sidebar-logo img {
            max-width: 170px;
            width: 100%;
            height: auto;
            display: block;
        }
        /* ===== LOGO SIDEBAR - ancré en bas de la sidebar visible ===== */

        /* La sidebar devient le repère du logo fixé en bas */
        section[data-testid="stSidebar"] {
            position: relative !important;
        }

        /* Le contenu garde sa hauteur normale, avec une réserve en bas pour le logo */
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-top: 0.9rem !important;
            padding-bottom: 11.5rem !important;
        }

        /* Wrapper Streamlit du logo : fixé au bas-gauche de la zone visible */
        section[data-testid="stSidebar"] .element-container:has(.soda-sidebar-brand) {
            position: absolute !important;
            left: 0.15rem !important;
            right: auto !important;
            bottom: 0.9rem !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 3 !important;
            pointer-events: none !important;
        }

        /* Bloc logo */
        section[data-testid="stSidebar"] .soda-sidebar-brand {
            display: flex !important;
            justify-content: flex-start !important;
            align-items: flex-end !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 0 !important;
            pointer-events: none !important;
        }

        /* Image */
        section[data-testid="stSidebar"] .soda-sidebar-brand img {
            display: block !important;
            width: 150px !important;
            max-width: 150px !important;
            height: auto !important;
            object-fit: contain !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }

        /* On enlève l'air inutile avant Nome clienti */
        section[data-testid="stSidebar"] .stTextInput {
            margin-top: 0 !important;
        }
        
        </style>
        """
    )


inject_brand_css()

inject_brand_logo()


# =========================
# 5) HELPERS DE FORMATAGE ET DE CALCUL
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


def _excel_pct_to_points(val):
    """
    Convertit une valeur Excel de pourcentage en points de pourcentage.
    - 0.4345 -> 43.45
    - 43.45 -> 43.45
    """
    v = clean_val(val)
    return v * 100 if abs(v) <= 1.5 else v


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


def month_labels_from_graph_dates(d):
    labels = []
    for dt in d["graph_cost_dates"]:
        if hasattr(dt, "month"):
            labels.append(MONTHS_IT.get(dt.month, str(dt)))
        else:
            labels.append(str(dt))
    return labels


MONTHS_IT_SHORT = {
    1: "Gen",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "Mag",
    6: "Giu",
    7: "Lug",
    8: "Ago",
    9: "Set",
    10: "Ott",
    11: "Nov",
    12: "Dic",
}


def _rolling_6m_period_label_from_report_date(raw_date):
    """
    Retourne le libellé court de la période glissante de 6 mois
    basée sur la date du report.
    Exemples :
    - Febbraio 2026 -> Set-Feb
    - Gennaio 2026 -> Ago-Gen
    - Dicembre 2025 -> Lug-Dic
    """
    if raw_date is None or not hasattr(raw_date, "month"):
        return "Lug-Dic"

    end_dt = pd.Timestamp(raw_date)
    start_dt = end_dt - pd.DateOffset(months=5)

    return f"{MONTHS_IT_SHORT[start_dt.month]}-{MONTHS_IT_SHORT[end_dt.month]}"


def _prev_month_label_from_report_date(raw_date):
    if raw_date is None or not hasattr(raw_date, "month"):
        return ""

    prev_dt = pd.Timestamp(raw_date) - pd.DateOffset(months=1)
    return f"{MONTHS_IT[prev_dt.month]} {prev_dt.year}"


def pdf_bytes_to_png_bytes(
    pdf_bytes: bytes, page_index: int = 0, zoom: float = 2.0
) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_index)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")


def merge_pdf_bytes(*pdf_chunks: bytes) -> bytes:
    """
    Fusionne plusieurs PDFs (bytes) en un seul document PDF.
    Ignore les chunks vides.
    """
    out_doc = fitz.open()

    for chunk in pdf_chunks:
        if not chunk:
            continue

        src = fitz.open(stream=chunk, filetype="pdf")
        out_doc.insert_pdf(src)
        src.close()

    merged = out_doc.tobytes()
    out_doc.close()
    return merged


def _compute_ratio_pct_series(costs, revenues):
    pct_series = []
    for cost, revenue in zip(costs, revenues):
        pctg = (cost / revenue) * 100 if revenue > 0 else 0.0
        pct_series.append(round(pctg, 2))
    return pct_series


def _safe_avg(values):
    return (sum(values) / len(values)) if values else 0.0


# =========================
# 6) CHARGEMENT ET PREPARATION DES DONNEES
# =========================
@st.cache_data
def load_data(file):
    df = pd.read_excel(file, sheet_name="Dati report", header=None)

    # --- 1. Extraction de la date du report ---
    raw_date = df.iloc[4, 2]  # Supposons que la date est en C5
    if hasattr(raw_date, "month"):
        mes_it = MONTHS_IT[raw_date.month]
        anno_n = raw_date.year
    else:
        mes_it = "Mese"
        anno_n = pd.Timestamp.now().year  # Valeur par défaut : année courante

    # --- 2. Extraction des donnees de chiffre d'affaires ---
    fatturato_n = clean_val(df.iloc[8, 2])  # Fatturato N (ligne 9, colonne C)
    fatturato_n_1 = clean_val(df.iloc[9, 2])  # Fatturato N-1 (ligne 10, colonne C)
    diff_fatturato = round(
        clean_val(df.iloc[8, 3]) * 100, 1
    )  # % variation (ligne 9, colonne D)

    # Ricavi - costi et marge
    ric_cost_n = clean_val(df.iloc[11, 2])  # Ricavi - Costi N (ligne 12, colonne C)
    ric_cost_n_1 = clean_val(df.iloc[12, 2])  # Ricavi - Costi N-1 (ligne 13, colonne C)
    marg_n = round(
        clean_val(df.iloc[14, 2]) * 100, 1
    )  # Margine N (ligne 15, colonne C)
    marg_n_1 = round(
        clean_val(df.iloc[15, 2]) * 100, 1
    )  # Margine N-1 (ligne 16, colonne C)

    # --- 3. Extraction des dates pour les 6 mois glissants ---
    graph_cost_dates = [df.iloc[i, 1] for i in range(24, 30)]  # Dates en colonne B
    graph_cost_dates_n_1 = [df.iloc[i, 7] for i in range(24, 30)]  # Dates en colonne H

    # --- 4. Extraction des bases de CA mensuel ---
    fatturato_mensile_n = [
        clean_val(df.iloc[i, 2]) for i in range(24, 30)
    ]  # Fatturato mensuel N en colonne C
    fatturato_mensile_n_1 = [
        clean_val(df.iloc[i, 8]) for i in range(24, 30)
    ]  # Fatturato mensuel N-1 en colonne I

    beverage_fatturato_n = [clean_val(df.iloc[i, 2]) for i in range(36, 42)]
    beverage_fatturato_n_1 = [clean_val(df.iloc[i, 8]) for i in range(36, 42)]
    staff_fatturato_n = [clean_val(df.iloc[i, 2]) for i in range(50, 56)]
    staff_fatturato_n_1 = [clean_val(df.iloc[i, 8]) for i in range(50, 56)]

    # --- 5. Extraction des coûts mensuels ---
    food_cost_monthly_n = [
        clean_val(df.iloc[i, 3]) for i in range(24, 30)
    ]  # Colonne D (N)
    food_cost_monthly_n_1 = [
        clean_val(df.iloc[i, 9]) for i in range(24, 30)
    ]  # Colonne J (N-1)

    beverage_cost_monthly_n = [
        clean_val(df.iloc[i, 3]) for i in range(36, 42)
    ]  # Colonne D (N)
    beverage_cost_monthly_n_1 = [
        clean_val(df.iloc[i, 9]) for i in range(36, 42)
    ]  # Colonne J (N-1)

    staff_monthly_n = [clean_val(df.iloc[i, 3]) for i in range(50, 56)]  # Colonne D (N)
    staff_monthly_n_1 = [
        clean_val(df.iloc[i, 9]) for i in range(50, 56)
    ]  # Colonne J (N-1)

    # --- 6. Calcul des pourcentages ---
    food_cost_pctg_n = _compute_ratio_pct_series(
        food_cost_monthly_n, fatturato_mensile_n
    )
    food_cost_pctg_n_1 = _compute_ratio_pct_series(
        food_cost_monthly_n_1,
        fatturato_mensile_n_1,
    )

    beverage_cost_pctg_n = _compute_ratio_pct_series(
        beverage_cost_monthly_n,
        beverage_fatturato_n,
    )
    beverage_cost_pctg_n_1 = _compute_ratio_pct_series(
        beverage_cost_monthly_n_1,
        beverage_fatturato_n_1,
    )

    staff_cost_pctg_n = _compute_ratio_pct_series(staff_monthly_n, staff_fatturato_n)
    staff_cost_pctg_n_1 = _compute_ratio_pct_series(
        staff_monthly_n_1,
        staff_fatturato_n_1,
    )

    # --- 7. Calcul des moyennes ---
    food_cost_avg_n = _safe_avg(food_cost_monthly_n)
    food_cost_avg_n_1 = _safe_avg(food_cost_monthly_n_1)
    beverage_cost_avg_n = _safe_avg(beverage_cost_monthly_n)
    beverage_cost_avg_n_1 = _safe_avg(beverage_cost_monthly_n_1)
    staff_cost_avg_n = _excel_pct_to_points(df.iloc[46, 2])  # C47
    staff_cost_avg_n_1 = _excel_pct_to_points(df.iloc[46, 3])  # D47

    # --- 8. Extraction des rankings (optionnel : sheets peuvent être absentes) ---
    xl_file = pd.ExcelFile(file)
    available_sheets = xl_file.sheet_names

    rank_articoli = []  # [(label, valeur), ...]
    rank_ricavi = []

    if "Export Rank Articoli" in available_sheets:
        df_ra = pd.read_excel(
            file, sheet_name="Export Rank Articoli", usecols="A:B", header=None
        )
        df_ra = df_ra.iloc[1:]  # skip header row
        df_ra = df_ra.dropna(how="any")  # ignore cellules vides
        df_ra.columns = ["label", "value"]
        df_ra["value"] = df_ra["value"].apply(clean_val)
        df_ra = df_ra[df_ra["value"] > 0]
        df_ra = df_ra.sort_values("value", ascending=True)  # plus grande en haut barh
        rank_articoli = list(zip(df_ra["label"].astype(str), df_ra["value"]))[-20:]

    if "Export Rank Ricavi" in available_sheets:
        df_rr = pd.read_excel(
            file, sheet_name="Export Rank Ricavi", usecols="A:B", header=None
        )
        df_rr = df_rr.iloc[1:]
        df_rr = df_rr.dropna(how="any")
        df_rr.columns = ["label", "value"]
        df_rr["value"] = df_rr["value"].apply(clean_val)
        df_rr = df_rr[df_rr["value"] > 0]
        df_rr = df_rr.sort_values("value", ascending=True)
        rank_ricavi = list(zip(df_rr["label"].astype(str), df_rr["value"]))[-20:]

    # --- 9. Retour des données ---
    return {
        # Fatturato
        "month_name": mes_it,
        "year_n": anno_n,
        "year_n_1": anno_n - 1,
        "full_date_n": f"{mes_it} {anno_n}",
        "full_date_n_1": f"{mes_it} {anno_n - 1}",
        "raw_date_n": raw_date,
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
        # Rankings (optionnel)
        "rank_articoli": rank_articoli,
        "rank_ricavi": rank_ricavi,
    }


# =========================
# 7) TEXTES DYNAMIQUES — PAGE 1
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


def build_page2_suggestions(d):
    """
    Préremplissages intelligents de la page 2.
    Base simple aujourd’hui, enrichissable plus tard sans toucher à l’UI.
    """
    fc_n = _avg_pct(d.get("food_cost_pctg_n"))
    fc_n_1 = _avg_pct(d.get("food_cost_pctg_n_1"))
    bc_n = _avg_pct(d.get("beverage_cost_pctg_n"))
    bc_n_1 = _avg_pct(d.get("beverage_cost_pctg_n_1"))
    rolling_6m_label = _rolling_6m_period_label_from_report_date(d.get("raw_date_n"))

    food_trend = "in miglioramento" if fc_n <= fc_n_1 else "in peggioramento"
    bev_trend = "in miglioramento" if bc_n <= bc_n_1 else "in peggioramento"

    food_text = (
        f"Nel periodo analizzato del {d['year_n']}, il Food Cost medio si attesta al "
        f"{fc_n:.1f}% rispetto al {fc_n_1:.1f}% dello stesso periodo dell’anno "
        f"precedente, mostrando un andamento {food_trend}."
    )

    beverage_text = (
        f"Nel periodo {rolling_6m_label} {d['year_n']}, il Beverage Cost medio si attesta al "
        f"{bc_n:.1f}% rispetto al {bc_n_1:.1f}% dello stesso periodo dell’anno "
        f"precedente, mostrando un andamento {bev_trend}."
    )

    return food_text, beverage_text


def build_page3_suggestion(d):
    staff_n = list(d.get("staff_cost_pctg_n") or [])
    staff_n_1 = list(d.get("staff_cost_pctg_n_1") or [])

    if len(staff_n) < 2 or len(staff_n_1) < 1:
        return ""

    cur_pct = float(staff_n[0])
    prev_month_pct = float(staff_n[1])
    cur_vs_pct = float(staff_n_1[0])
    avg_6m = float(d.get("staff_cost_avg_n", 0.0))

    trend_prev = "in miglioramento" if cur_pct <= prev_month_pct else "in peggioramento"
    trend_vs_last_year = "inferiore" if cur_pct <= cur_vs_pct else "superiore"
    target_text = "al di sotto" if cur_pct < 30 else "in prossimità"

    return (
        f"Il labour cost di {d['month_name']} {d['year_n']} si attesta al {cur_pct:.0f}%, "
        f"{trend_prev} rispetto al mese precedente ({prev_month_pct:.0f}%) e "
        f"{trend_vs_last_year} rispetto a {d['month_name']} {d['year_n_1']} "
        f"({cur_vs_pct:.0f}%). "
        f"Il valore medio degli ultimi sei mesi è pari al {avg_6m:.0f}%. "
        f"L’obiettivo è il mantenimento del labour cost {target_text} "
        f"della soglia del 30%."
    )


SUGGESTION_TEXT_STATE_KEYS = {
    "page1_p1": "page1_paragraph_1_suggestion",
    "page1_p2": "page1_paragraph_2_suggestion",
    "page2_food": "food_comment_suggestion",
    "page2_bev": "beverage_comment_suggestion",
    "page3_staff": "staff_comment_suggestion",
}

FINAL_TEXT_STATE_KEYS = {
    "page1_final": "page1_final_text",
    "page2_final": "page2_final_text",  # ← une seule clé
    "page3_staff_final": "page3_staff_final_text",
}

REPORT_TEXT_SIGNATURE_KEY = "__report_text_signature__"


def _make_report_text_signature(d, restaurant_name: str) -> str:
    """
    Signature simple du report courant.
    Si elle change, on réinitialise les textes par défaut.
    """
    parts = [
        (restaurant_name or "").strip().upper(),
        str(d.get("full_date_n", "")),
        str(round(float(d.get("fatturato_n", 0.0)), 2)),
        str(round(float(d.get("fatturato_n_1", 0.0)), 2)),
        str(round(_avg_pct(d.get("food_cost_pctg_n")), 2)),
        str(round(_avg_pct(d.get("beverage_cost_pctg_n")), 2)),
        str(round(_avg_pct(d.get("staff_cost_pctg_n")), 2)),
    ]
    return "|".join(parts)


def _ensure_report_text_state(d, restaurant_name: str):
    """
    Initialise les suggestions et les textes finaux.
    - Les suggestions sont toujours régénérées à partir du code courant.
    - Les textes finaux ne sont réinitialisés que si le report change.
    """
    signature = _make_report_text_signature(d, restaurant_name)

    p1_default, p2_default = build_page1_suggestions(d)
    food_default, beverage_default = build_page2_suggestions(d)
    staff_default = build_page3_suggestion(d)

    suggestion_defaults = {
        SUGGESTION_TEXT_STATE_KEYS["page1_p1"]: p1_default,
        SUGGESTION_TEXT_STATE_KEYS["page1_p2"]: p2_default,
        SUGGESTION_TEXT_STATE_KEYS["page2_food"]: food_default,
        SUGGESTION_TEXT_STATE_KEYS["page2_bev"]: beverage_default,
        SUGGESTION_TEXT_STATE_KEYS["page3_staff"]: staff_default,
    }

    final_defaults = {
        FINAL_TEXT_STATE_KEYS["page1_final"]: "",
        FINAL_TEXT_STATE_KEYS["page2_final"]: "",  # ← une seule clé
        FINAL_TEXT_STATE_KEYS["page3_staff_final"]: "",
    }

    signature_changed = st.session_state.get(REPORT_TEXT_SIGNATURE_KEY) != signature

    for k, v in suggestion_defaults.items():
        st.session_state[k] = v

    if signature_changed:
        for k, v in final_defaults.items():
            st.session_state[k] = v
        st.session_state[REPORT_TEXT_SIGNATURE_KEY] = signature
        return

    for k, v in final_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_report_text_state():
    return {
        "page1_final": st.session_state.get(FINAL_TEXT_STATE_KEYS["page1_final"], ""),
        "page2_final": st.session_state.get(FINAL_TEXT_STATE_KEYS["page2_final"], ""),
        "page3_staff_final": st.session_state.get(
            FINAL_TEXT_STATE_KEYS["page3_staff_final"], ""
        ),
    }


def _copy_page1_proposals_to_final():
    p1 = st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page1_p1"], "").strip()
    p2 = st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page1_p2"], "").strip()

    parts = [txt for txt in [p1, p2] if txt]
    st.session_state[FINAL_TEXT_STATE_KEYS["page1_final"]] = "\n".join(parts)


def _copy_page2_proposals_to_final():
    food = st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page2_food"], "").strip()
    bev = st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page2_bev"], "").strip()
    parts = [t for t in [food, bev] if t]
    st.session_state[FINAL_TEXT_STATE_KEYS["page2_final"]] = "\n".join(parts)


def _copy_staff_proposal_to_final():
    st.session_state[FINAL_TEXT_STATE_KEYS["page3_staff_final"]] = st.session_state.get(
        SUGGESTION_TEXT_STATE_KEYS["page3_staff"], ""
    ).strip()


def _join_text_blocks(*blocks):
    """
    Assemble proprement plusieurs blocs texte en supprimant les vides
    et en les séparant par une ligne blanche.
    """
    cleaned = []
    for block in blocks:
        txt = (block or "").strip()
        if txt:
            cleaned.append(txt)
    return "\n\n".join(cleaned)


def build_report_text_payload(report_texts: dict):
    page1_text = _join_text_blocks(report_texts.get("page1_final", ""))
    page2_text = _join_text_blocks(report_texts.get("page2_final", ""))  # ← direct
    page3_text = _join_text_blocks(report_texts.get("page3_staff_final", ""))

    return {
        "page1_analysis_text": page1_text,
        "page2_analysis_text": page2_text,
        "page3_analysis_text": page3_text,
    }


# =========================
# 8) PREVIEW DU GRAPHIQUE DE CHIFFRE D’AFFAIRES
# =========================
def _apply_fatturato_chart_style(
    ax,
    d,
    label,
    *,
    value_fontsize,
    label_fontsize,
    tick_fontsize,
    legend_fontsize,
    legend_markersize,
    legend_loc,
    legend_anchor,
):
    """Applique exactement le style du graphique Fatturato utilisé dans le PDF."""
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
            fontsize=value_fontsize,
            color=COLORS["white"],
            fontproperties=epilogue_semibold,
        )

    ax.set_xticks([0.5])
    ax.set_xticklabels(
        [label],
        color=COLORS["white"],
        fontsize=label_fontsize,
        fontproperties=epilogue_regular,
    )

    ax.tick_params(
        axis="y",
        colors=COLORS["white"],
        labelsize=tick_fontsize,
        length=0,
    )
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
            markeredgecolor="none",
            markeredgewidth=0,
            markersize=legend_markersize,
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
            markersize=legend_markersize,
            label=f"Fatturato {d['year_n_1']} €",
        ),
    ]
    ax.legend(
        handles=legend_handles,
        loc=legend_loc,
        bbox_to_anchor=legend_anchor,
        borderaxespad=0.0,
        ncol=2,
        frameon=False,
        fontsize=legend_fontsize,
        labelcolor=COLORS["white"],
    )


def make_fatturato_fig(d, label):
    """Preview Streamlit alignée visuellement sur le graphique du PDF."""
    fig = plt.figure(figsize=(6, 6), facecolor=COLORS["bg"])
    ax = fig.add_axes([0.10, 0.12, 0.80, 0.74], facecolor=COLORS["bg"])
    dpi = int(fig.dpi)

    _apply_fatturato_chart_style(
        ax,
        d,
        label,
        value_fontsize=_px_to_pt(BODY1_CFG["chart_value_font_px"], dpi),
        label_fontsize=_px_to_pt(BODY1_CFG["chart_label_font_px"], dpi),
        tick_fontsize=_px_to_pt(BODY1_CFG["chart_tick_font_px"], dpi),
        legend_fontsize=_px_to_pt(BODY1_CFG["chart_legend_font_px"], dpi),
        legend_markersize=8,
        legend_loc="lower center",
        legend_anchor=(0.5, 0.95),
    )

    return fig


def make_food_cost_fig(d, label):
    """
    Preview Streamlit du Food Cost.
    Reprend exactement le même moteur de rendu que le PDF.
    """
    fig = plt.figure(figsize=(6, 3.6), facecolor=COLORS["bg"])

    _draw_food_cost_chart_in_page_2(
        fig,
        left=0.08,
        bottom=0.18,
        width=0.88,
        height=0.68,
        d=d,
        label=label,
        dpi=int(fig.dpi),
    )

    return fig


def make_beverage_cost_fig(d, label):
    """
    Preview Streamlit du Beverage Cost.
    Reprend exactement le même moteur de rendu que le PDF.
    """
    fig = plt.figure(figsize=(6, 3.6), facecolor=COLORS["bg"])

    _draw_beverage_cost_chart_in_page_2(
        fig,
        left=0.08,
        bottom=0.18,
        width=0.88,
        height=0.68,
        d=d,
        label=label,
        dpi=int(fig.dpi),
    )

    return fig


# =========================
# 9) MISE EN PAGE PDF — COMPOSANTS COMMUNS
# =========================


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


# =========================
# 9.1) TOKENS DE MISE EN PAGE
# =========================
PAGE_TOKENS = {
    "pad_top_px": 20,
    "pad_bottom_px": 20,
    "gap_min_px": 15,
    "gap_body_to_footer_min_px": 20,
}

# =========================
# 9.2) HEADER — PAGE 1
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
    "logo_top_px": 20,  # distance depuis le haut
    "pill_enabled": True,
    "pill_top_px": 80,  # distance depuis le haut
    "pill_right_margin_px": 80,  # marge droite
    "pill_font_px": 14,
    "pill_pad_x_px": 6,
    "pill_pad_y_px": 6,
    "pill_border_width_px": 2,
    # --- Espacements verticaux (le layout "suit" automatiquement) ---
    "gap_after_toprow_px": 20,  # espace après la ligne logo/pill avant le titre
    "gap_title_to_restaurant_px": 10,  # espace titre -> restaurant
    "gap_restaurant_to_line_px": 15,  # espace restaurant -> ligne
    # --- Titre ---
    "title_text": "Report Mensile",
    "title_font_px": 64,
    "title_color": "highlight",  # clé dans COLORS
    "title_fontprops": "ivy_title",
    "title_fontstyle": "italic",
    # --- Restaurant ---
    "restaurant_font_px": 20,
    "restaurant_color": "accent",  # clé dans COLORS
    "restaurant_fontprops": "epilogue_regular",  # ou "epilogue_semibold"
    # --- Ligne ---
    "line_side_margin_px": 40,  # marge gauche/droite
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

    # ✅ imshow-safe : on verrouille le repère "page" et on empêche le letterboxing
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

    # 3) Curseur vertical : démarre sous la "top row" (logo/pill) de façon modulaire
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


def _draw_header1_bis(
    ax, W_PX, H_PX, month_label: str, restaurant_name: str, dpi: int, cfg=None
):
    """
    Identique à _draw_header1, MAIS sans dessiner le titre "Report Mensile".
    Important : on conserve la même "hauteur" de header (espacements inclus),
    donc restaurant + ligne restent alignés comme en page 1.
    """
    cfg = {**HEADER1_CFG, **(cfg or {})}

    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    def x(px):
        return px / W_PX

    def y_from_top(top_px):
        return 1.0 - (top_px / H_PX)

    def rect_from_top(left_px, top_px, w_px, h_px):
        x0 = x(left_px)
        y1 = y_from_top(top_px)
        y0 = y_from_top(top_px + h_px)
        return x0, y0, (w_px / W_PX), (h_px / H_PX)

    # 1) Logo
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
            aspect="auto",
        )

        logo_bottom_px = LOGO_TOP_PX + logo_h_px

    # 2) Pill (date)
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

    # 3) Curseur vertical sous top row (logo/pill)
    toprow_bottom_px = max(logo_bottom_px, pill_bottom_px)

    # GAP FIXE demandé : 20px entre le bas du logo (ou pill si plus bas) et le resto
    y_cursor_px = toprow_bottom_px + 20

    # 5) Restaurant (inchangé)
    resto_text = (restaurant_name or "").upper()
    resto_font_px = cfg["restaurant_font_px"]
    resto_color = COLORS[cfg["restaurant_color"]]
    resto_fontprops = globals()[cfg["restaurant_fontprops"]]

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

    # 6) Ligne (inchangé)
    SIDE_MARGIN_PX = cfg["line_side_margin_px"]
    ax.hlines(
        y=y_from_top(y_cursor_px),
        xmin=x(SIDE_MARGIN_PX),
        xmax=x(W_PX - SIDE_MARGIN_PX),
        colors=COLORS[cfg["line_color"]],
        linewidth=_px_to_pt(cfg["line_width_px"], dpi),
        zorder=800,
    )
    return y_cursor_px


# =========================
# 9.3) CORPS — PAGE 1 / FATTURATO
# =========================
# Dépendances attendues (déjà chez toi) :
# - COLORS, ARROW_UP_PATH, ARROW_DOWN_PATH
# - epilogue_regular, epilogue_semibold, ivy_title
# - _px_to_pt(px, dpi), _img_rgba(path), _trim_transparent(img)
# - fmt_eur_dot(x), (optionnel) fmt_pct_1(x)
# - matplotlib.ticker as ticker

BODY1_CFG = {
    # --- Marges / colonnes ---
    "side_margin_px": 80,  # marge gauche/droite globale
    "right_edge_margin_px": 40,  # ✅ bord droit (ligne + texte) à 40px
    "col_gap_px": 20,  # espace entre colonne gauche et droite
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
    "section_title_gap_after_px": 15,
    # --- Sous-titres colonne gauche ---
    "left_title_font_px": 20,  # "Venduto ..."
    "left_subtitle_font_px": 16,  # "2025 vs 2024"
    "left_titles_gap_px": 8,
    "left_titles_to_chart_gap_px": 18,
    # --- Chart (barres) ---
    "chart_h_px": 250,  # hauteur chart dans la page
    "chart_value_font_px": 16,  # valeurs au dessus des barres
    "chart_tick_font_px": 14,
    "chart_label_font_px": 14,
    "chart_legend_font_px": 14,
    "chart_top_extra_px": 36,  # espace interne pour loger la légende
    # --- Bloc stats colonne droite ---
    "stats_title_font_px": 16,  # "Fatturato Dicembre 2025 €"
    "stats_value_font_px": 30,  # "565.048 €"
    "stats_vs_font_px": 16,  # "vs 2024"
    "stats_pct_font_px": 30,  # "+3.1%"
    "stats_gap_1_px": 10,
    "stats_gap_2_px": 18,
    "stats_gap_3_px": 16,
    # --- Flèche variation ---
    "arrow_w_px": 24,  # taille icône flèche
    "arrow_gap_right_px": 10,  # espace entre flèche et %
    # --- Ligne sous stats ---
    "stats_line_enabled": True,
    "stats_line_width_px": 2,
    "stats_line_gap_after_px": 15,
    "stats_line_left_inset_px": 0,  # décale le début de la ligne dans la colonne droite (0 = align à gauche)
    # La fin de la ligne est alignée à droite avec la même marge que "side_margin_px"
    # --- Paragraphe (texte) ---
    "para_font_px": 16,
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


def _measure_text_w_px(ax, s, font_px, fontprops, dpi):
    t = ax.text(
        0,
        0,
        s,
        transform=ax.transAxes,
        fontsize=_px_to_pt(font_px, dpi),
        fontproperties=fontprops,
        alpha=0.0,
    )
    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    w = t.get_window_extent(renderer=r).width
    t.remove()
    return w


def _wrap_text_by_px(ax, text, max_width_px, font_px, fontprops, dpi):
    words = (text or "").split()
    lines, cur = [], []
    for w in words:
        trial = (" ".join(cur + [w])) if cur else w
        if (not cur) or (
            _measure_text_w_px(ax, trial, font_px, fontprops, dpi) <= max_width_px
        ):
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _justify_line_to_px(ax, line, target_width_px, font_px, fontprops, dpi):
    # pas de justification si 0/1 mot
    if " " not in line:
        return line

    words = line.split()
    gaps = len(words) - 1
    base = " ".join(words)

    w = _measure_text_w_px(ax, base, font_px, fontprops, dpi)
    if w >= target_width_px:
        return base

    space_w = _measure_text_w_px(ax, " ", font_px, fontprops, dpi)
    if space_w <= 0:
        return base

    extra_spaces = int(round((target_width_px - w) / space_w))
    if extra_spaces <= 0:
        return base

    add_each = extra_spaces // gaps
    rem = extra_spaces % gaps

    out = []
    for i, word in enumerate(words[:-1]):
        out.append(word)
        n_spaces = 1 + add_each + (1 if i < rem else 0)
        out.append(" " * n_spaces)
    out.append(words[-1])
    return "".join(out)


def _justify_paragraph_to_px(ax, text, width_px, font_px, fontprops, dpi):
    """Justifie un paragraphe sur la largeur width_px (en pixels render)."""
    paras = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    out_lines = []

    for pi, p in enumerate(paras):
        lines = _wrap_text_by_px(
            ax, p.replace("\n", " "), width_px, font_px, fontprops, dpi
        )
        for li, ln in enumerate(lines):
            if li < len(lines) - 1:
                out_lines.append(
                    _justify_line_to_px(ax, ln, width_px, font_px, fontprops, dpi)
                )
            else:
                out_lines.append(ln)

        if pi < len(paras) - 1:
            out_lines.append("")

    return "\n".join(out_lines)


def _wrap_paragraph_simple(ax, text, width_px, font_px, fontprops, dpi):
    paras = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    out_lines = []
    for p in paras:
        lines = _wrap_text_by_px(
            ax, p.replace("\n", " "), width_px, font_px, fontprops, dpi
        )
        out_lines.extend(lines)
    return "\n".join(out_lines)


def _measure_multiline_h_render_px(ax, s, font_px, fontprops, dpi, linespacing):
    t = ax.text(
        0,
        0,
        s,
        transform=ax.transAxes,
        fontsize=_px_to_pt(font_px, dpi),
        fontproperties=fontprops,
        linespacing=linespacing,
        alpha=0.0,
    )
    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    h = t.get_window_extent(renderer=r).height
    t.remove()
    return h


def _fit_justified_paragraph_to_height(
    ax, text, width_px, font_px, fontprops, dpi, linespacing, max_height_render_px
):
    raw = (text or "").strip()
    if not raw:
        return ""

    # Conserve les paragraphes via un token.
    token = "<P>"
    tokens = raw.replace("\n\n", f" {token} ").split()

    def build(i):
        s = " ".join(tokens[:i]).replace(token, "\n\n").strip()
        if i < len(tokens):
            s = (s + " …").strip()
        return s

    # Si ça passe déjà, on renvoie la version justifiée complète.
    full = _justify_paragraph_to_px(ax, raw, width_px, font_px, fontprops, dpi)
    if (
        _measure_multiline_h_render_px(ax, full, font_px, fontprops, dpi, linespacing)
        <= max_height_render_px
    ):
        return full

    lo, hi = 1, len(tokens)
    best = _justify_paragraph_to_px(ax, build(1), width_px, font_px, fontprops, dpi)
    while lo <= hi:
        mid = (lo + hi) // 2
        cand_raw = build(mid)
        cand = _justify_paragraph_to_px(ax, cand_raw, width_px, font_px, fontprops, dpi)
        h = _measure_multiline_h_render_px(
            ax, cand, font_px, fontprops, dpi, linespacing
        )
        if h <= max_height_render_px:
            best = cand
            lo = mid + 1
        else:
            hi = mid - 1
    return best


# =========================
# 9.4) CORPS — SYNTHESE FOOD / BEVERAGE COST
# =========================
BODY_FC_BC_SUMMARY_CFG = {
    # colonnes (comme page 1)
    "side_margin_px": BODY1_CFG["side_margin_px"],  # 80
    "right_edge_margin_px": BODY1_CFG["right_edge_margin_px"],  # 40
    "col_gap_px": 40,  # espace entre colonne gauche et texte
    "left_col_ratio": 0.5,  # largeur bloc métriques
    "rows_offset_px": 5,  # ✅ descend FC/BC (mais pas le header vs)
    "gap_after_header_px": BODY1_CFG["gap_after_header_px"],  # 20
    # styles (proches page 1)
    "label_font_px": BODY1_CFG["stats_vs_font_px"],  # 20 (Venduto...)
    "value_font_px": BODY1_CFG["stats_pct_font_px"],  # 30 (+3.1%)
    "arrow_font_px": BODY1_CFG[
        "stats_vs_font_px"
    ],  # 16 (vs 2024) — ou mets 18 si tu veux → aligner visuellement la flèche
    "vs_title_font_px": BODY1_CFG["stats_vs_font_px"],  # 16 (vs 2024)
    "vs_sub_font_px": BODY1_CFG[
        "left_subtitle_font_px"
    ],  # 16 (2025 vs 2024) ou BODY1_CFG["chart_label_font_px"]=14 si tu préfères plus petit
    "vs_gap_after_px": BODY1_CFG["stats_gap_2_px"],  # 18 (gap après la valeur)
    # layout interne bloc gauche
    "bullet_size_px": 6,
    "bullet_gap_px": 10,
    "vs_col_ratio": 0.34,  # part du bloc gauche dédiée au "vs"
    "row_gap_px": 55,  # espace entre FC et BC
    "row_bottom_pad_px": 22,
    # lignes séparatrices
    "hline_enabled": True,
    "hline_width_px": 1,
    "hline_gap_after_px": 0,
    "hline_to_vsep_gap_px": 22,  # coupe la ligne avant le séparateur vertical
    # séparateur vertical pointillé
    "vsep_enabled": True,
    "vsep_width_px": 3,
    "vsep_dash": (0, (6, 6)),
    "vsep_color": "highlight",
    "vsep_top_offset_px": 0,  # part du top commun
    "vsep_bottom_pad_px": 12,  # marge bas du séparateur
    # paragraphe justifié
    "para_font_px": BODY1_CFG["para_font_px"],  # 16
    "para_linespacing": BODY1_CFG["para_linespacing"],  # 1.6
}


def _avg_pct(vals):
    vals = [float(v) for v in (vals or []) if v is not None]
    return (sum(vals) / len(vals)) if vals else 0.0


def _fmt_pct1(v):
    return f"{v:.1f}%"


def _draw_body_fc_bc_summary(
    ax, W_PX, H_PX, d, restaurant_name: str, analysis_text: str, dpi: int, cfg=None
):
    """
    Body type screenshot:
    - gauche: FC/BC medio ultimi 6 mesi + vs N-1 (2 lignes)
    - droite: texte justifié
    - top align: 'vs N-1' == top du paragraphe
    """
    cfg = {**BODY_FC_BC_SUMMARY_CFG, **(cfg or {})}

    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax._W_PX = W_PX

    def x(px):
        return px / W_PX

    def y_from_top(top_px):
        return 1.0 - (top_px / H_PX)

    # --- zones colonnes (mêmes règles que page 1 : right_edge_margin_px = 40) ---
    left_margin = cfg["side_margin_px"]
    right_margin = cfg["right_edge_margin_px"]
    gap = cfg["col_gap_px"]

    usable_w = W_PX - left_margin - right_margin - gap
    left_w = int(usable_w * cfg["left_col_ratio"])
    right_w = usable_w - left_w

    left_x0 = left_margin
    left_x1 = left_x0 + left_w

    right_x0 = left_x1 + gap
    para_right_edge_px = W_PX - right_margin

    # --- top commun (vs + paragraphe) ---
    if cfg.get("top_px") is not None:
        top_px = int(cfg["top_px"])
    else:
        header_line_y_px = int(cfg.get("header_line_y_px", 0))
        top_px = int(header_line_y_px + cfg["gap_after_header_px"])

    # --- split interne bloc gauche : current | vsep | vs ---
    vs_col_w = int(left_w * cfg["vs_col_ratio"])
    cur_col_w = left_w - vs_col_w

    vsep_x_px = left_x0 + cur_col_w
    vs_x0 = vsep_x_px
    vs_x1 = left_x1

    # --- HEADER "vs N-1" (TOP aligné avec paragraphe) ---
    vs_title = f"vs {d['year_n_1']}"
    vs_sub = _rolling_6m_period_label_from_report_date(d.get("raw_date_n"))

    # centré dans la zone vs
    ax.text(
        x((vs_x0 + vs_x1) / 2),
        y_from_top(top_px),
        vs_title,
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=_px_to_pt(cfg["vs_title_font_px"], dpi),
        fontproperties=epilogue_semibold,
        color=COLORS["white"],
        zorder=850,
    )
    _, h_vs_title = _measure_text_px(
        ax, vs_title, cfg["vs_title_font_px"], epilogue_semibold, dpi
    )

    ax.text(
        x((vs_x0 + vs_x1) / 2),
        y_from_top(top_px + h_vs_title + 4),
        vs_sub,
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=_px_to_pt(cfg["vs_sub_font_px"], dpi),
        fontproperties=epilogue_regular,
        color=COLORS["white"],
        zorder=850,
    )
    _, h_vs_sub = _measure_text_px(
        ax, vs_sub, cfg["vs_sub_font_px"], epilogue_regular, dpi
    )

    header_h_px = h_vs_title + 4 + h_vs_sub + cfg["vs_gap_after_px"]
    vsep_top_px = top_px + h_vs_title + 4 + h_vs_sub
    bc_label_bottom_px = None

    # --- données (moyennes % sur 6 mois) ---
    fc_n = _avg_pct(d.get("food_cost_pctg_n"))
    fc_n_1 = _avg_pct(d.get("food_cost_pctg_n_1"))
    bc_n = _avg_pct(d.get("beverage_cost_pctg_n"))
    bc_n_1 = _avg_pct(d.get("beverage_cost_pctg_n_1"))

    rows = [
        ("FC Medio\nultimi 6 mesi", fc_n, fc_n_1),
        ("BC Medio\nultimi 6 mesi", bc_n, bc_n_1),
    ]

    # --- dessin rows (gauche) ---
    y_row_top = top_px + header_h_px + cfg.get("rows_offset_px", 0)

    _, value_h = _measure_text_px(
        ax, "21%", cfg["value_font_px"], epilogue_semibold, dpi
    )

    bullet_sz = cfg["bullet_size_px"]
    bullet_gap = cfg["bullet_gap_px"]

    label_x = left_x0
    bullet_x0 = left_x0 - (bullet_sz + bullet_gap)

    cur_right = vsep_x_px - 14
    vs_left = vsep_x_px + 14

    for idx, (label, v_cur, v_vs) in enumerate(rows):
        _, label_h = _measure_text_px(
            ax, label, cfg["label_font_px"], epilogue_regular, dpi
        )

        _, value_h = _measure_text_px(
            ax, "21%", cfg["value_font_px"], epilogue_semibold, dpi
        )

        y_val_top = y_row_top + max(0, (label_h - value_h) / 2)
        bullet_top_px = y_row_top + max(0, (label_h - bullet_sz) / 2)

        ax.add_patch(
            FancyBboxPatch(
                (x(bullet_x0), y_from_top(bullet_top_px)),
                bullet_sz / W_PX,
                bullet_sz / H_PX,
                boxstyle="round,pad=0,rounding_size=0.002",
                transform=ax.transAxes,
                facecolor=COLORS["highlight"],
                edgecolor="none",
                zorder=900,
            )
        )

        ax.text(
            x(label_x),
            y_from_top(y_row_top),
            label,
            ha="left",
            va="top",
            transform=ax.transAxes,
            fontsize=_px_to_pt(cfg["label_font_px"], dpi),
            fontproperties=epilogue_regular,
            color=COLORS["white"],
            zorder=850,
            linespacing=1.2,
        )
        if idx == 1:
            bc_label_bottom_px = y_row_top + label_h
        # current
        cur_txt = _fmt_pct1(v_cur)
        ax.text(
            x(cur_right),
            y_from_top(y_val_top),
            cur_txt,
            ha="right",
            va="top",
            transform=ax.transAxes,
            fontsize=_px_to_pt(cfg["value_font_px"], dpi),
            fontproperties=epilogue_semibold,
            color=COLORS["highlight"],
            zorder=850,
        )

        # vs
        vs_txt = _fmt_pct1(v_vs)
        ax.text(
            x(vs_x1 - 10),
            y_from_top(y_val_top),
            vs_txt,
            ha="right",
            va="top",
            transform=ax.transAxes,
            fontsize=_px_to_pt(cfg["value_font_px"], dpi),
            fontproperties=epilogue_semibold,
            color=COLORS["highlight"],
            zorder=850,
        )
        # hauteur row (inchangée pour le flux vertical)
        row_h = (
            max(label_h, (y_val_top - y_row_top + value_h)) + cfg["row_bottom_pad_px"]
        )
        row_bottom_px = y_row_top + row_h

        if idx == 0:
            next_row_top_px = row_bottom_px + cfg["row_gap_px"]

            # ✅ séparateur au milieu entre :
            # - bas du label FC
            # - haut du label BC
            fc_label_bottom_px = y_row_top + label_h
            y_sep_px = fc_label_bottom_px + (next_row_top_px - fc_label_bottom_px) / 2

            if cfg["hline_enabled"]:
                cut = cfg["hline_to_vsep_gap_px"]

                ax.hlines(
                    y=y_from_top(y_sep_px),
                    xmin=x(left_x0),
                    xmax=x(vsep_x_px - cut),
                    colors=COLORS["highlight"],
                    linewidth=_px_to_pt(cfg["hline_width_px"], dpi),
                    zorder=800,
                )

                ax.hlines(
                    y=y_from_top(y_sep_px),
                    xmin=x(vsep_x_px + cut),
                    xmax=x(left_x1),
                    colors=COLORS["highlight"],
                    linewidth=_px_to_pt(cfg["hline_width_px"], dpi),
                    zorder=800,
                )

            # prochaine row inchangée
            y_row_top = next_row_top_px

    left_block_bottom_px = y_row_top

    # --- séparateur vertical (placement calé sur les vrais blocs) ---
    if cfg["vsep_enabled"] and bc_label_bottom_px is not None:
        y0 = vsep_top_px
        y1 = bc_label_bottom_px
        ax.vlines(
            x=x(vsep_x_px),
            ymin=y_from_top(y1),
            ymax=y_from_top(y0),
            colors=COLORS[cfg["vsep_color"]],
            linewidth=_px_to_pt(cfg["vsep_width_px"], dpi),
            linestyles=cfg["vsep_dash"],
            zorder=900,
        )

    # --- paragraphe (sans justification → objet PDF unique) ---
    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    ax_bb = ax.get_window_extent(renderer=r)
    ax_w_render = ax_bb.width
    scale_y = ax_bb.height / H_PX

    col_px_layout = para_right_edge_px - right_x0
    col_px_render = ax_w_render * (col_px_layout / W_PX)

    text_wrapped = _wrap_paragraph_simple(
        ax,
        (analysis_text or "").strip(),
        width_px=col_px_render,
        font_px=cfg["para_font_px"],
        fontprops=epilogue_regular,
        dpi=dpi,
    )

    ax.text(
        x(right_x0),
        y_from_top(top_px),
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
    Reproduit le graphique Fatturato directement dans la page PDF.
    left/bottom/width/height sont en coords figure (0..1).
    """
    axc = fig.add_axes([left, bottom, width, height], facecolor=COLORS["bg"])

    _apply_fatturato_chart_style(
        axc,
        d,
        label,
        value_fontsize=_px_to_pt(cfg["chart_value_font_px"], dpi),
        label_fontsize=_px_to_pt(cfg["chart_label_font_px"], dpi),
        tick_fontsize=_px_to_pt(cfg["chart_tick_font_px"], dpi),
        legend_fontsize=_px_to_pt(cfg["chart_legend_font_px"], dpi),
        legend_markersize=8,
        legend_loc="lower center",
        legend_anchor=(0.5, 0.95),
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

    # ✅ imshow-safe : on verrouille le repère "page"
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

    if cfg.get("top_px") is not None:
        y = int(cfg["top_px"])
    else:
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

    # Décalage appliqué uniquement à tout ce qui est SOUS "Fatturato" (pour le centrage)
    y += float(cfg.get("after_section_offset_px", 0))

    titles_top_px = y  # top commun (Venduto + stats droite) APRÈS décalage

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

    # --- Colonne gauche : chart (on définit son top "candidat") ---
    chart_top_left = y_left
    chart_h = cfg["chart_h_px"]
    chart_w = left_w

    # --- Colonne droite : bloc stats aligné au titre gauche ("Venduto ...") ---
    yR = titles_top_px

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

    # --- ALIGNEMENT DEMANDÉ ---
    # top du chart = top du "vs ..." (donc on choisit un top commun)
    yR_before_vs = yR
    chart_top = max(chart_top_left, yR_before_vs)

    # ✅ le "vs ..." commence au même niveau que le haut du chart
    yR = chart_top

    # --- Dessin du chart avec top recalé ---
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
    )  # avance "assez" (simple & stable)

    # --- ligne sous stats (bord droit à 40px) ---
    if cfg["stats_line_enabled"]:
        right_edge_px = W_PX - cfg.get("right_edge_margin_px", cfg["side_margin_px"])
        ax.hlines(
            y=y_from_top(yR),
            xmin=x(right_x0 + cfg["stats_line_left_inset_px"]),
            xmax=x(right_edge_px),
            colors=COLORS["highlight"],
            linewidth=_px_to_pt(cfg["stats_line_width_px"], dpi),
            zorder=800,
        )
        yR += cfg["stats_line_gap_after_px"]

    # --- paragraphe (à droite) : justifié + aligné sur la ligne ---
    para_right_edge_px = W_PX - cfg.get("right_edge_margin_px", cfg["side_margin_px"])
    col_px_layout = para_right_edge_px - right_x0

    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    ax_w_render = ax.get_window_extent(renderer=r).width
    col_px_render = ax_w_render * (col_px_layout / W_PX)

    para_max_bottom_px = cfg.get("para_max_bottom_px")
    if para_max_bottom_px is not None:
        scale_y = ax.get_window_extent(renderer=r).height / H_PX
        max_h_render = max(0.0, (para_max_bottom_px - yR) * scale_y)
        text_wrapped = _fit_justified_paragraph_to_height(
            ax,
            (analysis_text or "").strip(),
            width_px=col_px_render,
            font_px=cfg["para_font_px"],
            fontprops=epilogue_regular,
            dpi=dpi,
            linespacing=cfg["para_linespacing"],
            max_height_render_px=max_h_render,
        )
    else:
        text_wrapped = _justify_paragraph_to_px(
            ax,
            (analysis_text or "").strip(),
            width_px=col_px_render,
            font_px=cfg["para_font_px"],
            fontprops=epilogue_regular,
            dpi=dpi,
        )

    text_obj = ax.text(
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

    # Bas du paragraphe (px depuis le haut)
    ax.figure.canvas.draw()
    bb = text_obj.get_window_extent(renderer=r)
    scale_y = ax.get_window_extent(renderer=r).height / H_PX
    text_bottom_from_top_px = (ax.get_window_extent(renderer=r).y1 - bb.y0) / scale_y
    return float(text_bottom_from_top_px)


def _measure_body1_metrics(
    ax, W_PX, H_PX, d, restaurant_name: str, analysis_text: str, dpi: int, cfg=None
):
    """Mesure la hauteur totale du body (px) pour le centrage + overflow."""
    cfg = {**BODY1_CFG, **(cfg or {})}

    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    scale_y = ax.get_window_extent(renderer=r).height / H_PX
    ax_w_render = ax.get_window_extent(renderer=r).width

    def h_px(text, font_px, fontprops):
        _w, h = _measure_text_px(ax, text, font_px, fontprops, dpi)
        return h / scale_y

    side = cfg["side_margin_px"]
    gap = cfg["col_gap_px"]
    usable_w = W_PX - 2 * side - gap
    left_w = int(usable_w * cfg["left_col_ratio"])
    right_x0 = side + left_w + gap

    y = 0.0

    if cfg["kicker_enabled"]:
        y += (
            h_px(
                (restaurant_name or "").upper(),
                cfg["kicker_font_px"],
                epilogue_semibold,
            )
            + cfg["kicker_gap_after_px"]
        )
        if cfg.get("kicker_line_enabled"):
            y += cfg.get("kicker_line_gap_after_px", 0)

    y += (
        h_px(cfg["section_title_text"], cfg["section_title_font_px"], epilogue_semibold)
        + cfg["section_title_gap_after_px"]
    )
    section_bottom_px = y  # ✅ bas de "Fatturato" (ancré)
    titles_top_px = y  # (top des titres "Venduto..." avant offset)

    left_title = f"Venduto {restaurant_name} {d['month_name']}"
    left_sub = f"{d['year_n']} vs {d['year_n_1']}"

    y_left = (
        y
        + h_px(left_title, cfg["left_title_font_px"], epilogue_semibold)
        + cfg["left_titles_gap_px"]
    )
    y_left = (
        y_left
        + h_px(left_sub, cfg["left_subtitle_font_px"], epilogue_regular)
        + cfg["left_titles_to_chart_gap_px"]
    )
    chart_top_left = y_left

    yR = titles_top_px
    stats_title = f"Fatturato {d['month_name']} {d['year_n']} €"
    yR += (
        h_px(stats_title, cfg["stats_title_font_px"], epilogue_regular)
        + cfg["stats_gap_1_px"]
    )
    yR += (
        h_px(
            fmt_eur_dot(d["fatturato_n"]), cfg["stats_value_font_px"], epilogue_semibold
        )
        + cfg["stats_gap_2_px"]
    )

    chart_top = max(chart_top_left, yR)
    yR = chart_top

    yR += (
        h_px(f"vs {d['year_n_1']}", cfg["stats_vs_font_px"], epilogue_regular)
        + cfg["stats_gap_1_px"]
    )
    yR += cfg["stats_pct_font_px"] * 2 + cfg["stats_gap_3_px"]

    if cfg.get("stats_line_enabled", True):
        yR += cfg["stats_line_gap_after_px"]

    para_start_px = yR

    para_right_edge_px = W_PX - cfg.get("right_edge_margin_px", cfg["side_margin_px"])
    col_px_layout = para_right_edge_px - right_x0
    col_px_render = ax_w_render * (col_px_layout / W_PX)

    para = _justify_paragraph_to_px(
        ax,
        (analysis_text or "").strip(),
        width_px=col_px_render,
        font_px=cfg["para_font_px"],
        fontprops=epilogue_regular,
        dpi=dpi,
    )
    para_h_render = _measure_multiline_h_render_px(
        ax, para, cfg["para_font_px"], epilogue_regular, dpi, cfg["para_linespacing"]
    )
    para_h_px = para_h_render / scale_y

    chart_h_px = float(cfg["chart_h_px"])

    chart_bottom_px = float(chart_top + chart_h_px)
    para_bottom_px = float(para_start_px + para_h_px)
    bottom_px = max(chart_bottom_px, para_bottom_px)
    return {
        "height_px": float(bottom_px),
        "para_start_px": float(para_start_px),
        "section_bottom_px": float(
            section_bottom_px
        ),  # ✅ nécessaire pour centrer le reste
    }


# =========================
# 9.5) CORPS — PAGE 2 / FOOD & BEVERAGE COST
# =========================
BODY_PAGE_2_CFG = {
    # mêmes colonnes que page 1, mais charts alignés sur la ligne du header
    "side_margin_px": HEADER1_CFG["line_side_margin_px"],  # 40 (gauche)
    "right_edge_margin_px": BODY1_CFG["right_edge_margin_px"],  # 40 (droite)
    "col_gap_px": 40,  # espace entre les 2 charts
    "left_col_ratio": 0.5,
    "gap_after_header_px": BODY1_CFG["gap_after_header_px"],
    # --- Titre section (fixe) ---
    "section_title_text": "Food & Beverage cost",
    "section_title_font_px": BODY1_CFG["section_title_font_px"],
    "section_title_gap_after_px": 20,
    # charts
    "chart_h_px": 250,
    "charts_gap_after_title_px": 20,
    "gap_after_charts_px": 20,
}


def _plot_food_cost_axis(axc, d, label):
    """
    Style unique du graphique Food Cost.
    Utilisé à la fois par la preview Streamlit et par le rendu PDF.
    Construit dans le même esprit que le graphique page 1 : même moteur vectoriel,
    même logique de layout partagé entre preview et PDF.
    """
    x_labels = list(reversed(month_labels_from_graph_dates(d)))
    y = list(reversed(d["food_cost_pctg_n"]))

    axc.set_facecolor(COLORS["bg"])

    axc.plot(
        range(len(y)),
        y,
        marker="o",
        linewidth=3,
        markersize=10,
        color=COLORS["graph1"],
        zorder=3,
    )

    axc.text(
        0.0,
        1.03,
        f"Andamento Food Cost Mensile {d['year_n']}",
        transform=axc.transAxes,
        ha="left",
        va="bottom",
        color=COLORS["white"],
        fontsize=12,
        fontproperties=epilogue_semibold,
        clip_on=False,
        zorder=5,
    )

    # Légende ancrée DANS l'axe (clip_on=True) → pas de groupe PDF flottant
    axc.text(
        0.5,
        0.97,
        label,
        transform=axc.transAxes,
        ha="center",
        va="bottom",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
        clip_on=False,
        zorder=5,
    )

    axc.set_xticks(range(len(x_labels)))
    axc.set_xticklabels(
        x_labels,
        rotation=90,
        ha="right",
        color=COLORS["white"],
        fontsize=9,
        fontproperties=epilogue_regular,
    )
    axc.tick_params(axis="x", colors=COLORS["white"], labelsize=9, length=0)

    axc.tick_params(axis="y", colors=COLORS["white"], labelsize=9, length=0)
    axc.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, p: f"{v:.0f}%"))
    axc.set_ylim(0, max(25, (max(y) if y else 0) + 8))
    axc.margins(x=0.06)

    axc.grid(False)
    for s in axc.spines.values():
        s.set_visible(False)

    return axc


def _plot_beverage_cost_axis(axc, d, label):
    """
    Style unique du graphique Beverage Cost.
    Utilisé à la fois par la preview Streamlit et par le rendu PDF.
    Construit dans le même esprit que le graphique page 1 : même moteur vectoriel,
    même logique de layout partagé entre preview et PDF.
    """
    x_labels = list(reversed(month_labels_from_graph_dates(d)))
    y = list(reversed(d["beverage_cost_pctg_n"]))

    bev_color = "#e74c3c"

    axc.set_facecolor(COLORS["bg"])

    axc.plot(
        range(len(y)),
        y,
        marker="o",
        linewidth=3,
        markersize=10,
        color=bev_color,
        zorder=3,
    )

    axc.text(
        0.0,
        1.03,
        f"Andamento Beverage Cost Mensile {d['year_n']}",
        transform=axc.transAxes,
        ha="left",
        va="bottom",
        color=COLORS["white"],
        fontsize=12,
        fontproperties=epilogue_semibold,
        clip_on=False,
        zorder=5,
    )

    # Légende ancrée DANS l'axe (clip_on=True) → pas de groupe PDF flottant
    axc.text(
        0.5,
        0.97,
        label,
        transform=axc.transAxes,
        ha="center",
        va="bottom",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
        clip_on=False,
        zorder=5,
    )

    axc.set_xticks(range(len(x_labels)))
    axc.set_xticklabels(
        x_labels,
        rotation=90,
        ha="right",
        color=COLORS["white"],
        fontsize=9,
        fontproperties=epilogue_regular,
    )
    axc.tick_params(axis="x", colors=COLORS["white"], labelsize=9, length=0)

    axc.tick_params(axis="y", colors=COLORS["white"], labelsize=9, length=0)
    axc.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, p: f"{v:.0f}%"))
    axc.set_ylim(0, max(12, (max(y) if y else 0) + 4))
    axc.margins(x=0.06)

    axc.grid(False)
    for s in axc.spines.values():
        s.set_visible(False)

    return axc


def _draw_food_cost_chart_in_page_2(fig, left, bottom, width, height, d, label, dpi):
    """
    Wrapper PDF du graphique Food Cost.
    """
    axc = fig.add_axes([left, bottom, width, height], facecolor=COLORS["bg"])
    return _plot_food_cost_axis(axc, d=d, label=label)


def _draw_beverage_cost_chart_in_page_2(
    fig, left, bottom, width, height, d, label, dpi
):
    """
    Wrapper PDF du graphique Beverage Cost.
    """
    axc = fig.add_axes([left, bottom, width, height], facecolor=COLORS["bg"])
    return _plot_beverage_cost_axis(axc, d=d, label=label)


def _draw_body_page_2_food_beverage_cost(
    ax, W_PX, H_PX, d, restaurant_name: str, dpi: int, cfg=None
):
    cfg = {**BODY_PAGE_2_CFG, **(cfg or {})}

    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax._W_PX = W_PX

    def x(px):
        return px / W_PX

    def y_from_top(top_px):
        return 1.0 - (top_px / H_PX)

    left_margin = cfg["side_margin_px"]
    right_margin = cfg.get("right_edge_margin_px", left_margin)
    gap = cfg["col_gap_px"]

    usable_w = W_PX - left_margin - right_margin - gap
    left_w = int(usable_w * cfg["left_col_ratio"])
    right_w = usable_w - left_w

    left_x0 = left_margin
    right_x0 = left_margin + left_w + gap

    # top de body
    if cfg.get("top_px") is not None:
        y = int(cfg["top_px"])
    else:
        header_line_y_px = int(cfg.get("header_line_y_px", 0))
        y = header_line_y_px + cfg["gap_after_header_px"]

    # --- Titre section ---
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
    y += h_sec + cfg["section_title_gap_after_px"] + cfg["charts_gap_after_title_px"]

    chart_top = y
    chart_h = cfg["chart_h_px"]

    fig = ax.figure

    # --- Charts (2 colonnes) ---
    ax_food = _draw_food_cost_chart_in_page_2(
        fig,
        left=x(left_x0),
        bottom=y_from_top(chart_top + chart_h),
        width=(left_w / W_PX),
        height=(chart_h / H_PX),
        d=d,
        label=restaurant_name,
        dpi=dpi,
    )

    ax_bev = _draw_beverage_cost_chart_in_page_2(
        fig,
        left=x(right_x0),
        bottom=y_from_top(chart_top + chart_h),
        width=(right_w / W_PX),
        height=(chart_h / H_PX),
        d=d,
        label=restaurant_name,
        dpi=dpi,
    )

    # ✅ Mesure du vrai bas rendu (inclut tick labels / titres / etc.)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()

    page_bb = ax.get_window_extent(renderer=r)  # bbox de la page (display px)
    scale_y = page_bb.height / H_PX  # conversion display_px -> layout_px

    def bottom_from_top_layout_px(axc):
        tight = axc.get_tightbbox(r)  # bbox "tight" (display px)
        # distance depuis le haut de la page (layout px)
        return (page_bb.y1 - tight.y0) / scale_y

    true_bottom = max(
        bottom_from_top_layout_px(ax_food),
        bottom_from_top_layout_px(ax_bev),
    )

    return float(true_bottom)


# =========================
# 9.6) CORPS — PAGE 3 / INCIDENZA STAFF
# =========================
BODY_PAGE_3_CFG = {
    # mêmes marges / logique que les autres pages
    "side_margin_px": BODY1_CFG["side_margin_px"],
    "right_edge_margin_px": BODY1_CFG["right_edge_margin_px"],
    "gap_after_header_px": BODY1_CFG["gap_after_header_px"],
    # --- Titre section ---
    "section_title_text": "Incidenza staff",
    "section_title_font_px": BODY1_CFG["section_title_font_px"],
    "section_title_gap_after_px": 20,
    # --- Sous-titre du bloc graphique ---
    "chart_title_text": "Costo azienda",
    "chart_title_font_px": 22,
    "chart_title_gap_after_px": 18,
    # --- Zone graphique centrée ---
    "gauge_w_px": 170,
    "gauge_h_px": 100,
    "gauge_gap_px": 46,
    # --- Arc gauge ---
    "gauge_theta1_deg": 20,
    "gauge_theta2_deg": 160,
    "gauge_line_width_px": 26,
    "gauge_max_pct": 75.0,
    # couleurs provisoires = comme ton exemple
    "gauge_base_color": "#3f47bf",
    "gauge_fill_color": "#72d7cf",
    # --- Textes sous gauges ---
    "gauge_value_font_px": 28,
    "gauge_to_pct_gap_px": -30,
    "pct_to_month_gap_px": 12,
    "gauge_month_font_px": 16,
    "gauge_month_gap_after_px": 16,
    "vs_label_font_px": 16,
    "vs_value_font_px": 18,
    "vs_row_gap_after_month_px": 16,
    "para_font_px": BODY1_CFG["para_font_px"],
    "para_linespacing": BODY1_CFG["para_linespacing"],
    "para_gap_after_vs_px": 24,
    "para_max_lines": 10,
    "para_left_px": HEADER1_CFG["line_side_margin_px"],
}


def make_staff_gauge_fig(d):
    """
    Preview Streamlit du bloc gauge de la page 3.
    On réutilise la vraie fonction de gauge du PDF pour garder le même style.
    """
    fig = plt.figure(figsize=(6, 3.6), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    dpi = int(fig.dpi)
    cfg = BODY_PAGE_3_CFG

    staff_n = list(d.get("staff_cost_pctg_n") or [])
    staff_n_1 = list(d.get("staff_cost_pctg_n_1") or [])

    if len(staff_n) < 2 or len(staff_n_1) < 2:
        return fig

    cur_pct = float(staff_n[0])
    prev_month_pct = float(staff_n[1])

    cur_vs_pct = float(staff_n_1[0])
    prev_month_vs_pct = float(staff_n_1[1])

    cur_label = d["full_date_n"]
    prev_month_label = _prev_month_label_from_report_date(d.get("raw_date_n"))

    # titre interne comme sur la page 3 PDF
    ax.text(
        0.0,
        0.96,
        cfg["chart_title_text"],
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=COLORS["white"],
        fontsize=16,
        fontproperties=epilogue_semibold,
    )

    # gauges
    _draw_staff_gauge_in_page_3(
        fig,
        left=0.10,
        bottom=0.38,
        width=0.30,
        height=0.34,
        value_pct=cur_pct,
        dpi=dpi,
        cfg=cfg,
    )

    _draw_staff_gauge_in_page_3(
        fig,
        left=0.60,
        bottom=0.38,
        width=0.30,
        height=0.34,
        value_pct=prev_month_pct,
        dpi=dpi,
        cfg=cfg,
    )

    # valeurs
    ax.text(
        0.25,
        0.34,
        _fmt_pct_no_sign(cur_pct, decimals=0),
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=18,
        fontproperties=epilogue_regular,
    )
    ax.text(
        0.75,
        0.34,
        _fmt_pct_no_sign(prev_month_pct, decimals=0),
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=18,
        fontproperties=epilogue_regular,
    )

    # labels mois
    ax.text(
        0.25,
        0.24,
        cur_label,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_semibold,
    )
    ax.text(
        0.75,
        0.24,
        prev_month_label,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_semibold,
    )

    # ligne vs N-1
    ax.text(
        0.25,
        0.13,
        f"vs {d['year_n_1']}",
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
    )
    ax.text(
        0.75,
        0.13,
        f"vs {d['year_n_1']}",
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=10,
        fontproperties=epilogue_regular,
    )

    ax.text(
        0.25,
        0.06,
        _fmt_pct_no_sign(cur_vs_pct, decimals=0),
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=12,
        fontproperties=epilogue_semibold,
    )
    ax.text(
        0.75,
        0.06,
        _fmt_pct_no_sign(prev_month_vs_pct, decimals=0),
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=12,
        fontproperties=epilogue_semibold,
    )

    return fig


def make_rank_bar_fig(items, value_fmt="qty", fig_h=None):
    """
    Graphique barres horizontales pour les rankings (Streamlit preview).
    items     : [(label, value), ...] déjà triés asc (la plus grande en haut)
    value_fmt : "qty" -> entier,  "eur" -> fmt_eur_dot
    Retourne None si items vide.
    """
    if not items:
        return None

    # APRÈS
    import textwrap

    labels = ["\n".join(textwrap.wrap(item[0], 22)) for item in items]
    values = [float(item[1]) for item in items]
    n = len(labels)

    fig_h = fig_h if fig_h is not None else max(4.0, n * 0.40)
    fig = plt.figure(figsize=(8, fig_h), facecolor=COLORS["bg"])
    # APRÈS
    ax = fig.add_axes([0.32, 0.04, 0.58, 0.94], facecolor=COLORS["bg"])
    ax.set_ylim(-0.5, n - 0.5)

    # Barres alternees graph1 / graph2

    # Barres alternees graph1 / graph2
    colors = [COLORS["graph1"] if i % 2 == 0 else COLORS["graph2"] for i in range(n)]
    bars = ax.barh(range(n), values, color=colors, height=0.65, zorder=3)

    # Valeur au bout de chaque barre
    for bar, v in zip(bars, values):
        label_str = (
            fmt_eur_dot(v)
            if value_fmt == "eur"
            else f"{int(round(v)):,}".replace(",", ".")
        )
        ax.text(
            v + max(values) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            label_str,
            va="center",
            ha="left",
            fontsize=7,
            color=COLORS["white"],
            fontproperties=epilogue_semibold,
        )

    # Noms sur l'axe Y
    ax.set_yticks(range(n))
    ax.set_yticklabels(
        labels, fontsize=7, color=COLORS["white"], fontproperties=epilogue_regular
    )
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=COLORS["white"], labelsize=6, length=0)

    # Formatter axe X
    if value_fmt == "eur":
        ax.xaxis.set_major_formatter(
            ticker.FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", "."))
        )
    else:
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{int(v)}"))

    ax.set_xlim(0, max(values) * 1.28)

    # Style identique aux autres graphiques
    ax.grid(axis="x", linestyle="-", alpha=0.15, color=COLORS["white"], zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)

    fig.tight_layout(pad=0.3)
    return fig


def _fmt_pct_no_sign(x, decimals=0):
    if decimals == 0:
        return f"{int(round(float(x)))}%"
    return f"{float(x):.{decimals}f}%"


def _draw_staff_gauge_in_page_3(
    fig, left, bottom, width, height, value_pct, dpi: int, cfg=None
):
    """
    Gauge simple sans fond blanc :
    - arc de base
    - arc de progression
    - valeur centrée
    """
    cfg = {**BODY_PAGE_3_CFG, **(cfg or {})}

    axg = fig.add_axes([left, bottom, width, height], facecolor="none")
    axg.set_axis_off()
    axg.set_xlim(-1.35, 1.35)
    axg.set_ylim(-1.25, 1.25)
    axg.set_aspect("equal")

    theta1 = float(cfg["gauge_theta1_deg"])
    theta2 = float(cfg["gauge_theta2_deg"])
    span = max(1.0, theta2 - theta1)

    max_pct = max(1.0, float(cfg["gauge_max_pct"]))
    frac = min(max(float(value_pct) / max_pct, 0.0), 1.0)

    lw_pt = _px_to_pt(cfg["gauge_line_width_px"], dpi)

    # arc complet
    axg.add_patch(
        Arc(
            (0, 0),
            2.0,
            2.0,
            theta1=theta1,
            theta2=theta2,
            linewidth=lw_pt,
            color=cfg["gauge_base_color"],
            capstyle="round",
            clip_on=False,
            zorder=2,
        )
    )

    # arc rempli (part depuis la gauche)
    if frac > 0:
        fill_theta1 = theta2 - span * frac
        fill_theta2 = theta2
        axg.add_patch(
            Arc(
                (0, 0),
                2.0,
                2.0,
                theta1=fill_theta1,
                theta2=fill_theta2,
                linewidth=lw_pt,
                color=cfg["gauge_fill_color"],
                capstyle="round",
                clip_on=False,
                zorder=3,
            )
        )


def _draw_body_page_3_staff(
    ax, W_PX, H_PX, d, restaurant_name: str, analysis_text: str, dpi: int, cfg=None
):
    cfg = {**BODY_PAGE_3_CFG, **(cfg or {})}

    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax._W_PX = W_PX

    def x(px):
        return px / W_PX

    def y_from_top(top_px):
        return 1.0 - (top_px / H_PX)

    # --- top du body ---
    if cfg.get("top_px") is not None:
        y = int(cfg["top_px"])
    else:
        header_line_y_px = int(cfg.get("header_line_y_px", 0))
        y = header_line_y_px + cfg["gap_after_header_px"]

    # --- Titre section ---
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

    # --- Titre interne du bloc graphique ---
    h_chart_title = _draw_text_top_center_px(
        ax,
        y_from_top,
        y,
        cfg["chart_title_text"],
        cfg["chart_title_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["white"],
        z=850,
    )
    y += h_chart_title + cfg["chart_title_gap_after_px"]

    # --- Données : mois du report + mois précédent ---
    staff_n = list(d.get("staff_cost_pctg_n") or [])
    staff_n_1 = list(d.get("staff_cost_pctg_n_1") or [])
    raw_dates = list(d.get("graph_cost_dates") or [])

    if not staff_n:
        return float(y)

    # On aligne les dates sur la longueur réelle des données staff

    if len(staff_n) < 2 or len(staff_n_1) < 2:
        return float(y)

    cur_pct = float(staff_n[0])  # mois du report
    prev_month_pct = float(staff_n[1])  # mois m-1

    cur_vs_pct = float(staff_n_1[0])  # même mois en N-1
    prev_month_vs_pct = float(staff_n_1[1])  # mois m-1 en N-1

    cur_label = d["full_date_n"]
    prev_month_label = _prev_month_label_from_report_date(d.get("raw_date_n"))

    # --- Zone gauges centrée ---
    gauge_w = int(cfg["gauge_w_px"])
    gauge_h = int(cfg["gauge_h_px"])
    gauge_gap = int(cfg["gauge_gap_px"])

    total_gauges_w = gauge_w * 2 + gauge_gap
    left_gauge_x0 = int((W_PX - total_gauges_w) / 2)
    right_gauge_x0 = left_gauge_x0 + gauge_w + gauge_gap

    gauge_top_px = y
    fig = ax.figure

    _draw_staff_gauge_in_page_3(
        fig,
        left=x(left_gauge_x0),
        bottom=y_from_top(gauge_top_px + gauge_h),
        width=(gauge_w / W_PX),
        height=(gauge_h / H_PX),
        value_pct=cur_pct,
        dpi=dpi,
        cfg=cfg,
    )

    _draw_staff_gauge_in_page_3(
        fig,
        left=x(right_gauge_x0),
        bottom=y_from_top(gauge_top_px + gauge_h),
        width=(gauge_w / W_PX),
        height=(gauge_h / H_PX),
        value_pct=prev_month_pct,
        dpi=dpi,
        cfg=cfg,
    )

    left_cx = left_gauge_x0 + gauge_w / 2
    right_cx = right_gauge_x0 + gauge_w / 2

    # --- % blancs puis labels des mois sous les gauges ---
    gauge_bottom_px = gauge_top_px + gauge_h

    _, pct_h = _measure_text_px(
        ax,
        _fmt_pct_no_sign(cur_pct, decimals=0),
        cfg["gauge_value_font_px"],
        epilogue_regular,
        dpi,
    )

    pct_top_px = gauge_bottom_px + cfg["gauge_to_pct_gap_px"]
    months_top_px = pct_top_px + pct_h + cfg["pct_to_month_gap_px"]

    _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        pct_top_px,
        left_cx,
        _fmt_pct_no_sign(cur_pct, decimals=0),
        cfg["gauge_value_font_px"],
        epilogue_regular,
        dpi,
        COLORS["white"],
        z=850,
    )

    _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        pct_top_px,
        right_cx,
        _fmt_pct_no_sign(prev_month_pct, decimals=0),
        cfg["gauge_value_font_px"],
        epilogue_regular,
        dpi,
        COLORS["white"],
        z=850,
    )

    # --- Labels des mois sous les gauges ---
    h_m1 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        months_top_px,
        left_cx,
        cur_label,
        cfg["gauge_month_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["white"],
        z=850,
    )

    h_m2 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        months_top_px,
        right_cx,
        prev_month_label,
        cfg["gauge_month_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["white"],
        z=850,
    )

    months_h = max(h_m1, h_m2)

    # --- Ligne "vs N-1" alignée à gauche ---
    vs_top_px = months_top_px + months_h + cfg["vs_row_gap_after_month_px"]

    _draw_text_top_left_px(
        ax,
        cfg["side_margin_px"],
        y_from_top,
        vs_top_px,
        f"vs {d['year_n_1']}",
        cfg["vs_label_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["accent"],
        z=850,
    )

    h_vs_0 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        vs_top_px,
        left_cx,
        _fmt_pct_no_sign(cur_vs_pct, decimals=0),
        cfg["vs_value_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["accent"],
        z=850,
    )

    h_vs_1 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        vs_top_px,
        right_cx,
        _fmt_pct_no_sign(prev_month_vs_pct, decimals=0),
        cfg["vs_value_font_px"],
        epilogue_semibold,
        dpi,
        COLORS["accent"],
        z=850,
    )

    # --- Texte justifié pleine largeur (hors marges) ---
    analysis_text = (analysis_text or "").strip()

    para_top_px = vs_top_px + max(h_vs_0, h_vs_1) + cfg["para_gap_after_vs_px"]

    para_left_px = cfg.get("para_left_px", HEADER1_CFG["line_side_margin_px"])
    para_right_edge_px = W_PX - cfg.get("right_edge_margin_px", cfg["side_margin_px"])
    col_px_layout = para_right_edge_px - para_left_px

    ax.figure.canvas.draw()
    r = ax.figure.canvas.get_renderer()
    ax_bb = ax.get_window_extent(renderer=r)
    ax_w_render = ax_bb.width
    scale_y = ax_bb.height / H_PX

    col_px_render = ax_w_render * (col_px_layout / W_PX)

    # borne basse max = moitié de la page
    max_lines_sample = "\n".join(["Ag"] * int(cfg["para_max_lines"]))
    max_h_render = _measure_multiline_h_render_px(
        ax,
        max_lines_sample,
        cfg["para_font_px"],
        epilogue_regular,
        dpi,
        cfg["para_linespacing"],
    )

    text_wrapped = _fit_justified_paragraph_to_height(
        ax,
        analysis_text,
        width_px=col_px_render,
        font_px=cfg["para_font_px"],
        fontprops=epilogue_regular,
        dpi=dpi,
        linespacing=cfg["para_linespacing"],
        max_height_render_px=max_h_render,
    )

    text_obj = ax.text(
        para_left_px / W_PX,
        y_from_top(para_top_px),
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

    # bas réel du texte pour le return
    ax.figure.canvas.draw()
    bb = text_obj.get_window_extent(renderer=r)
    text_bottom_from_top_px = (ax_bb.y1 - bb.y0) / scale_y

    return float(text_bottom_from_top_px)


# =========================
# 9.7) FOOTER COMMUN
# =========================

FOOTER1_CFG = {
    # Position du footer (top = position de la ligne du footer, depuis le haut)
    "top_px": 700,
    # Ligne (identique header)
    "line_side_margin_px": HEADER1_CFG.get("line_side_margin_px", 40),
    "line_width_px": HEADER1_CFG.get("line_width_px", 2),
    "line_color": HEADER1_CFG.get("line_color", "highlight"),
    "gap_after_line_px": 26,
    # Layout colonnes
    "side_margin_px": BODY1_CFG.get("side_margin_px", 80),  # pour le contenu footer
    "mid_gap_px": 40,  # espace "vide" au centre (où vit la séparation)
    "block_inner_gap_px": 60,  # espace entre les 2 sous-colonnes dans chaque bloc
    # Titres (même taille que "Venduto", même couleur que "Fatturato")
    "title_font_px": BODY1_CFG.get("left_title_font_px", 20),
    "title_color": "accent",
    "title_fontprops": "epilogue_semibold",
    "gap_after_titles_px": 28,
    # Labels au-dessus des valeurs (ex: "Dicembre 2025" / "vs 2024")
    "label_font_px": BODY1_CFG.get("stats_title_font_px", 14),
    "label_color": "white",
    "label_fontprops": "epilogue_regular",
    "gap_label_to_value_px": 16,
    # Valeurs (même style que valeur Fatturato)
    "value_font_px": BODY1_CFG.get("stats_value_font_px", 26),
    "value_color": "highlight",
    "value_fontprops": "epilogue_semibold",
    # Pourcent (marge)
    "marg_decimals": 1,  # 0 => "36%" ; 1 => "36.0%"
    # Séparateur vertical
    "vsep_enabled": True,
    "vsep_color": "highlight",
    "vsep_width_px": 3,
    "vsep_dash": (0, (6, 6)),  # motif pointillé
    "vsep_top_offset_px": 38,  # descend le haut du trait vs la ligne
    "vsep_height_px": 90,  # hauteur du trait (à ajuster)
}


def _draw_text_top_center_x_px(
    ax,
    W_PX,
    y_from_top,
    top_px,
    center_x_px,
    s,
    font_px,
    fontprops,
    dpi,
    color,
    z=10,
    fontstyle=None,
):
    """Texte aligné center/top à X (en px), retourne hauteur px."""
    t = ax.text(
        center_x_px / W_PX,
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


def _fmt_pct(x, decimals=0):
    if decimals <= 0:
        return f"{int(round(x))}%"
    return f"{x:.{decimals}f}%"


def _measure_footer1_height_px(ax, W_PX, H_PX, d, dpi: int, cfg=None) -> float:
    cfg = {**FOOTER1_CFG, **(cfg or {})}
    title_fp = globals()[cfg["title_fontprops"]]
    label_fp = globals()[cfg["label_fontprops"]]
    value_fp = globals()[cfg["value_fontprops"]]

    _, ht = _measure_text_px(ax, "Ricavi - Costi", cfg["title_font_px"], title_fp, dpi)
    _, hl = _measure_text_px(ax, d["full_date_n"], cfg["label_font_px"], label_fp, dpi)
    _, hv = _measure_text_px(
        ax, fmt_eur_dot(d["ric_cost_n"]), cfg["value_font_px"], value_fp, dpi
    )

    return float(
        cfg["gap_after_line_px"]
        + ht
        + cfg["gap_after_titles_px"]
        + hl
        + cfg["gap_label_to_value_px"]
        + hv
    )


def _draw_footer1(ax, W_PX, H_PX, d, dpi: int, cfg=None):
    cfg = {**FOOTER1_CFG, **(cfg or {})}

    # Repère page (ne touche pas au imshow)
    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    def x(px):
        return px / W_PX

    def y_from_top(top_px):
        return 1.0 - (top_px / H_PX)

    # Polices via globals() (comme header/body)
    title_fp = globals()[cfg["title_fontprops"]]
    label_fp = globals()[cfg["label_fontprops"]]
    value_fp = globals()[cfg["value_fontprops"]]

    # --- Ligne du footer (même que header) ---
    y_line = cfg["top_px"]
    side_line = cfg["line_side_margin_px"]
    ax.hlines(
        y=y_from_top(y_line),
        xmin=x(side_line),
        xmax=x(W_PX - side_line),
        colors=COLORS[cfg["line_color"]],
        linewidth=_px_to_pt(cfg["line_width_px"], dpi),
        zorder=800,
    )

    y = y_line + cfg["gap_after_line_px"]

    # --- Colonnes (2 blocs) centrées dans les cadres définis par la ligne + séparateur ---
    mid_x = W_PX / 2
    mid_gap = cfg["mid_gap_px"]

    # bornes EXACTES des cadres : début/fin de la ligne
    line_left_px = cfg["line_side_margin_px"]
    line_right_px = W_PX - cfg["line_side_margin_px"]

    # cadres gauche/droite : entre ligne et séparateur (avec mid_gap)
    left_block_x0 = line_left_px
    left_block_x1 = mid_x - mid_gap / 2
    right_block_x0 = mid_x + mid_gap / 2
    right_block_x1 = line_right_px

    # centres blocs
    left_cx = (left_block_x0 + left_block_x1) / 2
    right_cx = (right_block_x0 + right_block_x1) / 2

    # --- Titres (Ricavi - Costi / Margine) ---
    h_t1 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y,
        left_cx,
        "Ricavi - Costi",
        cfg["title_font_px"],
        title_fp,
        dpi,
        COLORS[cfg["title_color"]],
        z=850,
    )
    h_t2 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y,
        right_cx,
        "Margine % su ricavi",
        cfg["title_font_px"],
        title_fp,
        dpi,
        COLORS[cfg["title_color"]],
        z=850,
    )

    y += max(h_t1, h_t2) + cfg["gap_after_titles_px"]

    # --- Sous-colonnes dans chaque bloc (date / vs) ---
    inner_gap = cfg["block_inner_gap_px"]

    def split_two_cols(x0, x1):
        w = (x1 - x0 - inner_gap) / 2
        c1x0 = x0
        c1cx = c1x0 + w / 2
        c2x0 = x0 + w + inner_gap
        c2cx = c2x0 + w / 2
        return (c1cx, c2cx)

    l_c1cx, l_c2cx = split_two_cols(left_block_x0, left_block_x1)
    r_c1cx, r_c2cx = split_two_cols(right_block_x0, right_block_x1)

    # labels
    label_left = d["full_date_n"]  # "Dicembre 2025"
    label_right = f"vs {d['year_n_1']}"  # "vs 2024"

    hl1 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y,
        l_c1cx,
        label_left,
        cfg["label_font_px"],
        label_fp,
        dpi,
        COLORS[cfg["label_color"]],
        z=850,
    )
    hl2 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y,
        l_c2cx,
        label_right,
        cfg["label_font_px"],
        label_fp,
        dpi,
        COLORS[cfg["label_color"]],
        z=850,
    )

    hr1 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y,
        r_c1cx,
        label_left,
        cfg["label_font_px"],
        label_fp,
        dpi,
        COLORS[cfg["label_color"]],
        z=850,
    )
    hr2 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y,
        r_c2cx,
        label_right,
        cfg["label_font_px"],
        label_fp,
        dpi,
        COLORS[cfg["label_color"]],
        z=850,
    )

    y_vals = y + max(hl1, hl2, hr1, hr2) + cfg["gap_label_to_value_px"]

    # --- Valeurs ---
    ric_n = fmt_eur_dot(d["ric_cost_n"])
    ric_p = fmt_eur_dot(d["ric_cost_n_1"])
    marg_n = _fmt_pct(d["marg_n"], decimals=cfg["marg_decimals"])
    marg_p = _fmt_pct(d["marg_n_1"], decimals=cfg["marg_decimals"])

    hv1 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y_vals,
        l_c1cx,
        ric_n,
        cfg["value_font_px"],
        value_fp,
        dpi,
        COLORS[cfg["value_color"]],
        z=850,
    )
    hv2 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y_vals,
        l_c2cx,
        ric_p,
        cfg["value_font_px"],
        value_fp,
        dpi,
        COLORS[cfg["value_color"]],
        z=850,
    )

    hv3 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y_vals,
        r_c1cx,
        marg_n,
        cfg["value_font_px"],
        value_fp,
        dpi,
        COLORS[cfg["value_color"]],
        z=850,
    )
    hv4 = _draw_text_top_center_x_px(
        ax,
        W_PX,
        y_from_top,
        y_vals,
        r_c2cx,
        marg_p,
        cfg["value_font_px"],
        value_fp,
        dpi,
        COLORS[cfg["value_color"]],
        z=850,
    )

    # --- Séparateur vertical pointillé (au centre) ---
    if cfg["vsep_enabled"]:
        x_mid = mid_x
        y0 = y_line + cfg["vsep_top_offset_px"]
        y1 = y0 + cfg["vsep_height_px"]
        ax.vlines(
            x=x(x_mid),
            ymin=y_from_top(y1),
            ymax=y_from_top(y0),
            colors=COLORS[cfg["vsep_color"]],
            linewidth=_px_to_pt(cfg["vsep_width_px"], dpi),
            linestyles=cfg["vsep_dash"],
            zorder=900,
        )


# =========================
# 10) CONSTRUCTION DE LA PAGE 1
# =========================


def _draw_a4_page(ax, W_PX, H_PX, d, restaurant_name: str, analysis_text: str = ""):
    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    dpi = int(ax.figure.dpi)

    # Header (retourne le y de la ligne)
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

    # Footer ancré : bas des valeurs à 20px du bas
    footer_h = _measure_footer1_height_px(ax, W_PX, H_PX, d, dpi)
    footer_line_y_px = int(H_PX - PAGE_TOKENS["pad_bottom_px"] - footer_h)

    # Zone utile (footer déjà ancré)
    region_start = float(header_line_y_px + BODY1_CFG["gap_after_header_px"])
    region_end = float(footer_line_y_px - PAGE_TOKENS["gap_body_to_footer_min_px"])
    region_h = max(0.0, region_end - region_start)

    gap_default = float(BODY1_CFG["stats_line_gap_after_px"])
    gap_min = float(PAGE_TOKENS["gap_min_px"])

    # Mesure body (avec gap variable)
    m0 = _measure_body1_metrics(
        ax,
        W_PX,
        H_PX,
        d,
        restaurant_name,
        analysis_text,
        dpi,
        cfg={"stats_line_gap_after_px": gap_default},
    )
    section_bottom = float(m0["section_bottom_px"])
    body_h0 = float(m0["height_px"])

    # On centre uniquement CE QUI EST SOUS "Fatturato"
    rest_h0 = max(0.0, body_h0 - section_bottom)

    rest_start = region_start + section_bottom + 20.0
    rest_end = region_end
    rest_region_h = max(0.0, rest_end - rest_start)

    chosen_gap = gap_default
    m = m0

    # Compression du gap stats->paragraphe si nécessaire
    if rest_h0 > rest_region_h and gap_default > gap_min:
        overflow = rest_h0 - rest_region_h
        chosen_gap = max(gap_min, gap_default - overflow)
        m = _measure_body1_metrics(
            ax,
            W_PX,
            H_PX,
            d,
            restaurant_name,
            analysis_text,
            dpi,
            cfg={"stats_line_gap_after_px": chosen_gap},
        )
        section_bottom = float(m["section_bottom_px"])
        body_h = float(m["height_px"])
    else:
        body_h = body_h0

    rest_h = max(0.0, body_h - section_bottom)

    if rest_h <= rest_region_h:
        after_section_offset = (rest_region_h - rest_h) / 2.0
        para_max_bottom_px = None
    else:
        after_section_offset = 0.0
        para_max_bottom_px = rest_end

    _draw_body1_fatturato(
        ax,
        W_PX,
        H_PX,
        d,
        restaurant_name,
        analysis_text,
        dpi,
        cfg={
            "top_px": int(region_start),
            "after_section_offset_px": float(after_section_offset),
            "stats_line_gap_after_px": int(round(chosen_gap)),
            **(
                {"para_max_bottom_px": float(para_max_bottom_px)}
                if para_max_bottom_px is not None
                else {}
            ),
        },
    )

    _draw_footer1(
        ax,
        W_PX,
        H_PX,
        d,
        dpi,
        cfg={"top_px": int(footer_line_y_px)},
    )


# =========================
# 11) CONSTRUCTION DE LA PAGE 2
# =========================


def _draw_a4_page_2(ax, W_PX, H_PX, d, restaurant_name: str, analysis_text: str = ""):
    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    dpi = int(ax.figure.dpi)

    # Header bis (sans "Report Mensile")
    header_line_y_px = (
        _draw_header1_bis(
            ax,
            W_PX=W_PX,
            H_PX=H_PX,
            month_label=d["full_date_n"],
            restaurant_name=restaurant_name,
            dpi=dpi,
        )
        or 0
    )

    # charts_bottom_px = vrai bas rendu des charts (ticks inclus)
    charts_bottom_px = _draw_body_page_2_food_beverage_cost(
        ax,
        W_PX,
        H_PX,
        d,
        restaurant_name,
        dpi,
        cfg={"header_line_y_px": int(header_line_y_px)},
    )

    # --- Proposition B : ax dédié pour le bloc synthèse FC/BC + texte analytique ---
    # On positionne cet ax dans la zone basse de la figure (sous les charts),
    # ce qui isole ce groupe dans le PDF et le rend sélectionnable dans Canva.
    # Le système de coordonnées interne (top_px=0) est recalibré pour que le
    # rendu final soit pixel-perfect identique à l'original.
    summary_top_layout_px = int(charts_bottom_px + 20)
    summary_h_layout_px = H_PX - summary_top_layout_px

    # Coordonnées normalisées dans la figure (bottom-left origin de matplotlib)
    ax_sum_bottom = 1.0 - (summary_top_layout_px + summary_h_layout_px) / H_PX
    ax_sum_height = summary_h_layout_px / H_PX

    ax_summary = ax.figure.add_axes(
        [0.0, ax_sum_bottom, 1.0, ax_sum_height],
        facecolor="none",
    )
    ax_summary.patch.set_alpha(0)  # fond transparent

    # On passe top_px=0 car l'ax_summary commence exactement au bon endroit :
    # la fonction dessine à partir du haut de son propre repère.
    _draw_body_fc_bc_summary(
        ax_summary,
        W_PX,
        summary_h_layout_px,  # H_PX local = hauteur de la zone summary
        d,
        restaurant_name,
        analysis_text,
        dpi,
        cfg={
            "top_px": 0,
            "para_max_bottom_px": float(summary_h_layout_px - 10),
        },
    )


# Pas de footer en page 2 ✅


# =========================
# 12) CONSTRUCTION DE LA PAGE 3
# =========================
def _draw_a4_page_3(ax, W_PX, H_PX, d, restaurant_name: str, analysis_text: str = ""):
    ax.set_axis_off()
    ax.set_aspect("auto")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    dpi = int(ax.figure.dpi)

    # Header bis (sans "Report Mensile")
    header_line_y_px = (
        _draw_header1_bis(
            ax,
            W_PX=W_PX,
            H_PX=H_PX,
            month_label=d["full_date_n"],
            restaurant_name=restaurant_name,
            dpi=dpi,
        )
        or 0
    )

    _draw_body_page_3_staff(
        ax,
        W_PX,
        H_PX,
        d,
        restaurant_name,
        analysis_text,
        dpi,
        cfg={"header_line_y_px": int(header_line_y_px)},
    )


# Pas de footer en page 3 ✅

# =========================
# 13) CONFIGURATION GLOBALE DES PAGES (suite)
# =========================


# ✅ Taille cible en pixels (ton nouveau "format")
PAGE_W_PX = 800
PAGE_H_PX = 1000

# ✅ DPI de référence : fixe la taille physique du PDF
BASE_DPI = 100

# ✅ Taille "physique" (inches) qui correspond à 800x1000 px à BASE_DPI
PAGE_SIZE_INCH = (PAGE_W_PX / BASE_DPI, PAGE_H_PX / BASE_DPI)

# =========================
# 14) GENERATION PDF ET PNG
# =========================


def _build_page_bytes(draw_fn, d, restaurant_name, analysis_text, fmt, dpi_render):
    """Factorisation commune des 6 builders PDF/PNG."""
    use_dpi = BASE_DPI if fmt == "pdf" else dpi_render
    fig = plt.figure(figsize=PAGE_SIZE_INCH, dpi=use_dpi, facecolor=COLORS["bg"])
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    draw_fn(ax, PAGE_W_PX, PAGE_H_PX, d, restaurant_name, analysis_text=analysis_text)
    buf = BytesIO()
    fig.savefig(
        buf,
        format=fmt,
        bbox_inches=None,
        pad_inches=0,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


@st.cache_data
def build_a4_pdf_bytes(
    d, restaurant_name: str, analysis_text: str = "", dpi=300
) -> bytes:
    return _build_page_bytes(
        _draw_a4_page, d, restaurant_name, analysis_text, "pdf", dpi
    )


def build_a4_png_preview_bytes(
    d, restaurant_name: str, analysis_text: str = "", dpi=150
) -> bytes:
    return _build_page_bytes(
        _draw_a4_page, d, restaurant_name, analysis_text, "png", dpi
    )


@st.cache_data
def build_a4_page_2_pdf_bytes(
    d, restaurant_name: str, analysis_text: str = "", dpi=300
) -> bytes:
    return _build_page_bytes(
        _draw_a4_page_2, d, restaurant_name, analysis_text, "pdf", dpi
    )


def build_a4_page_2_png_preview_bytes(
    d, restaurant_name: str, analysis_text: str = "", dpi=150
) -> bytes:
    return _build_page_bytes(
        _draw_a4_page_2, d, restaurant_name, analysis_text, "png", dpi
    )


@st.cache_data
def build_a4_page_3_pdf_bytes(
    d, restaurant_name: str, analysis_text: str = "", dpi=300
) -> bytes:
    return _build_page_bytes(
        _draw_a4_page_3, d, restaurant_name, analysis_text, "pdf", dpi
    )


def build_a4_page_3_png_preview_bytes(
    d, restaurant_name: str, analysis_text: str = "", dpi=150
) -> bytes:
    return _build_page_bytes(
        _draw_a4_page_3, d, restaurant_name, analysis_text, "png", dpi
    )


# =========================
# 15) INTERFACE STREAMLIT
# =========================
st.title("Report Fizzy Automatizzazione ⚡️")

soda_logo_uri = _img_to_data_uri(LOGO_PATH)

if soda_logo_uri:
    st.sidebar.markdown(
        f"""
        <div class="soda-sidebar-brand">
            <img src="{soda_logo_uri}" alt="We are Soda" />
        </div>
        """,
        unsafe_allow_html=True,
    )

restaurant_input = st.sidebar.text_input(
    "Nome clienti *", placeholder="es: Ristorante Da Mario"
)
uploaded = st.sidebar.file_uploader("Caricare il Report (.xslx))", type="xlsx")

if uploaded and restaurant_input:
    data = load_data(uploaded)
    _ensure_report_text_state(data, restaurant_input)
    report_texts = get_report_text_state()
    report_payload = build_report_text_payload(report_texts)
    page1_analysis_text = report_payload["page1_analysis_text"]
    page2_analysis_text = report_payload["page2_analysis_text"]
    page3_analysis_text = report_payload["page3_analysis_text"]

    col_viz, col_edit = st.columns([1.2, 1], gap="large")

    with col_viz:
        st.subheader("📊 Fatturato (mensile) ")
        preview_fig = make_fatturato_fig(data, label=restaurant_input)
        st.pyplot(preview_fig)

    with col_edit:
        st.subheader("✍️ Analisa scritta")

        st.text_area(
            "💡 Proposta paragrafo 1",
            value=st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page1_p1"], ""),
            height=150,
            disabled=True,
        )
        st.text_area(
            "💡 Proposta paragrafo 2",
            value=st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page1_p2"], ""),
            height=150,
            disabled=True,
        )
        st.text_area(
            "📝 Testo finale (modificabile)",
            height=300,
            key=FINAL_TEXT_STATE_KEYS["page1_final"],
            placeholder="Copia qui la proposta e modificala.",
        )
        btn_spacer, btn_col = st.columns([2.4, 1])
        with btn_col:
            st.button(
                "📥 Usa le proposte",
                key="use_proposal_page1",
                on_click=_copy_page1_proposals_to_final,
                width="stretch",
            )

    # --- Section graphs pleine largeur ---
    st.divider()

    # =========================
    # FOOD & BEVERAGE COST — graphiques (inchangés)
    # =========================
    food_title_col_left, food_title_col_right = st.columns([1, 1], gap="large")
    with food_title_col_left:
        st.subheader("📈 Food cost (mensile)")
    with food_title_col_right:
        st.subheader("📈 Beverage cost (mensile)")

    food_col_graph, bev_col_graph = st.columns([1, 1], gap="large")
    with food_col_graph:
        food_fig = make_food_cost_fig(data, label=restaurant_input)
        st.pyplot(food_fig)
    with bev_col_graph:
        bev_fig = make_beverage_cost_fig(data, label=restaurant_input)
        st.pyplot(bev_fig)

    # =========================
    # TEXTE PAGE 2 — bloc unique (même structure que page 1 et page 3)
    # =========================
    st.subheader("✍️ Analisa scritta — Food & Beverage cost")

    p2_col_suggest, p2_col_edit = st.columns([1, 1], gap="large")

    with p2_col_suggest:
        st.text_area(
            "💡 Proposta Food Cost",
            value=st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page2_food"], ""),
            height=150,
            disabled=True,
        )
        st.text_area(
            "💡 Proposta Beverage Cost",
            value=st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page2_bev"], ""),
            height=150,
            disabled=True,
        )

    with p2_col_edit:
        st.text_area(
            "📝 Testo finale (modificabile)",
            height=330,
            key=FINAL_TEXT_STATE_KEYS["page2_final"],
            placeholder="Copia qui le proposte e modificala.",
        )
        btn_spacer, btn_col = st.columns([2.4, 1])
        with btn_col:
            st.button(
                "📥 Usa le proposte",
                key="use_proposal_page2",
                on_click=_copy_page2_proposals_to_final,
                width="stretch",
            )

    # --- Section staff ---
    st.divider()

    # =========================
    # INCIDENZA STAFF
    # =========================
    staff_title_col_left, staff_title_col_right = st.columns([1.2, 1], gap="large")

    with staff_title_col_left:
        st.subheader("📉 Incidenza Staff")

    with staff_title_col_right:
        st.subheader("✍️ Analisa scritta")

    staff_col_graph, staff_col_text = st.columns([1.2, 1], gap="large")

    with staff_col_graph:
        staff_fig = make_staff_gauge_fig(data)
        st.pyplot(staff_fig)

    with staff_col_text:

        st.text_area(
            "💡 Proposta Incidenza Staff",
            value=st.session_state.get(SUGGESTION_TEXT_STATE_KEYS["page3_staff"], ""),
            height=150,
            key=SUGGESTION_TEXT_STATE_KEYS["page3_staff"],
            disabled=True,
        )
        st.text_area(
            "📝 Testo finale (modificabile)",
            height=150,
            key=FINAL_TEXT_STATE_KEYS["page3_staff_final"],
            placeholder="Copia qui la proposta e modificala.",
        )
        btn_spacer, btn_col = st.columns([2.4, 1])
        with btn_col:
            st.button(
                "📥 Usa la proposta",
                key="use_proposal_staff",
                on_click=_copy_staff_proposal_to_final,
                width="stretch",
            )

    # --- Section export PDF ---
    st.divider()

    # =========================
    # RANK ARTICOLI & RANK RICAVI
    # =========================
    rank_articoli = data.get("rank_articoli", [])
    rank_ricavi = data.get("rank_ricavi", [])

    if rank_articoli or rank_ricavi:
        rank_col_left, rank_col_right = st.columns([1, 1], gap="large")

        with rank_col_left:
            st.subheader("🏆 Top Articoli (Quantità)")
            if rank_articoli:
                _shared_h = max(4.0, max(len(rank_articoli), len(rank_ricavi)) * 0.40)
                fig_art = make_rank_bar_fig(
                    rank_articoli, value_fmt="qty", fig_h=_shared_h
                )
                st.pyplot(fig_art)
            else:
                st.info("Sheet 'Export Rank Articoli' non trovata o vuota.")

        with rank_col_right:
            st.subheader("💰 Top Articoli (Ricavi €)")
            if rank_ricavi:
                # APRÈS
                fig_ric = make_rank_bar_fig(
                    rank_ricavi, value_fmt="eur", fig_h=_shared_h
                )
                st.pyplot(fig_ric)
            else:
                st.info("Sheet 'Export Rank Ricavi' non trovata o vuota.")

        st.divider()

    # --- UI : Export PDF ---
    pdf_bytes_page_1 = build_a4_pdf_bytes(
        data,
        restaurant_input,
        analysis_text=page1_analysis_text,
        dpi=300,
    )
    pdf_bytes_page_2 = build_a4_page_2_pdf_bytes(
        data,
        restaurant_input,
        analysis_text=page2_analysis_text,
        dpi=300,
    )
    pdf_bytes_page_3 = build_a4_page_3_pdf_bytes(
        data,
        restaurant_input,
        analysis_text=page3_analysis_text,
        dpi=300,
    )

    merged_pdf_bytes = merge_pdf_bytes(
        pdf_bytes_page_1,
        pdf_bytes_page_2,
        pdf_bytes_page_3,
    )

    png_bytes_page_1 = pdf_bytes_to_png_bytes(pdf_bytes_page_1, page_index=0, zoom=2.0)
    png_bytes_page_2 = pdf_bytes_to_png_bytes(pdf_bytes_page_2, page_index=0, zoom=2.0)
    png_bytes_page_3 = pdf_bytes_to_png_bytes(pdf_bytes_page_3, page_index=0, zoom=2.0)

    export_col_preview, export_col_action = st.columns([1.2, 1], gap="large")

    with export_col_preview:
        st.image(
            png_bytes_page_1, caption="Anteprima pagina 1 (rendu PDF)", width="stretch"
        )
        st.image(
            png_bytes_page_2, caption="Anteprima pagina 2 (rendu PDF)", width="stretch"
        )
        st.image(
            png_bytes_page_3, caption="Anteprima pagina 3 (rendu PDF)", width="stretch"
        )

    with export_col_action:
        st.subheader("📄 Export PDF")
        report_dt = (
            pd.Timestamp(data["raw_date_n"])
            if data.get("raw_date_n") is not None
            else None
        )
        report_prefix = report_dt.strftime("%y%m") if report_dt is not None else "0000"
        client_name_safe = str(restaurant_input).strip()

        st.download_button(
            label="⬇️ Scarica PDF",
            data=merged_pdf_bytes,
            file_name=f"{report_prefix} - Report {client_name_safe}.pdf",
            mime="application/pdf",
        )

else:
    st.info(
        "Importa un file Excel e inserisci il nome del cliente per generare il PDF. 📄"
    )
