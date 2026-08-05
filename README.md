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
├── app/                # Application Streamlit (infographie interactive)
├── rapports/           # Brouillons markdown des livrables
├── requirements.txt    # Dépendances Python
└── README.md
```

## Pipeline de traitement

| Étape | Entrée | Traitement | Sortie |
|-------|--------|-----------|--------|
| 1. Extraction | `docs/*.pdf` | Lecture des tableaux d'activité des rapports annuels, saisie / extraction structurée | `data/raw/*.csv` |
| 2. Données externes | Portail OSCOUR / open data | Téléchargement et filtrage sur le périmètre géographique pertinent | `data/external/*.csv` |
| 3. Consolidation | `data/raw/`, `data/external/` | Nettoyage, harmonisation des libellés et des périodes, contrôle de cohérence | `data/processed/serie_activite.csv` |
| 4. Analyse exploratoire | `data/processed/` | Statistiques descriptives, décomposition tendance / saisonnalité, tests de stationnarité (ADF) | `notebooks/`, figures |
| 5. Modélisation SARIMA | Série consolidée | Sélection d'ordre (`pmdarima.auto_arima`), estimation, diagnostic des résidus, validation hors échantillon | `data/processed/previsions.csv` |
| 6. Scénario de crise | Prévisions de référence | Application d'un choc d'activité paramétré (amplitude, durée, montée en charge) et comparaison au scénario tendanciel | `data/processed/scenario_crise.csv` |
| 7. Restitution | Séries + prévisions + scénarios | Infographie interactive et synthèse rédigée | `app/`, `rapports/` |

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
- [ ] Dépôt des 3 rapports annuels dans `docs/`
- [ ] Extraction des indicateurs vers `data/raw/`
- [ ] Récupération des données OSCOUR
- [ ] Construction des séries temporelles
- [ ] Modélisation SARIMA
- [ ] Scénario de crise sanitaire
- [ ] Application Streamlit
- [ ] Rédaction des livrables
