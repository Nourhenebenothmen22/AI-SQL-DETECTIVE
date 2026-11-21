# 🕵️‍♂️ AI SQL Detective

<p align="center">
  <img src="frontend/public/logo.svg" width="380" alt="AI SQL Detective Logo" />
</p>

<p align="center">
  <strong>L'assistant d'investigation PostgreSQL IA de nouvelle génération, sécurisé par AST déterministe, orchestré par LangGraph et propulsé par une architecture 100% Free-Tier résiliente avec observabilité FinOps (EvalLaps).</strong>
</p>

<p align="center">
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/PostgreSQL-16.0-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL 16" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/LangGraph-Multi--Agent-FF6F00?style=flat-square&logo=langchain&logoColor=white" alt="LangGraph" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/SQLGlot-AST_Security-blueviolet?style=flat-square" alt="SQLGlot" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Next.js-15.5-black?style=flat-square&logo=next.js&logoColor=white" alt="Next.js 15" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/TypeScript-Strict-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript Strict" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/TailwindCSS-v4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Pytest-135_Passed-success?style=flat-square&logo=pytest&logoColor=white" alt="Pytest 135 Passed" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Playwright-E2E_Verified-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Playwright Verified" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/LLM-100%25_Free--Tier-06B6D4?style=flat-square&logo=lightning&logoColor=white" alt="100% Free-Tier" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/EvalLaps-LLMOps_%26_FinOps-6366F1?style=flat-square&logo=speedtest&logoColor=white" alt="EvalLaps LLMOps & FinOps" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Security-100%25_Deterministic-10B981?style=flat-square&logo=shield&logoColor=white" alt="Deterministic Security" /></a>
</p>

---

## 📑 Sommaire

