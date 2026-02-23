import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Injection de la police Epilogue via Google Fonts pour le web
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Epilogue:wght@400;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Epilogue', sans-serif;
    }
    </style>
    """, unsafe_content_type=True)

# Configuration
COLORS = {
    "bg": "#172e4d",
    "accent": "#edf86c",
    "highlight": "#c8bcab",
    "graph_line": "#ece8e1",
    "white": "#ffffff"
}

def load_full_data(file):
    # On lit l'onglet 'Dati report'
    df = pd.read_excel(file, sheet_name='Dati report', header=None)
    
    # Page 1 Data
    data = {
        "month": "Novembre 2025",
        "ca_n": df.iloc[8, 1],
        "ca_n_1": df.iloc[9, 1],
        "diff_ca": round(df.iloc[8, 2] * 100, 1),
        "margine_n": round(df.iloc[16, 1] * 100, 1),
        "margine_n_1": round(df.iloc[17, 1] * 100, 1),
        "food_cost_avg": round(df.iloc[22, 1] * 100, 1),
        "food_cost_benchmark": round(df.iloc[22, 2] * 100, 1)
    }
    
    # Page 2 Data : Historique 6 mois (Lignes 26 à 31, colonnes A et E dans ton fichier)
    # On va chercher les 6 derniers mois de Food Cost
    history = df.iloc[26:32, [0, 4]] 
    history.columns = ['Mese', 'FC']
    history['FC'] = history['FC'] * 100
    data['history'] = history
    
    return data

def draw_report_p2(d):
    fig = plt.figure(figsize=(10, 14), facecolor=COLORS["bg"])
    ax = fig.add_axes([0, 0, 1, 1], facecolor=COLORS["bg"])
    
    # Header
    ax.text(0.05, 0.94, "We\nare_\nFIZZY", color=COLORS["white"], fontsize=18, fontweight='bold')
    ax.text(0.5, 0.88, "Food & Beverage Cost", color=COLORS["white"], fontsize=22, ha='center', fontweight='bold')

    # Graphique Courbe
    ax_plot = fig.add_axes([0.1, 0.60, 0.8, 0.20], facecolor=COLORS["bg"])
    ax_plot.plot(d['history']['Mese'], d['history']['FC'], color=COLORS["graph_line"], marker='o', linewidth=3)
    
    # Style du graphique
    ax_plot.set_frame_on(False)
    ax_plot.tick_params(colors=COLORS["white"], labelsize=10)
    ax_plot.grid(axis='y', color=COLORS["white"], alpha=0.1)
    
    # Ajout du Benchmark (Ligne pointillée)
    ax_plot.axhline(y=d['food_cost_benchmark'], color=COLORS["accent"], linestyle='--', alpha=0.6)
    ax_plot.text(0, d['food_cost_benchmark']+1, "Benchmark Gruppo", color=COLORS["accent"], fontsize=9)

    # Chiffres Clés
    ax.text(0.05, 0.50, "Media ultimi 6 mesi", color=COLORS["accent"], fontsize=16)
    ax.text(0.05, 0.44, f"{d['food_cost_avg']}%", color=COLORS["white"], fontsize=40, fontweight='bold')
    
    ax.text(0.50, 0.50, "Benchmark Gruppo", color=COLORS["highlight"], fontsize=16)
    ax.text(0.50, 0.44, f"{d['food_cost_benchmark']}%", color=COLORS["white"], fontsize=40, fontweight='bold')

    # Commentaire (Statique pour le test, peut être généré par IA)
    comment = "Il food cost si mantiene stabile e in linea con il benchmark del gruppo."
    ax.text(0.05, 0.30, comment, color=COLORS["white"], fontsize=12, wrap=True)

    plt.axis('off')
    return fig

# --- STREAMLIT ---
st.title("Fizzy Automator - Page 2")
uploaded = st.file_uploader("Upload Excel", type="xlsx")

if uploaded:
    data = load_full_data(uploaded)
    if st.button("Générer Page 2"):
        st.pyplot(draw_report_p2(data))