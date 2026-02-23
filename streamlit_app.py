import streamlit as st

# Création de deux colonnes
col1, col2 = st.columns([1, 1]) # 50% / 50%

with col1:
    st.subheader("Visualisation des données")
    # Utilisation du graphique natif Streamlit
    chart_data = pd.DataFrame(
        [data_dict["fatturato_n_1"], data_dict["fatturato_n"]],
        index=["2024", "2025"],
        columns=["Fatturato"]
    )
    st.bar_chart(chart_data)

with col2:
    st.subheader("Votre analyse")
    # Zone pour que l'utilisateur rédige son texte
    user_analysis = st.text_area(
        "Rédigez le commentaire pour le client :",
        value="Dal confronto con lo stesso periodo dell'anno precedente emerge che...",
        height=300
    )

# Bouton final
if st.button("🎨 Générer le rapport final (Image)"):
    # Ici on appelle notre fonction draw_full_report en lui passant 'user_analysis'
    fig = draw_full_report(data_dict, restaurant_input, user_analysis)
    st.pyplot(fig)