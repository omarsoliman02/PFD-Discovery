# PFD-Discovery : Decouverte de Pattern Functional Dependencies

> Mini-projet -- **Pattern-Based Dependencies and Agentic Discovery for Data Quality**
> Universite Paris Dauphine - PSL | LAMSADE | Cours de Khalid Belhajjame

---

## Table des matieres

- [Presentation du projet](#presentation-du-projet)
- [Concepts theoriques](#concepts-theoriques)
  - [Dependances Fonctionnelles (FDs)](#dependances-fonctionnelles-fds)
  - [Pattern Functional Dependencies (PFDs)](#pattern-functional-dependencies-pfds)
  - [PFDs Approximatives](#pfds-approximatives)
  - [Pipeline classique de decouverte](#pipeline-classique-de-decouverte)
  - [Approche agentique (IA)](#approche-agentique-ia)
- [Architecture du projet](#architecture-du-projet)
- [Installation](#installation)
- [Guide d'utilisation](#guide-dutilisation)
  - [1. Approche classique](#1-approche-classique)
  - [2. Approche agentique](#2-approche-agentique)
  - [3. Comparaison des approches](#3-comparaison-des-approches)
- [Datasets](#datasets)
- [Modules detailles](#modules-detailles)
- [Exemples de resultats](#exemples-de-resultats)
- [Technologies utilisees](#technologies-utilisees)

---

## Presentation du projet

Ce projet etudie la **decouverte de dependances fonctionnelles basees sur des patterns (PFDs)** dans des donnees reelles. Il compare deux approches :

1. **Approche classique (algorithmique)** : exploration systematique de toutes les transformations et candidats possibles
2. **Approche agentique (IA)** : utilisation de LLMs (Claude, Gemini) pour guider intelligemment la recherche

L'objectif est d'evaluer si l'IA agentique ameliore la **qualite**, l'**interpretabilite** et l'**efficacite** de la decouverte de PFDs par rapport a l'approche purement algorithmique.

---

## Concepts theoriques

### Dependances Fonctionnelles (FDs)

Une **Dependance Fonctionnelle** classique `X -> Y` signifie : si deux lignes ont la meme valeur pour l'attribut X, elles doivent avoir la meme valeur pour Y.

```
Exemple : Department -> Department Name
Si deux employes sont dans le meme departement "POL",
alors le nom du departement est toujours "Department of Police".
```

**Limitation** : Les FDs comparent des **valeurs entieres**. Elles ne detectent pas les regularites au niveau des patterns (prefixes, tokens, sous-chaines).

### Pattern Functional Dependencies (PFDs)

Une **PFD** `R(X -> Y, Tp)` generalise les FDs en utilisant des **patterns** au lieu de valeurs exactes.

```
Exemples :
- first_token(name) -> gender     ("John*" -> M, "Susan*" -> F)
- prefix(zip, 3) -> city          ("900" -> Los Angeles, "100" -> New York)
- domain(email) -> organization   ("@google.com" -> Google)
```

**Definition formelle** : Si deux tuples matchent le meme pattern sur X, alors ils doivent matcher le meme pattern sur Y.

### PFDs Approximatives

Les donnees reelles contiennent du **bruit**. On tolere donc un certain taux de violation :

| Metrique | Formule | Description |
|----------|---------|-------------|
| **Support** | `\|{t in R \| t \|= X}\|` | Nombre de tuples matchant le pattern X |
| **Confidence** | `\|{t \|= X et t \|= Y}\| / \|{t \|= X}\|` | Proportion de tuples coherents |
| **Noise** | `1 - confidence` | Taux de violation tolere |

On garde une regle si : `support >= K` (ex: 5) et `confidence >= theta` (ex: 0.85)

### Pipeline classique de decouverte

Le pipeline classique suit 5 etapes sequentielles :

```
Donnees brutes
    |
    v
[1. Extraction de patterns]     Prefixes, tokens, n-grams, longueurs...
    |
    v
[2. Groupement]                 Regrouper les tuples par pattern
    |
    v
[3. Generation de candidats]    Toutes les paires pattern(X) -> Y
    |
    v
[4. Validation]                 Calcul support + confidence + seuils
    |
    v
[5. Generalisation]             Fusion de patterns redondants
    |
    v
PFDs decouvertes
```

**Limites** :
- Espace de recherche **enorme** (toutes les combinaisons de transformations et colonnes)
- **Pas de comprehension semantique** (ne sait pas que "zip" est un code postal)
- Decouvre des **dependances spurieuses** (coincidences statistiques)

### Approche agentique (IA)

L'idee : utiliser un **LLM** (Large Language Model) pour completer l'algorithme avec du **raisonnement semantique**.

#### Workflow 1 : Feature-Enriched Discovery

```
Table R --> [Agent LLM] --> Suggere des transformations --> [Algo classique] --> PFDs
                            pertinentes
```

L'agent analyse les noms de colonnes et des echantillons de valeurs, puis suggere les transformations qui ont du **sens semantique** (ex: "cette colonne ressemble a un code postal, essaye `prefix(zip, 3)`").

#### Workflow 2 : Guided Search

```
Table R --> [Agent LLM] --> Suggere transformations    --> [Algo : valide] --> PFDs
                            + Priorise les candidats
                              X -> Y prometteurs
```

L'agent va plus loin : il ne suggere pas seulement les features, il **selectionne les candidats les plus prometteurs** a valider. Cela reduit drastiquement l'espace de recherche.

**Avantages de l'approche agentique** :
- Moins de candidats explores = **plus rapide**
- Dependances plus **interpretables** et **significatives**
- Filtre les resultats **triviaux** ou **sans sens**

---

## Architecture du projet

```
PFD-Discovery/
|
|-- Approximate_PFDs.pdf              # Specification du projet (40 slides)
|
|-- data/                             # 15 datasets CSV reels
|   |-- CHE/                          # Chimie / Biologie moleculaire (5 fichiers)
|   |   |-- mechanism_refs.csv
|   |   |-- metabolism_refs.csv
|   |   |-- protein_classification.csv
|   |   |-- research_companies.csv
|   |   +-- variant_sequences.csv
|   |
|   |-- DGOV/                         # Gouvernance de donnees (5 fichiers)
|   |   |-- 10492-1.csv
|   |   |-- 10642-1.csv
|   |   |-- 570-1.csv
|   |   |-- 6339-1.csv
|   |   +-- 6397-1.csv
|   |
|   +-- pfd_validation/               # Datasets de validation (4 fichiers)
|       |-- US_Phone_Code.csv
|       |-- t1.csv
|       |-- t2.csv
|       +-- t3.csv
|
|-- src/                              # Code source
|   |-- __init__.py
|   |-- data_loader.py                # Chargement et preprocessing CSV
|   |-- pattern_extraction.py         # Extraction de 7 types de patterns
|   |-- pattern_grouping.py           # Groupement de tuples par pattern
|   |-- candidate_generation.py       # Generation des candidats X -> Y
|   |-- validation.py                 # Calcul support/confidence + filtrage
|   |-- generalization.py             # Fusion de patterns redondants
|   |-- classical_pipeline.py         # Pipeline classique complet (5 etapes)
|   |-- llm_agent.py                  # Integration LLMs (Mistral, Llama, Gemini, Cohere)
|   |-- agentic_workflow.py           # Workflow 1 (Feature-Enriched) + Workflow 2 (Guided Search)
|   +-- evaluation.py                 # Metriques d'evaluation et comparaison
|
|-- experiments/                      # Scripts d'experimentation
|   |-- run_classical.py              # Executer l'approche classique sur tous les datasets
|   |-- run_agentic.py                # Executer les workflows agentiques
|   +-- compare_results.py            # Comparaison cote a cote classique vs agentique
|
|-- results/                          # Resultats sauvegardes (JSON)
|
|-- requirements.txt                  # Dependances Python
+-- README.md
```

---

## Installation

### Prerequis

- **Python 3.10+**
- **Ollama** (recommande, pour les modeles locaux -- zero quota, gratuit)

### Etapes

```bash
# 1. Cloner le repository
git clone https://github.com/omarsoliman02/PFD-Discovery.git
cd PFD-Discovery

# 2. Installer les dependances Python
pip install -r requirements.txt

# 3. Installer Ollama (modeles locaux -- RECOMMANDE)
brew install ollama
brew services start ollama
ollama pull mistral        # Mistral 7B (~4.4 Go)
ollama pull llama3.1       # Llama 3.1 8B (~4.9 Go)

# 4. (Optionnel) Configurer les APIs cloud
export GOOGLE_API_KEY="votre-cle-google"
export COHERE_API_KEY="votre-cle-cohere"
```

### LLMs disponibles

| Modele | Type | Quota | RAM requise | Commande |
|--------|------|-------|-------------|----------|
| **Mistral 7B** | Local (Ollama) | Illimite | ~6 Go | `--llm mistral` |
| **Llama 3.1 8B** | Local (Ollama) | Illimite | ~7 Go | `--llm llama` |
| Gemini 2.0 Flash | Cloud (API) | Limite | -- | `--llm gemini` |
| Cohere Command A | Cloud (API) | Limite | -- | `--llm cohere` |

---

## Guide d'utilisation

### 1. Approche classique

L'approche classique **ne necessite pas de cle API**. Elle explore toutes les transformations possibles de maniere systematique.

```bash
# Executer sur TOUS les datasets
python3 experiments/run_classical.py

# Les resultats sont affiches dans le terminal et sauvegardes dans results/
```

**Parametres ajustables** (dans `run_classical.py`) :

| Parametre | Defaut | Description |
|-----------|--------|-------------|
| `MIN_SUPPORT` | 5 | Nombre minimum de tuples dans un groupe |
| `MIN_CONFIDENCE` | 0.85 | Confidence minimum pour garder une regle |
| `MAX_PREFIX_LEN` | 4 | Longueur maximale des prefixes explores |

**Exemple de sortie** :
```
=== t1.csv ===
Shape: (9101, 9)

[1/5] Extraction: 59 transformations generees
[2-3/5] Candidats: 472 paires X -> Y a evaluer
[4/5] Validation: 123 PFDs valides trouvees
[5/5] Generalisation: 85 PFDs apres generalisation

Temps d'execution: 6.70s

--- Top PFDs decouvertes ---
  identity(Department) -> Department Name   [support=9090, conf=1.000]
  identity(Division) -> Department          [support=8527, conf=0.987]
  first_token(Position Title) -> Assignment Category [support=8999, conf=0.958]
```

### 2. Approche agentique

Par defaut, utilise les **modeles locaux** (Ollama) -- aucune cle API requise.

```bash
# Modeles locaux (Mistral + Llama) sur tous les datasets
python3 experiments/run_agentic.py

# Seulement Mistral sur le dataset t1
python3 experiments/run_agentic.py --llm mistral --dataset t1

# Seulement Workflow 1 avec Llama
python3 experiments/run_agentic.py --llm llama --workflow 1

# Modeles cloud (necessite cles API)
python3 experiments/run_agentic.py --llm gemini --dataset t1
```

**Options** :

| Option | Valeurs | Description |
|--------|---------|-------------|
| `--llm` | `mistral`, `llama`, `gemini`, `cohere`, `local`, `all` | LLM a utiliser |
| `--dataset` | nom du fichier (ex: `t1`) | Filtrer par dataset |
| `--workflow` | `1` ou `2` | Numero du workflow |

### 3. Comparaison des approches

Le script `compare_results.py` execute **les 3 approches** (classique + W1 + W2) sur un meme dataset et affiche un tableau comparatif.

```bash
# Comparaison avec modeles locaux (par defaut)
python3 experiments/compare_results.py --dataset t1

# Comparaison avec un seul LLM
python3 experiments/compare_results.py --dataset t2 --llm mistral
```

**Resultats reels (t1.csv -- 9101 employes gouvernementaux)** :
```
------------------------------------------------------------------------------------------------------------------------
Approche                              PFDs  Parfaites  Interes.   Conf.moy  Supp.moy  Candidats  Temps(s)
------------------------------------------------------------------------------------------------------------------------
Classique                               85         2        64     0.9133     7481.9       616     10.42
W1-mistral                              23         2         4     0.9310     6747.4        72     70.75
W2-mistral                              10         0         1     0.9386     5736.9        34     51.76
W1-llama                                12         0        12     0.9150     7804.3        40     62.52
W2-llama                                21         2         0     0.9335     7144.9        74     99.51
------------------------------------------------------------------------------------------------------------------------
```

---

## Datasets

### pfd_validation/ -- Datasets de validation

| Fichier | Lignes | Colonnes | PFDs attendues |
|---------|--------|----------|----------------|
| `US_Phone_Code.csv` | 51 | State, Short, Code | State -> Short (toutes uniques) |
| `t1.csv` | 9101 | Full Name, Gender, Department, ... | Department -> Department Name, first_token(Name) -> Gender |
| `t2.csv` | 3502 | NAME, CITY, STATE, ZIP, ... | prefix(ZIP,3) -> CITY, STATE -> patterns |
| `t3.csv` | 3230 | Licensee Name, City, State, Zip, ... | City -> State, prefix(Zip,5) -> City |

### CHE/ -- Chimie et Biologie moleculaire

| Fichier | Lignes | Domaine |
|---------|--------|---------|
| `mechanism_refs.csv` | 9561 | References de mecanismes pharmaceutiques (PubMed, DailyMed) |
| `metabolism_refs.csv` | 2410 | References de metabolisme de medicaments |
| `protein_classification.csv` | 859 | Taxonomie hierarchique des proteines |
| `research_companies.csv` | 813 | Entreprises de recherche pharmaceutique par pays |
| `variant_sequences.csv` | 1201 | Variants de sequences proteiques et mutations |

### DGOV/ -- Gouvernance de donnees

| Fichier | Lignes | Domaine |
|---------|--------|---------|
| `570-1.csv` | 9101 | Employes gouvernementaux (noms, departements, postes) |
| `10492-1.csv` | 3230 | Licences commerciales (noms, adresses, types) |
| `10642-1.csv` | 2767 | Agences d'emploi par ville/ZIP |
| `6339-1.csv` | 307 | Statistiques de criminalite par ville |
| `6397-1.csv` | 6705 | Donnees demographiques/census |

---

## Modules detailles

### `pattern_extraction.py` -- 7 types de transformations

| Transformation | Exemple | Usage typique |
|----------------|---------|---------------|
| `identity(col)` | "Chicago" -> "Chicago" | Colonnes categoriques |
| `prefix(col, k)` | prefix("90012", 3) -> "900" | Codes postaux, numeros |
| `suffix(col, k)` | suffix("report.pdf", 3) -> "pdf" | Extensions, suffixes |
| `first_token(col)` | first_token("John Smith") -> "John" | Prenoms, premiers mots |
| `last_token(col)` | last_token("John Smith") -> "Smith" | Noms de famille |
| `numeric_prefix(col, k)` | numeric_prefix("ZIP-90012", 3) -> "900" | Codes avec bruit |
| `length(col)` | length("Hello") -> "5" | Longueur de chaine |

### `validation.py` -- Metriques

Pour chaque candidat `pattern(X) -> Y` :
1. **Grouper** les tuples par valeur du pattern X
2. Pour chaque groupe, trouver la **valeur majoritaire** de Y
3. **Support** = nombre total de tuples couverts par les groupes
4. **Confidence** = tuples coherents / tuples totaux
5. **Filtrer** par seuils : `support >= K` et `confidence >= theta`

### `llm_agent.py` -- Integration LLM

- **Mistral 7B** (local) : via Ollama REST API, sans quota
- **Llama 3.1 8B** (local) : via Ollama REST API, sans quota
- **Gemini** (cloud) : via `google-genai` SDK, modele `gemini-2.0-flash`
- **Cohere** (cloud) : via `cohere` SDK, modele `command-a-03-2025`

Deux types de prompts :
1. **Suggestion de transformations** : le LLM analyse le schema et suggere les transformations pertinentes
2. **Priorisation de candidats** : le LLM classe les paires X -> Y par pertinence semantique

### `generalization.py` -- Strategies de generalisation

1. Parmi les prefixes `prefix(col, 1)`, `prefix(col, 2)`, ..., garder le **plus court** avec une bonne confidence
2. Si `identity(col)` a une bonne confidence, elle **subsume** les transformations sur la meme colonne
3. Eliminer les **doublons** par type de transformation

---

## Exemples de resultats

### Resultats classiques sur t1.csv (employes gouvernementaux)

| PFD | Support | Confidence |
|-----|---------|------------|
| `identity(Department) -> Department Name` | 9090 | 1.000 |
| `identity(Division) -> Department` | 8527 | 0.987 |
| `identity(Position Title) -> Assignment Category` | 8769 | 0.974 |
| `first_token(Position Title) -> Assignment Category` | 8999 | 0.958 |

### Resultats classiques sur t2.csv (entreprises)

| PFD | Support | Confidence |
|-----|---------|------------|
| `identity(NAME) -> COUNTRY` | 1994 | 1.000 |
| `identity(EMPLOYER_ID) -> NAME` | 404 | 1.000 |
| `identity(EMPLOYER_ID) -> CITY` | 404 | 1.000 |

---

## Technologies utilisees

| Technologie | Usage |
|-------------|-------|
| **Python 3.10+** | Langage principal |
| **pandas** | Manipulation de donnees CSV |
| **Ollama** | LLMs locaux (Mistral 7B, Llama 3.1 8B) -- sans quota |
| **Google GenAI SDK** | Integration Gemini API (cloud) |
| **Cohere SDK** | Integration Cohere Command A API (cloud) |

---

## Auteurs

- Omar Soliman

## Licence

Projet academique -- Universite Paris Dauphine - PSL, 2026.
