# Architecture cible — Bilan quotidien

## Sprint 3.8.0 — Validation finale

## 1. Statut et périmètre

L’architecture du bilan quotidien est validée selon le modèle **Provider → Registry → Service → résultat agrégé**, déjà éprouvé par la cartographie opérationnelle.

Le rapport sera initialement calculé à la demande. Le premier périmètre n’introduit ni table centrale de duplication, ni snapshot, ni exporteur.

Ce document fige l’architecture cible, les responsabilités, les contrats conceptuels, la politique d’erreur, les règles structurantes, les éléments différés, les risques et la feuille de route. Il n’autorise aucune implémentation fonctionnelle du Sprint 3.8.1 avant validation explicite.

## 2. Architecture cible

```text
Modules métier autonomes
    │
    ├── DailyReportProvider
    │       └── collect(report_date)
    │
    └── DailyReportItem (DTO immuable)
            │
            ▼
    DailyReportRegistry
            │
            ▼
    DailyReportService.generate(report_date)
            │
            ▼
    DailyReport
            │
            ├── Aperçu écran
            ├── Export Word
            ├── Export PDF
            ├── Impression
            └── Archivage / envoi
```

Chaque module métier reste autonome. Il ne dépend ni du moteur de synthèse ni d’un autre module métier. Son provider constitue l’adaptateur entre le service du module et le contrat transversal du rapport quotidien.

Flux métier cible :

```text
DailyReportProvider
    → DailyReportItem
    → DailyReportService
    → DailyReport
    → Renderer / Exporter
```

## 3. Objets transversaux

### 3.1 DailyReportItem

`DailyReportItem` représente la contribution normalisée d’un module au bilan quotidien. Il s’agit exclusivement d’un DTO de frontière entre un module et le moteur de synthèse.

Il doit être :

- typé ;
- minimal ;
- immuable ;
- utilisé uniquement en lecture ;
- indépendant des modèles persistants et de la présentation.

La recommandation technique pour son implémentation future est `@dataclass(frozen=True)`.

`DailyReportItem` ne doit être :

- ni une superclasse des modèles métier ;
- ni une table SQLite centrale ;
- ni un dictionnaire générique fourre-tout ;
- ni un mécanisme de duplication des données sources.

Son contrat devra contenir uniquement les informations nécessaires à l’agrégation, au classement et au calcul des résultats attendus.

### 3.2 DailyReport

`DailyReport` représente le résultat agrégé pour une journée. Il doit conceptuellement pouvoir exposer :

- la date concernée ;
- les éléments collectés et ordonnés ;
- les regroupements utiles ;
- les totaux calculés ;
- les avertissements rencontrés pendant la collecte ;
- un indicateur signalant que le rapport est partiel.

Dans le premier périmètre, `DailyReport` est calculé à la demande et n’est pas persisté.

### 3.3 DailyReportWarning

`DailyReportWarning`, ou un objet typé équivalent, décrit une anomalie non bloquante survenue pendant la génération.

Il doit permettre d’identifier au minimum :

- le provider concerné ;
- la nature ou le message de l’erreur ;
- le fait que sa contribution est absente ou incomplète.

Un avertissement est une donnée explicite du résultat. Il ne remplace pas la journalisation technique éventuelle de l’exception.

## 4. Contrat DailyReportProvider

Le nom de la méthode doit exprimer une transformation et non une simple lecture. Le contrat recommandé est :

```python
class DailyReportProvider(ABC):
    @abstractmethod
    def collect(self, report_date: date) -> Iterable[DailyReportItem]:
        ...
```

`build_items(report_date)` reste une appellation acceptable si elle est retenue uniformément, mais `collect(report_date)` constitue le choix privilégié.

Le provider :

- interroge le service public de son module ;
- récupère les données correspondant à la journée ;
- transforme les modèles métier ;
- construit une collection de `DailyReportItem` ;
- ne contient aucune logique d’affichage ;
- ne modifie aucune donnée métier.

Chaque provider doit également pouvoir être déclaré **essentiel** ou **non essentiel**. Cette caractéristique fait partie de son enregistrement ou de ses métadonnées explicites ; elle ne doit pas être déduite implicitement de son nom ou de sa position dans le registre.

Pour le premier périmètre :

