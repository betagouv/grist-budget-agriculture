def comment(e, group, ci):
    montant_type = e[ci["Type montant"]]
    if montant_type != "Montant engagé":
        return ""
    total_bc = e[ci["Montant_AE"]]
    montant_ligne = e[ci["Montant Chorus"]]

    if montant_ligne == total_bc:
        return "OK - BC initial"

    annee = e[ci["Exercice comptable"]]
    engage_c = group["Type montant"] == "Montant engagé"
    synchro_c = group["Exercice comptable"] == annee
    e_df = group[engage_c * synchro_c]
    engage = e_df["Montant Chorus"].sum()
    if engage == total_bc:
        return "OK - BC subdivisé"

    p_c = group["Type montant"] == "Montant payé"
    ante_c = group["Date de base de la DP - date"].dt.year < annee
    pas_avance_c = group["N° poste DP"] != "1"
    payedf = group[p_c * ante_c * pas_avance_c]

    paye = payedf["Montant Chorus"].sum()
    reste_a_payer = total_bc - paye
    diff = montant_ligne - reste_a_payer
    if abs(diff) < 0.01:
        return "OK - Reste à engager"
    else:
        return "KO - Écart non expliqué (diff={:>12_.2f})".format(diff)


def grouped_comment(group):
    ci = {v: i for (i, v) in enumerate(group.columns)}
    return group.apply(comment, axis=1, raw=True, group=group, ci=ci)


def add_check_column(df):
    df["Commentaire"] = (
        df.groupby("N° EJ")
        .apply(grouped_comment, include_groups=False)
        .reset_index("N° EJ", drop=True)
    )
