# 🎯 Plan de démo — Soutenance (dataset t1)

> Ouvre ce fichier sur un 2ᵉ écran/téléphone pendant la soutenance.
> Objectif : montrer **en live sur t1** que l'on passe du classique (beaucoup de règles bruitées)
> aux workflows agentiques (de moins en moins de candidats, des PFDs de plus en plus pertinentes),
> puis le Workflow 3 qui **s'auto-corrige**.

---

## ✅ 0. Pré-vol (à faire 5 min AVANT de présenter)

Ouvre un terminal dans le dossier du projet et lance ces 3 vérifications :

```bash
cd ~/Desktop/PatternFD-miniprojet

# 1. Ollama tourne et les 2 modèles sont là ?
curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"'
#   → doit afficher mistral et llama3.1. Si rien : lance  ollama serve  dans un autre terminal.

# 2. Python + pandas OK ?
python3 -c "import pandas; print('pandas', pandas.__version__)"

# 3. Test éclair du classique (~12 s) — si ça marche, tout le reste marchera
python3 experiments/run_classical.py >/dev/null 2>&1 && echo "CLASSIQUE OK"
```

Si les 3 lignes répondent bien → tu es prêt. **Garde Ollama lancé.**

---

## ⏱️ Minutage cible (~4-5 min de parole au total)

| Temps | Étape | Tu parles |
|---|---|---|
| 0:00 – 2:00 | **Partie 1 — Architecture** (schéma `architecture.pdf`) | ~2 min |
| 2:00 – 2:45 | Acte 1 — Classique sur t1 | ~45 s |
| 2:45 – 3:45 | Acte 2 — W2 guidé par le LLM | ~1 min |
| 3:45 – 4:45 | Acte 3 — W3 auto-correction | ~1 min |
| 4:45 – 5:00 | Phrase de conclusion | ~15 s |

> **Astuce timing :** lance la commande PUIS parle pendant qu'elle calcule (le LLM met ~1 min) —
> aucun temps mort. Si tu n'as que **4 min** : fais Partie 1 + Actes 1 et 2, et **décris** W3 à l'oral sans le lancer.

---

## 🎤 Partie 1 — Explication de l'architecture (~2 min, à dire)

> **Ouvre `rapport/architecture.pdf`** et parle en suivant les zones (0 → A → B → C/D).
> Texte à lire / adapter (pointe le schéma au fur et à mesure) :

> « Notre projet part d'une question simple : peut-on découvrir **automatiquement** les règles cachées
> d'un jeu de données — par exemple *“le code de département détermine le nom du département”* — et
> est-ce qu'une **IA** fait mieux qu'un algorithme classique ? On compare donc deux approches.
>
> *[Zone 0, en haut]* Tout part d'un fichier **CSV**. Le module `data_loader` le nettoie et en extrait
> le **schéma** : la liste des colonnes avec quelques exemples de valeurs.
>
> *[Zone A, bleue]* La première approche est **classique**, en cinq étapes. On génère des
> **transformations** sur les colonnes — par exemple les préfixes, ou le premier mot. On **regroupe**
> les lignes qui ont la même valeur transformée. On forme tous les **candidats** “X détermine Y”. On les
> **valide** avec deux mesures : le **support** — combien de lignes la règle couvre — et la **confiance** —
> le pourcentage de lignes cohérentes. Enfin on **généralise** pour fusionner les doublons. C'est
> exhaustif et très rapide, mais ça produit beaucoup de règles sans intérêt sémantique.
>
> *[Zone B, orange]* La deuxième approche est **agentique** : on fait intervenir un **LLM** — Mistral ou
> Llama — qui tourne **en local** via Ollama, donc gratuit, hors-ligne et confidentiel. On a **trois
> workflows**, avec un rôle **croissant** de l'IA. **W1** : le LLM suggère les bonnes transformations.
> **W2** : il **priorise** en plus les candidats. **W3** : il propose des hypothèses, l'algorithme les
> valide et lui renvoie un **retour**, et il **se corrige** tout seul, en boucle.
>
> *[Zones C et D, en bas]* Point clé : les deux approches partagent les **mêmes modules de validation**,
> et chaque hypothèse de l'IA est **revérifiée sur les vraies données** — donc même si le LLM invente une
> colonne, on la rejette. Tout finit dans le module d'**évaluation**, qui compare les deux approches.
> Et c'est ce qu'on va voir maintenant en direct. »

