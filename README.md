<p align="center">
  <img
    src="https://capsule-render.vercel.app/api?type=waving&color=0:173642,100:00A0AE&height=105&section=header"
    width="100%"
    alt=""
  />
</p>

<div align="center">

<img src="assets/logo.png" alt="YES — Young Enterprise Switzerland" height="86">

# Planificateur de débats

**La jeunesse débat**

Préparez une finale régionale et générez automatiquement un planning
**clair, équilibré et prêt à l'emploi**.

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img
    src="https://img.shields.io/badge/▶%20OUVRIR%20L'APPLICATION-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white"
    alt="Ouvrir l'application"
  >
</a>
&nbsp;
<a href="#installation-locale">
  <img
    src="https://img.shields.io/badge/↓%20INSTALLER%20EN%20LOCAL-28647A?style=for-the-badge&logo=python&logoColor=white"
    alt="Installer en local"
  >
</a>

<br><br>

<img src="https://img.shields.io/badge/Python-3.11+-28647A?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
<img src="https://img.shields.io/badge/Streamlit-App-00A0AE?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit">
<img src="https://img.shields.io/badge/Optimisation-MILP-173642?style=flat-square" alt="MILP">
<img src="https://img.shields.io/badge/Sauvegarde-SQLite-28647A?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">

<br><br>

<a href="#comment-ça-marche">Comment ça marche ?</a>
&nbsp;·&nbsp;
<a href="#utilisation">Utilisation</a>
&nbsp;·&nbsp;
<a href="#installation-locale">Installation</a>
&nbsp;·&nbsp;
<a href="#faq">FAQ</a>
&nbsp;·&nbsp;
<a href="#aide--contact">Contact</a>

</div>

---

<div align="center">

<img
  src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=18&pause=1200&color=00A0AE&center=true&vCenter=true&width=720&height=36&lines=%C3%89v%C3%A9nement+%E2%86%92+%C3%89quipes+%E2%86%92+Salles+%E2%86%92+Planning"
  alt="Événement → Équipes → Salles → Planning"
>

</div>

Le **Planificateur de débats** automatise la préparation des finales régionales
de **La jeunesse débat**.

Vous renseignez les équipes et les salles disponibles. L'application organise
les rencontres, les questions, les rôles et les sessions, puis vérifie le
planning avant de l'afficher.

---

<a id="comment-ça-marche"></a>

## Comment ça marche ?

<p align="center">
  <kbd>① Événement</kbd>
  &nbsp;→&nbsp;
  <kbd>② Équipes</kbd>
  &nbsp;→&nbsp;
  <kbd>③ Salles</kbd>
  &nbsp;→&nbsp;
  <kbd>④ Planning</kbd>
</p>

**① Événement** — choisissez le nom de la finale et les catégories présentes.

**② Équipes** — ajoutez les établissements, les équipes et, si nécessaire,
les noms des participant·es.

**③ Salles** — indiquez le nombre de salles disponibles. La configuration est
contrôlée immédiatement.

**④ Planning** — lancez l'optimisation. Le planning est généré, validé puis
présenté par session et par salle.

<br>

<div align="center">

<img src="https://img.shields.io/badge/2%20débats-par%20équipe-00A0AE?style=for-the-badge" alt="2 débats par équipe">
<img src="https://img.shields.io/badge/Q1%20%2B%20Q2-une%20fois%20chacune-28647A?style=for-the-badge" alt="Question 1 et Question 2">
<img src="https://img.shields.io/badge/Rôles-1%20↔%202-00A0AE?style=for-the-badge" alt="Rotation des rôles">

<br>

<img src="https://img.shields.io/badge/Aucun%20conflit-de%20session-28647A?style=for-the-badge" alt="Aucun conflit de session">
<img src="https://img.shields.io/badge/Planning-validé%20automatiquement-173642?style=for-the-badge" alt="Planning validé automatiquement">

</div>

<br>

<div align="center">

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img
    src="https://img.shields.io/badge/▶%20CRÉER%20UN%20PLANNING-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white"
    alt="Créer un planning"
  >
</a>

</div>

---

<a id="utilisation"></a>

## Choisir votre mode d'utilisation

<details open>
<summary><strong>🌐 Utiliser l'application en ligne — le plus simple</strong></summary>

<br>

Aucune installation n'est nécessaire.

Ouvrez simplement le planificateur dans votre navigateur, ajoutez vos équipes
et générez le planning.

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img
    src="https://img.shields.io/badge/OUVRIR%20L'APPLICATION-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white"
    alt="Ouvrir l'application"
  >
</a>

<br><br>

> [!IMPORTANT]
> La version en ligne est idéale pour utiliser rapidement le planificateur,
> mais elle ne doit pas être considérée comme un système de sauvegarde
> permanente.

</details>

<details>
<summary><strong>💾 Utiliser l'application en local — pour conserver vos événements</strong></summary>

<br>

La version locale utilise exactement la même application, mais les événements
sont enregistrés sur votre propre ordinateur.

Les sauvegardes sont stockées dans :

```text
data/app.db
```

> [!TIP]
> Conservez ce fichier si vous mettez l'application à jour ou changez
> d'ordinateur : il contient vos événements sauvegardés.

<br>

<a href="#installation-locale">
  <img
    src="https://img.shields.io/badge/VOIR%20L'INSTALLATION-28647A?style=for-the-badge&logo=python&logoColor=white"
    alt="Voir l'installation locale"
  >
</a>

</details>

---

<a id="installation-locale"></a>

