"""
Infographie interactive de l'activité des Hôpitaux universitaires
Pitié-Salpêtrière / Charles-Foix.

Public visé : direction d'établissement et équipes soignantes. L'application ne
recalcule aucun modèle : elle lit uniquement les fichiers préparés dans
data/processed/ et data/raw/.

Lancement :
    streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

# Permet de lancer l'application depuis n'importe quel dossier
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (  # noqa: E402
    MODES_PERIODE,
    MOIS_LONGS,
    PALETTE,
    PALETTE_CATEGORIES,
    SIGLES,
    charger_donnees_brutes,
    charger_prevision,
    charger_prevision_crise,
    charger_profil_saisonnier,
    charger_serie_annuelle,
    charger_serie_mensuelle,
    derniere_valeur,
    filtrer_periode,
    format_nombre,
    mise_en_page_plotly,
    valeurs_par_annee,
)

st.set_page_config(
    page_title="Activité PSL-CFX",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------

activite = charger_donnees_brutes("activite.csv")
capacite = charger_donnees_brutes("capacite.csv")
pathologies = charger_donnees_brutes("pathologies.csv")
rh = charger_donnees_brutes("rh.csv")
finance = charger_donnees_brutes("finance.csv")

serie_annuelle = charger_serie_annuelle()
serie_mensuelle = charger_serie_mensuelle()
profil = charger_profil_saisonnier()
prevision = charger_prevision()
prevision_crise = charger_prevision_crise()

# Correspondance entre le nom technique des séries et leur libellé à l'écran
LIBELLES_SERIES = {
    "Urgences (SAU)": "Passages aux urgences (SAU)",
    "Séjours hospitalisation complète": "Séjours en hospitalisation complète",
    "Séjours ambulatoires": "Séjours en ambulatoire",
    "Consultations externes": "Consultations externes",
}
SERIE_AVEC_PREVISION = "Urgences (SAU)"

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------

st.title("Hôpitaux universitaires Pitié-Salpêtrière · Charles-Foix")
st.markdown(
    "Panorama de l'activité du groupe hospitalier, de son rythme au fil de l'année "
    "et de sa sensibilité à une crise sanitaire."
)

with st.expander("Signification des sigles employés"):
    colonnes_sigles = st.columns(3)
    for rang, (sigle, definition) in enumerate(SIGLES.items()):
        with colonnes_sigles[rang % 3]:
            st.markdown(f"**{sigle}** : {definition}")

onglet_hopital, onglet_annee, onglet_crise = st.tabs([
    "L'hôpital aujourd'hui",
    "L'activité au fil de l'année",
    "Et si une crise arrive ?",
])

# ===========================================================================
# ONGLET 1 : L'hôpital aujourd'hui
# ===========================================================================

with onglet_hopital:
    st.subheader("Les grands chiffres")

    # --- Chiffres clés -----------------------------------------------------
    annee_lits, lits, lits_avant = derniere_valeur(capacite, "Lits installés", "Total")
    annee_sejours, sejours, sejours_avant = derniere_valeur(activite, "Séjours MCO", "Total")
    annee_consult, consultations, consult_avant = derniere_valeur(
        activite, "Consultations externes", "Total"
    )
    annee_urgences, urgences_an, _ = derniere_valeur(activite, "Urgences", "Passages")
    annee_budget, budget, _ = derniere_valeur(finance, "Budget", "Total")

    # Personnel : on additionne médical et non médical de la dernière année où les
    # deux totaux sont publiés dans la même unité, pour éviter d'additionner des
    # effectifs physiques avec des équivalents temps plein.
    annee_medical, medical, medical_avant = derniere_valeur(rh, "Personnel médical", "Total")
    annee_non_medical, non_medical, non_medical_avant = derniere_valeur(
        rh, "Personnel non médical", "Total"
    )
    personnel = medical + non_medical
    personnel_avant = medical_avant + non_medical_avant

    ligne_1 = st.columns(3)
    ligne_2 = st.columns(3)

    with ligne_1[0]:
        st.metric(
            f"Lits installés ({annee_lits})",
            format_nombre(lits),
            delta=format_nombre(lits - lits_avant) if lits_avant else None,
            help="Capacité d'hospitalisation, toutes disciplines confondues, sur les deux sites.",
        )
    with ligne_1[1]:
        st.metric(
            f"Séjours MCO ({annee_sejours})",
            format_nombre(sejours),
            delta=format_nombre(sejours - sejours_avant) if sejours_avant else None,
            help="Séjours de court séjour : médecine, chirurgie, obstétrique.",
        )
    with ligne_1[2]:
        st.metric(
            f"Consultations externes ({annee_consult})",
            format_nombre(consultations),
            delta=format_nombre(consultations - consult_avant) if consult_avant else None,
            help="Consultations de patients non hospitalisés.",
        )
    with ligne_2[0]:
        st.metric(
            f"Passages aux urgences ({annee_urgences})",
            format_nombre(urgences_an),
            help=(
                "Aucune évolution n'est affichée : le périmètre de comptage des urgences "
                "change d'un rapport à l'autre, ce qui rend les années non comparables entre elles."
            ),
        )
    with ligne_2[1]:
        st.metric(
            f"Personnel ({annee_medical})",
            f"{format_nombre(personnel)} ETP",
            delta=format_nombre(personnel - personnel_avant) if personnel_avant else None,
            help=(
                f"Personnel médical ({format_nombre(medical)} ETP) et non médical "
                f"({format_nombre(non_medical)} ETP)."
            ),
        )
    with ligne_2[2]:
        st.metric(
            f"Budget ({annee_budget})",
            f"{format_nombre(budget, 1)} M€",
            help="Budget annuel du groupe hospitalier.",
        )

    st.divider()

    # --- Bascule vers l'ambulatoire ---------------------------------------
    st.subheader("La bascule vers l'ambulatoire")

    modes = {
        "Séjours hospitalisation complète": "Hospitalisation complète",
        "Séjours ambulatoires": "Ambulatoire (moins de 24 h)",
    }
    evolution = serie_annuelle[serie_annuelle["INDICATEUR"].isin(modes)]

    figure_modes = go.Figure()
    for rang, (nom_technique, libelle) in enumerate(modes.items()):
        serie = evolution[evolution["INDICATEUR"] == nom_technique].sort_values("ANNEE")
        figure_modes.add_trace(go.Scatter(
            x=serie["ANNEE"], y=serie["VALEUR"],
            name=libelle, mode="lines+markers",
            line=dict(color=PALETTE_CATEGORIES[rang], width=3),
            marker=dict(size=9),
            hovertemplate="%{y:,.0f} séjours en %{x}<extra>" + libelle + "</extra>",
        ))

    figure_modes = mise_en_page_plotly(
        figure_modes,
        "Séjours de court séjour selon le mode d'hospitalisation",
        "Nombre de séjours",
    )
    figure_modes.update_xaxes(dtick=1, title_text="Année")
    st.plotly_chart(figure_modes, width="stretch")

    # Part de l'ambulatoire sur la dernière année observée, calculée et non supposée
    derniere = evolution["ANNEE"].max()
    valeurs_derniere = evolution[evolution["ANNEE"] == derniere].set_index("INDICATEUR")["VALEUR"]
    part_ambulatoire = (
        valeurs_derniere["Séjours ambulatoires"] / valeurs_derniere.sum() * 100
    )
    premiere = evolution["ANNEE"].min()
    valeurs_premiere = evolution[evolution["ANNEE"] == premiere].set_index("INDICATEUR")["VALEUR"]
    part_ambulatoire_debut = (
        valeurs_premiere["Séjours ambulatoires"] / valeurs_premiere.sum() * 100
    )

    st.caption(
        f"Lecture : l'ambulatoire représente {part_ambulatoire:.0f} % des séjours de court "
        f"séjour en {derniere}, contre {part_ambulatoire_debut:.0f} % en {premiere}. "
        "Les deux modes progressent, mais l'ambulatoire plus vite. "
        "Les années 2013 et 2014 sont des estimations, les rapports correspondants "
        "n'étant pas disponibles."
    )

    st.divider()

    # --- Répartition des lits et causes d'hospitalisation ------------------
    colonne_lits, colonne_causes = st.columns(2)

    with colonne_lits:
        st.subheader("À quoi servent les lits")

        disciplines = ["MCO", "SSR", "SLD", "PSY"]
        # On retient la dernière année où la répartition par discipline est publiée
        annees_detaillees = capacite.loc[
            (capacite["INDICATEUR"] == "Lits par discipline")
            & (capacite["SOUS_INDICATEUR"].isin(disciplines))
            & capacite["TOTAL"].notna(),
            "ANNEE",
        ]
        annee_disciplines = int(annees_detaillees.max())
        repartition = valeurs_par_annee(
            capacite, "Lits par discipline", annee_disciplines, disciplines
        )

        figure_lits = go.Figure(go.Bar(
            x=repartition["SOUS_INDICATEUR"], y=repartition["TOTAL"],
            marker_color=PALETTE_CATEGORIES[: len(repartition)],
            text=[format_nombre(v) for v in repartition["TOTAL"]],
            textposition="outside",
            hovertemplate="%{x} : %{y:,.0f} lits<extra></extra>",
        ))
        figure_lits = mise_en_page_plotly(
            figure_lits,
            f"Lits par discipline en {annee_disciplines}",
            "Nombre de lits",
            hauteur=400,
        )
        figure_lits.update_xaxes(title_text="Discipline")
        figure_lits.update_yaxes(range=[0, repartition["TOTAL"].max() * 1.18])
        st.plotly_chart(figure_lits, width="stretch")

        part_mco = repartition.set_index("SOUS_INDICATEUR")["TOTAL"]["MCO"] / \
            repartition["TOTAL"].sum() * 100
        st.caption(
            f"Lecture : le court séjour (MCO) concentre {part_mco:.0f} % des lits. "
            "Les soins de longue durée et de réadaptation sont portés très "
            "majoritairement par le site de Charles-Foix."
        )

    with colonne_causes:
        st.subheader("Pourquoi les patients sont hospitalisés")

        annee_pathologies = int(pathologies["ANNEE"].max())
        causes = (
            pathologies[pathologies["ANNEE"] == annee_pathologies]
            .sort_values("SEJOURS", ascending=True)
        )

        figure_causes = go.Figure(go.Bar(
            x=causes["SEJOURS"], y=causes["PATHOLOGIE"],
            orientation="h",
            marker_color=PALETTE["principal"],
            text=[format_nombre(v) for v in causes["SEJOURS"]],
            textposition="outside",
            hovertemplate="%{y} : %{x:,.0f} séjours<extra></extra>",
        ))
        figure_causes = mise_en_page_plotly(
            figure_causes,
            f"Principales causes d'hospitalisation en {annee_pathologies}",
            "",
            hauteur=400,
        )
        figure_causes.update_xaxes(title_text="Nombre de séjours",
                                   range=[0, causes["SEJOURS"].max() * 1.20])
        figure_causes.update_layout(margin=dict(l=200), hovermode="closest")
        st.plotly_chart(figure_causes, width="stretch")

        premiere_cause = causes.iloc[-1]
        part_premiere = premiere_cause["SEJOURS"] / causes["SEJOURS"].sum() * 100
        st.caption(
            f"Lecture : les pathologies {premiere_cause['PATHOLOGIE'].lower()} arrivent "
            f"en tête avec {format_nombre(premiere_cause['SEJOURS'])} séjours, soit "
            f"{part_premiere:.0f} % des séjours recensés ici."
        )

# ===========================================================================
# ONGLET 2 : L'activité au fil de l'année
# ===========================================================================

with onglet_annee:
    st.subheader("Le rythme naturel de l'année")

    figure_profil = go.Figure(go.Bar(
        x=profil["LIBELLE"], y=profil["PCT_NORMAL"],
        marker_color=PALETTE["principal"],
        text=[f"{v:.1f} %" for v in profil["PCT_NORMAL"]],
        textposition="outside",
        hovertemplate="%{x} : %{y:.2f} % de l'activité annuelle<extra></extra>",
    ))
    figure_profil.add_hline(
        y=100 / 12, line_dash="dash", line_color=PALETTE["neutre"],
        annotation_text="mois moyen", annotation_position="right",
    )
    figure_profil = mise_en_page_plotly(
        figure_profil,
        "Part de chaque mois dans l'activité de l'année",
        "Part de l'année (%)",
    )
    figure_profil.update_xaxes(title_text="Mois")
    figure_profil.update_yaxes(range=[0, profil["PCT_NORMAL"].max() * 1.25])
    st.plotly_chart(figure_profil, width="stretch")

    mois_haut = profil.loc[profil["PCT_NORMAL"].idxmax()]
    mois_bas = profil.loc[profil["PCT_NORMAL"].idxmin()]
    jour_haut = profil.loc[profil["PASSAGES_MOYENS_PAR_JOUR"].idxmax()]
    jour_bas = profil.loc[profil["PASSAGES_MOYENS_PAR_JOUR"].idxmin()]

    st.caption(
        f"Lecture : l'activité est la plus forte en {mois_haut['LIBELLE_LONG']} "
        f"({mois_haut['PCT_NORMAL']:.1f} % de l'année) et la plus faible en "
        f"{mois_bas['LIBELLE_LONG']} ({mois_bas['PCT_NORMAL']:.1f} %). "
        f"Ramené au nombre de passages par jour, le creux d'{jour_bas['LIBELLE_LONG']} "
        f"({format_nombre(jour_bas['PASSAGES_MOYENS_PAR_JOUR'])} par jour) est nettement plus "
        f"marqué que le pic de {jour_haut['LIBELLE_LONG']} "
        f"({format_nombre(jour_haut['PASSAGES_MOYENS_PAR_JOUR'])}). "
        "Février paraît creux uniquement parce qu'il compte 28 jours."
    )

    st.info(
        "**D'où vient ce rythme ?** Il est mesuré sur les passages aux urgences "
        "réellement enregistrés dans Paris entre 2017 et 2019, d'après les données "
        "publiques de la DREES (ministère de la Santé). Trois années sans épidémie "
        "ont été retenues afin de décrire une année ordinaire.",
        icon=None,
    )

    st.divider()

    # --- Filtres partagés avec l'onglet « crise » --------------------------
    st.subheader("Évolution mois par mois et prévision")

    colonne_serie, colonne_mode, colonne_detail = st.columns([2, 1, 1])

    with colonne_serie:
        libelle_choisi = st.selectbox(
            "Indicateur à afficher",
            options=list(LIBELLES_SERIES.values()),
            index=list(LIBELLES_SERIES).index(SERIE_AVEC_PREVISION),
            help="Les autres indicateurs sont affichés sur leur historique seul.",
        )
    serie_choisie = {v: k for k, v in LIBELLES_SERIES.items()}[libelle_choisi]

    with colonne_mode:
        mode_periode = st.selectbox("Période affichée", options=MODES_PERIODE)

    annee_choisie = None
    trimestre_choisi = None
    annees_disponibles = sorted(serie_mensuelle["DATE"].dt.year.unique())

    with colonne_detail:
        if mode_periode == "Par année":
            annee_choisie = st.selectbox("Année", options=annees_disponibles,
                                         index=len(annees_disponibles) - 1)
        elif mode_periode == "Par trimestre":
            sous_colonnes = st.columns(2)
            with sous_colonnes[0]:
                annee_choisie = st.selectbox("Année", options=annees_disponibles,
                                             index=len(annees_disponibles) - 1)
            with sous_colonnes[1]:
                trimestre_choisi = st.selectbox("Trimestre", options=[1, 2, 3, 4],
                                                format_func=lambda t: f"T{t}")
        else:
            st.caption("L'ensemble de la période 2011-2016 est affiché.")

    historique = serie_mensuelle[serie_mensuelle["INDICATEUR"] == serie_choisie]
    historique_affiche = filtrer_periode(historique, mode_periode,
                                         annee_choisie, trimestre_choisi)

    if historique_affiche.empty:
        st.warning("Aucune donnée disponible pour la période sélectionnée.")
    else:
        figure_serie = go.Figure()
        figure_serie.add_trace(go.Scatter(
            x=historique_affiche["DATE"], y=historique_affiche["VALEUR"],
            name="Activité constatée", mode="lines+markers",
            line=dict(color=PALETTE["principal"], width=2.5),
            marker=dict(size=6),
            hovertemplate="%{x|%B %Y} : %{y:,.0f}<extra></extra>",
        ))

        # La prévision n'existe que pour la série des urgences
        if serie_choisie == SERIE_AVEC_PREVISION and mode_periode == "Ensemble de la période":
            figure_serie.add_trace(go.Scatter(
                x=list(prevision["DATE"]) + list(prevision["DATE"])[::-1],
                y=list(prevision["BORNE_HAUTE"]) + list(prevision["BORNE_BASSE"])[::-1],
                fill="toself", fillcolor=PALETTE["marge"],
                line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip",
                name="Marge d'estimation",
            ))
            figure_serie.add_trace(go.Scatter(
                x=prevision["DATE"], y=prevision["PREVISION"],
                name="Prévision", mode="lines+markers",
                line=dict(color=PALETTE["accent"], width=2.5, dash="dash"),
                marker=dict(size=6, symbol="square"),
                hovertemplate="%{x|%B %Y} : %{y:,.0f} attendus<extra></extra>",
            ))

        figure_serie = mise_en_page_plotly(
            figure_serie, f"{libelle_choisi} : évolution mensuelle", "Nombre mensuel", hauteur=460
        )
        figure_serie.update_xaxes(title_text="Mois")
        st.plotly_chart(figure_serie, width="stretch")

        if serie_choisie == SERIE_AVEC_PREVISION and mode_periode == "Ensemble de la période":
            moyenne_prevue = prevision["PREVISION"].mean()
            marge_moyenne = (
                (prevision["BORNE_HAUTE"] - prevision["BORNE_BASSE"]) / 2
                / prevision["PREVISION"] * 100
            ).mean()
            st.caption(
                f"Lecture : après la dernière année connue, la prévision attend en moyenne "
                f"{format_nombre(moyenne_prevue)} passages par mois. La zone claire indique la "
                f"marge d'estimation, d'environ {marge_moyenne:.0f} % : plus l'échéance est "
                "lointaine, moins la prévision est précise. Les niveaux d'une année à l'autre "
                "ne sont pas comparables, le périmètre de comptage ayant changé : c'est la "
                "forme du rythme annuel qu'il faut lire ici."
            )
        elif serie_choisie == SERIE_AVEC_PREVISION:
            st.caption(
                "Lecture : sélectionnez « Ensemble de la période » pour afficher également "
                "la prévision des douze mois suivants."
            )
        else:
            st.caption(
                f"Lecture : l'activité suit le même rythme annuel que les urgences, appliqué "
                f"au volume propre de cet indicateur. Aucune prévision n'est disponible pour "
                f"{libelle_choisi.lower()}."
            )

# ===========================================================================
# ONGLET 3 : Et si une crise arrive ?
# ===========================================================================

with onglet_crise:
    st.subheader("Simuler une crise sanitaire")

    mode_crise = st.toggle(
        "Mode crise sanitaire",
        value=False,
        help="Applique à la prévision l'impact réellement observé pendant la crise du COVID.",
    )

    st.info(
        "Ce scénario rejoue l'impact réellement mesuré de la crise du COVID sur les "
        "urgences parisiennes en 2020, d'après les données publiques de la DREES. "
        "Pour chaque mois, on a comparé l'activité de 2020 à celle d'une année ordinaire, "
        "puis appliqué le même effet à la prévision. La crise est supposée démarrer au "
        "troisième mois affiché.",
        icon=None,
    )

    # Les choix effectués dans l'onglet précédent s'appliquent également ici
    crise_affichee = filtrer_periode(prevision_crise, mode_periode,
                                     annee_choisie, trimestre_choisi)

    if mode_periode != "Ensemble de la période":
        st.caption(
            f"Filtre actif : {mode_periode.lower()}"
            + (f", {annee_choisie}" if annee_choisie else "")
            + (f", T{trimestre_choisi}" if trimestre_choisi else "")
            + ". Il se règle dans l'onglet « L'activité au fil de l'année »."
        )

    if crise_affichee.empty:
        st.warning(
            "La période sélectionnée dans l'onglet précédent ne couvre pas les mois "
            "concernés par la prévision. Choisissez « Ensemble de la période » pour "
            "afficher le scénario."
        )
    else:
        mois_en_crise = crise_affichee[crise_affichee["DEBUT_CRISE"]]

        if mode_crise and not mois_en_crise.empty:
            # --- Chiffres d'impact, calculés depuis le fichier de scénario ---
            rapport = mois_en_crise["PREVISION_CRISE"] / mois_en_crise["PREVISION_NORMAL"]
            baisse_maximale = (1 - rapport.min()) * 100
            ligne_creux = mois_en_crise.loc[rapport.idxmin()]
            perte_cumulee = (
                mois_en_crise["PREVISION_NORMAL"] - mois_en_crise["PREVISION_CRISE"]
            ).sum()
            part_perdue = perte_cumulee / mois_en_crise["PREVISION_NORMAL"].sum() * 100

            colonnes_impact = st.columns(3)
            with colonnes_impact[0]:
                st.metric(
                    "Baisse maximale",
                    f"−{baisse_maximale:.0f} %",
                    help="Écart le plus fort entre l'activité attendue et l'activité sous crise.",
                )
            with colonnes_impact[1]:
                st.metric(
                    "Mois le plus touché",
                    MOIS_LONGS[ligne_creux["DATE"].month - 1].capitalize(),
                    help=(
                        f"{format_nombre(ligne_creux['PREVISION_NORMAL'])} passages attendus, "
                        f"{format_nombre(ligne_creux['PREVISION_CRISE'])} sous crise."
                    ),
                )
            with colonnes_impact[2]:
                st.metric(
                    "Activité en moins",
                    f"{format_nombre(perte_cumulee)} passages",
                    delta=f"−{part_perdue:.0f} % sur la période de crise",
                    delta_color="inverse",
                    help="Total cumulé sur les mois concernés par la crise.",
                )

        # --- Graphique ----------------------------------------------------
        figure_crise = go.Figure()

        if mode_crise and not mois_en_crise.empty:
            figure_crise.add_vrect(
                x0=mois_en_crise["DATE"].min(), x1=crise_affichee["DATE"].max(),
                fillcolor=PALETTE["zone_crise"], line_width=0, layer="below",
                annotation_text="période de crise", annotation_position="top left",
            )

        figure_crise.add_trace(go.Scatter(
            x=crise_affichee["DATE"], y=crise_affichee["PREVISION_NORMAL"],
            name="Activité attendue", mode="lines+markers",
            line=dict(color=PALETTE["principal"], width=3),
            marker=dict(size=8),
            hovertemplate="%{x|%B %Y} : %{y:,.0f}<extra></extra>",
        ))

        if mode_crise:
            figure_crise.add_trace(go.Scatter(
                x=crise_affichee["DATE"], y=crise_affichee["PREVISION_CRISE"],
                name="Activité en cas de crise", mode="lines+markers",
                line=dict(color=PALETTE["crise"], width=3, dash="dash"),
                marker=dict(size=8, symbol="square"),
                hovertemplate="%{x|%B %Y} : %{y:,.0f}<extra></extra>",
            ))

        titre_crise = (
            "Activité attendue et activité en cas de crise sanitaire"
            if mode_crise else "Activité attendue dans les douze prochains mois"
        )
        figure_crise = mise_en_page_plotly(
            figure_crise, titre_crise, "Passages mensuels", hauteur=470
        )
        figure_crise.update_xaxes(title_text="Mois")
        figure_crise.update_yaxes(rangemode="tozero")
        st.plotly_chart(figure_crise, width="stretch")

        if mode_crise and not mois_en_crise.empty:
            st.caption(
                f"Lecture : la courbe rouge montre l'activité qui serait constatée si une "
                f"crise comparable à celle de 2020 survenait. Le creux se situe en "
                f"{MOIS_LONGS[ligne_creux['DATE'].month - 1]}, avec "
                f"{baisse_maximale:.0f} % de passages en moins qu'attendu. "
                "Attention : une baisse des passages ne signifie pas une baisse des besoins. "
                "Une partie de ces soins est seulement différée, et revient plus tard."
            )
        elif mode_crise:
            st.caption(
                "Lecture : la période sélectionnée ne comprend aucun mois de crise."
            )
        else:
            st.caption(
                "Lecture : activité attendue en fonctionnement normal. Activez le mode "
                "crise sanitaire ci-dessus pour comparer avec un scénario de crise."
            )

# ===========================================================================
# Bandeau de sources
# ===========================================================================

st.divider()
st.caption(
    "Sources : rapports annuels PSL-CFX 2011-2016 (AP-HP) · "
    "Passages aux urgences DREES 2017-2023 · "
    "Réalisation étudiante, données publiques"
)
