# Vérification de la version UI simplifiée

## Résultat automatisé

```text
9 passed
```

Commande :

```bash
python -m pytest -q
```

## Points vérifiés

- le moteur d’optimisation reste valide après la refonte de l’interface ;
- les salles restent dédiées à une catégorie lorsque c’est possible ;
- une salle frontière ne change de catégorie qu’une fois lorsqu’un partage est inévitable ;
- les contraintes absolues restent validées indépendamment ;
- le mélange `Question 1` / `Question 2` dans une salle n’est plus classé comme anomalie ou préférence non satisfaite ;
- les fichiers Python se compilent sans erreur avec `python -m compileall`.

## Interface

La version actuelle :

- supprime la navigation latérale ;
- présente un parcours vertical en quatre étapes ;
- charge automatiquement `assets/logo.png` ;
- utilise une palette bleu pétrole / turquoise ;
- affiche le planning sous forme de cartes par salle et par session ;
- isole les contrôles techniques dans un onglet séparé ;
- conserve une vue tableau complète pour les besoins opérationnels.

L’environnement de construction ne contient pas Streamlit ; l’interface n’a donc pas été démarrée graphiquement dans cet environnement. Le code a été compilé et le moteur a été testé automatiquement.