👉 Enchaîne directement sur la démo (Partie 2). La dernière phrase sert de transition.

---

## 🎬 Partie 2 — La démo en 3 actes (~2,5 min)

### Acte 1 — Le classique sur t1 (rapide, ~12 s)

```bash
python3 experiments/run_classical.py --dataset t1
```

> Le script accepte aussi `--min-support`, `--min-confidence`, `--max-prefix-len` si le jury
> veut voir l'effet des seuils en direct (ex. `--min-confidence 0.95`).

**Ce qui s'affiche :** les 5 étapes, puis ~**85 PFDs** dont le top.

**Ce que tu dis :**
> « Voici l'approche classique. Elle teste **tout** : 68 transformations, 544 candidats X→Y,
> 143 règles valides puis 85 après généralisation. En tête on trouve de vraies règles parfaites comme
> `identity(Department) → Department Name` (un code de département détermine son nom, confiance 1.0).
> **Mais** la plupart des 85 règles sont bruitées ou sans intérêt sémantique : c'est exhaustif mais aveugle. »

👉 Pointe une règle parfaite ET dis qu'il y a beaucoup de bruit derrière.

---

### Acte 2 — Le workflow guidé par le LLM sur t1 (~1 à 1,5 min)

```bash
python3 experiments/run_agentic.py --llm mistral --workflow 2 --dataset t1
```

**Ce qui s'affiche :**
- Mistral suggère des transformations, puis **priorise des candidats** (avec une justification en français pour chacun) ;
- ~**19 PFDs** validées, **~58 candidats** seulement, et le tableau de comparaison final.

**Ce que tu dis (pendant que ça tourne, ~1 min) :**
> « Ici le LLM (Mistral, en local via Ollama) lit le **schéma** du dataset et propose seulement les
> transformations et les paires X→Y qui ont un **sens métier**. L'algorithme ne valide que celles-là.
> Résultat : on passe de ~600 candidats à ~58, la confiance moyenne monte, et on **garde** les
> bonnes règles parfaites (`Department → Department Name`). »

> « Petit point intéressant : Mistral **hallucine** parfois des colonnes qui n'existent pas
> (ex. *“Number of employees”*). Notre code **re-valide chaque hypothèse contre le vrai schéma**
> et rejette automatiquement ces inventions. »

👉 C'est l'idée centrale : **moins de candidats, plus de pertinence**.

---

### Acte 3 — Workflow 3 : l'auto-correction (sur US_Phone_Code, ~1,5 min)

> On le montre sur le **petit** dataset `US_Phone_Code` (51 lignes) car l'auto-correction y est
> nette et rapide — c'est l'exemple du rapport (section 6.3).

```bash
python3 experiments/run_workflow3.py --dataset US_Phone_Code --llm mistral --iterations 3
```

**Ce qui s'affiche :** le déroulé itération par itération (hypothèses → fortes/faibles/rejetées → raffinement).

**Ce que tu dis :**
> « Le Workflow 3 met le LLM **dans une boucle** : il propose des règles, l'algorithme les valide
> et lui renvoie un **feedback**, puis il raffine. À l'itération 0, Mistral propose une règle faible.
> Après le feedback, il l'**abandonne** et en propose une meilleure qui s'avère parfaite.
> C'est une vraie **auto-correction** — exactement ce que demandait le sujet (slides 31-34 du prof). »

👉 C'est le moment « waouh » : l'IA apprend de son erreur.

