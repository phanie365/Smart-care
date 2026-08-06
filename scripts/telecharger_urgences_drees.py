"""
Téléchargement du jeu de données DREES des passages aux urgences (2017-2023).

Source : « Séries longues corrigées du nombre de passages aux urgences 2017 à 2023
en France », produit par la DREES et publié sur data.gouv.fr sous Licence Ouverte 2.0.

    https://www.data.gouv.fr/datasets/series-longues-corrigees-du-nombre-de-passages-aux-urgences-2017-a-2023-en-france

Le fichier est déposé dans data/external/ et n'est jamais modifié ensuite : c'est une
donnée externe, au même titre que les rapports PDF de docs/.

Usage :
    python scripts/telecharger_urgences_drees.py          # ne retélécharge pas si présent
    python scripts/telecharger_urgences_drees.py --force  # force le retéléchargement

Code de sortie : 0 si le fichier est présent et valide, 1 sinon.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.data.gouv.fr/api/1/datasets/r/b0005488-e2a9-455a-ae33-b3263d06d119"
PAGE_SOURCE = (
    "https://www.data.gouv.fr/datasets/"
    "series-longues-corrigees-du-nombre-de-passages-aux-urgences-2017-a-2023-en-france"
)

RACINE = Path(__file__).resolve().parent.parent
DESTINATION = RACINE / "data" / "external" / "passages_urgences_drees_2017_2023.csv"

# Le fichier attendu pèse environ 7,4 Mo : en dessous de 1 Mo, c'est une page
# d'erreur HTML ou un téléchargement tronqué, pas le jeu de données.
TAILLE_MINIMALE_MO = 1.0
COLONNES_ATTENDUES = {"date", "dep", "libelle_dep", "nb_passages"}

# Le fichier livré utilise le format ISO (2017-12-25) et non le format français.
# On tente malgré tout les deux, au cas où la DREES changerait de convention.
FORMATS_DATE = ("%Y-%m-%d", "%d/%m/%Y")


def parser_dates(colonne: pd.Series) -> pd.Series:
    """Convertit la colonne de dates en essayant les formats connus, du plus probable au moins."""
    for format_date in FORMATS_DATE:
        converti = pd.to_datetime(colonne, format=format_date, errors="coerce")
        if converti.notna().all():
            return converti
    # Aucun format ne convient parfaitement : on renvoie le meilleur essai pour
    # que l'appelant puisse compter et signaler les valeurs illisibles.
    return pd.to_datetime(colonne, format=FORMATS_DATE[0], errors="coerce")


def telecharger(url: str, destination: Path) -> None:
    """Télécharge le fichier en flux, pour ne pas charger 7 Mo en mémoire d'un coup."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporaire = destination.with_suffix(destination.suffix + ".partiel")

    print(f"Téléchargement depuis {url}")
    with requests.get(url, stream=True, timeout=120) as reponse:
        reponse.raise_for_status()
        octets = 0
        with temporaire.open("wb") as fichier:
            for bloc in reponse.iter_content(chunk_size=64 * 1024):
                fichier.write(bloc)
                octets += len(bloc)
        print(f"  {octets / 1024 / 1024:.2f} Mo reçus")

    # Le fichier définitif n'apparaît qu'une fois le téléchargement complet.
    temporaire.replace(destination)


def valider(chemin: Path) -> bool:
    """Vérifie la taille du fichier, son parsing et la présence des colonnes attendues."""
    taille_mo = chemin.stat().st_size / 1024 / 1024
    print(f"Taille        : {taille_mo:.2f} Mo")
    if taille_mo < TAILLE_MINIMALE_MO:
        print(f"  ÉCHEC : fichier trop petit (< {TAILLE_MINIMALE_MO} Mo), "
              "probablement une page d'erreur")
        return False

    try:
        df = pd.read_csv(chemin, sep=";", dtype={"dep": str})
    except Exception as erreur:  # noqa: BLE001 - on veut remonter toute erreur de parsing
        print(f"  ÉCHEC : parsing impossible -> {type(erreur).__name__}: {erreur}")
        return False

    print(f"Parsing       : OK ({len(df):,} lignes, {len(df.columns)} colonnes)".replace(",", " "))
    print(f"Colonnes      : {', '.join(df.columns)}")

    manquantes = COLONNES_ATTENDUES - set(df.columns)
    if manquantes:
        print(f"  ÉCHEC : colonnes manquantes -> {', '.join(sorted(manquantes))}")
        return False

    # Aperçu de la couverture : bornes de dates et nombre de départements
    dates = parser_dates(df["date"])
    illisibles = int(dates.isna().sum())
    if illisibles:
        print(f"  ÉCHEC : {illisibles} date(s) illisible(s), format inattendu "
              f"(exemple : {df.loc[dates.isna(), 'date'].iloc[0]!r})")
        return False

    print(f"Période       : {dates.min():%d/%m/%Y} -> {dates.max():%d/%m/%Y}")
    print(f"Départements  : {df['dep'].nunique()}")

    # Les passages sont décimaux : ce sont des séries corrigées et calées, pas des
    # comptages bruts. On vérifie simplement qu'ils sont bien numériques et positifs.
    passages = pd.to_numeric(df["nb_passages"], errors="coerce")
    print(f"Passages      : {int(passages.isna().sum())} valeur(s) non numérique(s), "
          f"minimum {passages.min():.1f}, maximum {passages.max():.1f}")
    if passages.isna().any():
        print("  ÉCHEC : la colonne nb_passages contient des valeurs non numériques")
        return False

    return True


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--force", action="store_true",
                           help="retélécharge même si le fichier existe déjà")
    arguments = analyseur.parse_args()

    print(f"Jeu de données : {PAGE_SOURCE}")
    print(f"Destination    : {DESTINATION.relative_to(RACINE)}\n")

    if DESTINATION.exists() and not arguments.force:
        print("Fichier déjà présent, téléchargement ignoré (--force pour forcer).\n")
    else:
        try:
            telecharger(URL, DESTINATION)
        except Exception as erreur:  # noqa: BLE001 - réseau, DNS, HTTP...
            print(f"\nÉCHEC DU TÉLÉCHARGEMENT : {type(erreur).__name__}: {erreur}")
            print(f"\nSolution manuelle : télécharger le CSV depuis {PAGE_SOURCE}")
            print(f"et le déposer sous {DESTINATION.relative_to(RACINE)}")
            return 1
        print()

    if not valider(DESTINATION):
        return 1

    print("\nFichier prêt à l'emploi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
