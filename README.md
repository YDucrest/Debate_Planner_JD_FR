<div align="center">

<img src="assets/logo.png" alt="YES — Young Enterprise Switzerland" width="130">

# Planificateur de débats

### La jeunesse débat

**Préparez une finale régionale et générez automatiquement un planning clair, équilibré et prêt à l'emploi.**

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="https://img.shields.io/badge/▶%20OUVRIR%20L'APPLICATION-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white" alt="Ouvrir l'application">
</a>
&nbsp;
<a href="#-installation-locale">
  <img src="https://img.shields.io/badge/↓%20INSTALLER%20EN%20LOCAL-28647A?style=for-the-badge&logo=python&logoColor=white" alt="Installer en local">
</a>

<br><br>

<img src="https://img.shields.io/badge/Streamlit-00A0AE?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit">
<img src="https://img.shields.io/badge/Python-3.11+-28647A?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Optimisation-MILP-173642?style=flat-square" alt="MILP">
<img src="https://img.shields.io/badge/Sauvegarde-SQLite-008B98?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">

<br><br>

**[Découvrir](#-le-principe)** ·
**[Utiliser](#-comment-ça-marche)** ·
**[Sauvegarder](#-en-ligne-ou-en-local-)** ·
**[Installer](#-installation-locale)** ·
**[FAQ](#-faq)** ·
**[Contact](#-aide--contact)**

</div>

---

## ✦ Le principe

Le **Planificateur de débats** automatise la préparation des finales régionales de **La jeunesse débat**.

Vous renseignez les équipes et les salles disponibles.  
L'application s'occupe du reste.

<br>

<table>
<tr>
<td align="center" width="25%">

### 01

**Événement**

Nom de la finale  
et catégories

</td>
<td align="center" width="25%">

### 02

**Équipes**

Établissements  
et participant·es

</td>
<td align="center" width="25%">

### 03

**Salles**

Nombre de salles  
disponibles

</td>
<td align="center" width="25%">

### 04

**Planning**

Génération et  
validation automatique

</td>
</tr>
</table>

<div align="center">

**Événement　→　Équipes　→　Salles　→　Planning**

Une seule page. Quatre étapes. Aucun planning à construire manuellement.

</div>

---

## ✨ Ce que l'application fait pour vous

<table>
<tr>
<td width="33%" valign="top">

### 🎯 2 débats

Chaque équipe participe à **exactement deux débats**.

</td>
<td width="33%" valign="top">

### ❓ 2 questions

Chaque équipe traite une fois **Question 1** et une fois **Question 2**.

</td>
<td width="33%" valign="top">

### 👥 Rôles équilibrés

Les participant·es alternent automatiquement les rôles **1 ↔ 2**.

</td>
</tr>

<tr>
<td width="33%" valign="top">

### 🤝 Rencontres optimisées

Le moteur cherche à diversifier les adversaires et à limiter les rencontres au sein d'un même établissement.

</td>
<td width="33%" valign="top">

### 🚪 Salles organisées

Les salles et les catégories sont réparties de manière cohérente pour faciliter le déroulement de la finale.

</td>
<td width="33%" valign="top">

### ✅ Planning vérifié

Chaque résultat est soumis à une **validation indépendante** avant d'être affiché.

</td>
</tr>
</table>

---

## 🧭 Comment ça marche ?

### 1. Définir l'événement

Choisissez le nom de la finale et les catégories présentes :

`Secondaire 1`　`Secondaire 2`

Une seule catégorie ou les deux peuvent être organisées simultanément.

### 2. Ajouter les équipes

Ajoutez les établissements et indiquez leur nombre d'équipes.

Les équipes sont créées automatiquement :

`Équipe A`　`Équipe B`　`Équipe C`　…

Les noms des participant·es peuvent être ajoutés si nécessaire.

### 3. Indiquer les salles

Renseignez simplement le nombre de salles disponibles.

L'application vérifie immédiatement que la configuration peut fonctionner.

### 4. Générer

Le moteur optimise automatiquement :

**sessions · rencontres · questions · rôles · côtés · salles**

Le planning est ensuite présenté sous forme de cartes par session et par salle, avec une vue tableau complète.

<br>

<div align="center">

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="https://img.shields.io/badge/▶%20CRÉER%20UN%20PLANNING-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white" alt="Créer un planning">
</a>

</div>

---

## 🌐 En ligne ou en local ?

<table>
<tr>
<td width="50%" valign="top">

### 🌐 Utiliser en ligne

**Le plus simple pour commencer.**

- aucune installation ;
- fonctionne directement dans le navigateur ;
- même interface que la version locale ;
- idéal pour générer rapidement un planning.

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="https://img.shields.io/badge/OUVRIR%20L'APPLICATION-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white">
</a>

</td>

<td width="50%" valign="top">

### 💾 Utiliser en local

**Le bon choix pour conserver vos événements.**

- application installée sur votre ordinateur ;
- données enregistrées localement ;
- événements disponibles lors des prochaines utilisations ;
- aucune base de données externe nécessaire.

<br>

<a href="#-installation-locale">
  <img src="https://img.shields.io/badge/INSTALLER%20EN%20LOCAL-28647A?style=for-the-badge&logo=python&logoColor=white">
</a>

</td>
</tr>
</table>

> [!IMPORTANT]
> La version en ligne ne doit pas être utilisée comme système de sauvegarde permanent.
>
> Pour **enregistrer un événement et le retrouver plus tard**, utilisez la version locale.

En local, toutes les sauvegardes sont conservées dans :

```text
data/app.db
```

> [!TIP]
> **Conservez ce fichier.**
>
> Il contient vos événements sauvegardés et peut être copié lors d'un changement d'ordinateur ou d'une mise à jour de l'application.

---

## 💻 Installation locale

<details>
<summary><strong>Je n'ai jamais installé un projet Python</strong></summary>

<br>

Pas besoin de connaître Git ou de programmer.

### 1 · Télécharger le projet

Sur cette page GitHub, cliquez sur :

**Code → Download ZIP**

Puis extrayez le fichier ZIP sur votre ordinateur.

### 2 · Installer Python

L'application nécessite **Python 3.11 ou plus récent**.

Pour vérifier votre version :

```bash
python --version
```

### 3 · Ouvrir un terminal

Ouvrez **PowerShell** ou un terminal dans le dossier téléchargé, puis suivez les instructions correspondant à votre système ci-dessous.

</details>

<br>

<details open>
<summary><strong>🪟 Windows — PowerShell</strong></summary>

<br>

#### Première installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

#### Utilisations suivantes

```powershell
.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

</details>

<details>
<summary><strong>🍎 macOS / 🐧 Linux</strong></summary>

<br>

#### Première installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

#### Utilisations suivantes

```bash
source .venv/bin/activate
python -m streamlit run app.py
```

</details>

<br>

L'application s'ouvre normalement automatiquement.

Sinon :

```text
http://localhost:8501
```

---

## ❔ FAQ

<details>
<summary><strong>Dois-je installer quelque chose pour utiliser l'application ?</strong></summary>

<br>

**Non.**

La version en ligne est directement disponible ici :

https://debate-planner-jd-fr.streamlit.app/

L'installation locale est surtout nécessaire si vous souhaitez **conserver durablement vos événements**.

</details>

<details>
<summary><strong>Puis-je sauvegarder mes événements dans la version en ligne ?</strong></summary>

<br>

La version hébergée utilise également la base de données de l'application, mais son stockage distant ne doit pas être considéré comme permanent.

Pour une sauvegarde fiable, utilisez la version **locale**.

</details>

<details>
<summary><strong>Dois-je renseigner les noms des participant·es ?</strong></summary>

<br>

Non.

Vous pouvez simplement renseigner les établissements et le nombre d'équipes.

Les noms sont utiles si vous souhaitez gérer précisément les rôles individuels des deux participant·es.

</details>

<details>
<summary><strong>Que se passe-t-il si ma configuration est impossible ?</strong></summary>

<br>

L'application effectue des contrôles avant de lancer l'optimisation.

Si le nombre d'équipes ou de salles ne permet pas de créer un planning valide, vous êtes averti immédiatement.

</details>

<details>
<summary><strong>Une salle peut-elle accueillir Question 1 et Question 2 ?</strong></summary>

<br>

Oui.

C'est un fonctionnement parfaitement normal et cela n'est pas considéré comme un problème par le moteur d'optimisation.

</details>

<details>
<summary><strong>J'ai trouvé un bug ou quelque chose ne fonctionne pas.</strong></summary>

<br>

Vous pouvez me contacter à :

**[yann.ducrest@gmail.com](mailto:yann.ducrest@gmail.com)**

Si possible, indiquez :

- ce que vous essayiez de faire ;
- le nombre d'équipes et de salles ;
- le message d'erreur ;
- une capture d'écran si elle peut aider.

</details>

---

## ⚙️ Sous le capot

> Cette section n'est **pas nécessaire pour utiliser l'application**.

<details>
<summary><strong>Technologies utilisées</strong></summary>

<br>

| Technologie | Rôle |
|---|---|
| **Streamlit** | interface utilisateur |
| **Python** | logique de l'application |
| **SciPy** | formulation MILP |
| **HiGHS** | résolution du problème d'optimisation |
| **SQLite** | sauvegarde locale |

</details>

<details>
<summary><strong>Comment fonctionne l'optimisation ?</strong></summary>

<br>

Le planning est formulé comme un problème de **programmation linéaire en nombres entiers mixtes — MILP**.

Le moteur utilise :

```python
scipy.optimize.milp
```

avec le solveur **HiGHS**.

Les contraintes obligatoires garantissent notamment :

- exactement deux débats par équipe ;
- une Question 1 et une Question 2 ;
- aucune double participation pendant une même session ;
- la rotation des rôles individuels ;
- le respect du nombre de salles disponibles.

Parmi les solutions valides, le solveur cherche ensuite à améliorer la qualité générale du planning : nombre de sessions, diversité des rencontres, côtés, salles et chronologie.

</details>

<details>
<summary><strong>Exécuter les tests</strong></summary>

<br>

```bash
python -m pytest -q
```

Les tests couvrent notamment différentes tailles de finales, les deux catégories, les configurations avec peu de salles, plusieurs équipes d'un même établissement et les principales contraintes du moteur.

</details>

---

## 📚 Documentation

La documentation technique détaillée est volontairement séparée du README afin de garder cette page simple et accessible.

**[`PROJECT_SOURCE.md`](PROJECT_SOURCE.md)**  
Structure et fonctionnement interne du projet.

**[`VERIFICATION.md`](VERIFICATION.md)**  
Informations de vérification et de validation.

---

## ✉️ Aide & contact

<table>
<tr>
<td width="65%" valign="middle">

### Une question ? Une suggestion ? Un problème ?

Vous pouvez me contacter directement pour signaler un bug, poser une question ou proposer une amélioration.

**Yann Ducrest**  
Auteur et mainteneur

</td>

<td width="35%" align="center" valign="middle">

<a href="mailto:yann.ducrest@gmail.com">
  <img src="https://img.shields.io/badge/ENVOYER%20UN%20E--MAIL-00A0AE?style=for-the-badge&logo=gmail&logoColor=white">
</a>

<br><br>

<a href="https://github.com/YDucrest">
  <img src="https://img.shields.io/badge/GITHUB-YDucrest-173642?style=for-the-badge&logo=github&logoColor=white">
</a>

</td>
</tr>
</table>

---

<div align="center">

<img src="assets/logo.png" alt="YES — Young Enterprise Switzerland" width="80">

<br>

### La jeunesse débat

**Un planning plus simple à préparer.  
Une finale plus simple à organiser.**

<br>

<a href="https://debate-planner-jd-fr.streamlit.app/">
  <img src="https://img.shields.io/badge/▶%20OUVRIR%20LE%20PLANIFICATEUR-00A0AE?style=for-the-badge&logo=streamlit&logoColor=white">
</a>

<br><br>

<sub>Développé par <strong>Yann Ducrest</strong></sub>

</div>