# Bibliothèque de ressources PMP

Cette bibliothèque constitue le point d'accès unique aux ressources
applicatives officielles de PMP. Les consommateurs utilisent une clé métier et
ne construisent jamais eux-mêmes le chemin physique d'un fichier.

## Familles

Les ressources sont réparties entre logos, icônes, bannières, filigranes,
modèles documentaires, polices et ressources techniques de l'application.
Chaque famille possède sa propre énumération.

Les photographies et signatures personnelles sont des données utilisateur :
elles ne font pas partie de cette bibliothèque embarquée.

## Conventions

- Les valeurs des Enum sont des identifiants logiques stables, jamais des
  chemins.
- Les chemins du catalogue sont relatifs à la racine `app/resources`.
- Un fichier physique peut être renommé sans modifier ses consommateurs.
- Les ressources cartographiques et leurs licences restent groupées.
- Une ressource absente provoque une erreur explicite ; aucun remplacement
  silencieux n'est effectué.

## Catalogue

`catalog.py` contient uniquement les correspondances officielles entre les
clés logiques et les chemins relatifs. Il ne contient aucune résolution,
validation ou opération d'accès au disque.

Les entrées sous `assets/` préparent les familles dont les fichiers officiels
ne sont pas encore livrés. Les ressources historiques sous `images/` et `map/`
restent en place pendant la phase d'infrastructure.

## ResourceManager

`ResourceManager` est le seul composant autorisé à résoudre une clé. Il valide
la famille demandée, empêche la sortie de la racine, vérifie que la cible est
un fichier et retourne un `pathlib.Path`.

Les interfaces et futurs exporteurs restent responsables de convertir ce
chemin dans leur propre format technique. La bibliothèque ne dépend ni de
PySide6, ni de Word, ni de PDF.

## Utilisation

Les consommateurs demandent une ressource par son identité fonctionnelle :

```python
resources = ResourceManager()
logo_path = resources.logo(Logo.PMP)
```

Les chemins littéraux du catalogue ne doivent pas être copiés dans les
composants consommateurs.

Les profils communaux, thèmes et métadonnées graphiques sont volontairement
reportés à une évolution ultérieure.
