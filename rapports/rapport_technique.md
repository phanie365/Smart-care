# Rapport technique

**Analyse et prévision de l'activité des Hôpitaux universitaires Pitié-Salpêtrière / Charles-Foix**

*Document de travail, projet data PSL-CFX*

---

## 1. Contexte et objectifs

Les Hôpitaux universitaires Pitié-Salpêtrière / Charles-Foix forment l'un des plus
grands groupes hospitaliers de l'AP-HP : 2 229 lits installés et 367 places d'hôpital
de jour répartis en 11 pôles et 73 services, pour 175 398 séjours de court séjour et
644 602 consultations externes en 2016. Un établissement de cette taille se pilote mal
à l'année : l'activité des urgences suit un rythme saisonnier marqué, et une crise
sanitaire peut la bouleverser en quelques semaines, comme l'a montré 2020.

Ce projet répond à deux questions concrètes. D'abord : **à quel moment de l'année
l'activité est-elle la plus forte, et de combien ?** Ensuite : **que deviendrait
l'activité prévue si une crise sanitaire survenait ?**

Il livre une chaîne de traitement complète et reproductible, de l'extraction des
rapports annuels jusqu'à une infographie interactive, ainsi qu'un modèle de prévision
validé sur une année jamais vue par le modèle. Le parti pris méthodologique central est
que **la saisonnalité et l'ampleur de la crise sont mesurées sur données publiques, et
non supposées**.

---

## 2. Sources de données

