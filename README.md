# Projet data : groupe hospitalier Pitié-Salpêtrière / Charles-Foix (PSL-CFX)

Analyse de l'activité hospitalière du groupe PSL-CFX à partir des rapports annuels,
prévision de l'activité par modélisation SARIMA, simulation d'un scénario de crise
sanitaire, et restitution sous forme d'infographie interactive Streamlit.

## Objectifs

1. **Extraire** les indicateurs d'activité contenus dans les rapports annuels (PDF) et
   les convertir en jeux de données exploitables.
2. **Consolider** ces données avec des sources publiques (séries quotidiennes de passages
   aux urgences publiées par la DREES) pour construire des séries temporelles cohérentes.
3. **Prévoir** l'activité future à l'aide d'un modèle SARIMA, sur une saisonnalité
   mensuelle mesurée et non supposée.
4. **Simuler** un scénario de crise sanitaire (choc d'activité) et en mesurer l'impact
   sur les capacités du groupe hospitalier.
5. **Restituer** l'ensemble sous forme d'une infographie interactive (Streamlit + Plotly).

## Résultats en bref

**Le parti pris du projet : rien n'est supposé.** Là où un travail de ce type pose
généralement des hypothèses invérifiables (« admettons que l'hiver pèse 30 % de
l'activité », « admettons qu'une crise fasse chuter les passages de moitié »), la
saisonnalité et l'ampleur de la crise sont ici **mesurées sur données publiques**.

| Résultat | Valeur | D'où il vient |
|----------|--------|---------------|
| Rythme annuel des urgences | Creux en août à **−15,4 %**, pic en novembre à **+7,2 %**, soit **26,7 %** d'amplitude | 2 771 868 passages parisiens réellement enregistrés (DREES, 2017-2019) |
| Bascule vers l'ambulatoire | **55,8 %** des séjours de court séjour en 2011, **57,2 %** en 2016 | Rapports annuels PSL-CFX |
| Reconversion de Charles-Foix | Journées de soins de suite **+41,8 %**, soins de longue durée **−35,7 %** entre 2011 et 2016 | Rapports annuels PSL-CFX |
| Modèle de prévision | SARIMA (0,1,0)(1,1,0,12), erreur moyenne de **0,70 %** sur douze mois jamais vus | `notebooks/04`, `modele_info.json` |
| Impact d'une crise type COVID | **−21,0 %** d'activité sur douze mois, **−45,7 %** au mois le plus touché | Comparaison de 2020 à la moyenne 2017-2019 (DREES) |

Une réserve est assumée et documentée : **l'erreur de 0,70 % ne démontre pas une capacité
prédictive**. La saisonnalité de la série modélisée provenant du profil DREES appliqué
uniformément, le modèle retrouve un motif introduit par construction. Ce score valide la
cohérence de la chaîne de traitement, rien de plus. Le détail figure dans
[`rapports/rapport_technique.md`](rapports/rapport_technique.md).

## Structure du dépôt

```
projet-data-pslcfx/
├── docs/               # Rapports annuels sources (3 PDFs) et documentation de référence
├── data/
│   ├── raw/            # CSV bruts extraits des PDFs (aucune transformation)
│   ├── external/       # Données publiques téléchargées (DREES, open data santé)
│   └── processed/      # Séries temporelles construites, prévisions, scénarios
├── notebooks/          # Chaîne de traitement, exécutée dans l'ordre 01 → 05
│   ├── 01_serie_annuelle.ipynb
│   ├── 02_saisonnalite_urgences.ipynb
│   ├── 03_reconstruction_mensuelle.ipynb
│   ├── 04_prevision_sarima.ipynb
│   └── 05_scenario_crise.ipynb
├── scripts/            # Utilitaires reproductibles
│   ├── telecharger_urgences_drees.py
│   └── verifier_donnees.py
├── app/                # Application Streamlit (infographie interactive)
├── rapports/           # Livrables rédigés
├── requirements.txt    # Dépendances Python
└── README.md
```

## Pipeline de traitement

| Étape | Entrée | Traitement | Sortie |
|-------|--------|-----------|--------|
| 1. Extraction | `docs/*.pdf` | Saisie **manuelle** des indicateurs (les plaquettes sont des documents graphiques, illisibles par extraction automatique) puis contrôle qualité automatisé | `data/raw/*.csv` |
| 2. Données externes | Open data DREES (data.gouv.fr) | Téléchargement des séries quotidiennes de passages aux urgences 2017-2023 et filtrage géographique | `data/external/*.csv` |
| 3. Consolidation | `data/raw/`, `data/external/` | Nettoyage, harmonisation des libellés et des périodes, contrôle de cohérence | `data/processed/serie_annuelle.csv` |
| 4. Profil saisonnier | `data/external/` | Mesure de la saisonnalité mensuelle sur trois années pré-COVID, en part du total annuel et en intensité quotidienne | `data/processed/profil_saisonnier.csv` |
| 5. Reconstruction mensuelle | Série annuelle + profil saisonnier | Interpolation linéaire des années manquantes, puis répartition des totaux annuels selon le profil mesuré, avec contrôle de conservation | `data/processed/serie_annuelle_complete.csv`, `data/processed/serie_mensuelle.csv` |
| 6. Modélisation SARIMA | Série mensuelle | Sélection d'ordre (`pmdarima.auto_arima`), validation sur douze mois jamais vus, puis prévision à 12 mois | `data/processed/prevision_12mois.csv`, `data/processed/modele_info.json` |
| 7. Scénario de crise | Prévision de référence + année 2020 | Mesure de l'impact COVID réel (rapport mensuel 2020 sur moyenne 2017-2019) puis application à la trajectoire prévue | `data/processed/coefficients_crise.csv`, `data/processed/prevision_crise.csv` |
| 8. Restitution | Séries, prévision et scénario | Infographie interactive et livrables rédigés | `app/`, `rapports/` |

Chaque étape correspond à un notebook numéroté, exécutable dans l'ordre. Les fichiers
produits étant versionnés, aucune exécution n'est nécessaire pour consulter les résultats
ou lancer l'application.

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
- **Une cellule vide signifie « donnée non publiée dans le rapport »**, jamais zéro.
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

## Données externes : passages aux urgences (DREES)

Les rapports annuels ne publient qu'un total d'urgences par an, sur des périmètres
mouvants. Impossible d'en tirer une saisonnalité. Le profil mensuel est donc **mesuré**
sur une source publique à pas quotidien, plutôt que supposé.

| | |
|---|---|
| **Jeu de données** | Séries longues corrigées du nombre de passages aux urgences 2017 à 2023 en France |
| **Producteur** | DREES, Direction de la recherche, des études, de l'évaluation et des statistiques (ministère de la Santé) |
| **Diffusion** | [data.gouv.fr](https://www.data.gouv.fr/datasets/series-longues-corrigees-du-nombre-de-passages-aux-urgences-2017-a-2023-en-france) |
| **Licence** | Licence Ouverte 2.0 (Etalab), réutilisation libre avec mention de la source |
| **Période** | 1er janvier 2017 au 31 décembre 2023, pas quotidien |
| **Granularité** | Départementale (98 codes) |
| **Fichier local** | `data/external/passages_urgences_drees_2017_2023.csv` (7,4 Mo) |
| **Colonnes** | `date`, `dep`, `libelle_dep`, `nb_passages` |

### Méthode de construction de la source

Ces séries ne sont **pas des comptages bruts**. Les Résumés de Passages aux Urgences
(RPU) transmis par les établissements ont une couverture incomplète et variable dans le
temps : tous les services ne remontent pas leurs données, et pas toujours de façon
continue. La DREES corrige ce biais par **étalonnage-calage** sur les totaux de la SAE
(Statistique Annuelle des Établissements) et du PMSI, afin de produire des séries
continues et comparables d'une année à l'autre.

Conséquence pratique : `nb_passages` contient des **valeurs décimales** (par exemple
`397.1`). Ce sont des estimations calées, pas des effectifs. **Elles ne doivent pas être
arrondies à l'import**, sous peine d'introduire un biais systématique.

> **Écart de documentation** : la fiche du jeu de données annonce des dates au format
> `dd/mm/yyyy`, mais le fichier livré utilise le format ISO `yyyy-mm-dd` avec le
> séparateur `;`. Le code du projet essaie les deux formats et échoue explicitement si
> aucun ne convient, plutôt que de produire silencieusement des dates vides.

### Comment ce fichier a été obtenu

**Le fichier est déjà présent dans le dépôt** : cloner le projet suffit, il n'y a rien à
télécharger pour faire tourner les notebooks ou l'application.

Le script `scripts/telecharger_urgences_drees.py` documente néanmoins la provenance de
cette donnée : il va la chercher à la source sur data.gouv.fr et vérifie qu'elle est
conforme avant de la valider : taille du fichier, parsing, présence des colonnes
attendues, lisibilité des dates et caractère numérique des passages. La provenance est
ainsi reproductible plutôt que déclarative.

Il n'est utile que dans deux cas : si le fichier a été supprimé ou corrompu, ou si la
DREES publie une mise à jour du jeu de données.

```bash
python scripts/telecharger_urgences_drees.py          # ne fait rien si le fichier est là
python scripts/telecharger_urgences_drees.py --force  # retélécharge malgré tout
```

### Périmètre retenu et années exclues

Le fichier étant départemental, il ne permet pas d'isoler un établissement. On retient
le **département 75 (Paris)**, où se trouve la Pitié-Salpêtrière. Charles-Foix, à
Ivry-sur-Seine (94), n'a pas de service d'accueil des urgences.

Le profil « normal » est construit sur **2017, 2018 et 2019 uniquement**. Les années
2020 et suivantes sont écartées de la référence pour deux raisons : l'épidémie déforme
la saisonnalité habituelle, et les confinements ont fait chuter la fréquentation pour
des motifs sans rapport avec l'état de santé de la population : en avril 2020, Paris
n'enregistre que **54 %** des passages d'un mois d'avril normal.

**Le fichier complet est néanmoins conservé dans `data/external/`.** Les années 2020 à
2023 serviront à l'étape « scénario de crise » pour **mesurer** l'impact réel du COVID
(ratio mois par mois entre 2020 et la moyenne 2017-2019) au lieu de le supposer.

### Résultat

`data/processed/profil_saisonnier.csv` contient 12 lignes, colonnes `MOIS`, `PCT_NORMAL`
(part du mois dans le total annuel, somme = 100) et `PASSAGES_MOYENS_PAR_JOUR`.

La saisonnalité parisienne est réelle mais modérée : de **2 142 passages par jour en
août** à **2 713 en novembre**, soit 27 % d'écart entre le mois le plus creux et le plus
chargé. Rapporté à la moyenne de 2 531 par jour, **le creux estival (−15 %) est bien plus
marqué que le pic hivernal (+7 %)**. Le profil calculé sur l'Île-de-France entière est
quasi identique (écart mensuel maximal de 0,26 point, corrélation 0,983), ce qui valide
l'usage du seul département 75.

Détail de la méthode et graphiques : `notebooks/02_saisonnalite_urgences.ipynb`.

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

La progression apparente de +41,5 % entre 2012 et 2015 est un **artefact de périmètre**,
pas une croissance d'activité. Toute série temporelle sur les urgences devra donc
s'appuyer sur le **SAU seul**, à l'exclusion des urgences dentaires et spécialisées.

### 2. Soins dentaires : définitions différentes

377 686 actes sur le site de la Pitié-Salpêtrière en 2012 contre 25 529 en 2015, soit un
rapport de près de 1 à 15 qui traduit un changement de définition de l'acte, et non un
effondrement de l'activité. Sur le total des deux sites, l'écart reste de 1 à 12
(409 367 actes contre 32 847).
**Ces deux valeurs ne doivent jamais être comparées ni mises dans une même série.**

### 3. Rapport 2016 : totaux groupe uniquement

Le rapport 2016 ne publie quasiment aucun détail par site. Les colonnes `PSL` et `CFX`
y sont donc vides pour la plupart des indicateurs, seul `TOTAL` est renseigné. Toute
analyse comparant les deux sites doit se limiter aux années 2011, 2012 et 2015.

## Installation

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Le projet a été développé et validé sous **Python 3.12**, avec `pandas 3.0`,
`statsmodels 0.14`, `pmdarima 2.1` et `streamlit 1.61`.

> **Note :** `pmdarima` est sensible aux versions de `numpy` et `statsmodels`. Il
> fonctionne sans réserve avec les versions ci-dessus ; en cas d'erreur à l'import sur
> une autre combinaison, épingler les versions dans `requirements.txt` ou se replier sur
> `statsmodels.tsa.statespace.SARIMAX` avec une recherche d'ordre manuelle : c'est la
> vérification par grille exhaustive déjà présente dans le notebook 04.

## Livrables

Deux documents rédigés, dans `rapports/` :

| Document | Contenu |
|----------|---------|
| [`rapport_technique.md`](rapports/rapport_technique.md) | Sources, construction du dataset, pièges de comparabilité, pipeline, modèle et validation, scénario de crise, limites et perspectives |
| [`rapport_mise_en_place.md`](rapports/rapport_mise_en_place.md) | Recommandations opérationnelles : gestion des afflux, préparation aux crises, feuille de route |

À quoi s'ajoute l'infographie interactive (`app/`), dont la commande de lancement est
donnée ci-dessous.

**Tous les chiffres cités dans ces documents proviennent des fichiers du dépôt.** Aucune
valeur n'est estimée de mémoire ni arrondie sans contrôle.

## Lancer l'infographie

L'application vit dans l'environnement virtuel du projet. Le plus simple est d'appeler
Streamlit via le Python de cet environnement, sans activation préalable :

```powershell
# Windows
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

```bash
# macOS / Linux
./.venv/bin/python -m streamlit run app/app.py
```

Si l'environnement est déjà activé, `streamlit run app/app.py` suffit. La commande
`streamlit` seule échoue tant que l'environnement n'est pas activé : le paquet est
installé dans `.venv/`, pas au niveau du système.

L'application s'ouvre dans le navigateur sur `http://localhost:8501`. Elle **ne
recalcule aucun modèle** : elle lit uniquement les fichiers déjà produits dans
`data/raw/` et `data/processed/`. Les notebooks doivent donc avoir été exécutés au
préalable. Plus simplement, les fichiers déjà versionnés suffisent tels quels.

### Organisation de l'application

| Fichier | Rôle |
|---------|------|
| `app/app.py` | Interface : trois onglets, filtres, graphiques |
| `app/utils.py` | Chargement des fichiers (avec `@st.cache_data`), palette et glossaire |

### Les trois onglets

1. **L'hôpital aujourd'hui** : six chiffres clés, la bascule vers l'ambulatoire, la
   répartition des lits par discipline et les principales causes d'hospitalisation.
2. **L'activité au fil de l'année** : le rythme mensuel mesuré sur les données DREES,
   puis l'évolution mois par mois de l'indicateur choisi, prolongée par la prévision et
   sa marge d'estimation. Deux filtres : indicateur affiché et période.
3. **Et si une crise arrive ?** : un interrupteur « Mode crise sanitaire » qui superpose
   à la trajectoire normale celle qui serait constatée si une crise comparable à 2020
   survenait, avec trois indicateurs d'impact. Les filtres de l'onglet 2 s'y appliquent
   également.

### Parti pris de restitution

Le public visé est la direction d'établissement et les équipes soignantes, pas des
spécialistes de la donnée. Le vocabulaire statistique est donc banni de l'écran : on
parle de « prévision » et de « marge d'estimation », jamais de modèle ni de métrique
d'erreur. En revanche, le vocabulaire hospitalier est conservé (MCO, SSR, SLD,
ambulatoire, SAU) et chaque sigle est défini dans un dépliant en haut de page. Chaque
graphique est accompagné d'une phrase de lecture qui en donne le message principal.

## Conventions

- Documentation, code et livrables rédigés **en français**.
- Les fichiers de `data/raw/` ne sont jamais modifiés à la main après extraction : toute
  transformation passe par un notebook ou un script versionné.
- Nommage des fichiers en minuscules, sans accent ni espace (`serie_mensuelle.csv`).
- Les notebooks sont versionnés **avec leurs sorties**, afin que les résultats soient
  lisibles sans rien exécuter.