1. [Captures d'Écran & Démonstration Visuelle](#-captures-décran--démonstration-visuelle)
2. [Le Problème Résolu & La Vision](#-le-problème-résolu--la-vision)
3. [Les Enjeux & L'Impact Métier](#-les-enjeux--limpact-métier)
4. [Les Acteurs & Personas Ciblés](#-les-acteurs--personas-ciblés)
5. [Architecture & Workflow Multi-Agents (LangGraph)](#-architecture--workflow-multi-agents-langgraph)
6. [Architecture LLM 100% Free-Tier & Résilience Multi-Fournisseurs](#-architecture-llm-100-free-tier--résilience-multi-fournisseurs)
7. [Sécurité en Profondeur (Defense-in-Depth)](#-sécurité-en-profondeur-defense-in-depth)
8. [Module EvalLaps (LLMOps & FinOps Observability)](#-module-evallaps-llmops--finops-observability)
9. [Catalogue des Fonctionnalités Clés](#-catalogue-des-fonctionnalités-clés)
10. [Spécification des Endpoints de l'API REST (`/api/v1`)](#-spécification-des-endpoints-de-lapi-rest-apiv1)
11. [Guide de Démarrage & Déploiement Pas-à-Pas](#-guide-de-démarrage--déploiement-pas-à-pas)
12. [Qualité, Tests & Intégration Continue (CI/CD)](#-qualité-tests--intégration-continue-cicd)
13. [Stack Technique Complète](#-stack-technique-complète)

---

## 📸 Captures d'Écran & Démonstration Visuelle

Découvrez l'interface moderne Obsidian Dark d'AI SQL Detective à travers ses différents modules :

### 1. 🔍 Workbench & Explorateur de Schéma PostgreSQL
> Vue d'ensemble de la console d'investigation avec l'arborescence complète des 9 tables relationnelles (`ecommerce.orders`, `customers`, `products`, `order_items`, `inventory`, `payments`, `reviews`, `categories`, `addresses`), le décompte en temps réel des lignes, le statut de connexion L4 et la barre de prompt naturelle.

![Workbench Overview](docs/screenshots/01_workbench_overview.png)

---

### 2. ⚡ Éditeur SQL Monaco & Inspection Détaillée des Tables
> Zoom sur la décomposition d'une table avec ses index B-Tree, types de données stricts et éditeur Monaco synchronisé avec la passerelle déterministe AST SQLGlot.

![Workbench Schema and Editor](docs/screenshots/02_workbench_schema_and_editor.png)

---

### 3. ⏱️ EvalLaps — Observabilité LLMOps, Quotas & Burn Rate
> Tableau de bord exécutif inspiré de Google AI Studio : métriques de consommation quotidienne et mensuelle, tokens restants, compte à rebours de réinitialisation automatique UTC 00:00:00, et vélocité de consommation (Burn Rate).

![EvalLaps FinOps Overview](docs/screenshots/04_evallaps_finops_overview.png)

---

### 4. 🔀 EvalLaps — Télémétrie I/O, Load Balancer & Agents Cognitifs
> Ventilation Input/Output (Prompts vs Complétions), surveillance de charge des clés et consommation par étape de pipeline d'agents (Analyste, Générateur, Réviseur, Optimiseur, Explicateur).

![EvalLaps Telemetry and Stages](docs/screenshots/05_evallaps_telemetry_and_stages.png)

---

### 5. 📊 Analytics — Tendances d'Exécution & Métriques de Latence
> Visualisation Recharts des temps de réponse (latence moyenne et pic en ms), répartition des statuts de requêtes (Passed, Optimized, Security Blocked) et historique d'activité.

![Analytics Dashboard](docs/screenshots/03_analytics_dashboard.png)

---

### 6. 🧪 EvalOps — Banc d'Évaluation & Golden Benchmarks
> Évaluation automatisée sur jeu de données de référence avec scoring de fidélité sémantique, exactitude syntaxique et télémétrie des modèles.

![EvalOps Benchmarks](docs/screenshots/06_evalops_benchmarks.png)

---

### 7. 📜 History — Grand Livre d'Audit des Requêtes
> Audit trail complet traquant chaque requête exécutée, son temps de traitement, le nombre de lignes retournées et la validation de sécurité déterministe.

![History Ledger](docs/screenshots/07_history_ledger.png)

---

## 💡 Le Problème Résolu & La Vision

### La Vulnérabilité des Approches "Text-to-SQL" Traditionnelles

La promesse de convertir le langage naturel en requêtes SQL via un modèle de langage (LLM) se heurte généralement à des obstacles critiques en environnement professionnel :

*   ❌ **Risque de Destruction de Données :** Un LLM non bridé peut halluciner ou exécuter des requêtes destructives (`DROP TABLE`, `DELETE`, `UPDATE`, `TRUNCATE` ou des CTEs modifiantes comme `WITH d AS (DELETE ...)`).
*   ❌ **Hallucinations Structurelles :** Le LLM invente des colonnes, des jointures inexistantes ou cible des bases arbitraires hors périmètre.
*   ❌ **Attaques par Injection & DoS :** Des invites malveillantes peuvent déclencher des fonctions d'évasion système (`pg_read_file`, `pg_sleep`, `lo_import`, `dblink`) ou saturer la mémoire avec des `SELECT *` sans clause `LIMIT`.
*   ❌ **Dépendance & Coûts Prohibitifs des Modèles Propriétaires :** Verrouillage technologique auprès de modèles payants (ex: OpenAI GPT-4o) avec des factures imprévisibles et des risques de blocage par épuisement de quota.
*   ❌ **Effet « Boîte Noire » :** Les analystes et développeurs reçoivent des chiffres sans savoir quelle requête exacte a tourné, sans explication des résultats et sans visibilité sur le plan d'exécution PostgreSQL.

### La Réponse d'AI SQL Detective

**AI SQL Detective** résout cette impasse grâce à deux principes d'ingénierie fondamentaux :

1.  **Le LLM n'est JAMAIS la frontière de sécurité :** Toutes les requêtes (générées par IA ou saisies manuellement) doivent être interceptées et validées par une **Passerelle de Sécurité Déterministe (AST SQLGlot)**, exécutées par un utilisateur PostgreSQL strictement restreint en lecture seule avec un quota de temps (`statement_timeout`) et de lignes obligatoire.
2.  **Souveraineté & Résilience Économique :** Fonctionnement à 100% sur un pool de modèles gratuits et généreux (Groq, SambaNova, OpenRouter, Google, Cloudflare, Cohere, z.ai, Meta) orchestré par un Circuit Breaker intelligent et audité en continu par le module FinOps **EvalLaps**.

---

## 🎯 Les Enjeux & L'Impact Métier

| Enjeu Clé | Défi Technique | Réponse Apportée par AI SQL Detective |
|:---|:---|:---|
| **Intégrité Absolue des Données** | Éviter toute écriture accidentelle ou injection SQL. | Rôle PostgreSQL `sql_detective_ro` avec `default_transaction_read_only = on` et validation AST SQLGlot bloquant 100% du DDL/DML. |
| **Démocratisation sans Risque** | Ouvrir la donnée aux profils non-techniques. | Pipeline LangGraph en 7 agents avec vulgarisation contextuelle des résultats (`Result Explainer`). |
| **Zéro Dépendance Financière** | Éliminer les coûts d'inférence LLM récurrents. | Architecture 100% Free-Tier multi-fournisseurs avec cascade de secours automatique et temps de réponse < 20ms sur Groq. |
| **Protection des Ressources DB** | Empêcher les requêtes bloquantes ou les scans complets non maîtrisés. | `statement_timeout` (5000ms), `lock_timeout` (1000ms) et analyse des plans `EXPLAIN (FORMAT JSON)` sans jamais exécuter `EXPLAIN ANALYZE`. |
| **Observabilité & FinOps** | Maîtriser la consommation de jetons et quantifier le ROI. | Module **EvalLaps** : grand livre comptable PostgreSQL (`app_meta.llm_token_ledger`), diagnostic des renouvellements de quota et calcul des économies vs GPT-4o. |

---

## 👥 Les Acteurs & Personas Ciblés

```mermaid
flowchart LR
    A["Analyste Métier & Product Owner"] -->|"Pose une question en langage naturel"| DETECTIVE["AI SQL Detective"]
    B["Développeur Backend & Data Engineer"] -->|"Édite du SQL dans Monaco & valide l'AST"| DETECTIVE
    C["Administrateur de Base (DBA)"] -->|"Audite les plans EXPLAIN & l'historique"| DETECTIVE
    D["Lead FinOps & Architecte LLMOps"] -->|"Supervise quotas, tokens & économies sur EvalLaps"| DETECTIVE
```

### 1. L'Analyste Data & Product Owner
*   **Besoin :** Extraire rapidement des insights chiffrés (ex. *"Quels sont les 5 meilleurs clients par chiffre d'affaires total livré ?"*) sans attendre la disponibilité d'un data engineer.
*   **Bénéfice :** Saisie intuitive, progression visuelle par étape (SSE), grille de résultats triable, synthèse explicative générée et badge de consommation de tokens en direct.

### 2. Le Développeur Fullstack & Data Engineer
*   **Besoin :** Prototyper des requêtes complexes sur un schéma relationnel riche sans risque d'endommager la base.
*   **Bénéfice :** Explorateur de catalogue PostgreSQL complet, éditeur Monaco professionnel avec coloration syntaxique sombre, détection immédiate des violations de sécurité et recommandations d'optimisation d'index B-Tree.

### 3. Le Database Administrator (DBA)
*   **Besoin :** Garantir que les requêtes ne dégradent pas la performance du cluster de production.
*   **Bénéfice :** Isolation stricte des schémas (`ecommerce` vs `app_meta`), détection proactive des scans séquentiels (`Seq Scan`), historique d'audit exhaustif et métriques de latence consolidées (Recharts).

### 4. Le Lead FinOps & Architecte LLMOps
*   **Besoin :** Diagnostiquer la santé des clés d'API, anticiper les épuisements de quota et quantifier les économies budgétaires.
*   **Bénéfice :** Dashboard EvalLaps dédié (`/evallaps`), suivi en temps réel du Circuit Breaker avec compte à rebours de renouvellement et calcul automatique des économies nettes.

---

## 🧠 Architecture & Workflow Multi-Agents (LangGraph)

AI SQL Detective orchestre son intelligence cognitive via une machine à états typée **LangGraph** articulée autour de **7 agents spécialisés**, sans aucune heuristique `if-else` dans les couches de décision métier (conformément à `.agent/roles.md`) :

```mermaid
flowchart TD
    START([Question Utilisateur / Prompt]) --> SA["1. Schema Analyst<br/>(Catalog Introspection Context)"]
    SA --> SG["2. SQL Generator<br/>(PostgreSQL 16 SELECT)"]
    SG --> QR{"3. Query Reviewer<br/>(Semantic & Logic Review)"}

    QR -- "Révision requise (retries < 2)" --> SG
    QR -- "Approuvé" --> ISG{"4. Independent Security Gate<br/>(100% Déterministe - AST SQLGlot)"}

    MANUAL([Édition manuelle Monaco SQL]) --> ISG

    ISG -- "Violations Détectées" --> BLOCKED([Statut BLOQUÉ<br/>Exécution Interdite])
    ISG -- "Certifié Conforme" --> EX["5. SQL Executor<br/>(Psycopg 3 - Read-Only - Timeout - Probe LIMIT+1)"]

    EX -- "Erreur d'Exécution (retries < 2)" --> SG
    EX -- "Succès" --> RE["6. Result Explainer<br/>(Synthèse Métier & Findings)"]
    EX -- "Succès (Plan Disponible)" --> OPT["7. Optimization Agent<br/>(Plan EXPLAIN JSON - Parallèle)"]

    RE --> END([Réponse Structurée & Streaming SSE])
    OPT --> END
```

### Description des 7 Nœuds du Graphe

1.  **Schema Analyst & Runtime Classifier :** Introspecte le catalogue PostgreSQL (`pg_catalog`), classifie dynamiquement l'intention métier (`aggregation`, `filtering`, `trend`, `cohort`, `anomaly`, `comparison`, `lookup`, `general`) et la complexité sémantique (`simple`, `moderate`, `complex`), formule la stratégie de génération optimale et sélectionne les tables, colonnes et clés de jointure pertinentes.
2.  **SQL Generator :** Formule une requête `SELECT` PostgreSQL 16 dialecte strict guidée dynamiquement par l'intention et la stratégie formulées par l'agent précédent.
3.  **Query Reviewer :** Valide la logique métier, la cohérence des jointures, les groupements `GROUP BY` et le traitement des valeurs `NULL`. Boucle de révision bornée à 2 tentatives max.
4.  **Independent Security Gate (Non-LLM) :** Analyse l'AST via SQLGlot. Rejette toute tentative d'écriture, les injections, les fonctions système et force le plafond `LIMIT`.
5.  **SQL Executor (Non-LLM) :** Exécute **uniquement** les requêtes certifiées par la Security Gate au sein d'une transaction `READ ONLY` avec timeout strict.
6.  **Result Explainer :** Traduit le résultat brut et les données retournées en une synthèse claire répondant précisément à la question.
7.  **Optimization Agent (Exécution Parallèle Non Bloquante) :** Analyse le plan `EXPLAIN (FORMAT JSON)` en parallèle du Result Explainer pour suggérer des index composites et optimiser les prédicats sans retarder l'affichage des résultats.

> [!NOTE]
> **Streaming SSE & Annulation :** L'endpoint `POST /api/v1/queries/ask/stream` émet en temps réel les événements de progression des 6 étapes principales, puis les événements d'optimisation. Si l'utilisateur quitte la page ou annule la requête, le backend intercepte `request.is_disconnected()`, positionne un `threading.Event` d'annulation et interrompt immédiatement l'exécution en base PostgreSQL.

---

## ⚡ Architecture LLM 100% Free-Tier & Résilience Multi-Fournisseurs

### Éradication du Modèle Payant OpenAI & Souveraineté Technique

Conformément à la directive d'architecture, **AI SQL Detective n'utilise aucun modèle commercial payant d'OpenAI**. 
* Les variables `OPENAI_API_KEY` ont été définitivement éradiquées du projet.
* L'accès LLM s'effectue au travers du protocole HTTP standardisé OpenAI-compatible (`model_provider="openai"` de LangChain), ce qui permet de piloter les infrastructures gratuites les plus performantes du marché avec une interopérabilité totale.

### Fournisseur Primaire & Chaîne de Repli (Failover Cascade)

Le système est configuré avec **Groq Cloud LPU** en fournisseur primaire par défaut (< 20ms de latence d'inférence), adossé à une cascade ordonnée de fournisseurs gratuits :

```
LLM_FALLBACK_CHAIN="groq,sambanova,openrouter,google,cohere,cloudflare,zai,meta"
```

```mermaid
flowchart LR
    REQ([Requête Cognitive]) --> G["1. Groq Cloud<br/>(qwen/qwen3.8-27b)"]
    G -- "HTTP 429 / Erreur" --> SN["2. SambaNova<br/>(gemma-4-31B-it)"]
    SN -- "HTTP 429 / Erreur" --> OR["3. OpenRouter<br/>(dolphin3.0-r1-mistral:free)"]
    OR -- "HTTP 429 / Erreur" --> GOOG["4. Google AI Studio<br/>(gemini-2.5-flash)"]
    GOOG -- "HTTP 429 / Erreur" --> COH["5. Cohere Platform<br/>(command-r-plus)"]
    COH -- "HTTP 429 / Erreur" --> CF["6. Cloudflare Workers AI<br/>(@cf/meta/llama-3.3-70b)"]
    CF -- "HTTP 429 / Erreur" --> ZAI["7. z.ai / Zhipu<br/>(glm-4-flash)"]
    ZAI -- "HTTP 429 / Erreur" --> META["8. Meta AI Direct<br/>(llama-3.3-70b-instruct)"]
```

### Cartographie des Modèles Vérifiés & Garantis HTTP 200

Chaque fournisseur gratuit est appairé avec un modèle testé et validé, garantissant l'absence d'erreurs 404/403 :

| Fournisseur | Variable Clé API | Modèle Garanti HTTP 200 | Atout Spécifique |
|:---|:---|:---|:---|
| **Groq Cloud** | `GROQ_API_KEYS` | `qwen/qwen3.8-27b` | Ultra-faible latence (< 20ms LPU) |
| **SambaNova Systems** | `SAMBANOVA_API_KEYS` | `gemma-4-31B-it` | Débit record (> 440 tokens/s sur SN40L) |
| **OpenRouter Hub** | `OPENROUTER_API_KEYS` | `cognitivecomputations/dolphin3.0-r1-mistral-24b:free` | Réseau distribué gratuit |
| **Google AI Studio** | `GOOGLE_API_KEYS` | `gemini-2.5-flash` | Raisonnement poussé & large contexte |
| **Cohere Platform** | `COHERE_API_KEYS` | `command-r-plus` | Analyse sémantique & extraction structurée |
| **Cloudflare Workers AI**| `CLOUDFLARE_API_KEYS` | `@cf/meta/llama-3.3-70b-instruct` | Inférence Edge mondiale |
| **z.ai Platform** | `ZAI_API_KEYS` | `glm-4-flash` | Inférence cognitive rapide |
| **Meta AI Direct** | `META_API_KEYS` | `llama-3.3-70b-instruct` | Modèle open-source de référence |

### Circuit Breaker Intelligent avec Quarantaine Adaptative

En cas de saturation de quota (`HTTP 429 Too Many Requests`) ou d'erreur d'autorisation (`HTTP 401/402`) :
1.  Le `LLMCircuitBreaker` isole **immédiatement et uniquement** l'empreinte de la clé concernée (`ex: groq:y3HA`) pour une durée paramétrable (TTL 300s).
2.  Le moteur bascule de manière transparente sur la clé suivante ou le fournisseur suivant dans la chaîne de repli, **sans interruption pour l'utilisateur**.
3.  À l'expiration du TTL, la clé est automatiquement réintégrée dans le pool sain.

---

## 🛡️ Sécurité en Profondeur (Defense-in-Depth)

La sécurité d'AI SQL Detective repose sur **5 niveaux hermétiques** :

```mermaid
flowchart LR
    L1["1. AST Security Gate<br/>(SQLGlot Validator)"] --> L2["2. Sealed Token<br/>(ValidatedSQL Artifact)"]
    L2 --> L3["3. PostgreSQL Isolation<br/>(3 Rôles Dédiés)"]
    L3 --> L4["4. Resource Boundaries<br/>(Timeouts & LIMIT+1 Probe)"]
    L4 --> L5["5. Secrets & Logging<br/>(SecretRedactingFilter)"]
```

### 1. Passerelle AST Déterministe (SQLGlot)
*   **Allowlist stricte de nœuds AST :** Seuls `exp.Select` et les unions en lecture seule sont permis.
*   **Interdiction catégorique :** `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `COPY`, `CALL`, `DO`, `EXECUTE`, `SET`, `LOCK`, `SELECT INTO`.
*   **Blocage des CTEs d'écriture :** Rejet systématique de constructs tels que `WITH x AS (DELETE ...) SELECT * FROM x`.
*   **Fonctions & Tables Système Interdites :** Rejet des tables et fonctions préfixées par `pg_`, `inet_`, `txid_`, `lo_`, `dblink_`.

### 2. Artefact Scellé `ValidatedSQL`
L'exécuteur SQL (`SQLExecutor`) refuse structurellement les chaînes de caractères brutes (`str`). Il exige obligatoirement une instance de la dataclass scellée `ValidatedSQL`, protégée par un jeton de sentinelle privé accessible uniquement par la Security Gate.

### 3. Isolation des Rôles PostgreSQL 16
La base de données est partitionnée entre 3 rôles aux privilèges minimaux :
*   `sql_detective_migrator` : Propriétaire des schémas `ecommerce` et `app_meta` (utilisé uniquement par Alembic et le script de seed).
*   `sql_detective_ro` : Dédié à l'exécution des requêtes du Workbench. Accès `SELECT` exclusif sur le schéma `ecommerce`. `default_transaction_read_only = on`. Zéro privilège sur `app_meta` ou `public`.
*   `sql_detective_app` : Dédié à la télémétrie. Accès restreint à `app_meta.query_runs` et `app_meta.llm_token_ledger`. Zéro accès en lecture/écriture sur `ecommerce`.

### 4. Sonde de Troncation Déterministe (`LIMIT + 1`)
Pour éviter la saturation de la mémoire et les faux positifs de troncature :
*   La passerelle injecte ou bride la clause `LIMIT` au plafond configuré (ex. 200 lignes).
*   Elle exécute une sonde à `LIMIT 201`. Si la base retourne 201 lignes, la 201ème ligne est retirée et l'indicateur `was_truncated = true` est positionné avec certitude, sans jamais tronquer faussement une table faisant exactement 200 lignes.
*   Application systématique de `statement_timeout = 5000ms` et `lock_timeout = 1000ms`.

### 5. Hygiène des Secrets & Masquage des Logs
*   Tous les mots de passe et DSNs sont encapsulés dans des objets Pydantic `SecretStr`.
*   Le filtre de journalisation `SecretRedactingFilter` intercepte et masque automatiquement les identifiants dans les URLs PostgreSQL (`postgresql://user:***@host`), les Bearer tokens et les clés d'API.
*   Les clés d'API ne sont **JAMAIS** persistées en clair en base : seule une empreinte anonymisée de 4 caractères (ex: `...y3HA`) est stockée pour l'audit.

---

## 📊 Module EvalLaps (LLMOps & FinOps Observability)

**EvalLaps** est le sous-système natif d'observabilité LLMOps et FinOps d'AI SQL Detective. Il permet de mesurer avec précision chirurgicale l'efficience des modèles, la consommation de tokens et la rentabilité financière de l'architecture gratuite.

```mermaid
flowchart TD
    AGENT["Agent Cognitif (LangChain Node)"] -->|"Usage Metadata natif"| CAPTURE["Capture Asynchrone"]
    CAPTURE --> LEDGER[("Table PostgreSQL<br/>app_meta.llm_token_ledger")]
    
    LEDGER --> FINOPS["Calculateur FinOps<br/>(Économies vs GPT-4o Reference)"]
    LEDGER --> RENEWAL["Moteur de Diagnostic Quotas<br/>(4 Profils de Renouvellement)"]
    LEDGER --> CB_HUD["Circuit Breaker Health HUD<br/>(Quarantaines & Décompte TTL)"]

    FINOPS --> DASHBOARD["Dashboard UI /evallaps & Workbench Badge"]
    RENEWAL --> DASHBOARD
    CB_HUD --> DASHBOARD
```

### 1. Le Grand Livre Comptable des Tokens (`app_meta.llm_token_ledger`)

Chaque appel cognitif (Schema Analyst, SQL Generator, Query Reviewer, Result Explainer, Optimization Agent) enregistre de manière asynchrone sa télémétrie dans PostgreSQL :
*   `run_id` (UUID) : Lien vers la session d'investigation.
*   `stage_id` : L'agent précis ayant sollicité le LLM.
*   `provider_name` : Le fournisseur d'inférence (`groq`, `sambanova`, etc.).
*   `key_fingerprint` : Empreinte sécurisée anonymisée (ex: `...y3HA`).
*   `prompt_tokens`, `completion_tokens`, `total_tokens` : Données de consommation exactes issues des métadonnées LangChain.
*   `estimated_savings_usd` : Économies nettes estimées.
*   `latency_ms`, `http_status` : Performance d'inférence et statut HTTP.

### 2. Calculateur d'Économies FinOps (Baseline GPT-4o)

EvalLaps compare en continu le coût réel engagé (**0,00 \$** grâce au pool gratuit) face aux tarifs de référence de l'industrie :
$$\text{Coût Référent} = \left(\text{Prompt Tokens} \times \frac{\$2.50}{1\,000\,000}\right) + \left(\text{Completion Tokens} \times \frac{\$10.00}{1\,000\,000}\right)$$
$$\text{Économies Financières Réalisées} = \text{Coût Référent} - \$0.00$$

### 3. Diagnostic des 4 Profils de Renouvellement de Quota

EvalLaps catégorise dynamiquement chaque fournisseur pour offrir une visibilité prédictive sur la recharge des quotas :
1.  **Sliding Window 1m (Fenêtre Glissante 60s) :** Réinitialisation continue du quota TPM/RPM toutes les 60 secondes (ex: Groq, SambaNova, Meta).
2.  **Rolling Daily 24h (Journalier Glissant) :** Remise à zéro automatique du compteur RPD chaque jour à 00:00 UTC (ex: Google AI Studio, Cloudflare Workers AI, OpenRouter).
3.  **Monthly Credits (Crédits Mensuels) :** Renouvellement de l'enveloppe le 1er de chaque mois calendaire (ex: Cohere Platform).
4.  **Quota Static Tier (Niveau Statique) :** Volume fixe d'expérimentation sans recharge automatique programmée (ex: z.ai).

### 4. Circuit Breaker Health HUD en Temps Réel

Accessible directement sur la page `/evallaps` avec actualisation continue par polling à 5 secondes :
*   **Statut Global du Pool :** Indicateur visuel `All Healthy` ou alerte `Keys Quarantined`.
*   **Gestion des Quarantaines :** Affichage de la clé mise à l'écart suite à une erreur 429, du code d'erreur HTTP, de la durée de mise en quarantaine et du compte à rebours précis avant réintégration.
*   **Visualiseur de Pipeline de Repli :** Chaîne de secours active montrant en direct vers quel fournisseur le trafic bascule.

---

## 🖥️ Catalogue des Fonctionnalités Clés

AI SQL Detective propose une interface DevTools haut de gamme (style Linear, Supabase, Vercel) articulée autour du thème **Obsidian Dark Workbench** (palette officielle `#070A12`, `#0D121F`, `#131B2E`, `#1E2B45`, `#6366F1`, `#06B6D4`, `#10B981`) avec alignement numérique strict `tabular-nums`, bordures de précision et contraste certifié WCAG AAA :

| Composant UI | Description & Capacités |
|:---|:---|
| **Schema Explorer** | Arborescence pliable des 9 tables e-commerce (`customers`, `orders`, etc.), avec recherche instantanée, détection visuelle des clés primaires (`PK`), clés étrangères (`FK`), types de données et nombre de lignes estimé. |
| **NL-to-SQL Composer** | Saisie en langage naturel inspirée de Linear/Perplexity avec boutons "pills" d'exemples rapides, suivi de progression interactif sur 6 étapes ordonnées (SSE) et affichage transparent du SQL généré. |
| **Monaco SQL Editor** | Éditeur professionnel intégré avec le thème sombre dédié `ai-sql-detective-dark`, coloration syntaxique PostgreSQL, indentation automatique, exécution au clavier (`Ctrl+Enter` / `Ctrl+↵`) et badge d'état certifié `READ-ONLY`. |
| **Grille de Résultats Interactive** | Tableau de données fluide avec en-têtes collants (*sticky headers*), zébrures douces, tri multi-colonnes (`aria-sort`), formatage typé (dates, devises, badges pour `NULL`), alerte de troncature et export instantané au format CSV. |
| **Security & Review Panel** | Rapport détaillé affichant le statut déterministe (`PASSED` / `BLOCKED`), la liste des 6 règles vérifiées par l'AST SQLGlot et les notes de révision sémantique. |
| **Optimization Panel** | Synthèse des métriques du plan `EXPLAIN (FORMAT JSON)` (coût total, nœud racine, scan séquentiel détecté) et propositions d'index B-Tree composites avec copie en un clic. |
| **Dashboard EvalLaps (`/evallaps`)** | Tableau de bord FinOps complet avec cartes KPI, répartition des tokens par agent (Recharts), catalogue des renouvellements de quota et HUD du Circuit Breaker. |
| **FinOps Live Badge (Workbench)** | Badge visuel sous les résultats SQL indiquant le fournisseur utilisé, les tokens consommés sur la requête et les économies nettes générées. |
| **Analytics Dashboard (Recharts)** | Tableaux de bord graphiques modernisés intégrant les 5 visualisations réelles : tendances de latence, donut des statuts, activité dans le temps, comparaisons et métriques des tables. |
| **Audit & History Log** | Consultation des exécutions passées paginées, filtrage par statut et bouton de rechargement direct dans le Workbench via le paramètre d'URL `?runId=`. |

---

## 📡 Spécification des Endpoints de l'API REST (`/api/v1`)

Tous les endpoints sont fortement typés avec Pydantic v2 et documentés via OpenAPI (`/docs`) :

| Méthode | Chemin | Modèle Entrant | Modèle Sortant | Description |
|:---:|:---|:---|:---|:---|
| `GET` | `/api/v1/health` | *-* | `HealthResponse` | Vérification de l'état du backend, connectivité PostgreSQL et configuration du LLM. |
| `GET` | `/api/v1/connections` | *-* | `ConnectionListResponse` | Liste des connexions cibles en lecture seule (les DSNs restent masqués côté backend). |
| `GET` | `/api/v1/schema` | `?connection_id=` | `SchemaIntrospectionResponse` | Introspection dynamique du catalogue PostgreSQL (`ecommerce`). |
| `POST` | `/api/v1/queries/validate` | `ValidateSQLRequest` | `ValidateSQLResponse` | Validation de sécurité déterministe par AST SQLGlot (sans exécution en base). |
| `POST` | `/api/v1/queries/execute` | `ExecuteSQLRequest` | `ExecuteSQLResponse` | Validation AST + Exécution en lecture seule + Plan `EXPLAIN JSON` + Télémétrie. |
| `POST` | `/api/v1/queries/ask` | `AskQueryRequest` | `AskQueryResponse` | Exécution synchrone du workflow complet des 7 agents LangGraph. |
| `POST` | `/api/v1/queries/ask/stream` | `AskQueryRequest` | `StreamingResponse` (SSE) | Streaming temps réel de la progression (6 étapes ordonnées + événements d'optimisation). |
| `GET` | `/api/v1/history` | `?limit=&offset=&status=` | `QueryRunHistoryResponse` | Historique paginé des exécutions enregistrées dans `app_meta.query_runs`. |
| `GET` | `/api/v1/history/{run_id}` | *-* | `QueryRunHistoryDetail` | Détail d'une exécution pour rechargement complet dans le Workbench. |
| `GET` | `/api/v1/analytics` | `?connection_id=` | `AnalyticsDashboardResponse` | Agrégations télémétriques et statistiques de taille/lignes des tables PostgreSQL. |
| `GET` | `/api/v1/evallaps/summary` | `?window_days=` | `EvalLapsSummaryResponse` | Synthèse FinOps : tokens consommés, requêtes 200 OK et économies cumulées en USD. |
| `GET` | `/api/v1/evallaps/providers` | `?window_days=` | `ProviderUsageResponse` | Consommation granulaire par fournisseur avec empreintes de clés anonymisées. |
| `GET` | `/api/v1/evallaps/stages` | `?window_days=` | `StageUsageResponse` | Répartition de la consommation de jetons (Prompt vs Completion) par agent. |
| `GET` | `/api/v1/evallaps/runs/{run_id}`| *-* | `RunLedgerDetailResponse` | Télémétrie détaillée de tous les appels LLM ayant constitué une exécution donnée. |
| `GET` | `/api/v1/evallaps/renewals` | *-* | `RenewalCatalogResponse` | Catalogue exhaustif des 10 fournisseurs avec périodicité de renouvellement et quotas. |
| `GET` | `/api/v1/evallaps/circuit-breaker`| *-* | `CircuitBreakerStatusResponse`| Statut live du Circuit Breaker : quarantaines actives, décomptes TTL et chaîne active. |
| `GET` | `/api/v1/evallaps/models` | `?window_days=` | `ModelBreakdownResponse` | Télémétrie granulaire par modèle, décomposition des coûts Input/Output et quotas restants. |
| `GET` | `/api/v1/evallaps/balance` | *-* | `LoadBalancerDistribution` | Répartition de charge déterministe (Load Balancer sans if-else) et modèle désigné. |

---

## 🚀 Guide de Démarrage & Déploiement Pas-à-Pas

### Prérequis Système
*   **Docker & Docker Compose**
*   **Python 3.11+ / 3.12+** avec le gestionnaire de paquets [**uv**](https://docs.astral.sh/uv/)
*   **Node.js 20+ / 22+** avec **npm**

---

### 1. Configuration de l'Environnement (Racine `.env`)

Copiez le template `.env.example` à la racine du projet et configurez vos identifiants :

```bash
cp .env.example .env
```

> [!TIP]
> **Port PostgreSQL Hôte :** Le port hôte est configuré par défaut sur `5434` (`POSTGRES_PORT=5434`) afin d'éviter tout conflit si vous avez déjà d'autres instances PostgreSQL locales sur les ports `5432` ou `5433`.

Variables recommandées dans le fichier `.env` :

```ini
# Base de données PostgreSQL
POSTGRES_DB=ai_sql_detective
POSTGRES_USER=postgres
POSTGRES_PASSWORD=votre_mot_de_passe_admin_local
POSTGRES_PORT=5434

PG_MIGRATOR_USER=sql_detective_migrator
PG_MIGRATOR_PASSWORD=votre_mot_de_passe_migrator_local

PG_RO_USER=sql_detective_ro
PG_RO_PASSWORD=votre_mot_de_passe_ro_local

PG_APP_USER=sql_detective_app
PG_APP_PASSWORD=votre_mot_de_passe_app_local

# DSNs Backend
DATABASE_RO_URL=postgresql+psycopg://sql_detective_ro:votre_mot_de_passe_ro_local@localhost:5434/ai_sql_detective
DATABASE_APP_URL=postgresql+psycopg://sql_detective_app:votre_mot_de_passe_app_local@localhost:5434/ai_sql_detective
DATABASE_MIGRATOR_URL=postgresql+psycopg://sql_detective_migrator:votre_mot_de_passe_migrator_local@localhost:5434/ai_sql_detective

# CORS (Frontend Next.js)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ==============================================================================
# CONFIGURATION LLM 100% FREE-TIER (ZÉRO OPENAI PAYANT)
# ==============================================================================
LLM_PROVIDER=groq
LLM_FALLBACK_CHAIN="groq,sambanova,openrouter,google,cohere,cloudflare,zai,meta"

# Fournisseurs Gratuits (ajoutez vos tokens)
GROQ_API_KEYS="gsk_..."
GROQ_MODEL="qwen/qwen3.8-27b"

SAMBANOVA_API_KEYS="..."
SAMBANOVA_MODEL="gemma-4-31B-it"

OPENROUTER_API_KEYS="sk-or-v1-..."
OPENROUTER_MODEL="cognitivecomputations/dolphin3.0-r1-mistral-24b:free"

GOOGLE_API_KEYS="AIzaSy..."
GOOGLE_MODEL="gemini-2.5-flash"

COHERE_API_KEYS="..."
COHERE_MODEL="command-r-plus"

CLOUDFLARE_API_KEYS="..."
CLOUDFLARE_MODEL="@cf/meta/llama-3.3-70b-instruct"

ZAI_API_KEYS="..."
ZAI_MODEL="glm-4-flash"
```

---

### 2. Démarrage de la Base, Migrations & Seeding Déterministe

Démarrez le conteneur PostgreSQL 16, appliquez les migrations Alembic (dont `0003_add_llm_token_ledger`) et injectez les **57 427 lignes de démonstration e-commerce** :

```bash
# Lancement du conteneur PostgreSQL isolé
docker compose up -d --wait postgres

# Installation des dépendances backend
cd backend
uv sync --extra dev

# Exécution des migrations réversibles Alembic
uv run alembic upgrade head

# Seeding déterministe (57 427 enregistrements reproductibles)
uv run python -m app.modules.database.seed
```

---

### 3. Lancement des Services en Local

Ouvrez deux terminaux distincts :

```bash
# Terminal 1 — Backend FastAPI (http://localhost:8000)
cd backend
uv run uvicorn app.main:create_app --factory --reload --port 8000
```

```bash
# Terminal 2 — Frontend Next.js (http://localhost:3000)
cd frontend
npm ci
npm run dev
```

Accédez à l'application sur [http://localhost:3000](http://localhost:3000) et au dashboard EvalLaps sur [http://localhost:3000/evallaps](http://localhost:3000/evallaps).

---

### 4. Déploiement Conteneurisé Complet (Docker Compose)

Vous pouvez également lancer la stack entière (PostgreSQL + Backend + Frontend) via Docker Compose :

```bash
docker compose --profile full up --build
```

---

## 🧪 Qualité, Tests & Intégration Continue (CI/CD)

Le projet fait l'objet d'une suite de vérification automatisée stricte :

```bash
# 1. Vérification du formatage et linting Python (Ruff)
cd backend
uv run ruff check .
uv run ruff format --check .

# 2. Exécution de la suite de tests Pytest (130 tests unitaires, EvalLaps, Circuit Breaker & intégration PG16)
uv run pytest -v

# 3. Contrôle du typage strict TypeScript et linting frontend
cd ../frontend
npm run typecheck
npm run lint

# 4. Compilation et vérification du build Next.js
npm run build

# 5. Tests End-to-End Playwright (Workbench, Sécurité, SSE, Analytics, History)
npm run test:e2e
```

### Pipeline GitHub Actions (`.github/workflows/ci.yml`)

À chaque `push` ou `pull request` sur la branche `main`, 4 jobs s'exécutent en parallèle :
1.  **Backend Lint & Unit Tests :** Ruff + Pytest unitaire, suite adversariale AST et tests d'observabilité EvalLaps.
2.  **Backend PostgreSQL 16 Integration :** Provisioning d'un conteneur éphémère PG16, migrations montantes/descendantes, seeding et tests d'isolation des rôles.
3.  **Frontend Typecheck & Build :** `tsc --noEmit`, ESLint et build de production Next.js.
4.  **Playwright End-to-End :** Démarrage de la stack complète et validation des parcours utilisateurs critiques.

---

## 🛠️ Stack Technique Complète

```
AI SQL DETECTIVE
├── Backend (Python 3.12 / FastAPI)
│   ├── LangGraph & LangChain      # Orchestration cognitive multi-agents
│   ├── SQLGlot                    # Parser & validateur déterministe d'AST SQL
│   ├── SQLAlchemy 2 & Psycopg 3   # Moteur ORM asynchrone et pilote PostgreSQL natif
│   ├── Pydantic v2 & Settings     # Typage strict et validation de schéma
│   ├── Alembic                    # Migrations de schéma (0001, 0002, 0003_llm_token_ledger)
│   ├── EvalLaps Service           # Module FinOps & comptabilité des tokens LLM
│   ├── LLMCircuitBreaker          # Tolérance aux pannes & quarantaines 429 adaptatives
│   └── uv                         # Gestionnaire de paquets ultra-rapide
│
├── Base de données (PostgreSQL 16)
│   ├── ecommerce schema           # 9 tables de données métier (57 427 lignes)
│   ├── app_meta schema            # Télémétrie d'audit (query_runs) et Grand Livre (llm_token_ledger)
│   └── 3 Rôles Dédiés             # sql_detective_ro, sql_detective_app, sql_detective_migrator
│
├── Frontend (Next.js 15.5.29 / React 19)
│   ├── TypeScript Strict          # Typage rigoureux bout-en-bout
│   ├── Obsidian Dark Workbench    # Design tokens DevTools (#070A12, #0D121F, #131B2E, #1E2B45)
│   ├── Tailwind CSS v4            # Utility-first styling avec tabular-nums natifs
│   ├── Monaco Editor              # Thème dédié ai-sql-detective-dark & raccourci Ctrl+Enter
│   ├── Recharts                   # Visualisation analytique et graphique de tokens empilés
│   ├── EvalLaps Dashboard         # Observabilité des tokens, renouvellements et HUD Circuit Breaker
│   ├── TanStack Query             # Gestion d'état serveur et cache réactif
│   └── Lucide React               # Iconographie unifiée à 16px
│
└── Infrastructure & Tests
    ├── Docker & Docker Compose    # Environnement de développement et production
    ├── Pytest & HTTPX             # 130 tests automatisés (100% verts)
    ├── Playwright                 # Tests End-to-End multi-navigateurs
    └── GitHub Actions             # Intégration continue automatisée
```

---

<p align="center">
  Conçu avec rigueur pour apporter la puissance de l'IA aux bases relationnelles, sans jamais transiger sur la sécurité ni dépendre de modèles payants.
</p>
