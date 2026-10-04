<div align="center">

<img src="assets/logo.png" alt="YES — Young Enterprise Switzerland" width="92">

# Planificateur de débats

### La jeunesse débat

**Préparez une finale régionale et générez automatiquement un planning clair, équilibré et prêt à l'emploi.**

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="https://img.shields.io/badge/OUVRIR%20L'APPLICATION-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white" alt="Ouvrir l'application">
</a>
&nbsp;
<a href="#installation-locale">
  <img src="https://img.shields.io/badge/INSTALLER%20EN%20LOCAL-28647A?style=for-the-badge&logo=python&logoColor=white" alt="Installer en local">
</a>

<br><br>

<a href="#apercu">Aperçu</a>
&nbsp;·&nbsp;
<a href="#utilisation">Utilisation</a>
&nbsp;·&nbsp;
<a href="#installation-locale">Installation</a>
&nbsp;·&nbsp;
<a href="#faq">FAQ</a>
&nbsp;·&nbsp;
<a href="#contact">Contact</a>

<br><br>

<sub>Python 3.11+ · Streamlit · SciPy / HiGHS · SQLite</sub>

</div>

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="assets/readme/app-preview.png" alt="Aperçu du Planificateur de débats" width="100%">
</a>

<p align="center">
  <sub>Cliquez sur l'aperçu pour ouvrir l'application.</sub>
</p>

---

<a id="apercu"></a>

## Aperçu

Le **Planificateur de débats** automatise la préparation des finales régionales de **La jeunesse débat**.

Vous renseignez les équipes et les salles disponibles.  
L'application organise les **rencontres, questions, rôles, sessions et salles**, puis vérifie le planning avant de l'afficher.

<p align="center">
  <strong>01 · Événement</strong>
  &nbsp;&nbsp;→&nbsp;&nbsp;
  <strong>02 · Équipes</strong>
  &nbsp;&nbsp;→&nbsp;&nbsp;
  <strong>03 · Salles</strong>
  &nbsp;&nbsp;→&nbsp;&nbsp;
  <strong>04 · Planning</strong>
</p>

### Ce que le planning garantit

- ✓ exactement **2 débats par équipe** ;
- ✓ exactement **1 × Question 1** et **1 × Question 2** ;
- ✓ aucune équipe dans deux débats pendant la même session ;
- ✓ rotation individuelle des rôles **1 ↔ 2** ;
- ✓ respect du nombre de salles disponibles ;
- ✓ validation indépendante du planning après optimisation.

Le moteur cherche ensuite à améliorer la qualité du planning : diversité des rencontres, équilibre des côtés, ordre des questions, utilisation des salles et nombre de sessions.

<br>

<div align="center">
  <a href="https://debate-planner-jd-fr.streamlit.app/">
    <img src="https://img.shields.io/badge/CRÉER%20UN%20PLANNING-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white" alt="Créer un planning">
  </a>
</div>

---

<a id="utilisation"></a>

## Utilisation

<details open>
<summary><strong>🌐 Utiliser le planificateur en ligne</strong></summary>

<br>

C'est le moyen le plus simple de commencer.

Aucune installation : ouvrez l'application dans votre navigateur, ajoutez les équipes et générez le planning.

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="https://img.shields.io/badge/OUVRIR%20L'APPLICATION-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white" alt="Ouvrir l'application">
</a>

<br><br>

> [!IMPORTANT]
> La version en ligne est idéale pour générer un planning, mais elle ne doit pas être utilisée comme système de **sauvegarde permanente**.

</details>

<details>
<summary><strong>💾 Conserver mes événements</strong></summary>

<br>

Pour enregistrer vos événements et les retrouver plus tard, utilisez l'application **en local sur votre ordinateur**.

Les données sont enregistrées dans :

```text
data/app.db
```

> [!TIP]
> `app.db` est le fichier à conserver lors d'une mise à jour de l'application ou d'un changement d'ordinateur.

