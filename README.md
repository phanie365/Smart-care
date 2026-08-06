# Projet data — Groupe hospitalier Pitié-Salpêtrière / Charles-Foix (PSL-CFX)

Analyse de l'activité hospitalière du groupe PSL-CFX à partir des rapports annuels,
prévision de l'activité par modélisation SARIMA, simulation d'un scénario de crise
sanitaire, et restitution sous forme d'infographie interactive Streamlit.

## Objectifs

1. **Extraire** les indicateurs d'activité contenus dans les rapports annuels (PDF) et
   les convertir en jeux de données exploitables.
2. **Consolider** ces données avec des sources publiques (réseau OSCOUR — passages aux
   urgences) pour construire des séries temporelles cohérentes.
3. **Prévoir** l'activité future à l'aide d'un modèle SARIMA (saisonnalité annuelle /
   mensuelle selon la granularité disponible).
4. **Simuler** un scénario de crise sanitaire (choc d'activité) et en mesurer l'impact
   sur les capacités du groupe hospitalier.
5. **Restituer** l'ensemble sous forme d'une infographie interactive (Streamlit + Plotly).

## Structure du dépôt

```
projet-data-pslcfx/
├── docs/               # Rapports annuels sources (3 PDFs) et documentation de référence
├── data/
│   ├── raw/            # CSV bruts extraits des PDFs (aucune transformation)
│   ├── external/       # Données publiques téléchargées (OSCOUR, open data santé)
│   └── processed/      # Séries temporelles construites, prévisions, scénarios
├── notebooks/          # Notebooks d'exploration, de modélisation et de validation
├── scripts/            # Scripts utilitaires reproductibles (contrôle qualité, etc.)
├── app/                # Application Streamlit (infographie interactive)
├── rapports/           # Brouillons markdown des livrables
├── requirements.txt    # Dépendances Python
└── README.md
```

## Pipeline de traitement

| Étape | Entrée | Traitement | Sortie |
|-------|--------|-----------|--------|
| 1. Extraction | `docs/*.pdf` | Saisie **manuelle** des indicateurs (les plaquettes sont des documents graphiques, illisibles par extraction automatique) puis contrôle qualité automatisé | `data/raw/*.csv` |
| 2. Données externes | Portail OSCOUR / open data | Téléchargement et filtrage sur le périmètre géographique pertinent | `data/external/*.csv` |
| 3. Consolidation | `data/raw/`, `data/external/` | Nettoyage, harmonisation des libellés et des périodes, contrôle de cohérence | `data/processed/serie_activite.csv` |
| 4. Analyse exploratoire | `data/processed/` | Statistiques descriptives, décomposition tendance / saisonnalité, tests de stationnarité (ADF) | `notebooks/`, figures |
| 5. Modélisation SARIMA | Série consolidée | Sélection d'ordre (`pmdarima.auto_arima`), estimation, diagnostic des résidus, validation hors échantillon | `data/processed/previsions.csv` |
| 6. Scénario de crise | Prévisions de référence | Application d'un choc d'activité paramétré (amplitude, durée, montée en charge) et comparaison au scénario tendanciel | `data/processed/scenario_crise.csv` |
| 7. Restitution | Séries + prévisions + scénarios | Infographie interactive et synthèse rédigée | `app/`, `rapports/` |

## Données sources

Les chiffres ont été **saisis manuellement** à partir des trois rapports annuels de
`docs/`. Ces plaquettes sont des documents de communication à la mise en page très
graphique : l'extraction automatique de tableaux y produit du texte entrelacé et
inexploitable. La saisie manuelle, colonne `SOURCE` à l'appui, garantit la traçabilité
de chaque valeur jusqu'à sa page d'origine.

Six fichiers dans `data/raw/`, tous encodés en UTF-8, séparateur virgule :

| Fichier | Lignes | Années | Contenu |
|---------|--------|--------|---------|
| `activite.csv` | 65 | 2011, 2012, 2015, 2016 | Séjours MCO, consultations externes, passages aux urgences, journées PSY/SSR/SLD, transplantations, actes et séances des plateaux techniques |
| `capacite.csv` | 33 | 2012, 2015, 2016 | Lits installés et par discipline, places de jour, pôles, services, blocs opératoires, lits de réanimation et de soins intensifs |
| `pathologies.csv` | 18 | 2012, 2015 | Séjours par grande cause d'hospitalisation (9 catégories) |
| `rh.csv` | 29 | 2012, 2015, 2016 | Effectifs médicaux et non médicaux par catégorie, répartition hommes/femmes, formation |
| `finance.csv` | 21 | 2012, 2015, 2016 | Dépenses d'exploitation, recettes, solde, crédits d'investissement |
| `patients.csv` | 14 | 2012, 2015 | Âge moyen, répartition par sexe, origine géographique des patients |

**Structure commune** aux fichiers d'indicateurs :
`ANNEE, INDICATEUR, SOUS_INDICATEUR, PSL, CFX, TOTAL, UNITE, NOTE, SOURCE`

- `PSL` = Pitié-Salpêtrière, `CFX` = Charles-Foix, `TOTAL` = groupe hospitalier.
- **Une cellule vide signifie « donnée non publiée dans le rapport »** — jamais zéro.
  La distinction est essentielle : les rapports 2016 ne publient presque aucun détail
  par site, ce qui produit de nombreuses cellules `PSL`/`CFX` vides qu'il ne faut
  surtout pas interpréter comme une activité nulle.
- `SOURCE` indique le rapport et la rubrique d'origine de la valeur.
- Deux exceptions de schéma : `pathologies.csv` utilise `ANNEE, PATHOLOGIE, SEJOURS,
  NOTE, SOURCE` (une ligne = une pathologie), et `capacite.csv` ne comporte pas de
  colonne `NOTE` (les précisions y sont intégrées à `SOURCE`).

### Contrôle qualité

Le script `scripts/verifier_donnees.py` rejoue à tout moment les vérifications :
lecture pandas, conformité du schéma, typage numérique des colonnes de valeurs,
comptage des cellules vides et des zéros, et cohérence arithmétique `PSL + CFX = TOTAL`.

```bash
python scripts/verifier_donnees.py
```

Résultat sur le jeu de données actuel : **180 lignes contrôlées, 6 fichiers lus sans
erreur, aucune valeur non numérique**. Trois points d'attention subsistent, volontairement
non corrigés puisque les CSV doivent reproduire fidèlement les rapports publiés :

1. `activite.csv` 2011, séjours ambulatoires : `83 911 + 1 080 = 84 991` alors que le
   total publié est `84 911` (écart de 80 séjours présent dans le rapport source).
2. `capacite.csv` 2012, lits SSR : `85 + 149 = 234` contre un total publié de `209`.
   Le détail par site provient d'une lecture de graphique, d'où son imprécision.
3. `capacite.csv` ne possède pas de colonne `NOTE`, contrairement aux autres fichiers.

## Pièges de comparabilité

Les trois rapports ne définissent pas leurs indicateurs de la même façon. Les points
suivants doivent être respectés dans toute analyse, sous peine de produire des
évolutions purement artificielles.

### 1. Passages aux urgences : périmètres incompatibles

| Année | Valeur publiée | Périmètre réel |
|-------|----------------|----------------|
| 2012 | 85 993 passages | Pitié-Salpêtrière seule, **hors** urgences dentaires |
| 2015 | 121 721 passages | SAU 59 072 **+** urgences dentaires 62 649 |
| 2016 | 127 678 passages | Périmètre encore différent (dont 61 651 urgences spécialisées) |

La progression apparente de +48 % entre 2012 et 2015 est un **artefact de périmètre**,
pas une croissance d'activité. Toute série temporelle sur les urgences devra donc
s'appuyer sur le **SAU seul**, à l'exclusion des urgences dentaires et spécialisées.

### 2. Soins dentaires : définitions différentes

377 686 actes en 2012 contre 25 529 en 2015 — un rapport de 1 à 12 qui traduit un
changement de définition de l'acte, et non un effondrement de l'activité.
**Ces deux valeurs ne doivent jamais être comparées ni mises dans une même série.**

### 3. Rapport 2016 : totaux groupe uniquement

Le rapport 2016 ne publie quasiment aucun détail par site. Les colonnes `PSL` et `CFX`
y sont donc vides pour la plupart des indicateurs, seul `TOTAL` est renseigné. Toute
analyse comparant les deux sites doit se limiter aux années 2011, 2012 et 2015.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

> **Note :** `pmdarima` est sensible aux versions de `numpy` et `statsmodels`. En cas
> d'erreur à l'import, épingler les versions dans `requirements.txt` ou se replier sur
> `statsmodels.tsa.statespace.SARIMAX` avec une recherche d'ordre manuelle.

## Lancement de l'application

```bash
streamlit run app/app.py
```

## Conventions

- Documentation, code et livrables rédigés **en français**.
- Les fichiers de `data/raw/` ne sont jamais modifiés à la main après extraction : toute
  transformation passe par un notebook ou un script versionné.
- Nommage des fichiers en minuscules, sans accent ni espace (`serie_urgences_mensuelle.csv`).

## État d'avancement

- [x] Initialisation de la structure du projet
- [x] Dépôt des 3 rapports annuels dans `docs/`
- [x] Extraction manuelle des indicateurs vers `data/raw/` (6 fichiers, 180 lignes)
- [x] Script de contrôle qualité des données sources
- [ ] Récupération des données OSCOUR
- [ ] Construction des séries temporelles
- [ ] Modélisation SARIMA
- [ ] Scénario de crise sanitaire
- [ ] Application Streamlit
- [ ] Rédaction des livrables