- le provider du Journal pourra être déclaré essentiel ;
- les autres providers pourront initialement être déclarés non essentiels.

Cette classification devra rester configurable et testable.

## 5. DailyReportRegistry

`DailyReportRegistry` centralise les providers enregistrés lors de la composition de l’application.

Il doit :

- enregistrer les providers de manière explicite ;
- vérifier qu’ils respectent le contrat attendu ;
- conserver ou exposer leur caractère essentiel ;
- permettre au moteur d’énumérer les contributions disponibles.

Il ne doit contenir aucune logique SQL, métier, d’agrégation ou de présentation.

Il reste distinct de `MapRegistry` et d’un éventuel futur `ModuleRegistry`.

## 6. DailyReportService

L’interface cible du moteur est :

```python
generate(report_date: date) -> DailyReport
```

`DailyReportService` doit uniquement :

- recevoir et valider une date ;
- interroger `DailyReportRegistry` ;
- collecter les contributions des providers ;
- appliquer la politique d’erreur ;
- fusionner les éléments ;
- les trier et les ordonner ;
- calculer les totaux métier utiles ;
- construire et retourner un `DailyReport`.

Il ne doit pas :

- exécuter de SQL ou connaître les tables SQLite ;
- dépendre des pages UI ;
- construire du HTML ;
- définir une mise en page ;
- produire un PDF ou un document Word ;
- imprimer, archiver ou envoyer un rapport ;
- modifier les données métier ;
- contourner les services publics des modules.

## 7. Politique d’erreur

Aucune exception provenant d’un provider ne doit être ignorée silencieusement.

### 7.1 Échec d’un provider essentiel

Lorsqu’un provider essentiel échoue :

- la génération est arrêtée ;
- une erreur explicite est retournée à l’appelant ;
- aucun `DailyReport` présenté comme exploitable n’est produit.

L’erreur doit identifier le provider en cause et conserver une cause technique exploitable, sans exposer inutilement des détails internes à l’utilisateur final.

### 7.2 Échec d’un provider non essentiel

Lorsqu’un provider non essentiel échoue :

- la génération se poursuit ;
- les contributions déjà collectées sont conservées ;
- un avertissement est ajouté au `DailyReport` ;
- le rapport est explicitement marqué comme partiel.

Le rapport partiel ne doit jamais être présenté comme complet. L’aperçu et les futurs exporteurs devront rendre cet état et ses avertissements visibles.

### 7.3 Invariants

- `is_partial` est vrai dès qu’une contribution non essentielle attendue n’a pas pu être collectée complètement.
- Chaque échec non bloquant produit un avertissement identifiable.
- Les totaux sont calculés exclusivement à partir des éléments effectivement collectés.
- La politique d’erreur ne transforme jamais une erreur d’un provider essentiel en simple avertissement.
- Le traitement d’une exception ne provoque aucune modification des données métier.

## 8. Tri, ordre et règles temporelles

Les règles exactes seront fixées dans le Sprint 3.8.1 avant l’implémentation du moteur.

Elles devront définir explicitement :

- l’ordre des sections ou catégories ;
- la priorité entre providers ;
- les critères de tri des éléments au sein d’une section ;
- un départage stable en cas d’égalité ;
- le fuseau horaire de référence ;
- les bornes inclusives et exclusives d’une journée ;
- le traitement des dates ou heures absentes ;
- le comportement lors des changements d’heure.

Le résultat doit être déterministe : les mêmes données sources et la même date doivent produire le même ordre et les mêmes totaux.

## 9. Structure standard des modules

Tous les nouveaux modules devront suivre une structure cohérente :

```text
module/
├── models/
├── repositories/
├── services/
├── providers/
└── ui/
```

Le dossier `providers/` pourra notamment contenir :

```text
providers/
├── verbalization_report_provider.py
└── verbalization_map_provider.py
```

Un provider cartographique ne doit être créé que si les données du module sont géolocalisables.

Cette organisation cible s’applique notamment aux modules Verbalisations, Police Route, Interventions, Dossiers, Stationnements abusifs et aux futurs modules métier. La migration des modules existants devra être progressive et réalisée dans des jalons dédiés.

## 10. Règle concernant le Journal

Le Journal est un module métier autonome.

Il ne doit jamais devenir :