Les instructions se trouvent dans la section [Installation locale](#installation-locale).

</details>

---

<a id="installation-locale"></a>

## Installation locale

<details>
<summary><strong>Je n'ai jamais utilisé GitHub ou Python</strong></summary>

<br>

**1. Télécharger le projet**

Sur cette page GitHub, cliquez sur **Code → Download ZIP**, puis décompressez le dossier.

**2. Vérifier Python**

Python **3.11 ou plus récent** est recommandé.

```bash
python --version
```

**3. Choisir votre système**

Utilisez ensuite l'une des procédures ci-dessous.

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

Sinon :

```text
http://localhost:8501
```

---

<a id="faq"></a>

## FAQ

<details>
<summary><strong>Dois-je installer quelque chose pour utiliser l'application ?</strong></summary>

<br>

Non. La version en ligne fonctionne directement dans le navigateur :

**https://debate-planner-jd-fr.streamlit.app/**

L'installation locale est surtout utile pour conserver durablement vos événements.

</details>

<details>
<summary><strong>Mes événements sont-ils sauvegardés dans la version en ligne ?</strong></summary>

<br>

La version hébergée ne doit pas être considérée comme un stockage permanent.

Pour conserver vos événements de manière fiable, utilisez l'application en local.

</details>

<details>
<summary><strong>Dois-je renseigner les noms des participant·es ?</strong></summary>

<br>

Non.

Les noms sont optionnels. Vous pouvez préparer un événement uniquement avec les établissements et le nombre d'équipes.

</details>

<details>
<summary><strong>Que se passe-t-il si la configuration est impossible ?</strong></summary>

<br>

L'application vérifie les contraintes structurelles avant de lancer l'optimisation.

Une configuration impossible est donc signalée immédiatement.

</details>

<details>
<summary><strong>Une salle peut-elle accueillir Question 1 et Question 2 ?</strong></summary>

<br>

Oui.

C'est un fonctionnement normal et cela n'est pas considéré comme un problème par le planificateur.

</details>

<details>
<summary><strong>J'ai trouvé un problème ou une erreur.</strong></summary>

<br>

Vous pouvez me contacter à **[yann.ducrest@gmail.com](mailto:yann.ducrest@gmail.com)**.

Pour faciliter le diagnostic, indiquez si possible :

- ce que vous essayiez de faire ;
- le nombre d'équipes et de salles ;
- le message d'erreur affiché ;
- une capture d'écran.

</details>

---

## Pour aller plus loin

<details>
<summary><strong>⚙️ Fonctionnement du moteur</strong></summary>

<br>

Le planning est formulé comme un problème d'optimisation **MILP** (*Mixed-Integer Linear Programming*).

Le moteur utilise :

- `scipy.optimize.milp`
- le solveur **HiGHS**

Les contraintes obligatoires assurent la validité du planning.  
Le solveur optimise ensuite la qualité de la solution parmi les plannings valides.

Une validation indépendante contrôle le résultat après résolution.

</details>

<details>
<summary><strong>🧪 Tests</strong></summary>

<br>

```bash
python -m pytest -q
```

La suite de tests vérifie les principales contraintes du moteur sur différentes configurations de finales.

</details>

<details>
<summary><strong>📚 Documentation technique</strong></summary>

<br>

- [`PROJECT_SOURCE.md`](PROJECT_SOURCE.md) — fonctionnement interne du projet
- [`VERIFICATION.md`](VERIFICATION.md) — vérification et validation

</details>

---

<a id="contact"></a>

## Aide & contact

<div align="center">

**Une question, une suggestion ou un problème ?**

<br><br>

<a href="mailto:yann.ducrest@gmail.com">
  <img src="https://img.shields.io/badge/CONTACTER%20YANN-00A0AE?style=for-the-badge&logo=gmail&logoColor=white" alt="Contacter Yann">
</a>
&nbsp;
<a href="https://github.com/YDucrest">
  <img src="https://img.shields.io/badge/GITHUB-YDucrest-173642?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Yann Ducrest">
</a>

<br><br>

**Yann Ducrest**  
Auteur & mainteneur

</div>

---

<div align="center">

<img src="assets/logo.png" alt="YES — Young Enterprise Switzerland" width="64">

### Un planning plus simple à préparer.  
### Une finale plus simple à organiser.

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="https://img.shields.io/badge/OUVRIR%20LE%20PLANIFICATEUR-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white" alt="Ouvrir le planificateur">
</a>

</div>
