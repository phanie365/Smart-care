"""
Chargement et mise en forme des données pour l'infographie PSL-CFX.

Ce module ne fait aucun calcul de modèle : il se contente de lire les fichiers
préparés dans data/raw/ et data/processed/, et de les mettre en forme pour
l'affichage. Tous les chargements passent par @st.cache_data pour éviter de relire
les fichiers à chaque interaction de l'utilisateur.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_BRUT = RACINE / "data" / "raw"
DOSSIER_TRAITE = RACINE / "data" / "processed"

# --- Libellés français -------------------------------------------------------

MOIS_COURTS = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin",
               "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]
MOIS_LONGS = ["janvier", "février", "mars", "avril", "mai", "juin",
              "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

# --- Palette unique, sobre ---------------------------------------------------

PALETTE = {
    "principal": "#1F6FB2",       # bleu institutionnel, courbes et barres
    "secondaire": "#7FB2D9",      # bleu clair, séries secondaires
    "accent": "#0E4C7A",          # bleu foncé, mises en évidence
    "crise": "#C1443C",           # rouge sobre, réservé au scénario de crise
    "neutre": "#6B7280",          # gris, repères et moyennes
    "grille": "#E5E7EB",
    "marge": "rgba(31, 111, 178, 0.18)",    # bande de marge d'estimation
    "zone_crise": "rgba(193, 68, 60, 0.10)",
}

# Palette ordonnée pour les graphiques à plusieurs catégories
PALETTE_CATEGORIES = ["#1F6FB2", "#7FB2D9", "#0E4C7A", "#A8C8E3", "#4A8FC4"]

# --- Glossaire des sigles hospitaliers ---------------------------------------

SIGLES = {
    "MCO": "Médecine, chirurgie, obstétrique : les séjours de court séjour.",
    "SSR": "Soins de suite et de réadaptation : la rééducation après un séjour aigu.",
    "SLD": "Soins de longue durée : l'hébergement médicalisé au long cours.",
    "PSY": "Psychiatrie.",
    "SAU": "Service d'accueil des urgences.",
    "PSL": "Site de la Pitié-Salpêtrière, à Paris (13e arrondissement).",
    "CFX": "Site de Charles-Foix, à Ivry-sur-Seine (Val-de-Marne).",
    "ETP": "Équivalent temps plein : un agent à mi-temps compte pour 0,5.",
    "Ambulatoire": "Séjour de moins de 24 heures, sans nuit passée à l'hôpital.",
}


# --- Mise en forme des nombres ----------------------------------------------

def format_nombre(valeur: float, decimales: int = 0) -> str:
    """Formate un nombre à la française : espace fine comme séparateur de milliers."""
    if pd.isna(valeur):
        return "—"
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def format_signe(valeur: float, decimales: int = 0, suffixe: str = "") -> str:
    """Formate une variation avec son signe, pour les indicateurs d'évolution."""
    if pd.isna(valeur):
        return "—"
    signe = "+" if valeur >= 0 else "−"
    return f"{signe}{format_nombre(abs(valeur), decimales)}{suffixe}"


# --- Chargements -------------------------------------------------------------

@st.cache_data(show_spinner=False)
def charger_donnees_brutes(nom_fichier: str) -> pd.DataFrame:
    """Charge un fichier de data/raw/ (données extraites des rapports annuels)."""
    return pd.read_csv(DOSSIER_BRUT / nom_fichier, encoding="utf-8")


@st.cache_data(show_spinner=False)
def charger_serie_annuelle() -> pd.DataFrame:
    """Série annuelle complétée, années 2011 à 2016 selon les indicateurs."""
    return pd.read_csv(DOSSIER_TRAITE / "serie_annuelle_complete.csv", encoding="utf-8")


@st.cache_data(show_spinner=False)
def charger_serie_mensuelle() -> pd.DataFrame:
    """Série mensuelle reconstituée, avec la colonne DATE au format date."""
    donnees = pd.read_csv(DOSSIER_TRAITE / "serie_mensuelle.csv",
                          parse_dates=["DATE"], encoding="utf-8")
    return donnees.sort_values("DATE").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def charger_profil_saisonnier() -> pd.DataFrame:
    """Profil mensuel mesuré sur les passages aux urgences parisiens 2017-2019."""
    profil = pd.read_csv(DOSSIER_TRAITE / "profil_saisonnier.csv", encoding="utf-8")
    profil["LIBELLE"] = profil["MOIS"].map(lambda m: MOIS_COURTS[m - 1])
    profil["LIBELLE_LONG"] = profil["MOIS"].map(lambda m: MOIS_LONGS[m - 1])
    return profil