- le réceptacle universel des informations des autres modules ;
- une table de duplication ;
- un stockage intermédiaire du bilan quotidien ;
- un bus d’événements transversal implicite.

Les modules Verbalisations, Police Route, Interventions, Dossiers ou Stationnements abusifs ne doivent pas écrire automatiquement leurs données dans la table Journal pour alimenter le bilan.

Le bilan est construit en lecture par les providers de chaque module :

```text
Verbalisations ──┐
Police Route ────┤
Interventions ───┼── DailyReportProviders ── DailyReportService
Dossiers ────────┤
Journal ─────────┘
```

Le Journal contribue au rapport selon le même principe que les autres modules, même si son provider est initialement considéré comme essentiel.

## 11. Composition et injection

La centralisation de la composition des repositories, services, registries et pages constitue l’objectif architectural :

- une racine de composition unique ;
- aucun service instancié directement dans une page UI ;
- repositories injectables ;
- services partagés de manière cohérente ;
- registries construits au démarrage ;
- tests simplifiés par substitution des dépendances.

Ce refactoring ne doit pas être mélangé à la création du module Verbalisations. Il relève du Sprint 3.8.7.

## 12. ModuleRegistry — extension future

Un `ModuleRegistry` distinct pourra être étudié ultérieurement afin de :

- déclarer les modules installés ou actifs ;
- fournir leurs métadonnées ;
- faciliter la recherche globale ;
- permettre des statistiques transversales ;
- alimenter le tableau de bord ;
- préparer une éventuelle activation ou désactivation de modules.

Il ne remplace aucun registry spécialisé :

| Registry | Responsabilité unique |
|---|---|
| `DailyReportRegistry` | Contributions au bilan quotidien |
| `MapRegistry` | Contributions cartographiques |
| `ModuleRegistry` | Modules disponibles et métadonnées |

`ModuleRegistry` n’est pas nécessaire à la première implémentation du rapport quotidien et ne doit pas être codé prématurément.

## 13. Rendus et exports

Aucun `DailyReportExportService` ne doit être créé dans le premier périmètre.

Les étapes sont séparées :

1. génération des données ;
2. aperçu écran ;
3. export Word ;
4. export PDF ;
5. impression ;
6. archivage ou envoi.

Les renderers et exporteurs consomment exclusivement `DailyReport`. Ils ne dépendent jamais directement des modèles, repositories ou services métier de chaque module.

L’aperçu et les exports doivent présenter clairement les avertissements et l’état partiel du rapport.

## 14. Calcul à la demande et persistance

Le premier périmètre utilise le flux suivant :

```text
Clic utilisateur
    → DailyReportService.generate(date)
    → interrogation des providers
    → application de la politique d’erreur
    → agrégation
    → DailyReport
```

Aucune table de duplication ni aucun snapshot n’est prévu à ce stade.

La persistance d’un rapport ne sera envisagée que lorsqu’il faudra :

- figer officiellement une journée ;
- conserver des versions ;
- valider ou signer un rapport ;
- garantir sa traçabilité ;
- empêcher qu’une correction ultérieure des données métier ne modifie un bilan historique.

Cette évolution devra préciser les règles de versionnement, d’intégrité, de correction et de conservation.

## 15. Règles d’architecture figées

1. Chaque module possède ses propres modèles, repositories, services, providers et pages UI.
2. Chaque module peut exposer un `DailyReportProvider`.
3. Chaque module peut exposer un `MapProvider` si ses données sont géolocalisables.
4. Aucun module métier ne dépend directement d’un autre module métier.
5. Les providers de synthèse renvoient uniquement des `DailyReportItem` immuables.
6. Chaque provider de rapport est explicitement déclaré essentiel ou non essentiel.
7. `DailyReportService` agrège les données sans logique de présentation.
8. Les renderers et exporteurs sont séparés du moteur métier.
9. La base SQLite n’est jamais appelée directement depuis l’UI.
10. Le Journal n’est pas une table de duplication des autres modules.
11. Les nouveaux modules exposent des consultations filtrées par date au niveau service.
12. Les repositories restent responsables de la persistance propre à leur module.
13. Les registries spécialisés conservent une responsabilité unique.
14. Les exporteurs consomment `DailyReport`, jamais les modèles métier internes.
15. La génération d’un rapport ne modifie aucune donnée métier.
16. Aucune exception de provider n’est ignorée silencieusement.
17. Tout rapport incomplet est explicitement marqué comme partiel et documenté par des avertissements.

