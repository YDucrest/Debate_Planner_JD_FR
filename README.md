# Planificateur de débats — La jeunesse débat

Application Streamlit pour préparer et générer un planning optimisé de finales régionales de **La jeunesse débat**.

Le moteur utilise une optimisation MILP exacte via `scipy.optimize.milp` et HiGHS. L’interface est conçue comme un parcours guidé sur une seule page : **Événement → Équipes → Salles → Planning**.

## Interface

L’application n’utilise plus de navigation latérale. Les quatre étapes restent visibles sur la même page avec un indicateur de progression.

1. **Définir l’événement** : nom et catégories.
2. **Ajouter les équipes** : établissements, nombre d’équipes et noms des participant·es si nécessaire.
3. **Choisir les salles** : nombre de salles et vérification immédiate de la configuration.
4. **Générer le planning** : optimisation et affichage sous forme de cartes par session et par salle.

Le résultat comprend également une vue tableau complète et un onglet séparé pour les contrôles techniques afin de garder l’écran principal lisible.

## Logo YES

Placez simplement le logo officiel au format PNG ici :

```text
assets/logo.png
```

L’application le détecte automatiquement au prochain lancement ou rechargement. En son absence, un en-tête texte de secours est utilisé.

La palette visuelle de l’application reprend les tons bleu pétrole / turquoise de YES.

## Fonctionnalités principales

- une ou deux catégories : `Secondaire 1` et `Secondaire 2` ;
- ajout rapide des établissements et création automatique des équipes A, B, C, … ;
- saisie optionnelle des noms des participant·es dans un tableau éditable ;
- sauvegarde / chargement local via SQLite (`data/app.db`) ;
- blocage immédiat des configurations structurellement impossibles ;
- exactement deux débats par équipe ;
- exactement une fois `Question 1` et une fois `Question 2` par équipe ;
- aucune double participation dans une session ;
- rotation obligatoire des rôles individuels `1 ↔ 2` ;
- minimisation du nombre de sessions ;
- optimisation des rencontres, côtés et salles ;
- forte stabilité des salles entre `Secondaire 1` et `Secondaire 2` ;
- validation indépendante après résolution.

## Logique des salles

L’affectation des salles suit notamment cette priorité :

1. minimiser le nombre de salles qui accueillent plusieurs catégories ;
2. éviter les allers-retours `Secondaire 1 ↔ Secondaire 2` dans une même salle ;
3. favoriser `Secondaire 1` dans les premières salles et `Secondaire 2` dans les dernières ;
4. favoriser `Question 1` avant `Question 2` dans la chronologie d’une équipe ;
5. faire changer une équipe de salle entre ses deux débats lorsque possible.

Lorsqu’une salle doit nécessairement être partagée entre les deux catégories, le solveur cherche à en faire une **salle frontière** : d’abord Secondaire 1, puis Secondaire 2, sans alternances inutiles.

### Questions dans les salles

Une salle peut accueillir **Question 1 et Question 2** au cours de l’événement. C’est un fonctionnement normal :

- ce n’est pas un avertissement ;
- ce n’est pas une préférence négative ;
- cela n’influence pas l’affectation des salles.

## Architecture

```text
app.py
src/
    models.py
    optimizer.py
    validation.py
    database.py
    utils.py
components/
    event_form.py
    teams_form.py
    parameter_form.py
    schedule_view.py
    ui_helpers.py
assets/
    logo.png        # à ajouter
    README.txt
data/
    app.db          # créé automatiquement
tests/
    test_optimizer.py
requirements.txt
README.md
```

## Installation avec environnement virtuel

Python 3.11+ est recommandé.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Lancement

```powershell
python -m streamlit run app.py
```

Puis ouvrir si nécessaire :

```text
http://localhost:8501
```

## Sauvegarde

La sauvegarde locale repose sur SQLite :

```text
data/app.db
```

Pour conserver vos événements lors d’une mise à jour de l’application, conservez simplement ce fichier.

## Tests

```powershell
python -m pytest -q
```

La version actuelle comporte 9 tests automatisés couvrant notamment :

- 8 équipes ;
- 10 équipes avec peu de salles ;
- deux catégories simultanées ;
- plusieurs équipes du même établissement ;
- un nombre impair d’équipes ;
- une préférence impossible à respecter ;
- salles entièrement dédiées quand cela est possible ;
- salle frontière lorsqu’un partage est nécessaire ;
- absence de signalement négatif lorsqu’une salle accueille les deux questions.