@st.cache_data(show_spinner=False)
def charger_prevision() -> pd.DataFrame:
    """Prévision à 12 mois, avec sa marge d'estimation haute et basse."""
    return pd.read_csv(DOSSIER_TRAITE / "prevision_12mois.csv",
                       parse_dates=["DATE"], encoding="utf-8")


@st.cache_data(show_spinner=False)
def charger_prevision_crise() -> pd.DataFrame:
    """Trajectoire prévue en temps normal et sous scénario de crise sanitaire."""
    return pd.read_csv(DOSSIER_TRAITE / "prevision_crise.csv",
                       parse_dates=["DATE"], encoding="utf-8")


@st.cache_data(show_spinner=False)
def charger_impact_mesure() -> pd.DataFrame:
    """Impact mensuel mesuré de la crise du COVID sur les urgences parisiennes."""
    donnees = pd.read_csv(DOSSIER_TRAITE / "coefficients_crise.csv",
                          comment="#", encoding="utf-8")
    donnees["LIBELLE"] = donnees["MOIS"].map(lambda m: MOIS_COURTS[m - 1])
    return donnees


@st.cache_data(show_spinner=False)
def charger_fiche_modele() -> dict:
    """Fiche technique de la prévision (période couverte, horizon...)."""
    chemin = DOSSIER_TRAITE / "modele_info.json"
    return json.loads(chemin.read_text(encoding="utf-8"))


# --- Extraction de valeurs ---------------------------------------------------

def derniere_valeur(
    donnees: pd.DataFrame,
    indicateur: str,
    sous_indicateur: str | None = None,
    colonne: str = "TOTAL",
) -> tuple[int | None, float | None, float | None]:
    """Renvoie (année la plus récente, valeur, valeur de l'année précédente disponible).

    La valeur précédente sert à afficher une évolution ; elle vaut None si l'indicateur
    n'est publié que pour une seule année.
    """
    filtre = donnees["INDICATEUR"] == indicateur
    if sous_indicateur is not None:
        filtre &= donnees["SOUS_INDICATEUR"] == sous_indicateur

    extrait = donnees.loc[filtre & donnees[colonne].notna(), ["ANNEE", colonne]]
    if extrait.empty:
        return None, None, None

    extrait = extrait.sort_values("ANNEE")
    annee = int(extrait["ANNEE"].iloc[-1])
    valeur = float(extrait[colonne].iloc[-1])
    precedente = float(extrait[colonne].iloc[-2]) if len(extrait) > 1 else None
    return annee, valeur, precedente


def valeurs_par_annee(
    donnees: pd.DataFrame,
    indicateur: str,
    annee: int,
    sous_indicateurs: list[str],
    colonne: str = "TOTAL",
) -> pd.DataFrame:
    """Extrait plusieurs sous-indicateurs d'une même année, dans l'ordre demandé."""
    extrait = donnees[
        (donnees["INDICATEUR"] == indicateur)
        & (donnees["ANNEE"] == annee)
        & (donnees["SOUS_INDICATEUR"].isin(sous_indicateurs))
    ].copy()
    ordre = {nom: rang for rang, nom in enumerate(sous_indicateurs)}
    extrait["_ordre"] = extrait["SOUS_INDICATEUR"].map(ordre)
    return extrait.sort_values("_ordre").drop(columns="_ordre")


# --- Filtres de période partagés entre les onglets ---------------------------

MODES_PERIODE = ["Ensemble de la période", "Par année", "Par trimestre"]


def filtrer_periode(
    donnees: pd.DataFrame,
    mode: str,
    annee: int | None = None,
    trimestre: int | None = None,
    colonne_date: str = "DATE",
) -> pd.DataFrame:
    """Restreint un tableau daté selon le mode de période choisi par l'utilisateur."""
    if mode == "Ensemble de la période" or annee is None:
        return donnees

    filtre = donnees[colonne_date].dt.year == annee
    if mode == "Par trimestre" and trimestre is not None:
        filtre &= donnees[colonne_date].dt.quarter == trimestre
    return donnees[filtre]


def mise_en_page_plotly(figure, titre: str, titre_y: str, hauteur: int = 420):
    """Applique une mise en forme commune à toutes les figures, pour un rendu homogène."""
    figure.update_layout(
        title=dict(text=titre, font=dict(size=17, color="#111827")),
        yaxis_title=titre_y,
        height=hauteur,
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Source Sans Pro, sans-serif", size=13, color="#374151"),
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    figure.update_xaxes(showgrid=False, linecolor=PALETTE["grille"])
    figure.update_yaxes(gridcolor=PALETTE["grille"], zeroline=False)
    return figure