## Installation locale

<details>
<summary><strong>👋 Première fois avec GitHub ou Python ? Commencez ici</strong></summary>

<br>

### 1. Télécharger l'application

Sur cette page GitHub, cliquez sur :

**Code → Download ZIP**

Puis décompressez le dossier sur votre ordinateur.

### 2. Vérifier Python

Python **3.11 ou plus récent** est recommandé.

```bash
python --version
```

### 3. Installer et lancer

Choisissez votre système ci-dessous et copiez les commandes indiquées.

</details>

<details>
<summary><strong>🪟 Windows — PowerShell</strong></summary>

<br>

**Première installation**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

**Les fois suivantes**

```powershell
.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

</details>

<details>
<summary><strong>🍎 macOS / 🐧 Linux</strong></summary>

<br>

**Première installation**

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

**Les fois suivantes**

```bash
source .venv/bin/activate
python -m streamlit run app.py
```

</details>

L'application s'ouvre normalement automatiquement dans le navigateur.

Sinon, ouvrez :

```text
http://localhost:8501
```

---

<a id="faq"></a>

## FAQ

<details>
<summary><strong>Dois-je installer quelque chose pour utiliser le planificateur ?</strong></summary>

<br>

Non. Vous pouvez utiliser directement la version en ligne.

L'installation locale est surtout utile si vous souhaitez conserver vos
événements de manière durable.

</details>

<details>
<summary><strong>Mes événements sont-ils sauvegardés dans la version en ligne ?</strong></summary>

<br>

La version hébergée ne doit pas être considérée comme un système de sauvegarde
permanent.

Pour conserver vos événements de manière fiable, utilisez l'application en
local.

</details>

<details>
<summary><strong>Dois-je renseigner les noms des participant·es ?</strong></summary>

<br>

Non.

Les noms sont optionnels. Vous pouvez préparer un événement uniquement avec les
établissements et le nombre d'équipes.

</details>

<details>
<summary><strong>Que se passe-t-il si la configuration est impossible ?</strong></summary>

<br>

L'application effectue des contrôles avant de lancer l'optimisation.

Une configuration structurellement impossible est donc signalée immédiatement.

</details>

<details>
<summary><strong>Une salle peut-elle accueillir Question 1 et Question 2 ?</strong></summary>

<br>

Oui. C'est un fonctionnement normal du planificateur.

</details>

<details>
<summary><strong>J'ai trouvé un bug ou quelque chose ne fonctionne pas.</strong></summary>

<br>

Vous pouvez me contacter à
**[yann.ducrest@gmail.com](mailto:yann.ducrest@gmail.com)**.

Pour faciliter le diagnostic, indiquez si possible :

- ce que vous essayiez de faire ;
- le nombre d'équipes et de salles ;
- le message d'erreur affiché ;
- une capture d'écran.

</details>

---

## Pour aller plus loin

<details>
<summary><strong>⚙️ Sous le capot</strong></summary>

<br>

Le moteur utilise une optimisation **MILP** (*Mixed-Integer Linear
Programming*) via `scipy.optimize.milp` et le solveur **HiGHS**.

Il garantit notamment :

- exactement deux débats par équipe ;
- exactement une `Question 1` et une `Question 2` par équipe ;
- aucune double participation dans une même session ;
- la rotation des rôles individuels `1 ↔ 2` ;
- le respect du nombre de salles disponibles.

Parmi les solutions valides, le moteur optimise ensuite la qualité générale du
planning : nombre de sessions, rencontres, côtés et salles.

Une validation indépendante contrôle le résultat après la résolution.

</details>

<details>
<summary><strong>🧪 Tests</strong></summary>

<br>

```bash
python -m pytest -q
```

La suite de tests vérifie les principales contraintes du moteur sur différentes
configurations d'événements.

</details>

<details>
<summary><strong>📚 Documentation technique</strong></summary>

<br>

- [`PROJECT_SOURCE.md`](PROJECT_SOURCE.md) — fonctionnement interne du projet
- [`VERIFICATION.md`](VERIFICATION.md) — vérification et validation

</details>

---

<a id="aide--contact"></a>

## Aide & contact

<div align="center">

Une question, une suggestion ou un problème ?

<br><br>

<a href="mailto:yann.ducrest@gmail.com">
  <img
    src="https://img.shields.io/badge/CONTACTER%20YANN-00A0AE?style=for-the-badge&logo=gmail&logoColor=white"
    alt="Contacter Yann"
  >
</a>
&nbsp;
<a href="https://github.com/YDucrest">
  <img
    src="https://img.shields.io/badge/GITHUB-YDucrest-173642?style=for-the-badge&logo=github&logoColor=white"
    alt="GitHub Yann Ducrest"
  >
</a>

<br><br>

**Yann Ducrest**  
Auteur & mainteneur

</div>

---

<div align="center">

<img src="assets/logo.png" alt="YES — Young Enterprise Switzerland" height="66">

### Un planning plus simple à préparer.  
### Une finale plus simple à organiser.

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img
    src="https://img.shields.io/badge/▶%20OUVRIR%20LE%20PLANIFICATEUR-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white"
    alt="Ouvrir le planificateur"
  >
</a>

<br><br>

<sub>Développé par <strong>Yann Ducrest</strong></sub>

</div>

<p align="center">
  <img
    src="https://capsule-render.vercel.app/api?type=waving&color=0:173642,100:00A0AE&height=105&section=footer"
    width="100%"
    alt=""
  />
</p>