| Source | Producteur | Période couverte | Usage dans le projet | Licence |
|--------|-----------|------------------|----------------------|---------|
| Rapport annuel *Les chiffres clés 2012* (`SLP-CHF2012.pdf`) | AP-HP, Hôpitaux universitaires PSL-CFX | 2011 et 2012 | Activité, capacité, pathologies, ressources humaines, finances | Document institutionnel public |
| Livret *Les Chiffres Clés 2015* (`SLP-CHX2015.pdf`) | AP-HP, Hôpitaux universitaires PSL-CFX | 2015 | Idem, avec détail par site et par pôle | Document institutionnel public |
| Plaquette *Repères et chiffres clés* (`SLP-CHF2016.pdf`) | AP-HP, Hôpitaux universitaires PSL-CFX | 2016 | Totaux groupe uniquement | Document institutionnel public |
| [*Séries longues corrigées du nombre de passages aux urgences 2017 à 2023 en France*](https://www.data.gouv.fr/datasets/series-longues-corrigees-du-nombre-de-passages-aux-urgences-2017-a-2023-en-france) | DREES, ministère de la Santé | 01/01/2017 au 31/12/2023, pas quotidien, 98 départements | Mesure du profil saisonnier (2017-2019) et de l'impact de la crise (2020) | Licence Ouverte 2.0 (Etalab) |
| [*Passages aux urgences entre 2017 et 2023 : des dynamiques contrastées selon les départements*](https://drees.solidarites-sante.gouv.fr/publications-communique-de-presse/etudes-et-resultats/241212_ER_passages-aux-urgences), Études et Résultats n° 1320 | DREES, H. Khaoua et M. Suarez Castillo, 12/12/2024 | 1996-2023 | Contextualisation du scénario de crise | Publication publique |
| [*Covid-19 et continuité des soins - Continuer de se soigner, un impératif de santé publique*](https://www.santepubliquefrance.fr/presse/2020/covid-19-et-continuite-des-soins-continuer-de-se-soigner-un-imperatif-de-sante-publique), communiqué du 07/05/2020 | Santé publique France | Mars-avril 2020 | Explication des causes du repli des passages | Publication publique |

Les trois rapports annuels sont conservés dans `docs/`, le fichier DREES dans
`data/external/`. Le téléchargement de ce dernier est automatisé par
`scripts/telecharger_urgences_drees.py`, qui vérifie la taille du fichier, son parsing,
la présence des colonnes attendues, la lisibilité des dates et le caractère numérique
des passages avant de valider.

> **Écart de documentation relevé.** La fiche du jeu de données DREES annonce des dates
> au format `dd/mm/yyyy` ; le fichier livré utilise en réalité le format ISO
> `yyyy-mm-dd` avec le séparateur `;`. Le code du projet essaie les deux formats et
> échoue explicitement si aucun ne convient, plutôt que de produire silencieusement des
> dates vides.

---

## 3. Construction du dataset

### 3.1 Une extraction manuelle assumée

Les trois rapports annuels sont des **plaquettes de communication**, pas des annexes
statistiques. Leur mise en page est très graphique : les chiffres sont dispersés dans
des blocs colorés, des infographies et des encarts. Une extraction automatique de
tableaux y produit du texte entrelacé et inexploitable : les libellés d'un bloc se
mêlent aux valeurs du bloc voisin.

La saisie a donc été **manuelle**, et c'est un choix, pas un pis-aller. Chaque ligne
porte une colonne `SOURCE` qui indique le rapport et la rubrique d'origine de la valeur,
par exemple `SLP-CHX2015 - L'hospitalisation`. La traçabilité chiffre → rapport →
section est ainsi complète, ce qu'aucune extraction automatique n'aurait garanti sur ces
documents.

Un dump du texte brut de chaque PDF a néanmoins été conservé le temps de la saisie comme
trace d'audit, permettant de retrouver rapidement le contexte d'une valeur.

### 3.2 Structure des six fichiers

Tous les fichiers sont dans `data/raw/`, encodés en UTF-8, séparateur virgule.

| Fichier | Lignes | Années | Contenu |
|---------|--------|--------|---------|
| `activite.csv` | 65 | 2011, 2012, 2015, 2016 | Séjours MCO, consultations externes, passages aux urgences, journées PSY/SSR/SLD, transplantations, actes et séances des plateaux techniques |
| `capacite.csv` | 33 | 2012, 2015, 2016 | Lits installés et par discipline, places de jour, pôles, services, blocs, lits de réanimation et de soins intensifs |
| `pathologies.csv` | 18 | 2012, 2015 | Séjours par grande cause d'hospitalisation (9 catégories) |
| `rh.csv` | 29 | 2012, 2015, 2016 | Effectifs médicaux et non médicaux par catégorie, répartition hommes/femmes, formation |
| `finance.csv` | 21 | 2012, 2015, 2016 | Dépenses d'exploitation, recettes, solde, crédits d'investissement |
| `patients.csv` | 14 | 2012, 2015 | Âge moyen, répartition par sexe, origine géographique |

**Structure commune** : `ANNEE, INDICATEUR, SOUS_INDICATEUR, PSL, CFX, TOTAL, UNITE,
NOTE, SOURCE`, où `PSL` désigne le site de la Pitié-Salpêtrière et `CFX` celui de
Charles-Foix.

Une règle gouverne toute la lecture du dataset : **une cellule vide signifie « donnée non
publiée dans le rapport », jamais zéro**. La distinction est essentielle, le rapport 2016
ne publiant presque aucun détail par site.

Deux fichiers s'écartent du schéma commun : `pathologies.csv` utilise `ANNEE, PATHOLOGIE,
SEJOURS, NOTE, SOURCE` (une ligne = une pathologie), et `capacite.csv` ne comporte pas de
colonne `NOTE`, ses précisions étant intégrées à `SOURCE`.

### 3.3 Contrôle qualité

Le script `scripts/verifier_donnees.py` rejoue à tout moment l'ensemble des
vérifications : lecture pandas, conformité du schéma, typage numérique des colonnes de
valeurs, comptage des cellules vides et des zéros, cohérence arithmétique
`PSL + CFX = TOTAL`.

Résultat sur le jeu actuel : **180 lignes contrôlées, 6 fichiers lus sans erreur, aucune
valeur non numérique, aucun zéro parasite**. Trois points d'attention subsistent,
volontairement non corrigés puisque les CSV doivent reproduire fidèlement les rapports
publiés :

1. `activite.csv` 2011, séjours ambulatoires : `83 911 + 1 080 = 84 991` alors que le
   total publié est `84 911`, soit un écart de 80 séjours présent dans le rapport source.
2. `capacite.csv` 2012, lits SSR : `85 + 149 = 234` contre un total publié de `209`. Le
   détail par site provient d'une lecture de graphique, d'où son imprécision.
3. `capacite.csv` ne possède pas de colonne `NOTE`, contrairement aux autres fichiers.

Le script distingue par ailleurs ces écarts réels des simples arrondis de publication
(deux lignes à 0,01 M€ dans `finance.csv`), qu'il signale sans les compter comme
anomalies.

### 3.4 Pièges de comparabilité

Les trois rapports ne définissent pas leurs indicateurs de la même façon. Les points
suivants doivent être respectés dans toute analyse, sous peine de produire des évolutions
purement artificielles.

**Piège n° 1 : les passages aux urgences ne sont pas comparables entre années.**

| Année | Valeur publiée | Périmètre réel |
|-------|----------------|----------------|
| 2012 | 85 993 passages | Pitié-Salpêtrière seule, **hors** urgences dentaires |
| 2015 | 121 721 passages | SAU 59 072 **+** urgences dentaires 62 649 |
| 2016 | 127 678 passages | Périmètre encore différent, dont 61 651 urgences spécialisées |

La progression apparente de +41,5 % entre 2012 et 2015 est un **artefact de périmètre**,
pas une croissance d'activité. Toute série temporelle sur les urgences doit s'appuyer sur
le **SAU seul**.

**Piège n° 2 : les soins dentaires changent de définition.** Le rapport 2012 recense
377 686 actes sur le site de la Pitié-Salpêtrière, le rapport 2015 n'en recense que
25 529, soit un rapport de près de 1 à 15 qui traduit un changement de définition de l'acte,
et non un effondrement de l'activité. Sur le total des deux sites, l'écart reste de 1 à 12
(409 367 actes contre 32 847). **Ces valeurs ne doivent jamais être comparées ni placées
dans une même série.**

**Piège n° 3 : le rapport 2016 ne publie que des totaux groupe.** Les colonnes `PSL` et
`CFX` y sont vides pour la quasi-totalité des indicateurs. Toute analyse comparant les
deux sites doit se limiter aux années 2011, 2012 et 2015.

---

## 4. Méthodologie

### 4.1 Le pipeline

```
   docs/*.pdf                    data.gouv.fr (DREES)
   3 rapports annuels            passages quotidiens 2017-2023
        │                                  │
        │ saisie manuelle                  │ téléchargement + validation
        │ + colonne SOURCE                 │ (scripts/telecharger_urgences_drees.py)
        ▼                                  ▼
   ┌──────────────┐                 ┌──────────────────┐
   │  data/raw/   │                 │  data/external/  │
   │   6 CSV      │                 │  247 933 lignes  │
   │  180 lignes  │                 └────────┬─────────┘
   └──────┬───────┘                          │
          │                                  │ filtre département 75
          │ ÉTAPE 1                          │ + années 2017-2019
          │ sélection des séries             │
          ▼                                  ▼ ÉTAPE 2
   ┌──────────────────┐              ┌────────────────────────┐
   │ serie_annuelle   │              │ profil_saisonnier.csv  │
   │ 33 obs, 9 séries │              │ 12 parts mensuelles    │
   └──────┬───────────┘              └───────────┬────────────┘
          │                                      │
          └──────────────┬───────────────────────┘
                         │ ÉTAPE 3
                         │ niveau annuel × part du mois
                         │ contrôle : somme des 12 mois = total annuel
                         ▼
                ┌──────────────────────┐
                │ serie_mensuelle.csv  │
                │ 276 observations     │
                └──────────┬───────────┘
                           │ ÉTAPE 4
                           │ SARIMA, validation hors échantillon
                           ▼
                ┌──────────────────────┐        ┌──────────────────────┐
                │ prevision_12mois.csv │◄───────┤ ÉTAPE 5              │
                │ + modele_info.json   │        │ coefficients mesurés │
                └──────────┬───────────┘        │ sur 2020 (DREES)     │
                           │                    └──────────┬───────────┘
                           └───────────┬───────────────────┘
                                       ▼
                            ┌──────────────────────┐
                            │ prevision_crise.csv  │
                            └──────────┬───────────┘
                                       ▼
                              app/ : infographie Streamlit
```

### 4.2 Le choix méthodologique central

Un projet de ce type se règle habituellement en posant des hypothèses : « admettons que
l'hiver représente 30 % de l'activité », « admettons qu'une crise fasse chuter les
passages de moitié ». Ces chiffres sont invérifiables et ne résistent pas à la première
question d'un jury.

**Ici, la saisonnalité et l'ampleur de la crise sont mesurées.** Le profil mensuel repose
sur 2 771 868 passages réellement enregistrés à Paris entre 2017 et 2019, et les
coefficients de crise sur la comparaison entre l'année 2020 et cette même référence. Les
rapports annuels ne pouvaient pas fournir cette information : ils ne publient qu'un total
par an, sur des périmètres mouvants.

### 4.3 Étape 2 : le profil saisonnier mesuré

Le fichier DREES est départemental. On retient le **département 75 (Paris)**, où se
trouve la Pitié-Salpêtrière ; Charles-Foix, à Ivry-sur-Seine, n'a pas de service d'accueil
des urgences. Les années **2017, 2018 et 2019** servent de référence, à l'exclusion de
2020 et suivantes : l'épidémie déforme la saisonnalité, et les confinements ont fait
chuter la fréquentation pour des motifs sans rapport avec l'état de santé de la
population.

Le profil est calculé de deux façons complémentaires :

| Mois | Part de l'année (%) | Passages moyens par jour |
|------|--------------------|--------------------------|
| Janvier | 8,65 | 2 578,9 |
| Février | 7,66 | 2 528,2 |
| Mars | 8,54 | 2 546,0 |
| Avril | 8,14 | 2 506,6 |
| Mai | 8,47 | 2 525,7 |
| Juin | 8,45 | 2 600,8 |
| Juillet | 8,12 | 2 419,8 |
| **Août** | **7,19** | **2 141,8** |
| Septembre | 8,13 | 2 502,9 |
| **Octobre** | **8,98** | 2 675,4 |
| Novembre | 8,81 | **2 712,8** |
| Décembre | 8,87 | 2 643,9 |

La distinction entre les deux colonnes n'est pas cosmétique : **février paraît creux
(7,66 % de l'année) alors que son intensité quotidienne est dans la moyenne** : son
déficit tient uniquement à ses 28 jours. Le même décalage explique que le pic soit en
octobre en part annuelle, mais en novembre en intensité réelle.

Pour une moyenne de 2 531,9 passages par jour, **août tombe à −15,4 % et novembre monte à
+7,2 %** : le creux estival est nettement plus marqué que le pic hivernal, et l'amplitude
entre les deux extrêmes atteint 26,7 %.

**Test de sensibilité.** Le profil recalculé sur les huit départements franciliens est
quasi identique : écart mensuel maximal de **0,26 point de pourcentage** (en décembre) et
corrélation de **0,983** entre les deux séries. Le choix du seul département 75 est donc
robuste.

### 4.4 Étape 3 : reconstruction mensuelle

Les rapports 2013 et 2014 n'étant pas disponibles, ces années sont comblées par
interpolation linéaire, indicateur par indicateur, **sans aucune extrapolation** au-delà
des années observées. Une colonne `INTERPOLE` distingue mesure et estimation. Le fichier
`serie_annuelle_complete.csv` compte 51 lignes.

La valeur d'un mois vaut ensuite : **total annuel × part du mois**. Quatre indicateurs
d'activité sont mensualisés (séjours en hospitalisation complète, séjours ambulatoires,
consultations externes et passages au SAU), soit **276 observations** dans
`serie_mensuelle.csv`.

**Contrôle de conservation.** Pour chacun des 23 couples (indicateur, année), la somme des
douze mois doit redonner le total annuel. Le contrôle est fait par `assert` : l'écart
relatif maximal constaté est de **2 × 10⁻¹⁶**, soit la seule imprécision des nombres
flottants. La mensualisation ne crée ni ne perd d'activité.

Une précision technique mérite d'être signalée : les parts mensuelles étant enregistrées
arrondies à quatre décimales, leur somme vaut 99,9999 % et non 100 %. Elles sont donc
renormalisées avant usage : correction de l'arrondi d'écriture, pas modification du profil
mesuré, la déformation relative maximale étant de 1 × 10⁻⁶.

---

## 5. Modèle de prévision et validation

### 5.1 Paramètres retenus

| Élément | Valeur |
|---------|--------|
| Indicateur modélisé | Passages au SAU |
| Modèle | SARIMA **(0, 1, 0)(1, 1, 0, 12)** |
| Sélection | `pmdarima 2.1.1`, `auto_arima`, critère AIC |
| Période d'entraînement (validation) | 2011-01 à 2014-12 (48 mois) |
| Période de test | 2015-01 à 2015-12 (12 mois) |
| **Erreur moyenne sur le test** | **0,70 %** |
| Réentraînement final | 2011-01 à 2015-12 (60 observations) |
| AIC du modèle final | 610,74 |
| Horizon de prévision | 12 mois (2016-01 à 2016-12) |
| Niveau de confiance | 95 % |
| Marge moyenne | ± 18,2 % (de 7,2 % au premier mois à 24,9 % au douzième) |
| Total annuel prévu | 49 744 passages |

En clair, le modèle retenu **regarde l'écart avec le mois précédent et le même mois de
l'année précédente**, sans autre terme. Aucune composante supplémentaire n'a été jugée
utile : une fois la tendance et le cycle annuel retirés, il ne reste presque rien à
expliquer.

Le test de stationnarité (Dickey-Fuller augmenté) donne une p-value de 0,999, très
au-dessus de 0,05 : la série a une tendance, que le modèle différencie lui-même.

### 5.2 Protocole de validation

Le découpage diffère du plan initial pour une raison tenant aux données : la série des
passages au SAU **s'arrête en décembre 2015**, le rapport 2016 ne permettant pas d'isoler
le SAU des urgences spécialisées, et l'extrapolation étant proscrite. Le protocole a donc
été décalé d'un an, à principe inchangé : entraînement sur les quatre premières années,
test sur la dernière année entière jamais vue, puis réentraînement sur tout l'historique
avant projection.

**Un enseignement méthodologique.** Une vérification par grille exhaustive
(p, d, q ∈ {0,1,2} × P, D, Q ∈ {0,1}) montre que les modèles les mieux classés par l'AIC
produisent des intervalles inexploitables : jusqu'à ± 40 000 % pour le premier d'entre
eux. C'est le symptôme d'un surajustement : la série étant quasi déterministe, un modèle
riche colle parfaitement au passé mais n'a plus d'information résiduelle pour estimer son
incertitude. **Sur ce jeu de données, l'AIC seul est un mauvais juge**, et le modèle
parcimonieux a été conservé.

### 5.3 Interprétation honnête du score

Une erreur moyenne de **0,70 %** est spectaculairement basse. Il ne faut pas s'en réjouir
trop vite.

**Ce résultat est attendu, et il ne prouve pas une capacité prédictive.** La saisonnalité
de cette série n'a pas été observée sur l'hôpital : elle provient du profil DREES appliqué
uniformément à chaque année. Le modèle retrouve donc un motif introduit par construction,
sur une série dont le niveau annuel varie de façon presque linéaire. **Le score valide la
cohérence du pipeline (la chaîne profil → série mensuelle → modèle → prévision fonctionne
de bout en bout), mais il ne démontre aucune capacité à prévoir des données hospitalières
brutes.**

Deux réserves s'y ajoutent. D'une part, les années 2013 et 2014 du jeu d'entraînement sont
interpolées : le modèle a appris pour moitié sur des valeurs estimées. D'autre part, la
tendance baissière qu'il extrapole (49 744 passages prévus pour 2016 contre 59 072 en
2015, soit −15,8 %) **est un artefact de périmètre**, le passage de 85 993 passages en
2012 à 59 072 en 2015 traduisant un changement de comptage et non une désaffection des
urgences.

Une validation sur données réelles supposerait d'entraîner le modèle directement sur la
série quotidienne DREES du département 75, qui offre 1 095 observations réelles pré-COVID
au lieu de 48 points reconstitués.

---

## 6. Scénario de crise sanitaire

### 6.1 Méthode

Le principe est simple et entièrement mesurable : pour chaque mois, on compare l'activité
réelle de 2020 à celle d'une année ordinaire.

> coefficient(mois) = passages 2020(mois) ÷ moyenne 2017-2019(mois)

La référence est calculée année par année puis moyennée, afin que chacune des trois années
pèse identiquement. Le résultat est enregistré dans `coefficients_crise.csv`, avec un
en-tête documentant méthode, périmètre et source, de sorte que le fichier reste
interprétable indépendamment du notebook.

### 6.2 Les douze valeurs mesurées

| Mois | Coefficient | Lecture |
|------|-------------|---------|
| Janvier | 1,0505 | +5 %, **avant la crise** |
| Février | 1,1109 | +11 %, **avant la crise** |
| Mars | 0,7980 | −20 %, confinement à partir du 17 |
| **Avril** | **0,5432** | **−46 %, plein confinement** |
| Mai | 0,6358 | −36 % |
| Juin | 0,7630 | −24 % |
| Juillet | 0,8431 | −16 % |
| Août | 0,9161 | −8 % |
| Septembre | 0,9528 | −5 %, presque revenu à la normale |
| Octobre | 0,7590 | −24 %, deuxième confinement |
| Novembre | 0,6364 | −36 % |
| Décembre | 0,6869 | −31 % |

Sur l'année entière, Paris enregistre **742 410 passages en 2020 contre 923 956 en moyenne
sur 2017-2019, soit −19,7 %**.

### 6.3 Un constat contre-intuitif

Le résultat le plus frappant est que **les passages aux urgences ont chuté pendant la
crise sanitaire**, au moment même où l'hôpital était le plus sollicité. Avril 2020 ne
compte que 54 % des passages d'un avril ordinaire.

Un détail conforte la méthode : **janvier et février 2020 ressortent au-dessus de 1**
(1,05 et 1,11). Ce ne sont pas des mois de crise (le premier confinement débute le
17 mars) mais des mois de saison grippale soutenue. Autrement dit, **les coefficients
détectent d'eux-mêmes le début de la crise**, sans qu'on ait eu à le leur indiquer.

Les deux sources documentaires confirment et expliquent ce phénomène. La DREES établit que
le nombre de passages aux urgences en France **chute à 18,1 millions en 2020**, contre
22 millions en 2019, avec les baisses les plus marquées lors des confinements de mars et
de novembre, exactement le calendrier retrouvé sur le département 75. Santé publique
France apporte les causes : recul des passages pour pathologies cardio- et
neuro-vasculaires dès les semaines 12-13, puis remontée en semaine 17 traduisant un
**retard de prise en charge par crainte de la contamination**, ainsi qu'une chute des
consultations de 25 % chez les généralistes et de 51 % chez les spécialistes à la
mi-avril 2020.

**Conséquence pour la lecture des résultats : une baisse des passages n'est pas une baisse
des besoins.** Une partie de cette activité est différée, non disparue, et revient plus
tard, parfois aggravée. Un coefficient de 0,54 ne justifie pas de réduire les moyens de
moitié.

### 6.4 Application à la prévision

Le scénario simule une crise démarrant au troisième mois de l'horizon. Les coefficients
sont appliqués dans l'ordre chronologique de la crise réelle : le premier mois touché
reçoit celui de mars 2020, le deuxième celui d'avril 2020, et ainsi de suite. Les deux
premiers mois restent en fonctionnement normal.

| Grandeur | Valeur |
|----------|--------|
| Total sur 12 mois, sans crise | 49 744 passages |
| Total sur 12 mois, avec crise | 39 307 passages |
| Activité en moins | **10 437 passages, soit −21,0 %** |
| Sur les 10 mois de crise seuls | −25,1 % |
| Mois le plus touché | **avril, −45,7 %** (4 036 attendus, 2 192 sous crise) |

---

## 7. Limites et perspectives

### 7.1 Limites

**Très peu d'années observées.** Le dataset repose sur quatre années publiées (2011,
2012, 2015 et 2016), dont toutes ne couvrent pas tous les indicateurs. C'est la contrainte
structurante du projet : elle interdit toute estimation de saisonnalité à partir des seules
données hospitalières.

**Les années 2013 et 2014 sont estimées.** Sur ces deux années, seule la forme saisonnière
est informative ; le niveau résulte d'une interpolation linéaire entre 2012 et 2015. Elles
représentent la moitié du jeu d'entraînement du modèle.

**Le profil saisonnier est départemental, appliqué à un établissement.** On suppose que la
saisonnalité des urgences de la Pitié-Salpêtrière ressemble à celle de l'ensemble des
services parisiens. L'hypothèse est raisonnable (la saisonnalité tient à des facteurs
collectifs qui touchent tous les établissements d'un même bassin) et le test de
sensibilité francilien la conforte, mais elle reste une hypothèse.

**Le profil est mesuré sur 2017-2019 et appliqué à 2011-2016.** On suppose donc aussi que
la forme saisonnière est stable dans le temps. C'est le meilleur choix disponible, aucune
source à pas fin ne couvrant les années antérieures à 2017.

**La crise est calibrée sur le seul COVID-2020.** Les coefficients portent la signature
d'une épidémie respiratoire accompagnée de confinements. **Une autre crise produirait un
profil différent, et parfois de signe opposé** : une canicule, une épidémie de grippe
majeure ou un attentat provoquent une hausse brutale des passages, pas une baisse.

**Le scénario est déterministe.** Il répond à « que se passerait-il si », pas à « quelle
est la probabilité que cela arrive ». Le choix du troisième mois comme point de départ est
arbitraire.

**Les coefficients ne valent que pour les urgences.** Les étendre aux séjours ou aux
consultations serait abusif : la déprogrammation chirurgicale et le report des consultations
obéissent à des logiques différentes, et exigeraient des coefficients propres.

### 7.2 Perspectives

**Basculer sur des données mensuelles internes.** La limite principale n'est pas
méthodologique mais documentaire. Le système d'information de l'établissement produit des
données mensuelles, voire quotidiennes, par service. Alimenté par ces données, le pipeline
tel qu'il existe fournirait immédiatement une prévision exploitable en niveau, et non plus
seulement en forme.

**Mesurer d'autres types de crise dans le même fichier.** Le jeu DREES couvre 2017 à 2023
et contient bien d'autres épisodes que le COVID : l'épidémie de grippe de l'hiver
2018-2019, les vagues de chaleur estivales, les tensions hivernales récurrentes. La même
méthode de mesure (comparaison à une référence pluriannuelle mois par mois) permettrait
de constituer une **bibliothèque de scénarios**, dont certains à la hausse, et de sortir du
scénario unique.

**Étendre la modélisation aux autres indicateurs.** Séjours, consultations et journées
d'hospitalisation n'ont pas encore de coefficients de crise propres. Les données ATIH sur
l'activité hospitalière 2020, qui documentent la déprogrammation, permettraient de les
construire selon la même méthode.

**Valider le modèle sur données brutes.** Entraîner un SARIMA directement sur la série
quotidienne DREES du département 75 (1 095 observations réelles pré-COVID) donnerait une
mesure honnête de la capacité prédictive, que le score actuel ne fournit pas.

---

*Les chiffres de ce rapport proviennent des fichiers du dépôt : `data/raw/`,
`data/processed/serie_annuelle_complete.csv`, `profil_saisonnier.csv`,
`prevision_12mois.csv`, `coefficients_crise.csv`, `prevision_crise.csv` et
`modele_info.json`. Les traitements sont reproductibles par les notebooks `01` à `05`.*
