# PFD-Discovery : Decouverte de Pattern Functional Dependencies

> Mini-projet -- **Pattern-Based Dependencies and Agentic Discovery for Data Quality**
> Universite Paris Dauphine - PSL | LAMSADE | Cours de Khalid Belhajjame
> Annee 2025-2026

---

## Table des matieres

- [Presentation du projet](#presentation-du-projet)
- [Demarrage rapide](#demarrage-rapide)
- [Concepts theoriques](#concepts-theoriques)
- [Architecture du projet](#architecture-du-projet)
- [Installation](#installation)
- [Guide d'utilisation](#guide-dutilisation)
  - [1. Approche classique](#1-approche-classique)
  - [2. Workflows agentiques (W1, W2, W3)](#2-workflows-agentiques-w1-w2-w3)
  - [3. Analyses bonus](#3-analyses-bonus)
  - [4. Comparaison des approches](#4-comparaison-des-approches)
- [Datasets](#datasets)
- [Resultats principaux](#resultats-principaux)
- [Documentation complete](#documentation-complete)

---

## Presentation du projet

Ce projet etudie la **decouverte de dependances fonctionnelles basees sur des patterns (PFDs)** dans des donnees reelles. Il compare deux paradigmes :

1. **Approche classique** : exploration systematique de toutes les transformations possibles par algorithme deterministe.
2. **Approche agentique** : utilisation de LLMs locaux (Mistral 7B, Llama 3.1 8B via Ollama) pour guider intelligemment la recherche.

L'objectif est d'evaluer si l'IA agentique ameliore la **qualite**, l'**interpretabilite** et l'**efficacite** de la decouverte de PFDs par rapport a l'approche purement algorithmique.

### Ce que contient ce projet

- L'algorithme classique en 5 etapes (extraction, groupement, candidats, validation, generalisation).
- **Les TROIS workflows agentiques** presentes dans le cours :
  - **W1** -- Feature-Enriched Discovery (le LLM suggere les transformations)
  - **W2** -- Guided Search (le LLM priorise aussi les candidats)
  - **W3** -- Agent-in-the-Loop (boucle iterative avec feedback)
- Une **generalisation semantique par LLM** (etape 5 LLM-aware).
- Une **analyse de sensibilite** aux seuils K et theta.
- Une **analyse d'erreur** automatique des PFDs manquees.
- 14 datasets reels (46 351 lignes au total) couvrant 3 domaines.
- Comparaison Mistral 7B vs Llama 3.1 8B.

---

## Demarrage rapide

```bash
# 1. Cloner et installer
git clone https://github.com/omarsoliman02/PFD-Discovery.git
cd PFD-Discovery
pip3 install -r requirements.txt

# 2. Installer les LLMs locaux
brew install ollama && brew services start ollama
ollama pull mistral && ollama pull llama3.1

# 3. Lancer une demo (3 minutes)
python3 experiments/compare_results.py --dataset t1 --llm mistral
```

Pour aller plus loin, consulte le [guide de soutenance complet](GUIDE_SOUTENANCE.md).

---

## Concepts theoriques

### Dependances Fonctionnelles (FDs)

Une **FD** classique `X -> Y` exprime que deux lignes avec la meme valeur de X doivent avoir la meme valeur de Y.

```
Exemple : Department -> Department Name
Si deux employes ont le code "POL", le nom est toujours "Department of Police".
```

**Limite** : compare des valeurs entieres. Ne capture pas les regularites partielles (prefixes, tokens, sous-chaines).

### Pattern Functional Dependencies (PFDs)

Une **PFD** s'ecrit `R(X -> Y, Tp)` ou `Tp` est une transformation sur X.

```
Exemples :
- first_token(name) -> gender     ("John*" -> M, "Susan*" -> F)
- prefix(zip, 3) -> city          ("900" -> Los Angeles, "100" -> New York)
- domain(email) -> organization   ("@google.com" -> Google)
```

### PFDs approximatives

Les donnees reelles contiennent du bruit. On tolere donc un certain taux de violation :

| Metrique | Formule | Description |
|----------|---------|-------------|
| **Support** | `count(t : t \|= X)` | Tuples couverts par le pattern X |
| **Confidence** | `coherent / couverts` | Proportion de tuples coherents |
| **Noise** | `1 - confidence` | Taux de violation tolere |

On garde une regle si `support >= K` (par defaut K=5) et `confidence >= theta` (par defaut theta=0.85).

### Pipeline classique

```
Donnees -> Extraction -> Groupement -> Candidats -> Validation -> Generalisation -> PFDs
```

### Les 3 workflows agentiques

| Workflow | Role du LLM | Reduction de l'espace |
|---|---|---|
| **W1** Feature-Enriched | Suggere les transformations | ~87% |
| **W2** Guided Search | Suggere + priorise les candidats | ~94% |
| **W3** Agent-in-the-Loop | Boucle iterative LLM <-> algorithme avec feedback | ~97% |

---

## Architecture du projet

```
PFD-Discovery/
|
|-- Approximate_PFDs.pdf              # Specification du projet (40 slides du prof)
|-- GUIDE_SOUTENANCE.md               # Guide pedagogique complet pour la soutenance
|
|-- data/                             # 14 datasets CSV reels
|   |-- CHE/                          # Chimie / Biologie moleculaire (5 fichiers)
|   |-- DGOV/                         # Gouvernance de donnees (5 fichiers)
|   +-- pfd_validation/               # Datasets de validation (4 fichiers)
|
|-- src/                              # Code source
|   |-- data_loader.py                # Chargement et preprocessing CSV
|   |-- pattern_extraction.py         # 7 transformations (identity, prefix, suffix, tokens, length...)
|   |-- pattern_grouping.py           # Groupement de tuples par pattern
|   |-- candidate_generation.py       # Generation des candidats X -> Y
|   |-- validation.py                 # Calcul support/confidence + filtrage
|   |-- generalization.py             # Fusion algorithmique + semantique (LLM)
|   |-- classical_pipeline.py         # Pipeline classique complet (5 etapes)
|   |-- llm_agent.py                  # Integration LLMs + 5 prompts (W1/W2/W3 + gen semantique)
|   |-- agentic_workflow.py           # Workflows agentiques 1, 2 et 3
|   +-- evaluation.py                 # Metriques d'evaluation et comparaison
|
|-- experiments/                      # Scripts d'experimentation
|   |-- run_classical.py              # Approche classique sur tous les datasets
|   |-- run_agentic.py                # W1 et W2 (avec choix du LLM)
|   |-- run_workflow3.py              # W3 (Agent-in-the-Loop)
|   |-- compare_results.py            # Comparaison cote-a-cote classique vs W1/W2
|   |-- sensitivity_analysis.py       # Analyse de sensibilite aux seuils K et theta
|   |-- error_analysis.py             # Diagnostic des PFDs manquees par les LLMs
|   +-- run_llm_generalization.py     # Generalisation semantique par LLM
|
|-- results/                          # Resultats sauvegardes (JSON, gitignore)
|
|-- rapport/
|   |-- rapport.tex                   # Source LaTeX
|   +-- rapport.pdf                   # Rapport academique final (25 pages)
|
|-- requirements.txt                  # Dependances Python (pandas)
+-- README.md                         # Ce fichier
```

---

## Installation

### Prerequis

- **Python 3.10+**
- **Ollama** (pour les LLMs locaux -- zero quota, gratuit, offline)
- **8 Go de RAM minimum** (16 Go recommandes pour confort)

### Etapes

```bash
# 1. Cloner le repository
git clone https://github.com/omarsoliman02/PFD-Discovery.git
cd PFD-Discovery

# 2. Installer les dependances Python
pip3 install -r requirements.txt

# 3. Installer Ollama
# Sur Mac :
brew install ollama
brew services start ollama

# Sur Linux :
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama

# 4. Telecharger les modeles LLM
ollama pull mistral        # Mistral 7B (~4.4 Go)
ollama pull llama3.1       # Llama 3.1 8B (~4.9 Go)

# 5. Verifier que tout marche
curl http://localhost:11434/api/tags
# Doit renvoyer un JSON listant mistral et llama3.1
```

### LLMs disponibles

| Modele | Type | Quota | RAM | Style |
|---|---|---|---|---|
| **Mistral 7B** | Local (Ollama) | Illimite | ~6 Go | Conservateur, precis |
| **Llama 3.1 8B** | Local (Ollama) | Illimite | ~7 Go | Creatif, diversifie |

---

## Guide d'utilisation

### 1. Approche classique

```bash
# Sur tous les datasets
python3 experiments/run_classical.py

# Les resultats sont affiches et sauvegardes dans results/
```

**Parametres ajustables** :

| Parametre | Defaut | Description |
|-----------|--------|-------------|
| `MIN_SUPPORT` | 5 | Nombre minimum de tuples dans un groupe |
| `MIN_CONFIDENCE` | 0.85 | Confidence minimum pour garder une regle |
| `MAX_PREFIX_LEN` | 4 | Longueur maximale des prefixes explores |

### 2. Workflows agentiques (W1, W2, W3)

#### W1 et W2 (Feature-Enriched et Guided Search)

```bash
# Tous les datasets, Mistral + Llama
python3 experiments/run_agentic.py

# Cibler un LLM et un dataset
python3 experiments/run_agentic.py --llm mistral --workflow 2 --dataset t1
python3 experiments/run_agentic.py --llm llama --workflow 1 --dataset t2
```

**Options** :

| Option | Valeurs | Description |
|--------|---------|-------------|
| `--llm` | `mistral`, `llama`, `all` | LLM a utiliser |
| `--dataset` | nom du fichier (ex: `t1`) | Filtrer par dataset |
| `--workflow` | `1` ou `2` | Workflow a executer |

#### W3 (Agent-in-the-Loop)

```bash
# Demo rapide sur petit dataset (~2 min)
python3 experiments/run_workflow3.py --dataset US_Phone_Code --llm mistral --iterations 2

# Vrai test sur t1.csv (~6 min)
python3 experiments/run_workflow3.py --dataset t1 --llm mistral --iterations 3
```

### 3. Analyses bonus

#### Analyse de sensibilite aux seuils

```bash
# Classique uniquement (rapide, ~2 min)
python3 experiments/sensitivity_analysis.py --dataset t1 \
  --thetas 0.85,0.90,0.95,1.00 --supports 5,10,20

# Avec workflows agentiques inclus (lent, ~30 min)
python3 experiments/sensitivity_analysis.py --dataset t1 \
  --thetas 0.85,0.95 --supports 5 --include-agentic --llm mistral
```

#### Analyse d'erreur (PFDs manquees par W2)

```bash
python3 experiments/error_analysis.py --dataset t1 --llm mistral
# Diagnostique pourquoi le LLM rate certaines PFDs parfaites
```

#### Generalisation semantique par LLM

```bash
python3 experiments/run_llm_generalization.py --dataset t1 --llm mistral
# Affiche les concepts metier formes par le LLM (au lieu de la dedup syntaxique)
```

### 4. Comparaison des approches

```bash
# Tableau recapitulatif classique vs W1 vs W2 sur un dataset
python3 experiments/compare_results.py --dataset t1 --llm mistral

# Comparer les deux LLMs
python3 experiments/compare_results.py --dataset t1 --llm all
```

**Exemple de sortie** (sur t1.csv) :

```
Approche          PFDs  Parfaites  Conf.moy  Supp.moy  Candidats  Temps(s)
------------------------------------------------------------------------------
Classique           85         2     0.913    7481.9       544     8.50
W1-Mistral          23         2     0.931    6747.4        72    70.75
W2-Mistral          19         2     0.939    5736.9        34    51.76
W3-Mistral           8         3     0.950    8500.2        17   361.40
```

---

## Datasets

### pfd_validation/ -- Datasets de validation

| Fichier | Lignes | Domaine |
|---------|--------|---------|
| `US_Phone_Code.csv` | 51 | Codes telephoniques US |
| `t1.csv` | 9 101 | Employes gouvernementaux |
| `t2.csv` | 3 502 | Entreprises commerciales |
| `t3.csv` | 1 077 | Licences commerciales |

### CHE/ -- Chimie et biologie moleculaire

| Fichier | Lignes | Domaine |
|---------|--------|---------|
| `mechanism_refs.csv` | 9 536 | References pharmaceutiques |
| `metabolism_refs.csv` | 2 409 | Metabolisme de medicaments |
| `protein_classification.csv` | 858 | Taxonomie des proteines |
| `research_companies.csv` | 812 | Entreprises pharma |
| `variant_sequences.csv` | 1 200 | Variants de sequences |

### DGOV/ -- Gouvernance de donnees

| Fichier | Lignes | Domaine |
|---------|--------|---------|
| `570-1.csv` | 9 101 | Employes gouvernementaux |
| `10492-1.csv` | 1 077 | Licences commerciales |
| `10642-1.csv` | 920 | Agences d'emploi |
| `6339-1.csv` | 306 | Statistiques de criminalite |
| `6397-1.csv` | 6 704 | Donnees demographiques |

---

## Resultats principaux

### Comparaison globale sur t1.csv (9 101 employes)

| Approche | Candidats | PFDs | Parfaites | Temps |
|---|---|---|---|---|
| Classique | 544 | 85 | 2 | 8.5 s |
| W1-Mistral | 72 | 23 | 2 | 71 s |
| W2-Mistral | 34 | 19 | 2 | 52 s |
| W2-Llama | 74 | 21 | 2 | 100 s |
| **W3-Mistral** | **17** | 8 | **3** | 361 s |

### Enseignements

- **Classique** : exhaustif et rapide, mais beaucoup de regles bruitees.
- **W1/W2** : reduction massive de l'espace de recherche (~87-94%), confidence moyenne superieure.
- **W3** : capacite d'**auto-correction** observee ; trouve plus de PFDs parfaites avec moins de candidats.
- **theta domine K** : l'analyse de sensibilite montre que la confidence minimale impacte beaucoup plus que le support minimal.
- **Prompt engineering critique** : un biais Mistral envers `identity(col)` a ete identifie puis corrige par modification du prompt.

---

## Documentation complete

| Document | Description |
|---|---|
| [`rapport/rapport.pdf`](rapport/rapport.pdf) | Rapport academique final (25 pages, 8 sections + annexes) |
| [`GUIDE_SOUTENANCE.md`](GUIDE_SOUTENANCE.md) | Guide pedagogique complet pour la soutenance (de zero a expert) |
| [`Approximate_PFDs.pdf`](Approximate_PFDs.pdf) | Specification originale du cours (40 slides du prof) |

---

## Technologies utilisees

| Technologie | Usage |
|-------------|-------|
| **Python 3.10+** | Langage principal |
| **pandas** | Manipulation de donnees CSV |
| **Ollama** | Serveur de LLMs locaux (REST API sur localhost:11434) |
| **Mistral 7B** + **Llama 3.1 8B** | LLMs locaux pour les workflows agentiques |
| **LaTeX** | Generation du rapport academique |

---

## Auteurs

- **SOLIMAN** Omar
- **DERRADJI** Fahd
- **HADDAR** Djena
- **TSOULI** Abderrahmane
- **KARAOUANE** Guillaume

## Licence

Projet academique -- Universite Paris Dauphine - PSL, 2025-2026.
