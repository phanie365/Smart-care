"""
Vérification de la qualité des données extraites des rapports annuels PSL-CFX.

Ce script ne modifie AUCUNE donnée : il ne fait que lire les CSV de data/raw/ et
produire un rapport de contrôle. Il sert à démontrer, en soutenance, que le jeu de
données saisi manuellement à partir des plaquettes PDF est cohérent et traçable.

Contrôles effectués sur chaque fichier :
  1. Lecture sans erreur par pandas
  2. Conformité du schéma aux colonnes attendues
  3. Années couvertes et inventaire des indicateurs
  4. Typage : les colonnes de valeurs contiennent bien des nombres
  5. Cellules vides (donnée non publiée) vs zéros explicites
  6. Cohérence arithmétique : PSL + CFX == TOTAL quand les trois sont renseignés

Usage :
    python scripts/verifier_donnees.py

Code de sortie : 0 si aucune anomalie bloquante, 1 sinon.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DONNEES = RACINE / "data" / "raw"

# Schéma commun aux fichiers de type « indicateur ».
SCHEMA_STANDARD = [
    "ANNEE",
    "INDICATEUR",
    "SOUS_INDICATEUR",
    "PSL",
    "CFX",
    "TOTAL",
    "UNITE",
    "NOTE",
    "SOURCE",
]

# pathologies.csv suit une structure propre (une ligne = une pathologie).
SCHEMA_PATHOLOGIES = ["ANNEE", "PATHOLOGIE", "SEJOURS", "NOTE", "SOURCE"]

FICHIERS = {
    "activite.csv": SCHEMA_STANDARD,
    "capacite.csv": SCHEMA_STANDARD,
    "pathologies.csv": SCHEMA_PATHOLOGIES,
    "rh.csv": SCHEMA_STANDARD,
    "finance.csv": SCHEMA_STANDARD,
    "patients.csv": SCHEMA_STANDARD,
}

COLONNES_VALEURS = ["PSL", "CFX", "TOTAL", "SEJOURS"]

# En deçà de ce seuil, un écart PSL + CFX vs TOTAL est un simple arrondi de
# publication (les montants en M€ sont arrondis au centième dans les rapports).
SEUIL_ARRONDI = 0.05


def titre(texte: str, niveau: int = 1) -> None:
    marque = "=" if niveau == 1 else "-"
    print(f"\n{marque * 72}\n{texte}\n{marque * 72}")


def controler_schema(df: pd.DataFrame, attendu: list[str]) -> list[str]:
    """Compare les colonnes présentes au schéma attendu."""
    anomalies = []
    presentes = list(df.columns)

    manquantes = [c for c in attendu if c not in presentes]
    en_trop = [c for c in presentes if c not in attendu]

    if manquantes:
        anomalies.append(f"colonnes manquantes : {', '.join(manquantes)}")
    if en_trop:
        anomalies.append(f"colonnes inattendues : {', '.join(en_trop)}")
    if not anomalies:
        print(f"  Schéma        : conforme ({len(presentes)} colonnes)")
    else:
        print(f"  Schéma        : ÉCART -> {' ; '.join(anomalies)}")
    return anomalies


def controler_typage(df: pd.DataFrame) -> list[str]:
    """Vérifie que les colonnes de valeurs ne contiennent que du numérique."""
    anomalies = []
    for colonne in COLONNES_VALEURS:
        if colonne not in df.columns:
            continue
        converti = pd.to_numeric(df[colonne], errors="coerce")
        # Une valeur non convertible est une chaîne parasite, pas une cellule vide.
        parasites = df[converti.isna() & df[colonne].notna()]
        if not parasites.empty:
            exemples = parasites[colonne].astype(str).head(3).tolist()
            anomalies.append(f"{colonne} : {len(parasites)} valeur(s) non numérique(s) {exemples}")
    if anomalies:
        for a in anomalies:
            print(f"  Typage        : ANOMALIE -> {a}")
    else:
        print("  Typage        : toutes les colonnes de valeurs sont numériques")
    return anomalies


def decrire_remplissage(df: pd.DataFrame) -> None:
    """Distingue les cellules vides (non publié) des zéros explicites."""
    details = []
    for colonne in COLONNES_VALEURS:
        if colonne not in df.columns:
            continue
        serie = pd.to_numeric(df[colonne], errors="coerce")
        vides = int(serie.isna().sum())
        zeros = int((serie == 0).sum())
        details.append(f"{colonne} : {vides} vide(s), {zeros} zéro(s)")
    print(f"  Remplissage   : {' | '.join(details)}")


def controler_totaux(df: pd.DataFrame, nom: str) -> list[str]:
    """Vérifie PSL + CFX == TOTAL sur les lignes où les trois sont renseignés."""
    if not {"PSL", "CFX", "TOTAL"}.issubset(df.columns):
        print("  Somme PSL+CFX : non applicable (colonnes absentes)")
        return []

    psl = pd.to_numeric(df["PSL"], errors="coerce")
    cfx = pd.to_numeric(df["CFX"], errors="coerce")
    total = pd.to_numeric(df["TOTAL"], errors="coerce")

    testables = psl.notna() & cfx.notna() & total.notna()
    ecart = (psl + cfx - total).abs()

    arrondis = df[testables & (ecart > 0) & (ecart <= SEUIL_ARRONDI)]
    incoherentes = df[testables & (ecart > SEUIL_ARRONDI)]

    print(f"  Somme PSL+CFX : {int(testables.sum())} ligne(s) testable(s)", end="")
    if incoherentes.empty and arrondis.empty:
        print(" -> toutes cohérentes")
        return []

    resume = []
    if incoherentes.empty:
        resume.append("aucun écart significatif")
    else:
        resume.append(f"{len(incoherentes)} ÉCART(S)")
    if not arrondis.empty:
        resume.append(f"{len(arrondis)} arrondi(s) de publication (ignoré(s))")
    print(f" -> {', '.join(resume)}")

    def decrire(idx, ligne) -> str:
        somme = psl[idx] + cfx[idx]
        libelle = f"{ligne['INDICATEUR']} / {ligne['SOUS_INDICATEUR']}"
        return (
            f"{nom} [{ligne['ANNEE']}] {libelle} : "
            f"PSL {psl[idx]:,.2f} + CFX {cfx[idx]:,.2f} = {somme:,.2f} "
            f"mais TOTAL = {total[idx]:,.2f} (écart {somme - total[idx]:+,.2f})"
        )

    anomalies = []
    for idx, ligne in incoherentes.iterrows():
        message = decrire(idx, ligne)
        print(f"      - {message}")
        anomalies.append(message)
    for idx, ligne in arrondis.iterrows():
        print(f"      . (arrondi) {decrire(idx, ligne)}")
    return anomalies


def inventorier(df: pd.DataFrame, nom: str) -> None:
    """Affiche lignes, années et indicateurs du fichier."""
    annees = sorted(pd.to_numeric(df["ANNEE"], errors="coerce").dropna().astype(int).unique())
    print(f"  Lignes        : {len(df)}")
    print(f"  Années        : {', '.join(str(a) for a in annees)} ({len(annees)} années)")

    colonne_cle = "PATHOLOGIE" if nom == "pathologies.csv" else "INDICATEUR"
    indicateurs = sorted(df[colonne_cle].dropna().unique())
    print(f"  Indicateurs   : {len(indicateurs)}")
    for ind in indicateurs:
        annees_ind = sorted(
            pd.to_numeric(df.loc[df[colonne_cle] == ind, "ANNEE"], errors="coerce")
            .dropna()
            .astype(int)
            .unique()
        )
        print(f"      - {ind} ({', '.join(str(a) for a in annees_ind)})")


def main() -> int:
    titre("VÉRIFICATION DES DONNÉES SOURCES - PSL-CFX")
    print(f"Dossier analysé : {DOSSIER_DONNEES}")
    print(f"Version de pandas : {pd.__version__}")

    anomalies_globales: list[str] = []
    lignes_totales = 0
    annees_globales: set[int] = set()

    for nom, schema in FICHIERS.items():
        chemin = DOSSIER_DONNEES / nom
        titre(nom, niveau=2)

        if not chemin.exists():
            print("  Lecture       : ÉCHEC -> fichier introuvable")
            anomalies_globales.append(f"{nom} : fichier introuvable")
            continue

        try:
            df = pd.read_csv(chemin, encoding="utf-8")
        except Exception as erreur:  # noqa: BLE001 - on veut remonter toute erreur de lecture
            print(f"  Lecture       : ÉCHEC -> {type(erreur).__name__}: {erreur}")
            anomalies_globales.append(f"{nom} : illisible ({erreur})")
            continue

        print("  Lecture       : OK")
        anomalies_globales += [f"{nom} : {a}" for a in controler_schema(df, schema)]
        inventorier(df, nom)
        anomalies_globales += [f"{nom} : {a}" for a in controler_typage(df)]
        decrire_remplissage(df)
        anomalies_globales += controler_totaux(df, nom)

        lignes_totales += len(df)
        annees_globales |= set(
            pd.to_numeric(df["ANNEE"], errors="coerce").dropna().astype(int).unique()
        )

    titre("SYNTHÈSE")
    print(f"Fichiers contrôlés : {len(FICHIERS)}")
    print(f"Lignes de données  : {lignes_totales}")
    print(f"Années couvertes   : {', '.join(str(a) for a in sorted(annees_globales))}")

    if not anomalies_globales:
        print("\nAucune anomalie détectée.")
        return 0

    print(f"\n{len(anomalies_globales)} point(s) d'attention :")
    for anomalie in anomalies_globales:
        print(f"  - {anomalie}")
    print(
        "\nCes points sont documentés et assumés (voir la section « Pièges de "
        "comparabilité » du README). Aucune valeur n'a été corrigée : les CSV "
        "reproduisent fidèlement les rapports publiés."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
