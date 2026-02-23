def load_data(file):
    df = pd.read_excel(file, sheet_name='Dati report', header=None)

    # Dictionnaire de traduction des mois
    months_it = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }

    # --- 1. Extraction de la date (ex: "Dicembre 2025") ---
    raw_date = df.iloc[4, 2]  # Supposons que la date est toujours en C5
    if hasattr(raw_date, 'month'):
        mes_it = months_it[raw_date.month]
        anno_n = raw_date.year
    else:
        mes_it = "Mese"
        anno_n = 2026  # Valeur par défaut

    # --- 2. Extraction des données "Fatturato" ---
    # Chercher la ligne contenant "Fatturato 2025" et "Fatturato 2024"
    fatturato_n_row = df[df.apply(lambda row: row.astype(str).str.contains("Fatturato 2025", na=False).any(), axis=1)].index[0]
    fatturato_n_1_row = df[df.apply(lambda row: row.astype(str).str.contains("Fatturato 2024", na=False).any(), axis=1)].index[0]

    fatturato_n = clean_val(df.iloc[fatturato_n_row, 2])
    fatturato_n_1 = clean_val(df.iloc[fatturato_n_1_row, 2])
    diff_fatturato = round(clean_val(df.iloc[fatturato_n_row, 3]) * 100, 1)

    # Ricavi - Costi et Margine (supposons qu'ils sont 4 lignes après "Fatturato 2025")
    ric_cost_n = clean_val(df.iloc[fatturato_n_row + 4, 2])
    ric_cost_n_1 = clean_val(df.iloc[fatturato_n_row + 5, 2])
    marg_n = round(clean_val(df.iloc[fatturato_n_row + 8, 2]) * 100, 1)
    marg_n_1 = round(clean_val(df.iloc[fatturato_n_row + 9, 2]) * 100, 1)

    # --- 3. Extraction des données "Food & Beverage Cost" ---
    # Chercher la ligne contenant "Food Cost" ou "Andamento Food Cost Mensile"
    food_cost_title_row = df[df.apply(lambda row: row.astype(str).str.contains("Food Cost", na=False).any(), axis=1)].index[0]
    beverage_cost_title_row = df[df.apply(lambda row: row.astype(str).str.contains("Beverage Cost", na=False).any(), axis=1)].index[0]

    # Extraire les valeurs mensuelles (supposons qu'elles sont sur les 6 prochaines lignes)
    food_cost_monthly = [clean_val(df.iloc[food_cost_title_row + i, 2]) for i in range(1, 7)]
    beverage_cost_monthly = [clean_val(df.iloc[beverage_cost_title_row + i, 2]) for i in range(1, 7)]

    # Moyennes (supposons qu'elles sont 1 ligne après les valeurs mensuelles)
    food_cost_avg = clean_val(df.iloc[food_cost_title_row + 7, 2])
    beverage_cost_avg = clean_val(df.iloc[beverage_cost_title_row + 7, 2])

    # --- 4. Extraction des données "Incidenza Staff" ---
    # Chercher la ligne contenant "Incidenza Staff" ou "Labour Cost"
    staff_cost_title_row = df[df.apply(lambda row: row.astype(str).str.contains("Incidenza Staff|Labour Cost", na=False).any(), axis=1)].index[0]

    # Extraire les pourcentages (supposons qu'ils sont sur les 3 prochaines lignes)
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