## 16. Éléments différés

Sont explicitement hors du premier périmètre :

- export Word ;
- export PDF ;
- impression ;
- archivage et envoi ;
- persistance et versionnement des rapports ;
- snapshots ;
- signature ou validation officielle ;
- `ModuleRegistry` ;
- activation dynamique des modules ;
- refactoring global de l’injection avant le Sprint 3.8.7 ;
- migration simultanée de tous les modules existants.

## 17. Risques et mesures de maîtrise

| Risque | Mesure recommandée |
|---|---|
| DTO générique devenant un fourre-tout | Définir un contrat minimal, typé et revu lors de chaque extension |
| Logique métier dupliquée dans les providers | Conserver les calculs propres au domaine dans les services métier |
| Dépendance du rapport aux tables SQLite | Autoriser uniquement les appels aux services des modules |
| Couplage entre données et rendu | Tester le moteur sans UI ni exporteur |
| Ordre des sections implicite | Définir une priorité et un tri stables dans les contrats |
| Exception ignorée ou rapport faussement complet | Appliquer la politique essentiel/non essentiel et exposer les avertissements |
| Provider mal classé comme non essentiel | Rendre la classification explicite, revue et couverte par des tests |
| Totaux trompeurs dans un rapport partiel | Signaler l’état partiel et calculer uniquement sur les éléments collectés |
| Totaux ambigus entre modules | Documenter l’unité, le sens et la source de chaque total |
| Dates et heures incohérentes | Figer le fuseau et les bornes journalières avant l’implémentation |
| Refactoring trop large avec Verbalisations | Isoler la composition et l’injection dans le Sprint 3.8.7 |
| Historique recalculé différemment | Introduire un snapshot uniquement lorsqu’un besoin officiel le justifie |

## 18. Feuille de route validée

### Sprint 3.8.1 — Contrats et politique d’erreur

- définir `DailyReportItem` ;
- définir `DailyReport` ;
- définir `DailyReportWarning` ou un équivalent ;
- définir `DailyReportProvider` ;
- définir le caractère essentiel d’un provider ;
- fixer les règles de tri ;
- fixer les règles temporelles ;
- écrire les tests de contrat.

Ce sprint ne doit pas être lancé avant validation explicite.

### Sprint 3.8.2 — Registry et moteur d’agrégation

- créer `DailyReportRegistry` ;
- créer `DailyReportService` ;
- implémenter la collecte multi-provider ;
- appliquer la politique de gestion des erreurs ;
- produire les rapports partiels et leurs avertissements ;
- calculer les totaux ;
- tester avec des providers factices.

### Sprint 3.8.3 — Première intégration réelle

- créer `JournalDailyReportProvider` ;
- ajouter une consultation du Journal par date au niveau service si nécessaire ;
- connecter le Journal au registry ;
- tester avec des données réelles ;
- ne modifier aucune donnée métier.

### Sprint 3.8.4 — Aperçu fonctionnel

- créer une page ou un dialogue simple ;
- permettre la sélection d’une date ;
- générer le `DailyReport` ;
- afficher les éléments, les totaux et les avertissements ;
- ne créer aucune mise en page définitive ;
- ne créer aucun export.

### Sprint 3.8.5 — Module Verbalisations

- créer les modèles ;
- créer le repository ;
- créer le service ;
- créer l’UI ;
- créer le `DailyReportProvider` ;
- créer un `MapProvider` seulement si nécessaire.

### Sprint 3.8.6 — Module Police Route

- créer les modèles ;
- créer le repository ;
- créer le service ;
- créer l’UI ;
- créer le `DailyReportProvider` ;
- créer un `MapProvider` pour les éléments géolocalisables.

### Sprint 3.8.7 — Composition et injection

- introduire une racine de composition unique ;
- injecter les services et repositories ;
- construire et partager les registries de manière cohérente ;
- supprimer progressivement les instanciations directes dans les pages.

### Sprint 3.8.8 — Exports et cycle de vie

- export Word ;
- export PDF ;
- impression ;
- archivage ;
- envoi ;
- étude du versionnement et des snapshots.
