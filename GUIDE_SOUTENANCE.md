# 📘 Guide de Soutenance — PFD-Discovery

> **À lire avant la soutenance — explique le projet en partant de zéro.**
> Aucun prérequis technique nécessaire. Lis-le dans l'ordre.

---

## Table des matières

1. [À quoi sert ce projet ? (en 3 phrases)](#1-a-quoi-sert-ce-projet-en-3-phrases)
2. [Le contexte académique](#2-le-contexte-académique)
3. [Notions de base (qualité de données)](#3-notions-de-base-qualite-de-données)
4. [Des FDs aux PFDs : la grande idée](#4-des-fds-aux-pfds-la-grande-idée)
5. [Ce qu'on a vraiment fait (l'algorithme)](#5-ce-quon-a-vraiment-fait-lalgorithme)
6. [L'approche agentique (LLM)](#6-lapproche-agentique-llm)
7. [Le code en 5 minutes](#7-le-code-en-5-minutes)
8. [🚀 Comment lancer le code (pas à pas)](#8--comment-lancer-le-code-pas-à-pas)
9. [Les résultats à retenir](#9-les-résultats-à-retenir)
10. [Les 4 améliorations bonus](#10-les-4-améliorations-bonus)
11. [Questions probables du jury](#11-questions-probables-du-jury)
12. [Cheat-sheet à emporter](#12-cheat-sheet-à-emporter)

---

## 1. À quoi sert ce projet ? (en 3 phrases)

> **On a un fichier de données (CSV) qui contient des erreurs et des incohérences. On veut découvrir automatiquement les "règles cachées" qui devraient être respectées par les données. On compare deux façons de faire : une méthode mathématique classique vs une méthode "intelligente" qui utilise une IA (LLM).**

**Exemple concret** : dans un fichier d'employés, on devrait avoir la règle « code de département → nom de département » (chaque code POL correspond toujours à "Department of Police"). Si une ligne dit "POL → Department of Education", c'est probablement une erreur.

Notre projet **trouve ces règles automatiquement** sans qu'on lui dise lesquelles chercher.

---

## 2. Le contexte académique

- **Cours** : *Qualité de Données, Data Wrangling*
- **Université** : Paris Dauphine — PSL, Laboratoire LAMSADE
- **Enseignant** : Khalid Belhajjame
- **Année** : 2025–2026
- **Équipe** : Omar Soliman, Fahd Derradji, Djena Haddar, Abderrahmane Tsouli, Guillaume Karaouane
- **Document de référence** : `Approximate_PFDs.pdf` (40 slides du prof)

**Ce que demandait le prof** :
1. Implémenter un algorithme classique de découverte de PFDs (5 étapes).
2. Implémenter **au moins un** workflow agentique utilisant un LLM.
3. Faire des expériences comparatives sur les datasets fournis.
4. Rendre un rapport + faire une démo de 15 minutes.

**Ce qu'on a livré** (largement au-dessus du minimum) :
- ✅ L'algorithme classique
- ✅ **Les 3 workflows agentiques** (alors qu'un seul était requis)
- ✅ Comparaison de 2 LLMs (Mistral 7B et Llama 3.1 8B)
- ✅ Tests sur 14 datasets réels
- ✅ Rapport de 25 pages (`rapport/rapport.pdf`)
- ✅ Bonus : analyse de sensibilité, généralisation par LLM, analyse d'erreur

---

## 3. Notions de base (qualité de données)

### 3.1 C'est quoi la "qualité de données" ?

Quand on stocke des informations dans une base de données ou un fichier Excel, on aimerait qu'elles soient **propres** :
- Pas de doublons
- Pas d'incohérences (genre "Paris" écrit "Pari", "Pariis", "PARIS")
- Pas d'erreurs de saisie (un homme nommé "Susan")
- Les relations entre colonnes sont respectées (un code postal correspond à une seule ville)

La **qualité de données** est la discipline qui s'occupe de détecter et corriger ces problèmes.

### 3.2 Les Dépendances Fonctionnelles (FDs)

Une **FD** est une règle qui dit : *« si deux lignes ont la même valeur dans la colonne X, alors elles doivent avoir la même valeur dans la colonne Y »*.

On l'écrit : `X → Y`.

**Exemple** : `Département → Nom du département`

| Code | Nom |
|------|-----|
| POL  | Department of Police |
| POL  | Department of Police |
| EDU  | Department of Education |
| POL  | Department of Education ❌ |

La 4e ligne **viole** la FD : même code "POL" mais nom différent.

### 3.3 Le problème : les FDs classiques sont limitées

Les FDs comparent des **valeurs entières**. Elles ne détectent pas les régularités **partielles**.

**Exemple parlant** : dans une colonne *Prénom*, les FDs ne sauront jamais que **« John », « Johnny » et « Jonathan » commencent tous par "John" et désignent des hommes**. Pourquoi ? Parce qu'elles ne regardent que la valeur complète, pas un morceau.

---

## 4. Des FDs aux PFDs : la grande idée

### 4.1 La solution : transformer les valeurs

Au lieu de comparer "John Smith" tel quel, on **applique une transformation** :
- `first_token("John Smith")` → `"John"` (premier mot)
- `prefix("90012", 3)` → `"900"` (3 premiers caractères)
- `suffix("report.pdf", 3)` → `"pdf"` (3 derniers caractères)

Puis on cherche des dépendances sur ces **patterns** (morceaux transformés) au lieu des valeurs brutes.

### 4.2 Définition d'une PFD

Une **Pattern Functional Dependency** s'écrit :
```
R(X → Y, Tp)
```
- `R` = la table
- `X → Y` = la dépendance entre deux colonnes
- `Tp` = la transformation appliquée à `X` (le "pattern")

### 4.3 Exemples concrets

| PFD | Lecture en français |
|-----|---------------------|
| `prefix(zip, 3) → city` | Les 3 premiers chiffres d'un code postal déterminent la ville |
| `first_token(name) → gender` | Le prénom détermine le genre (John = M, Susan = F) |
| `domain(email) → organization` | Le domaine d'un email détermine l'organisation (@google.com = Google) |

### 4.4 PFDs approximatives (avec bruit)

Dans la vraie vie, **les règles ne sont jamais parfaites à 100%**. Il y a du bruit, des erreurs, des cas particuliers. On tolère donc un certain pourcentage de violations.

On définit deux métriques :

#### **Support** (`K`)
Le **nombre de lignes** qui satisfont la règle. Plus c'est gros, plus la règle est "importante".
- Une règle avec support = 9000 sur 9100 lignes est **massive**.
- Une règle avec support = 3 lignes est **anecdotique**.
- **Seuil minimum dans notre projet** : K = 5 (on ignore les règles qui couvrent < 5 lignes).

#### **Confidence** (`θ` ou theta)
Le **pourcentage de lignes cohérentes** parmi celles couvertes. C'est un score entre 0 et 1.
- Confidence = 1.0 → la règle est **parfaite** (FD classique).
- Confidence = 0.85 → 85% des cas sont cohérents, 15% violent la règle.
- **Seuil minimum dans notre projet** : θ = 0.85 (on rejette les règles trop bruitées).

#### Exemple chiffré

Sur une colonne avec 100 lignes ayant le pattern `John*` :
- 92 sont des hommes, 8 sont des femmes (probablement des erreurs)
- **Support** = 100
- **Confidence** = 92/100 = 0.92 → on **garde** la règle (0.92 ≥ 0.85)

---

## 5. Ce qu'on a vraiment fait (l'algorithme)

L'algorithme classique fait **5 étapes** (slides 9-15 du prof) :

### Étape 1 — Extraction de patterns
Pour chaque colonne, on génère plein de transformations possibles :
- `identity(col)` : valeur brute
- `prefix(col, 1)`, `prefix(col, 2)`, ..., `prefix(col, 5)` : préfixes de longueur 1 à 5
- `suffix(col, k)`
- `first_token(col)` / `last_token(col)` (premier/dernier mot)
- `numeric_prefix(col, k)` : préfixe numérique (pour codes postaux)
- `length(col)` : longueur

→ Pour `t1.csv` (9 colonnes), ça génère **~60 transformations**.

### Étape 2 — Groupement
Pour chaque transformation, on **regroupe les lignes qui ont la même valeur transformée**.

Exemple : `first_token(Name) = "John"` regroupe John Smith, John Brown, Johnny Walker.

### Étape 3 — Génération de candidats
On crée toutes les paires possibles `transformation(X) → Y` où Y est une autre colonne.

→ Sur `t1.csv` : **544 candidats** à tester.

### Étape 4 — Validation
Pour chaque candidat, on calcule :
- Le **support** (nb de lignes couvertes)
- La **confidence** (% de lignes cohérentes)

On **garde** uniquement les candidats avec `support ≥ 5` et `confidence ≥ 0.85`.

→ Sur `t1.csv` : **143 PFDs valides**.

### Étape 5 — Généralisation
Les 143 PFDs contiennent **plein de doublons** (`prefix(name, 1) → gender` et `prefix(name, 2) → gender` disent la même chose). On les **fusionne** :
- Plus court préfixe avec bonne confidence
- Subsomption (si `identity` marche, on jette les variantes)
- Déduplication par type

→ **85 PFDs généralisées** à la fin.

**Temps total** : ~8 secondes sur t1.csv.

---

## 6. L'approche agentique (LLM)

### 6.1 LLM = quoi exactement ?

Un **LLM** (Large Language Model) est une IA comme ChatGPT, qui peut comprendre des questions en français/anglais et répondre.

Dans notre projet, on utilise **Mistral 7B** et **Llama 3.1 8B** via **Ollama** (qui les fait tourner **sur la machine, sans Internet**, sans quota, sans clé API).

### 6.2 Pourquoi utiliser un LLM ?

L'algorithme classique a une **grosse faiblesse** : il teste **tout**, y compris des règles qui n'ont aucun sens. Exemple : il pourrait trouver `length(name) → gender` (la longueur du nom prédit le genre) parce que statistiquement ça matche, mais c'est **n'importe quoi sémantiquement**.

Le LLM, lui, **comprend ce que représentent les colonnes**. Si on lui montre une colonne `ZIP` avec des valeurs `90012, 90013, ...`, il sait que c'est un code postal et suggère `prefix(zip, 3) → city`.

### 6.3 Les 3 workflows agentiques

#### 🟦 Workflow 1 (W1) — Feature-Enriched Discovery
- **Le LLM suggère les transformations pertinentes** (pas toutes les 60 random).
- L'algorithme classique fait ensuite tout le reste.
- **Résultat** : on réduit l'espace de recherche de ~87%.

#### 🟩 Workflow 2 (W2) — Guided Search
- W1 + le LLM **priorise aussi les paires candidates X → Y**.
- L'algorithme ne valide que celles que le LLM juge prometteuses.
- **Résultat** : réduction de ~94% des candidats (34 au lieu de 544).

#### 🟥 Workflow 3 (W3) — Agent-in-the-Loop *(le plus avancé)*
- **Boucle itérative** : le LLM propose des hypothèses → l'algorithme les valide → renvoie un feedback structuré au LLM → le LLM raffine ses hypothèses → on recommence.
- Le LLM voit ses erreurs et **s'auto-corrige**.
- **Exemple observé** : à l'itération 0, Mistral propose `length(State) → Code` qui obtient une faible confidence. À l'itération 1, après avoir lu le feedback, il **abandonne** cette règle et propose `numeric_prefix(Code, 3) → Short` qui s'avère **parfaite** (confidence = 1.0).
- **Résultat** : 17 candidats au lieu de 544 (réduction de 97%), 3 PFDs parfaites au lieu de 2.

### 6.4 Bonus : généralisation sémantique par LLM
À l'étape 5, au lieu de juste dédupliquer mécaniquement, on demande au LLM de **regrouper les PFDs par concept métier**.

Exemple : `prefix(name, 1) → gender`, `first_token(name) → gender`, `identity(name) → gender` sont 3 PFDs syntaxiquement différentes mais expriment **toutes le même concept** : *« le prénom détermine le genre »*.

Le LLM produit alors un résumé interprétable :
> Concept : « Le code de division détermine la catégorie d'affectation »
> Représentant : `numeric_prefix(Division, 1) → Assignment Category`
> Fusionne 4 PFDs avec k=1,2,3,4

---

## 7. Le code en 5 minutes

### 7.1 Structure du dossier

```
PatternFD-miniprojet/
├── data/                         # Les 14 datasets CSV
│   ├── pfd_validation/           #   t1, t2, t3, US_Phone_Code (datasets de test)
│   ├── CHE/                      #   chimie/biologie
│   └── DGOV/                     #   gouvernance (criminalité, employés, etc.)
│
├── src/                          # Le code Python (1 479 lignes)
│   ├── data_loader.py            # Charge les CSV
│   ├── pattern_extraction.py     # Définit les 7 transformations
│   ├── pattern_grouping.py       # Étape 2 : regroupement
│   ├── candidate_generation.py   # Étape 3 : génération des candidats
│   ├── validation.py             # Étape 4 : calcul support/confidence
│   ├── generalization.py         # Étape 5 : dédup algorithmique + LLM
│   ├── classical_pipeline.py     # Orchestre les 5 étapes
│   ├── llm_agent.py              # Appels aux LLMs + 5 prompts
│   ├── agentic_workflow.py       # Workflows 1, 2, 3
│   └── evaluation.py             # Métriques, comparaison
│
├── experiments/                  # Les scripts à lancer
│   ├── run_classical.py          # Classique sur tous les datasets
│   ├── run_agentic.py            # W1 et W2
│   ├── run_workflow3.py          # W3 (nouveau)
│   ├── compare_results.py        # Comparaison côte-à-côte
│   ├── sensitivity_analysis.py   # Étude des seuils K et θ (nouveau)
│   ├── error_analysis.py         # Diagnostic Mistral W2 (nouveau)
│   └── run_llm_generalization.py # Généralisation LLM (nouveau)
│
├── results/                      # JSON sauvegardés (ignoré par git)
├── rapport/
│   ├── rapport.tex               # Source LaTeX
│   └── rapport.pdf               # ⭐ Le rapport final, 25 pages
├── Approximate_PFDs.pdf          # L'énoncé du prof
└── README.md
```

### 7.2 Comment ça marche en pratique

```bash
# Installation
pip install -r requirements.txt
ollama pull mistral && ollama pull llama3.1

# Lancer le classique sur tous les datasets
python3 experiments/run_classical.py

# Lancer les workflows agentiques
python3 experiments/run_agentic.py --llm mistral --dataset t1
python3 experiments/run_workflow3.py --dataset t1 --llm mistral

# Analyses bonus
python3 experiments/sensitivity_analysis.py --dataset t1
python3 experiments/error_analysis.py --dataset t1 --llm mistral
```

### 7.3 Le fichier le plus important : `agentic_workflow.py`

Trois fonctions :
- `workflow1_feature_enriched(df, llm_name, ...)` → W1
- `workflow2_guided_search(df, llm_name, ...)` → W2
- `workflow3_agent_in_the_loop(df, llm_name, ..., max_iterations=3)` → W3

Chacune retourne un dictionnaire avec :
- `pfds` : la liste des PFDs trouvées
- `generalized` : après l'étape 5
- `execution_time`, `num_candidates`, etc.

---

## 8. 🚀 Comment lancer le code (pas à pas)

> Cette section te permet de **lancer toutes les expériences** depuis zéro, sur un Mac ou Linux. Si jamais le jury demande une démo live, suis ces étapes dans l'ordre.

### 8.1 Prérequis matériel

- **OS** : macOS ou Linux (Windows : utilise WSL2)
- **RAM** : 8 Go minimum, 16 Go recommandés (les LLMs prennent ~5-7 Go en mémoire)
- **Disque** : ~10 Go libres (les 2 modèles LLM font ~9 Go cumulés)
- **CPU** : tout CPU moderne suffit (M1/M2/M3 Mac très confortable, sinon Intel/AMD récent)
- **GPU** : pas nécessaire, Ollama tourne très bien sur CPU

### 8.2 Installation (5 étapes)

#### Étape 1 — Cloner le projet
```bash
git clone https://github.com/omarsoliman02/PFD-Discovery.git
cd PFD-Discovery
```

#### Étape 2 — Vérifier Python 3.10+
```bash
python3 --version
# Si tu vois "Python 3.10.x" ou plus, tu es bon
# Sinon : brew install python@3.11 (Mac) ou sudo apt install python3.11 (Linux)
```

#### Étape 3 — Installer les dépendances Python
```bash
pip3 install -r requirements.txt
# Installe pandas (le seul vrai requis, le reste est dans la stdlib Python)
```

#### Étape 4 — Installer Ollama (les LLMs locaux)
```bash
# Sur Mac avec Homebrew :
brew install ollama
brew services start ollama   # Démarre Ollama en arrière-plan

# Sur Linux :
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama
```

#### Étape 5 — Télécharger les 2 modèles LLM
```bash
ollama pull mistral       # ~4.4 Go, prend 5-10 min selon la connexion
ollama pull llama3.1      # ~4.9 Go, idem
```

### 8.3 Vérifier que tout marche

#### Tester Ollama
```bash
curl http://localhost:11434/api/tags
# Doit renvoyer un JSON listant "mistral" et "llama3.1"
```

#### Tester l'import des modules Python
```bash
python3 -c "from src.agentic_workflow import workflow3_agent_in_the_loop; print('OK')"
# Doit afficher : OK
```

### 8.4 Lancer le pipeline classique

#### Sur tous les datasets (env. 2 minutes)
```bash
python3 experiments/run_classical.py
```
**Sortie attendue** : pour chaque dataset, le nombre de PFDs trouvées, le temps d'exécution. Les résultats JSON sont sauvegardés dans `results/`.

#### Sur un seul dataset (ex : t1.csv)
```bash
python3 -c "
from src.data_loader import load_csv
from src.classical_pipeline import run_classical_pipeline
df = load_csv('data/pfd_validation/t1.csv')
run_classical_pipeline(df, min_support=5, min_confidence=0.85)
"
```

### 8.5 Lancer les workflows agentiques

> ⚠️ **Plus lent** : chaque appel LLM prend 10-60 secondes selon le modèle et le dataset.

#### W1 + W2 sur tous les datasets, avec Mistral et Llama (env. 30-60 min)
```bash
python3 experiments/run_agentic.py
```

#### W1 ou W2 seul, sur un seul dataset (recommandé pour démo)
```bash
# W1 avec Mistral sur t1
python3 experiments/run_agentic.py --llm mistral --workflow 1 --dataset t1

# W2 avec Llama sur t2
python3 experiments/run_agentic.py --llm llama --workflow 2 --dataset t2
```

#### W3 (Agent-in-the-Loop) — le plus impressionnant pour la démo
```bash
# Petit dataset pour démo rapide (~2 minutes)
python3 experiments/run_workflow3.py --dataset US_Phone_Code --llm mistral --iterations 2

# Vrai test sur t1 (~6 minutes)
python3 experiments/run_workflow3.py --dataset t1 --llm mistral --iterations 3
```

#### Comparaison côte-à-côte classique + W1 + W2 (idéal pour la soutenance)
```bash
python3 experiments/compare_results.py --dataset t1 --llm mistral
# Affiche un tableau récapitulatif final
```

### 8.6 Lancer les analyses bonus (les 4 améliorations)

#### Analyse de sensibilité aux seuils K et θ
```bash
# Test rapide sur t1 (classique uniquement, ~2 minutes)
python3 experiments/sensitivity_analysis.py --dataset t1 \
  --thetas 0.85,0.90,0.95,1.00 --supports 5,10,20

# Avec workflows agentiques inclus (lent, ~30 minutes)
python3 experiments/sensitivity_analysis.py --dataset t1 \
  --thetas 0.85,0.95 --supports 5 --include-agentic --llm mistral
```

#### Analyse d'erreur Mistral W2
```bash
python3 experiments/error_analysis.py --dataset t1 --llm mistral
# Identifie les PFDs parfaites manquées par W2 et explique pourquoi
```

#### Généralisation sémantique par LLM
```bash
python3 experiments/run_llm_generalization.py --dataset t1 --llm mistral
# Affiche les concepts métier formés par le LLM
```

### 8.7 Compiler le rapport LaTeX (si besoin)

```bash
cd rapport
pdflatex -interaction=nonstopmode rapport.tex
pdflatex -interaction=nonstopmode rapport.tex   # 2e passe pour les références
# Le rapport.pdf est généré (25 pages)
```

### 8.8 Démo recommandée pour la soutenance (5 minutes chrono)

Voici une séquence de commandes à lancer **en live** devant le jury :

```bash
# 1. Montrer le classique (rapide, ~10s)
python3 experiments/run_classical.py 2>&1 | head -30

# 2. Montrer W2 sur t1 (rapide ~1 min)
python3 experiments/run_agentic.py --llm mistral --workflow 2 --dataset t1

# 3. Montrer W3 sur US_Phone_Code (impressionnant, ~2 min)
python3 experiments/run_workflow3.py --dataset US_Phone_Code --llm mistral --iterations 2
# → fait apparaître l'auto-correction !

# 4. Montrer le tableau de comparaison final
python3 experiments/compare_results.py --dataset t1 --llm mistral
```

### 8.9 Troubleshooting (problèmes fréquents)

| Problème | Cause | Solution |
|---|---|---|
| `ConnectionRefusedError` | Ollama n'est pas démarré | `brew services start ollama` (Mac) ou `sudo systemctl start ollama` |
| `model 'mistral' not found` | Modèle non téléchargé | `ollama pull mistral` |
| `TimeoutError` après 600s | LLM trop lent sur ce dataset | Réduire la taille du dataset ou utiliser `--llm llama` (plus rapide) |
| `ModuleNotFoundError: pandas` | Dépendances manquantes | `pip3 install -r requirements.txt` |
| Hallucinations LLM (colonnes inventées) | Prompt insuffisant | Notre code rejette automatiquement les hypothèses invalides — c'est normal |
| W3 trouve 0 PFDs | LLM trop "créatif", n'utilise pas les vrais noms de colonnes | Relancer (la température est à 0.1 mais reste un peu aléatoire) |
| Latex `! LaTeX Error: File ... not found` | Package LaTeX manquant | `brew install --cask mactex` (Mac) ou `sudo apt install texlive-full` |

### 8.10 Où trouver les résultats

Après exécution, les résultats sont dans :
- `results/*.json` : un fichier par approche/dataset avec horodatage (ex : `workflow3_mistral_t1_20260527_144627.json`)
- Le terminal affiche aussi un résumé en sortie standard
- Le rapport LaTeX final est dans `rapport/rapport.pdf` (25 pages)

---

## 9. Les résultats à retenir

### 9.1 Tableau magique à mémoriser

Sur **t1.csv** (9 101 employés gouvernementaux) :

| Approche | Candidats explorés | PFDs trouvées | PFDs parfaites | Temps |
|---|---|---|---|---|
| **Classique** | 544 | 85 | 2 | **8.5 s** |
| W1-Mistral | 72 | 23 | 2 | 71 s |
| W2-Mistral | 34 | 19 | 2 | 52 s |
| W2-Llama | 74 | 21 | 2 | 100 s |
| **W3-Mistral** | **17** | 8 | **3** | 361 s |

### 9.2 Les 3 phrases à retenir

1. **Classique** = exhaustif (trouve tout), rapide (~8s), mais bruité (beaucoup de PFDs sans sens).
2. **Agentique W1/W2** = précis (PFDs sémantiquement pertinentes), plus lent à cause des appels LLM (~1 min).
3. **W3** = capacité d'**auto-correction** observée — le LLM voit ses erreurs et propose des alternatives ; trouve les meilleures PFDs avec le moins de candidats explorés (réduction 97%).

### 9.3 Mistral vs Llama

| Critère | Mistral 7B | Llama 3.1 8B |
|---|---|---|
| Style | **Conservateur**, précis | **Créatif**, diversifié |
| Réponses JSON | Plus fiables | Parfois verbeux |
| Confidence moyenne | 0.939 | 0.934 |
| Temps moyen | ~61 s | ~81 s |

---

## 10. Les 4 améliorations bonus

Le rapport contient 4 sections "au-dessus du minimum requis" :

### 10.1 Workflow 3 (Agent-in-the-Loop)
Le prof demandait UN workflow. On en a fait TROIS. Le W3 démontre l'**auto-correction** par feedback.

### 10.2 Analyse de sensibilité
On a testé 12 combinaisons de seuils (K ∈ {5, 10, 20} × θ ∈ {0.85, 0.90, 0.95, 1.0}).

**Découverte** : `θ` domine totalement `K`. Passer de θ=0.85 à θ=0.95 fait passer de **85 à 16 PFDs**. K ne change quasiment rien.

### 10.3 Généralisation sémantique par LLM
Au lieu de la dédup mécanique, on demande au LLM de regrouper en **concepts métier nommés**. Résultat : 30 PFDs → **10 concepts** interprétables.

### 10.4 Analyse d'erreur Mistral W2
On a découvert que **W2-Mistral ratait les 2 PFDs parfaites** trouvées par le classique. On a écrit un script qui diagnostique automatiquement la cause :
- Soit la transformation n'a pas été suggérée
- Soit la paire X→Y n'a pas été priorisée
- Soit elle a été filtrée par les seuils

**Cause trouvée** : Mistral interprétait `identity(col)` comme "trivial" et l'évitait. **Fix** : on a ajouté une instruction explicite dans le prompt. **Résultat** : les 2 PFDs parfaites sont maintenant retrouvées.

---

## 11. Questions probables du jury

### Q1 : « Quelle est la différence entre une FD et une PFD ? »
**Réponse** : La FD compare les valeurs entières (`name → gender` ne marche pas car chaque nom est unique). La PFD transforme d'abord la valeur (`first_token(name) → gender` regroupe John Smith et John Brown sous "John" et trouve une régularité).

### Q2 : « Pourquoi avoir choisi des LLMs locaux ? »
**Réponse** : Trois raisons : (1) **gratuité** (pas de quota OpenAI), (2) **reproductibilité** (pas de dépendance à un service cloud qui peut changer), (3) **confidentialité** (les données ne quittent pas la machine — important en qualité de données réelles).

### Q3 : « Pourquoi 0.85 comme seuil de confidence ? »
**Réponse** : C'est un compromis classique en data mining. Trop bas (0.5) → beaucoup de bruit ; trop haut (0.99) → on rate les règles approximatives intéressantes. Notre **analyse de sensibilité** (section 6.6 du rapport) montre qu'à 0.95 on garde 16 PFDs au lieu de 85, ce qui est plus strict mais perd des règles utiles.

### Q4 : « Le LLM hallucine, c'est un problème ? »
**Réponse** : Oui, on l'a observé. Sur le petit dataset `US_Phone_Code`, Mistral a halluciné des noms de colonnes inexistants à la première version du prompt. On a corrigé en ajoutant une **règle critique dans le prompt** : *« tu DOIS utiliser EXACTEMENT les noms de colonnes ci-dessus »*. Notre code **valide** ensuite chaque hypothèse contre le vrai schéma, donc même si le LLM hallucine, on rejette les règles invalides.

### Q5 : « Combien de temps prend votre approche agentique ? »
**Réponse** : 50 à 100 secondes pour W1/W2, environ 6 minutes pour W3 (à cause des 3 itérations). Le classique fait 8 secondes. Mais c'est un compromis : on échange du temps contre de la **qualité sémantique** et de l'**interprétabilité** (chaque suggestion du LLM est justifiée en langage naturel).

### Q6 : « Vous avez quoi comme datasets ? »
**Réponse** : 14 fichiers CSV pour 46 351 lignes au total :
- 4 datasets de validation (US_Phone_Code, t1, t2, t3) — fournis par le prof
- 5 datasets de chimie/biologie (CHE/)
- 5 datasets de gouvernance (DGOV/ — employés gouvernementaux, criminalité, etc.)

### Q7 : « C'est quoi cette histoire de "auto-correction" de W3 ? »
**Réponse** : C'est l'exemple observé sur US_Phone_Code :
1. Itération 0 : Mistral propose `length(State) → Code`. L'algorithme valide et trouve une faible confidence.
2. Itération 1 : Mistral reçoit ce feedback ("ta règle est faible") et **abandonne `length`**, propose à la place `numeric_prefix(Code, 3) → Short`.
3. Cette nouvelle règle s'avère **parfaite** (confidence = 1.0).

C'est exactement ce que demandait l'approche **Agent-in-the-Loop** des slides du prof (slide 31-34).

### Q8 : « Pourquoi pas un seul script de bout en bout ? »
**Réponse** : Modularité. Chaque module (extraction, validation, généralisation) est testable indépendamment. On peut combiner classique + LLM librement. Et chaque expérience (sensibilité, erreur, W3) a son propre script dédié pour reproductibilité.

### Q9 : « Si on enlève le seuil K (support), que se passe-t-il ? »
**Réponse** : On garderait des règles "anecdotiques" qui tiennent sur 2-3 lignes par chance. Notre analyse montre que **K a moins d'impact que θ** : passer K de 5 à 20 ne change presque rien (85 → 85 PFDs sur t1.csv), parce que la plupart des PFDs intéressantes ont déjà un support massif (~9000).

### Q10 : « Concrètement, à quoi ça sert en entreprise ? »
**Réponse** : Trois usages :
1. **Détection d'erreurs** : si une règle a confidence=0.95, les 5% qui violent sont probablement des fautes de saisie à corriger.
2. **Nettoyage de données (data cleaning)** : on peut utiliser les PFDs pour normaliser les valeurs (ex : tous les "Pariis" deviennent "Paris").
3. **Documentation automatique** : les PFDs forment une documentation lisible des contraintes implicites du dataset.

---

## 12. Cheat-sheet à emporter

### Définitions à savoir réciter
- **FD** : `X → Y` strict, valeurs entières
- **PFD** : `R(X → Y, Tp)`, Tp est une transformation
- **Support** : nombre de lignes couvertes (seuil K=5)
- **Confidence** : % de lignes cohérentes (seuil θ=0.85)
- **Approximative** : on tolère un peu de bruit (confidence < 1.0)

### Les 7 transformations
1. `identity(col)` — valeur brute
2. `prefix(col, k)` — k premiers caractères
3. `suffix(col, k)` — k derniers caractères
4. `first_token(col)` — premier mot
5. `last_token(col)` — dernier mot
6. `numeric_prefix(col, k)` — k premiers chiffres
7. `length(col)` — longueur

### Pipeline classique = 5 étapes
1. Extraction → 2. Groupement → 3. Candidats → 4. Validation → 5. Généralisation

### Les 3 workflows
- **W1** : LLM suggère les transformations
- **W2** : W1 + LLM priorise les candidats
- **W3** : boucle itérative LLM ↔ algorithme avec feedback

### Chiffre choc à sortir
> *« Sur t1.csv (9 101 lignes), notre Workflow 3 trouve 3 PFDs parfaites en n'explorant que 17 candidats, contre 544 candidats pour l'approche classique qui n'en trouve que 2 parfaites. Soit une réduction de 97% de l'espace de recherche tout en améliorant la qualité. »*

### Outils
- Python 3.10+, pandas
- Ollama (REST API sur localhost:11434)
- Mistral 7B (4.4 Go), Llama 3.1 8B (4.9 Go)
- LaTeX pour le rapport (25 pages)

### Liens utiles
- 📄 Le rapport : `rapport/rapport.pdf`
- 🐍 Le code : dossier `src/`
- 📊 Les résultats JSON : dossier `results/`
- 🌐 GitHub : [github.com/omarsoliman02/PFD-Discovery](https://github.com/omarsoliman02/PFD-Discovery)

---

## ✅ Récap final en une phrase

> **Notre projet implémente automatiquement la découverte de règles cachées dans des fichiers de données, en comparant une approche mathématique classique (rapide mais bruitée) à une approche IA agentique (3 workflows utilisant des LLMs locaux, plus lente mais sémantiquement pertinente), et démontre que la boucle itérative LLM-algorithme (W3) permet à l'IA de s'auto-corriger pour trouver les meilleures règles avec un minimum d'exploration.**

Bonne soutenance ! 🎓
