# 🎓 Le cours PFD expliqué de zéro

> **Pour quelqu'un qui n'a jamais entendu parler de qualité de données, FD ou PFD.**
> On va construire la compréhension brique par brique, sans jargon, avec plein d'exemples.

---

## Sommaire

1. [C'est quoi une base de données ? (avant même de parler de qualité)](#1-cest-quoi-une-base-de-données)
2. [La qualité de données, c'est quoi le problème ?](#2-la-qualité-de-données-cest-quoi-le-problème)
3. [Les "règles" qu'on aimerait dans les données](#3-les-règles-quon-aimerait-dans-les-données)
4. [Les Dépendances Fonctionnelles (FDs) — l'outil de base](#4-les-dépendances-fonctionnelles-fds)
5. [Pourquoi les FDs ne suffisent pas](#5-pourquoi-les-fds-ne-suffisent-pas)
6. [Les Pattern Functional Dependencies (PFDs) — la grande idée](#6-les-pattern-functional-dependencies-pfds)
7. [Approximatif = on tolère un peu d'erreur](#7-approximatif--on-tolère-un-peu-derreur)
8. [Comment "découvrir" les PFDs ? (le pipeline)](#8-comment-découvrir-les-pfds-le-pipeline)
9. [Pourquoi c'est dur et pourquoi l'IA peut aider](#9-pourquoi-cest-dur-et-pourquoi-lia-peut-aider)
10. [À quoi ça sert dans la vraie vie](#10-à-quoi-ça-sert-dans-la-vraie-vie)
11. [Quiz récapitulatif (corrigé)](#11-quiz-récapitulatif)

---

## 1. C'est quoi une base de données ?

**Imagine un tableur Excel**. Voilà, c'est ça.

Une **base de données** (ou plus simplement, une "table") c'est juste un tableau avec :
- Des **lignes** (chacune représente UN truc : une personne, une commande, un produit...)
- Des **colonnes** (chacune décrit UN aspect : nom, âge, prix...)

Exemple — une table d'employés :

| Nom         | Genre | Département | Code département |
|-------------|-------|-------------|------------------|
| John Smith  | M     | Police      | POL              |
| Sarah Brown | F     | Éducation   | EDU              |
| Mike Jones  | M     | Police      | POL              |
| Lisa Davis  | F     | Santé       | SAN              |

**Vocabulaire savant** (utile pour la soutenance mais c'est tout) :
- Une **ligne** s'appelle un **tuple** ou un **enregistrement**
- Une **colonne** s'appelle un **attribut**
- L'ensemble s'appelle une **relation** (notée `R`)

Note : dans le cours, on note `R(X → Y, Tp)`. Le `R`, c'est juste le nom de cette table. Rien de plus mystérieux.

---

## 2. La qualité de données, c'est quoi le problème ?

Quand on **saisit** des données dans un système (formulaire web, base RH, etc.), il y a **toujours des erreurs** :
- Fautes de frappe : "Pariss" au lieu de "Paris"
- Incohérences : "POL" et "POLICE" pour le même département
- Valeurs manquantes
- Erreurs d'attribution : un homme nommé "Sarah" (probablement une erreur de saisie)

### Exemple parlant

Imagine la table d'employés :

| Nom         | Genre |
|-------------|-------|
| John Smith  | M     |
| Sarah Brown | F     |
| Mike Jones  | M     |
| **Sarah Clark** | **M** ← erreur ? |

L'œil humain remarque tout de suite que **"Sarah" est habituellement un prénom féminin**. Mais la machine, elle, ne sait pas. Sauf si on lui apprend.

### La question centrale du cours

> **Comment apprendre automatiquement à une machine les "règles cachées" qu'on aimerait voir respectées dans les données ?**

Ces règles permettront :
1. De **détecter** les erreurs (la ligne "Sarah Clark / M" est suspecte)
2. De **corriger** les erreurs (probablement "Sarah Clark / F")
3. De **documenter** la base (on sait ce qui est censé être respecté)

---

## 3. Les "règles" qu'on aimerait dans les données

Imagine que tu es chef d'équipe et que tu donnes des consignes à tes employés saisissant les données :

> *« Faites attention : si deux personnes sont dans le même département, le nom du département doit toujours être écrit pareil. Et si quelqu'un a le code POL, ça doit toujours être le département "Police". »*

Ces **consignes** sont en fait des **règles** sur les données. En informatique, on les appelle des **contraintes d'intégrité**.

Les **dépendances fonctionnelles** (FDs) sont une manière mathématique d'exprimer ces consignes.

---

## 4. Les Dépendances Fonctionnelles (FDs)

### 4.1 Définition (simple)

Une **FD** dit ceci :
> *« Si deux lignes ont la même valeur dans la colonne X, alors elles DOIVENT avoir la même valeur dans la colonne Y. »*

On note ça : **`X → Y`** (qui se lit "X détermine Y").

### 4.2 Exemple basique

Table :

| Code département | Nom département |
|------------------|-----------------|
| POL              | Police          |
| EDU              | Éducation       |
| POL              | Police          |
| SAN              | Santé           |
| EDU              | Éducation       |

**Question** : la FD `Code département → Nom département` est-elle respectée ?

**Méthode pour vérifier** : on regarde toutes les paires de lignes qui ont la même valeur dans la colonne X, et on regarde si elles ont aussi la même valeur dans Y.
- Lignes 1 et 3 : même code "POL", même nom "Police" ✅
- Lignes 2 et 5 : même code "EDU", même nom "Éducation" ✅
- Pas d'autres paires avec même X

→ **OUI**, la FD est respectée.

### 4.3 Contre-exemple

| Code département | Nom département |
|------------------|-----------------|
| POL              | Police          |
| EDU              | Éducation       |
| POL              | **Police Dept** ← incohérence |
| SAN              | Santé           |

Lignes 1 et 3 : même code "POL", mais noms différents ("Police" vs "Police Dept") ❌

→ **NON**, la FD `Code → Nom` est violée.

### 4.4 Plein d'exemples de FDs dans la vraie vie

| FD | Lecture humaine |
|----|-----------------|
| `Numéro_de_sécu → Nom` | Chaque numéro de sécu correspond à une seule personne |
| `ISBN → Titre_livre` | Chaque ISBN désigne un seul livre |
| `Code_pays → Nom_pays` | "FR" = "France", toujours |
| `Email → Utilisateur` | Une adresse email = un utilisateur unique |

### 4.5 Notation formelle (pour faire savant en soutenance)

Officiellement :
> Soit $R$ une relation. Une FD $X \to Y$ tient sur $R$ si :
> $$\forall t_1, t_2 \in R : t_1[X] = t_2[X] \Rightarrow t_1[Y] = t_2[Y]$$

Traduction :
- $\forall$ = "pour toutes"
- $t_1, t_2 \in R$ = "deux lignes de la table"
- $t_1[X] = t_2[X]$ = "ont la même valeur dans X"
- $\Rightarrow$ = "alors"
- $t_1[Y] = t_2[Y]$ = "elles ont la même valeur dans Y"

Donc : *« Pour toute paire de lignes, si elles sont d'accord sur X, elles doivent être d'accord sur Y. »*

---

## 5. Pourquoi les FDs ne suffisent pas

C'est ici qu'arrive le **gros problème** que le cours essaie de résoudre.

### 5.1 Le piège : les FDs comparent des valeurs ENTIÈRES

Reprenons la table d'employés :

| Nom         | Genre |
|-------------|-------|
| John Smith  | M     |
| John Brown  | M     |
| John Taylor | M     |
| Susan Miller| F     |
| Susan Clark | **M** ← suspect |

Question : est-ce que la FD `Nom → Genre` est respectée ?

**Méthode** : trouver deux lignes avec même valeur de "Nom"...
- John Smith ≠ John Brown ≠ John Taylor (différentes valeurs entières)
- Susan Miller ≠ Susan Clark (différentes valeurs entières)

→ **Personne n'a le même nom complet**, donc la FD `Nom → Genre` est **techniquement respectée** (par défaut).

**Pourtant**, l'œil humain voit clairement que "Susan Clark / M" est probablement une erreur (les "Susan" sont normalement des femmes).

### 5.2 Le constat

> Les FDs **regardent la valeur entière** et ratent les **régularités partielles**.

L'œil humain, lui, sait "découper" :
- "John Smith" → premier mot = "John" → prénom masculin
- "Susan Miller" → premier mot = "Susan" → prénom féminin

C'est cette **idée de découpage** qui mène aux PFDs.

---

## 6. Les Pattern Functional Dependencies (PFDs)

### 6.1 L'idée centrale

> Au lieu de comparer les valeurs **entières**, on les **transforme d'abord**, puis on compare les morceaux transformés.

Exemple : au lieu de comparer "John Smith" vs "John Brown", on compare :
- `first_token("John Smith")` = `"John"`
- `first_token("John Brown")` = `"John"`

Maintenant c'est la **même chose** ! Et on peut écrire la règle :

```
first_token(Nom) → Genre
```

Qui se lit : *« Le premier mot du nom détermine le genre. »*

### 6.2 Les transformations classiques (= les "patterns")

| Transformation | Que fait-elle ? | Exemple |
|---|---|---|
| `identity(col)` | Valeur brute (ne change rien) | `identity("Paris")` = `"Paris"` |
| `prefix(col, k)` | k premiers caractères | `prefix("90012", 3)` = `"900"` |
| `suffix(col, k)` | k derniers caractères | `suffix("report.pdf", 3)` = `"pdf"` |
| `first_token(col)` | Premier mot | `first_token("John Smith")` = `"John"` |
| `last_token(col)` | Dernier mot | `last_token("John Smith")` = `"Smith"` |
| `numeric_prefix(col, k)` | k premiers **chiffres** | `numeric_prefix("ZIP-90012", 3)` = `"900"` |
| `length(col)` | Longueur de la chaîne | `length("Hello")` = `"5"` |

### 6.3 Définition formelle d'une PFD

Une PFD s'écrit :

$$R(X \to Y, T_p)$$

avec :
- `R` = la table
- `X → Y` = la dépendance (entre deux colonnes)
- `T_p` = la **transformation** appliquée à X (le "pattern")

**Sémantique** :
> Deux lignes qui ont le **même pattern** sur X doivent avoir la **même valeur** sur Y.

Mathématiquement :
$$\forall t_1, t_2 \in R : T_p(t_1[X]) = T_p(t_2[X]) \Rightarrow t_1[Y] = t_2[Y]$$

### 6.4 Le "pattern tableau" T_p

Dans le cours, le prof parle de **pattern tableau** `T_p`. C'est juste **la liste des règles de pattern** qu'on applique.

**Cas simple** : `T_p` est une seule transformation, par exemple `first_token`.

**Cas général** (théorique) : `T_p` peut être plusieurs patterns différents combinés. Par exemple :
- "John*" → masculin
- "Susan*" → féminin

Le `*` veut dire "n'importe quoi après". Donc :
- "John Smith" matche le pattern "John*"
- "John Brown" matche le pattern "John*"
- "Susan Miller" matche le pattern "Susan*"

Dans notre projet (et la pratique), on simplifie : on utilise une **seule transformation par PFD** (`first_token`, `prefix(3)`, etc.).

### 6.5 Exemples de PFDs

| PFD | Lecture humaine |
|-----|-----------------|
| `first_token(Nom) → Genre` | Le prénom détermine le genre |
| `prefix(ZIP, 3) → Ville` | Les 3 premiers chiffres du code postal déterminent la ville |
| `domain(Email) → Organisation` | Le domaine email détermine l'organisation |
| `prefix(ISBN, 3) → Pays_éditeur` | Les 3 premiers chiffres ISBN identifient le pays |
| `first_token(Adresse) → Type_voie` | "rue", "avenue", "boulevard"... |

### 6.6 Pourquoi c'est mieux que les FDs ?

Les FDs ratent les régularités au niveau des **morceaux**. Les PFDs les capturent.

| Donnée | FD `Nom → Genre` | PFD `first_token(Nom) → Genre` |
|---|---|---|
| Détecte que "John*" sont masculins | ❌ | ✅ |
| Détecte que "Susan Clark / M" est suspect | ❌ | ✅ |
| Marche sur des données nettoyées parfaitement | ✅ | ✅ |

### 6.7 PFDs des deux côtés (théoriquement)

Le cours mentionne qu'on pourrait avoir :

$$\text{pattern}(X) \to \text{pattern}(Y)$$

avec une transformation aussi sur Y. Par exemple : `prefix(ZIP, 3) → prefix(Ville, 5)`.

**En pratique on ne le fait pas** parce que c'est moins intuitif et moins utile pour la qualité de données. On garde `pattern(X) → Y` (seulement le côté gauche transformé).

---

## 7. Approximatif = on tolère un peu d'erreur

### 7.1 Le problème : les données réelles ont du bruit

Reprenons :

| Nom         | Genre |
|-------------|-------|
| John Smith  | M     |
| John Brown  | M     |
| John Taylor | M     |
| Susan Miller| F     |
| Susan Clark | **M** ← anomalie |

La PFD `first_token(Nom) → Genre` est-elle **strictement vraie** ?

- "John" → 3 fois "M" ✅
- "Susan" → 1 fois "F" + 1 fois "M" ❌

→ Strictement, la PFD est **violée** par la ligne 5.

Mais on aimerait **garder cette règle** parce que c'est ÇA qu'on cherche : la règle "normale" est correcte, la ligne 5 est probablement une erreur.

### 7.2 La solution : tolérer un pourcentage d'erreur

On définit **deux métriques** pour mesurer la qualité d'une PFD.

#### Métrique 1 : Support

> Le **nombre de lignes** couvertes par la règle.

Plus c'est gros, plus la règle est "importante" / "statistiquement significative".

**Exemple** : Pour `first_token(Nom) → Genre` sur la table ci-dessus :
- Toutes les 5 lignes ont un pattern (John×3 + Susan×2)
- **Support = 5**

Une règle qui ne couvre que 2 lignes est faible. Une règle qui couvre 9000 lignes est forte.

**Seuil dans le projet** : on ne garde que les règles avec **support ≥ K** (par défaut K=5).

#### Métrique 2 : Confidence

> Le **pourcentage de lignes cohérentes** parmi celles couvertes.

C'est un nombre entre 0 et 1.

**Comment calculer** :
1. Regrouper les lignes par valeur de pattern
2. Dans chaque groupe, trouver la valeur Y **majoritaire**
3. Compter combien de lignes sont cohérentes (ont la valeur majoritaire)
4. Diviser par le total

**Exemple détaillé** :

Groupes par `first_token(Nom)` :
- Groupe "John" : [Smith→M, Brown→M, Taylor→M]
  - Y majoritaire = "M"
  - Cohérent = 3 (toutes les lignes)
- Groupe "Susan" : [Miller→F, Clark→M]
  - Y majoritaire = "F" (ou "M", c'est ex æquo... mais bon, disons "F")
  - Cohérent = 1 (seulement Miller)

**Total** = 3 + 2 = 5 lignes couvertes
**Cohérent** = 3 + 1 = 4 lignes cohérentes
**Confidence** = 4/5 = **0.8** (= 80%)

**Seuil dans le projet** : on ne garde que les règles avec **confidence ≥ θ** (par défaut θ=0.85, c'est-à-dire 85% cohérent).

#### Métrique 3 : Noise (bruit)

> Simplement `1 - confidence`. Le **taux d'erreur** toléré.

Si confidence = 0.85, le noise = 0.15 (15% de lignes peuvent violer la règle).

### 7.3 Exemple complet de calcul

Table :

| ID | Prénom | Genre |
|----|--------|-------|
| 1  | John   | M     |
| 2  | John   | M     |
| 3  | John   | M     |
| 4  | John   | F     | ← erreur ?
| 5  | Susan  | F     |
| 6  | Susan  | F     |
| 7  | Mike   | M     |

**Question** : la PFD `identity(Prénom) → Genre` est-elle valide avec K=2, θ=0.85 ?

**Calcul** :
1. Grouper par Prénom :
   - "John" : 3 fois M + 1 fois F → majoritaire = M, cohérent = 3
   - "Susan" : 2 fois F → majoritaire = F, cohérent = 2
   - "Mike" : 1 fois M → groupe de taille 1, **on l'élimine** car < K=2
2. Lignes couvertes (après filtre K=2) : 4 (John) + 2 (Susan) = **6**
3. Lignes cohérentes : 3 (John) + 2 (Susan) = **5**
4. **Confidence** = 5/6 ≈ **0.83**

**Décision** : 0.83 < 0.85 = θ → la PFD est **rejetée**.

Si on avait `identity(Prénom) → Genre` avec aucune erreur sur John (4 fois M), on aurait confidence = 6/6 = 1.0 = PFD parfaite.

### 7.4 PFD approximative en formule

Officiellement :

$$\text{support}(X) = |\{t \in R : t \models X\}|$$

$$\text{conf}(X \to Y) = \frac{|\{t \in R : t \models X \land t \models Y\}|}{|\{t \in R : t \models X\}|}$$

$$\text{noise} = 1 - \text{conf}(X \to Y)$$

Décodage :
- `t ⊨ X` = la ligne `t` satisfait le pattern X
- Support = nombre de lignes satisfaisant le pattern
- Confidence = fraction de lignes "cohérentes" (la majorité Y dans leur groupe)

---

## 8. Comment "découvrir" les PFDs ? Le pipeline

### 8.1 Le problème de la découverte

Si quelqu'un te donne une **PFD candidate** ("est-ce que `first_token(Nom) → Genre` tient ?"), tu peux la vérifier en calculant son support et sa confidence.

**Mais** : si on te donne juste une table SANS savoir quelles règles chercher, comment trouves-tu toutes les PFDs intéressantes ?

C'est le **problème de découverte** (PFD discovery).

### 8.2 Approche naïve

Tu essaies **toutes** les combinaisons possibles :
- Toutes les transformations sur toutes les colonnes
- Toutes les paires `(transformation_X, colonne_Y)`
- Pour chaque, tu calcules support et confidence

Et tu gardes celles qui passent les seuils.

C'est exactement ce que fait notre **pipeline en 5 étapes**.

### 8.3 Le pipeline (5 étapes)

```
   CSV brut
     │
     ▼
┌────────────────────────────────┐
│ Étape 1 : Extraction           │  Générer toutes les transformations
│ → 60 transformations possibles │  possibles pour chaque colonne
└────────────────────────────────┘
     │
     ▼
┌────────────────────────────────┐
│ Étape 2 : Groupement           │  Pour chaque transformation,
│ → groupes par pattern          │  regrouper les lignes
└────────────────────────────────┘
     │
     ▼
┌────────────────────────────────┐
│ Étape 3 : Candidats            │  Croiser transformations × colonnes Y
│ → 500 candidats X → Y          │  → toutes les paires possibles
└────────────────────────────────┘
     │
     ▼
┌────────────────────────────────┐
│ Étape 4 : Validation           │  Pour chaque candidat,
│ → calculer support et conf     │  garder si support≥K et conf≥θ
└────────────────────────────────┘
     │
     ▼
┌────────────────────────────────┐
│ Étape 5 : Généralisation       │  Fusionner les doublons,
│ → PFDs finales propres         │  garder les règles générales
└────────────────────────────────┘
```

### 8.4 Détail de chaque étape (avec mini-exemple)

#### Étape 1 — Extraction de patterns

On regarde chaque colonne et on génère les transformations qui ont du sens.

Pour la colonne `Nom = "John Smith"` :
- `identity` (toujours)
- `first_token` (parce que contient un espace)
- `last_token`
- `prefix(1)` = "J", `prefix(2)` = "Jo", `prefix(3)` = "Joh", ...
- `length` = "10"

Pour la colonne `ZIP = "90012"` :
- `identity`, `prefix(1..5)`, `numeric_prefix(1..5)`, `length`

Sur une table de 9 colonnes → ~60 transformations.

#### Étape 2 — Groupement

Pour CHAQUE transformation, on regroupe les lignes ayant la même valeur transformée.

Pour `first_token(Nom)` sur 5 lignes :
- "John" → [ligne 1, 2, 3]
- "Susan" → [ligne 4, 5]

Pour `length(Nom)` :
- "10" → [ligne 1] (John Smith)
- "11" → [ligne 2, 3] (John Brown, John Taylor)
- "12" → [ligne 4] (Susan Miller)
- "11" → [ligne 5] (Susan Clark)

→ Le groupement dépend de la transformation choisie.

#### Étape 3 — Génération de candidats

On crée toutes les paires `(transformation, colonne_Y)`.

Avec 60 transformations × 9 colonnes Y = 540 candidats (en pratique on enlève les triviaux comme `identity(Nom) → Nom`).

#### Étape 4 — Validation

Pour CHAQUE candidat, on calcule support et confidence et on filtre.

Sur 544 candidats → 143 passent les seuils → on les garde.

#### Étape 5 — Généralisation

On a souvent des PFDs redondantes. Exemple :
- `prefix(Nom, 1) → Genre` : confidence = 0.88
- `prefix(Nom, 2) → Genre` : confidence = 0.90
- `prefix(Nom, 3) → Genre` : confidence = 0.92
- `first_token(Nom) → Genre` : confidence = 0.95
- `identity(Nom) → Genre` : confidence = 1.0 (chaque nom est unique → trivial)

→ On garde la **plus générale et la plus simple** (souvent `first_token`).

Sur 143 PFDs → ~85 après déduplication.

### 8.5 La sortie finale : un ensemble de PFDs

À la fin, on a une liste comme :

```
1. identity(Département) → Nom_département     [support=9090, conf=1.00]
2. first_token(Position) → Catégorie           [support=8999, conf=0.96]
3. prefix(ZIP, 3) → Ville                      [support=200,  conf=0.95]
4. ...
```

Ces PFDs constituent un **schéma de qualité** : on peut s'en servir pour détecter les erreurs futures.

---

## 9. Pourquoi c'est dur et pourquoi l'IA peut aider

### 9.1 Les défis du pipeline classique

#### Défi 1 : Espace de recherche énorme
- 60 transformations × 9 colonnes = 540 candidats sur un petit dataset
- Sur 20 colonnes avec préfixes de longueur 1 à 10 → des milliers de candidats
- Sur des "n-grammes" (sous-chaînes de taille n) → encore plus

#### Défi 2 : Pas de compréhension sémantique
L'algorithme teste **tout**, même les règles qui n'ont aucun sens :
- `length(Nom) → Catégorie` : peut tomber par hasard avec une bonne confidence, mais n'a aucune signification réelle.
- `prefix(Email, 1) → Ville` : statistiquement possible mais absurde.

#### Défi 3 : Dépendances spurieuses
Sur un petit dataset, des règles peuvent "tenir" par pur hasard (coïncidence statistique). Plus on teste de règles, plus on a de faux positifs.

#### Défi 4 : Choix des paramètres
Comment choisir les seuils K et θ ? Trop bas → trop de bruit. Trop haut → on rate des règles utiles.

### 9.2 Ce qu'apporte un LLM (= une IA type ChatGPT)

Un **Large Language Model** comprend le **sens** des données :
- Si tu lui montres une colonne ZIP avec des valeurs comme "90012", il sait que c'est un code postal américain.
- Si tu lui montres une colonne `Nom complet` avec "John Smith", il sait que c'est un nom de personne et que le prénom est devant.

Donc il peut **suggérer** :
- Pour ZIP : "essaye `prefix(ZIP, 3) → city`"
- Pour Nom : "essaye `first_token(Nom) → Genre`"

→ On évite de tester des règles absurdes.

### 9.3 Les 3 niveaux d'utilisation du LLM (les 3 workflows)

| Workflow | Ce que fait le LLM | Ce qui reste à l'algorithme |
|---|---|---|
| **W1 Feature-Enriched** | Suggère les transformations pertinentes | Tout le pipeline classique |
| **W2 Guided Search** | Suggère transformations + **priorise** les paires X→Y | Validation et généralisation |
| **W3 Agent-in-the-Loop** | Propose des PFDs, **lit le feedback**, **se corrige** en boucle | Validation à chaque itération |

W3 est le plus avancé : l'IA **apprend de ses erreurs** itération après itération.

---

## 10. À quoi ça sert dans la vraie vie

### 10.1 Détection d'erreurs

Tu as une base d'employés avec 10 000 lignes. Tu lances la découverte de PFDs et tu trouves la règle :
```
first_token(Nom) → Genre  [support=9990, confidence=0.998]
```

Les **20 lignes** qui violent cette règle (ex : "Susan Clark / M") sont les **erreurs à investiguer**.

### 10.2 Nettoyage de données (data cleaning)

Si la règle `Code département → Nom département` te dit que "POL = Police", tu peux **corriger** automatiquement toutes les variantes (POLICE, police, Police Dept, etc.) en "Police".

### 10.3 Documentation automatique d'une base

Les PFDs forment une **documentation lisible** des contraintes implicites de la base. Tu peux les présenter à l'équipe métier :
> *« Voici les 50 règles que respecte notre base à 95%. Si vous ajoutez de nouvelles données, elles devraient les respecter aussi. »*

### 10.4 Validation de nouvelles données

Quand de nouvelles données arrivent (depuis un formulaire web), tu peux **vérifier** qu'elles respectent les PFDs connues. Si la nouvelle ligne dit "Code = POL, Nom = Education", c'est probablement une erreur → on alerte l'utilisateur.

### 10.5 Schémas d'évolution

Si à 10 ans d'écart tu redécouvres les PFDs et qu'elles ont changé, c'est intéressant : la sémantique de ta base a évolué.

---

## 11. Quiz récapitulatif

> **Teste ta compréhension avant la soutenance.** Cache les réponses et essaie de répondre.

### Question 1
*Qu'est-ce qui distingue une FD d'une PFD ?*

<details>
<summary>👉 Cliquer pour voir la réponse</summary>

La **FD** compare des valeurs **entières** (`John Smith` vs `John Brown` sont différents).
La **PFD** applique d'abord une **transformation** (ex : `first_token`) puis compare (`"John"` vs `"John"` sont identiques). La PFD capture des **régularités partielles** que la FD rate.
</details>

### Question 2
*Comment se calcule la confidence d'une PFD ?*

<details>
<summary>👉 Réponse</summary>

1. Grouper les lignes par valeur de pattern X
2. Dans chaque groupe, trouver la valeur Y majoritaire
3. Compter les lignes cohérentes (= ayant la valeur majoritaire)
4. Confidence = lignes cohérentes / lignes totales (après filtre support)
</details>

### Question 3
*Que veut dire `prefix(ZIP, 3) → Ville` ?*

<details>
<summary>👉 Réponse</summary>

*« Les 3 premiers caractères du code postal déterminent la ville. »*
Exemple : "90012" et "90013" ont tous deux `prefix=900` donc doivent avoir la même ville.
</details>

### Question 4
*Pourquoi les seuils K et θ ?*

<details>
<summary>👉 Réponse</summary>

- **K (support)** : ignorer les règles qui ne portent que sur quelques lignes (anecdotique).
- **θ (confidence)** : ignorer les règles trop bruitées (qui se trompent trop souvent).
Sans ces seuils, on accepterait n'importe quoi.
</details>

### Question 5
*Pourquoi utiliser un LLM (IA) au lieu du pipeline classique pur ?*

<details>
<summary>👉 Réponse</summary>

Le LLM comprend le **sens** des colonnes (ZIP = code postal, Email = adresse...).
Il peut **filtrer** les règles absurdes et **suggérer** des règles intelligentes.
Le pipeline classique teste tout, y compris des combinaisons qui n'ont aucun sens (ex : `length(Nom) → Salaire`).
</details>

### Question 6
*Qu'est-ce que l'Agent-in-the-Loop (W3) ?*

<details>
<summary>👉 Réponse</summary>

C'est un workflow **itératif** où :
1. Le LLM propose des PFDs candidates
2. L'algorithme les valide et **rapporte** lesquelles sont fortes, faibles, rejetées
3. Le LLM **lit le feedback** et propose des raffinements (modifie les paramètres, abandonne les mauvaises règles)
4. On recommence jusqu'à convergence

C'est de l'**IA agentique autonome** : la machine s'auto-corrige.
</details>

### Question 7
*Donne 3 exemples concrets de PFDs.*

<details>
<summary>👉 Réponse</summary>

- `first_token(Nom) → Genre` (le prénom détermine le genre)
- `prefix(ZIP, 3) → Ville` (les 3 premiers chiffres ZIP déterminent la ville)
- `domain(Email) → Organisation` (le domaine email détermine l'entreprise)
</details>

### Question 8
*Que signifie "PFD approximative" ?*

<details>
<summary>👉 Réponse</summary>

Une PFD qui ne tient pas à 100% mais **majoritairement**. On tolère un certain pourcentage de violations (le **bruit**).
Une PFD est dite "valide" si **confidence ≥ θ** (typiquement 0.85, soit 85% de cohérence minimum).
</details>

### Question 9
*Que fait l'étape 5 (généralisation) ?*

<details>
<summary>👉 Réponse</summary>

Elle **fusionne les PFDs redondantes** et garde les plus générales. Par exemple, si `prefix(Nom, 1)`, `prefix(Nom, 2)` et `first_token(Nom)` donnent toutes la même règle `→ Genre`, on garde une seule représentante (la plus simple et la plus générale).
</details>

### Question 10
*À quoi servent les PFDs en pratique ?*

<details>
<summary>👉 Réponse</summary>

1. **Détecter** les erreurs dans une base (lignes qui violent les règles).
2. **Nettoyer** les données (normaliser les valeurs).
3. **Documenter** les contraintes implicites de la base.
4. **Valider** les nouvelles données entrantes.
</details>

---

## ✅ Résumé en une page

| Concept | Définition courte |
|---|---|
| **FD** `X → Y` | Si X est égal, Y est égal (valeurs entières) |
| **PFD** `R(X → Y, Tp)` | Si pattern(X) est égal, Y est égal |
| **Pattern** | Transformation : prefix, first_token, suffix, length, identity... |
| **Support** | Nombre de lignes couvertes par la règle (seuil K) |
| **Confidence** | % de lignes cohérentes (seuil θ) |
| **Approximative** | On tolère ~15% de violations |
| **Pipeline 5 étapes** | Extraction → Groupement → Candidats → Validation → Généralisation |
| **W1** | LLM suggère les transformations |
| **W2** | + LLM priorise les candidats |
| **W3** | + boucle itérative avec auto-correction |

### Trois exemples à retenir

1. **FD classique** : `Code département → Nom département` (POL = Police, toujours)
2. **PFD parfaite** : `first_token(Nom complet) → Genre` (John* = M, Susan* = F)
3. **PFD approximative** : `prefix(ZIP, 3) → Ville` (à 95%, certains ZIP frontaliers sont ambigus)

### La phrase qui résume tout

> **Une PFD est une règle qui dit que certains MORCEAUX (patterns) des données déterminent d'autres colonnes — c'est plus puissant qu'une FD classique parce qu'on capture des régularités partielles, et on tolère un peu de bruit pour rester réaliste.**

Bonne soutenance ! 🎓