---

## 📊 Le tableau à retenir (t1)

| Approche | Candidats | PFDs | Parfaites | Confiance moy. | Temps |
|---|---|---|---|---|---|
| Classique | **544** | 85 | 2 | 0.913 | ~9-12 s |
| W1 (Feature-Enriched) | ~70-80 | ~23 | 2 | ~0.93 | ~56-71 s |
| W2 (Guided Search) | ~34-58 | ~19 | 2 | ~0.94 | ~52-66 s |
| W3 (Agent-in-the-Loop) | ~17 | ~8 | ~3 | ~0.95 | ~1-6 min |

> Le **classique est déterministe** : tu obtiendras toujours **544 candidats / 85 PFDs** (identique au rapport).

⚠️ **Les chiffres des workflows agentiques varient à chaque exécution** : le LLM est non-déterministe
(température 0.1, mais pas 0). Si les nombres diffèrent un peu du rapport, dis-le au jury — c'est normal
et attendu. Ce qui ne change pas, c'est la **tendance**.

**La phrase choc :**
> « De haut en bas, l'espace de recherche **s'effondre** (544 → ~17 candidats) pendant que la
> qualité **monte**. On échange un peu de temps de calcul contre de la pertinence sémantique. »

---

## 🛠️ 2 corrections apportées juste avant la soutenance (bon à mentionner)

Si le jury demande « avez-vous rencontré des problèmes ? », voici un **vrai** échange technique :

1. **Règles triviales X→X.** Le LLM proposait parfois `identity(Gender) → Gender`
   (une colonne qui se prédit elle-même) — vrai à 100 % mais **vide de sens**. Le pipeline classique
   excluait déjà ce cas ; on a ajouté le **même filtre** dans les workflows agentiques
   (`_parse_candidate_string` dans `src/agentic_workflow.py`) pour une comparaison équitable.

2. **Prompts renforcés.** On a explicité dans les prompts que X et Y doivent être des colonnes
   **différentes**, ce qui réduit ces propositions triviales à la source.

> Ça montre que vous comprenez le code ET les pièges de l'approche LLM. C'est un **plus**, pas un aveu de faiblesse.

---

## 🧯 Si quelque chose plante (plan B)

| Problème | Solution immédiate |
|---|---|
| `ConnectionRefusedError` / Ollama injoignable | Dans un autre terminal : `ollama serve` (puis réessaie) |
| Le LLM est trop lent / ça fige | `Ctrl+C`, et relance avec `--llm llama` (parfois plus rapide) |
| Un workflow agentique trouve peu de PFDs | Relance une fois (non-déterministe), ou bascule sur l'autre LLM |
| Tout l'agentique échoue en live | Montre les résultats **déjà sauvegardés** : `ls -lt results/*.json | head` puis ouvre le plus récent. Le classique, lui, marche toujours (pas de LLM). |

---

## ❓ Caveat à anticiper (question piège possible)

Si le W3 sur t1 affiche `identity(Full Name) → Gender` (ou `→ Position Title`) comme « parfaite » :
> C'est une colonne **quasi-unique** (presque une clé : ~9075 noms distincts sur 9101 lignes).
> Une colonne-clé « détermine » trivialement les autres. C'est une **limite connue** des FD/PFD
> (slide 20 du prof : *spurious dependencies*) — et justement une des raisons d'introduire le
> **guidage sémantique par LLM** et les seuils support/confiance. Le savoir et le dire = maîtrise du sujet.

---

## 🗂️ Fichiers à garder ouverts pendant la soutenance

- **`rapport/architecture.pdf`** — le schéma à projeter pour la Partie 1 (source modifiable : `rapport/architecture.tex`).
- **Ce fichier (`PLAN_DEMO_T1.md`)** — sur un 2ᵉ écran/téléphone pour suivre le minutage et les phrases.
- Un **terminal** dans `~/Desktop/PatternFD-miniprojet`, Ollama lancé.
