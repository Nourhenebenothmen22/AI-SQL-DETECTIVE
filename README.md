# 🕵️‍♂️ AI SQL Detective

<p align="center">
  <strong>L'assistant d'investigation PostgreSQL IA de nouvelle génération, sécurisé par AST déterministe et orchestré par LangGraph.</strong>
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
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Pytest-108_Passed-success?style=flat-square&logo=pytest&logoColor=white" alt="Pytest 108 Passed" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Playwright-6_E2E_Verified-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Playwright Verified" /></a>
  <a href="#-badges--technologies"><img src="https://img.shields.io/badge/Security-100%25_Deterministic-10B981?style=flat-square&logo=shield&logoColor=white" alt="Deterministic Security" /></a>
</p>

---

## 📑 Sommaire

1. [Le Problème Résolu & La Vision](#-le-problème-résolu--la-vision)
2. [Les Enjeux & L'Impact Métier](#-les-enjeux--limpact-métier)
3. [Les Acteurs & Personas Ciblés](#-les-acteurs--personas-ciblés)
4. [Architecture & Workflow Multi-Agents (LangGraph)](#-architecture--workflow-multi-agents-langgraph)
5. [Sécurité en Profondeur (Defense-in-Depth)](#-sécurité-en-profondeur-defense-in-depth)
6. [Catalogue des Fonctionnalités Clés](#-catalogue-des-fonctionnalités-clés)
7. [Spécification des Endpoints de l'API REST (`/api/v1`)](#-spécification-des-endpoints-de-lapi-rest-apiv1)
8. [Guide de Démarrage & Déploiement Pas-à-Pas](#-guide-de-démarrage--déploiement-pas-à-pas)
9. [Qualité, Tests & Intégration Continue (CI/CD)](#-qualité-tests--intégration-continue-cicd)
10. [Stack Technique Complète](#-stack-technique-complète)

---

## 💡 Le Problème Résolu & La Vision

### La Vulnérabilité des Approches "Text-to-SQL" Traditionnelles

La promesse de convertir le langage naturel en requêtes SQL via un modèle de langage (LLM) se heurte généralement à des obstacles critiques en environnement professionnel :

*   ❌ **Risque de Destruction de Données :** Un LLM non bridé peut halluciner ou exécuter des requêtes destructives (`DROP TABLE`, `DELETE`, `UPDATE`, `TRUNCATE` ou des CTEs modifiantes comme `WITH d AS (DELETE ...)`).
*   ❌ **Hallucinations Structurelles :** Le LLM invente des colonnes, des jointures inexistantes ou cible des bases arbitraires hors périmètre.
*   ❌ **Attaques par Injection & DoS :** Des invites malveillantes peuvent déclencher des fonctions d'évasion système (`pg_read_file`, `pg_sleep`, `lo_import`, `dblink`) ou saturer la mémoire avec des `SELECT *` sans clause `LIMIT`.
*   ❌ **Effet « Boîte Noire » :** Les analystes et développeurs reçoivent des chiffres sans savoir quelle requête exacte a tourné, sans explication des résultats et sans visibilité sur le plan d'exécution PostgreSQL.

### La Réponse d'AI SQL Detective

**AI SQL Detective** résout cette impasse grâce à un principe d'ingénierie fondamental : **Le LLM n'est JAMAIS la frontière de sécurité**.

> [!IMPORTANT]
> **Règle d'or de sécurité :** Toutes les requêtes (générées par IA ou saisies manuellement) doivent être interceptées et validées par une **Passerelle de Sécurité Déterministe (AST SQLGlot)**, exécutées par un utilisateur PostgreSQL strictement restreint en lecture seule avec un quota de temps (`statement_timeout`) et de lignes obligatoires.

---

## 🎯 Les Enjeux & L'Impact Métier

| Enjeu Clé | Défi Technique | Réponse Apportée par AI SQL Detective |
|:---|:---|:---|
| **Intégrité Absolue des Données** | Éviter toute écriture accidentelle ou injection SQL. | Rôle PostgreSQL `sql_detective_ro` avec `default_transaction_read_only = on` et validation AST SQLGlot bloquant 100% du DDL/DML. |
| **Démocratisation sans Risque** | Ouvrir la donnée aux profils non-techniques. | Pipeline LangGraph en 7 agents avec vulgarisation contextuelle des résultats (`Result Explainer`). |
| **Protection des Ressources DB** | Empêcher les requêtes bloquantes ou les scans complets non maîtrisés. | `statement_timeout` (5000ms), `lock_timeout` (1000ms) et analyse des plans `EXPLAIN (FORMAT JSON)` sans jamais exécuter `EXPLAIN ANALYZE`. |
| **Transparence & Auditabilité** | Savoir qui a exécuté quoi et quand. | Enregistrement automatique de la télémétrie complète dans le schéma dédié `app_meta.query_runs`. |

---

## 👥 Les Acteurs & Personas Ciblés

```mermaid
flowchart LR
    A["Analyste Métier & Product Owner"] -->|"Pose une question en langage naturel"| DETECTIVE["AI SQL Detective"]
    B["Développeur Backend & Data Engineer"] -->|"Édite du SQL dans Monaco & valide l'AST"| DETECTIVE
    C["Administrateur de Base (DBA)"] -->|"Audite les plans EXPLAIN & l'historique"| DETECTIVE
```

### 1. L'Analyste Data & Product Owner
*   **Besoin :** Extraire rapidement des insights chiffrés (ex. *"Quel est le revenu livré par segment de client ?"*) sans attendre la disponibilité d'un data engineer.
*   **Bénéfice :** Saisie intuitive, progression visuelle par étape (SSE), grille de résultats triable, synthèse explicative générée et suggestion de graphiques.

### 2. Le Développeur Fullstack & Data Engineer
*   **Besoin :** Prototyper des requêtes complexes sur un schéma relationnel riche sans risque de casser la base.
*   **Bénéfice :** Explorateur de catalogue PostgreSQL complet, éditeur Monaco professionnel avec coloration syntaxique sombre, détection immédiate des violations de sécurité et recommandations d'optimisation d'index B-Tree.

### 3. Le Database Administrator (DBA)
*   **Besoin :** Garantir que les requêtes ne dégradent pas la performance du cluster de production.
*   **Bénéfice :** Isolation stricte des schémas (`ecommerce` vs `app_meta`), détection proactive des scans séquentiels (`Seq Scan`), historique d'audit exhaustif et métriques de latence consolidées (Recharts).

---

## 🧠 Architecture & Workflow Multi-Agents (LangGraph)

AI SQL Detective orchestre son intelligence via une machine à états typée **LangGraph** articulée autour de **7 agents spécialisés** :

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
*   `sql_detective_app` : Dédié à la télémétrie. Accès restreint à `app_meta.query_runs`. Zéro accès en lecture/écriture sur `ecommerce`.

### 4. Sonde de Troncation Déterministe (`LIMIT + 1`)
Pour éviter la saturation de la mémoire et les faux positifs de troncature :
*   La passerelle injecte ou bride la clause `LIMIT` au plafond configuré (ex. 200 lignes).
*   Elle exécute une sonde à `LIMIT 201`. Si la base retourne 201 lignes, la 201ème ligne est retirée et l'indicateur `was_truncated = true` est positionné avec certitude, sans jamais tronquer faussement une table faisant exactement 200 lignes.
*   Application systématique de `statement_timeout = 5000ms` et `lock_timeout = 1000ms`.

### 5. Hygiène des Secrets & Masquage des Logs
*   Tous les mots de passe et DSNs sont encapsulés dans des objets Pydantic `SecretStr`.
*   Le filtre de journalisation `SecretRedactingFilter` intercepte et masque automatiquement les identifiants dans les URLs PostgreSQL (`postgresql://user:***@host`), les Bearer tokens et les clés d'API (OpenAI, Anthropic, Google).
*   Aucun secret n'est exposé au frontend (zéro préfixe `NEXT_PUBLIC_` sur des données sensibles).

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
| **Analytics Dashboard (Recharts)** | Tableaux de bord graphiques modernisés intégrant les 5 visualisations réelles : tendances de latence, donut des statuts, activité dans le temps, comparaisons et métriques des tables (tooltips Obsidian Dark avec police JetBrains Mono). |
| **Audit & History Log** | Consultation des exécutions passées paginées, filtrage par statut et bouton de rechargement direct dans le Workbench via le paramètre d'URL `?runId=`. |
| **AI What-If Scenario Sandbox** | Simulateur de conditions de marché par IA (Black Friday, Churn VIP, Ruptures de stock) avec injection relationnelle atomique (PK/FK cohérentes) et réinitialisation instantanée au seed doré de baseline. |

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
| `POST` | `/api/v1/scenarios/generate` | `ScenarioGenerateRequest` | `ScenarioGenerateResponse` | Simulation en langage naturel de scénarios synthétiques avec insertion atomique. |
| `POST` | `/api/v1/scenarios/reset` | *-* | `ScenarioResetResponse` | Réinitialisation instantanée de la base au seed déterministe de référence. |

---

## 🚀 Guide de Démarrage & Déploiement Pas-à-Pas

### Prérequis Système
*   **Docker & Docker Compose**
*   **Python 3.12+** avec le gestionnaire de paquets [**uv**](https://docs.astral.sh/uv/)
*   **Node.js 22+** avec **npm**

---

### 1. Configuration de l'Environnement (Racine `.env`)

Copiez le template `.env.example` à la racine du projet et définissez vos identifiants locaux :

```bash
cp .env.example .env
```

> [!TIP]
> **Port PostgreSQL Hôte :** Le port hôte est configuré par défaut sur `5434` (`POSTGRES_PORT=5434`) afin d'éviter tout conflit si vous avez déjà d'autres instances PostgreSQL locales sur les ports `5432` ou `5433`.

Variables requises dans le fichier `.env` :
```ini
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

# Configuration CORS (Requis pour l'accès web local & les tests Playwright)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Configuration LLM (Optionnelle pour la saisie manuelle, requise pour le langage naturel)
# Option A : OpenAI Direct
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...

# Option B : OpenRouter (Modèles gratuits ou open-source)
# LLM_PROVIDER=openai
# LLM_BASE_URL=https://openrouter.ai/api/v1
# LLM_MODEL=nvidia/nemotron-3.5-lightning:free
# LLM_API_KEY=sk-or-v1-...
```

---

### 2. Démarrage de la Base, Migrations & Seeding Déterministe

Démarrez le conteneur PostgreSQL 16, appliquez les migrations Alembic et injectez les **57 427 lignes de démonstration e-commerce** :

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

Accédez à l'application sur [http://localhost:3000](http://localhost:3000).

---

### 4. Déploiement Conteneurisé Complet (Docker Compose)

Vous pouvez également lancer la stack entière (PostgreSQL + Backend + Frontend) via Docker Compose en mode production :

```bash
docker compose --profile full up --build
```

---

### 5. Configuration Multi-Fournisseurs LLM

L'architecture supporte nativement plusieurs fournisseurs LLM grâce à `init_chat_model` de LangChain :

*   **OpenAI (Par défaut) :** `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o-mini`, `LLM_API_KEY=sk-...`
*   **OpenRouter (Recommandé pour tester sans quota OpenAI) :** Définissez `LLM_PROVIDER=openai`, `LLM_BASE_URL=https://openrouter.ai/api/v1`, votre clé `LLM_API_KEY=sk-or-v1-...`, et choisissez un modèle comme `nvidia/nemotron-3.5-lightning:free` (100% gratuit et rapide) ou `openai/gpt-4o-mini`.
*   **Anthropic :** `LLM_PROVIDER=anthropic`, `LLM_MODEL=claude-3-5-sonnet-20241022` (installez le package avec `uv sync --extra anthropic`)
*   **Google Gemini :** `LLM_PROVIDER=google_genai`, `LLM_MODEL=gemini-1.5-pro` (installez le package avec `uv sync --extra google`)
*   **Passerelles Compatibles OpenAI (Local/Ollama/vLLM) :** Définissez `LLM_PROVIDER=openai` et configurez `LLM_BASE_URL=http://localhost:11434/v1`.

> [!NOTE]
> L'image Docker de production (`docker/backend.Dockerfile`) pré-installe automatiquement les adaptateurs Anthropic et Google GenAI, permettant un basculement immédiat par variable d'environnement sans reconstruction de l'image.

---

## 🧪 Qualité, Tests & Intégration Continue (CI/CD)

Le projet fait l'objet d'une suite de vérification automatisée stricte :

```bash
# 1. Vérification du formatage et linting Python (Ruff)
cd backend
uv run ruff check .
uv run ruff format --check .

# 2. Exécution de la suite de tests Pytest (103 tests unitaires, de sécurité & intégration PG16)
uv run pytest -v

# 3. Contrôle du typage strict TypeScript et linting frontend
cd ../frontend
npm run typecheck
npm run lint

# 4. Tests End-to-End Playwright (Workbench, Sécurité, SSE, Analytics, History)
npm run test:e2e
```

### Pipeline GitHub Actions (`.github/workflows/ci.yml`)

À chaque `push` ou `pull request` sur la branche `main`, 4 jobs s'exécutent en parallèle :
1.  **Backend Lint & Unit Tests :** Ruff + Pytest unitaire et suite adversariale AST.
2.  **Backend PostgreSQL 16 Integration :** Provisioning d'un conteneur éphémère PG16, migrations montantes/descendantes, seeding et tests d'isolation des rôles.
3.  **Frontend Typecheck & Build :** `tsc --noEmit`, ESLint et build de production Next.js.
4.  **Playwright End-to-End :** Démarrage de la stack complète et validation des parcours utilisateurs critiques.

---

## 🛠️ Stack Technique Complète

```
AI SQL DETECTIVE
├── Backend (Python 3.12 / FastAPI)
│   ├── LangGraph & LangChain      # Orchestration multi-agents
│   ├── SQLGlot                    # Parser & validateur déterministe d'AST SQL
│   ├── SQLAlchemy 2 & Psycopg 3   # Moteur ORM et pilote PostgreSQL natif
│   ├── Pydantic v2 & Settings     # Typage strict et gestion sécurisée des secrets
│   ├── Alembic                    # Migrations de schéma versionnées
│   └── uv                         # Gestionnaire de paquets ultra-rapide
│
├── Base de données (PostgreSQL 16)
│   ├── ecommerce schema           # 9 tables de données métier (57 427 lignes)
│   ├── app_meta schema            # Télémétrie d'audit (query_runs)
│   └── 3 Rôles Dédiés             # sql_detective_ro, sql_detective_app, sql_detective_migrator
│
├── Frontend (Next.js 15.5.29 / React 19)
│   ├── TypeScript Strict          # Typage rigoureux bout-en-bout
│   ├── Obsidian Dark Workbench    # Design tokens DevTools (#070A12, #0D121F, #131B2E, #1E2B45)
│   ├── Tailwind CSS v4            # Utility-first styling avec tabular-nums natifs
│   ├── Monaco Editor              # Thème dédié ai-sql-detective-dark & raccourci Ctrl+Enter
│   ├── Recharts                   # Visualisation analytique (5 figures harmonisées)
│   ├── TanStack Query             # Gestion d'état serveur et cache réactif
│   └── Lucide React               # Iconographie unifiée à 16px
│
└── Infrastructure & Tests
    ├── Docker & Docker Compose    # Environnement de développement et production
    ├── Pytest & HTTPX             # 103 tests automatisés (unitaires & intégration)
    ├── Playwright                 # Tests End-to-End multi-navigateurs
    └── GitHub Actions             # Intégration continue automatisée
```

---

<p align="center">
  Conçu avec rigueur pour apporter la puissance de l'IA aux bases relationnelles, sans jamais transiger sur la sécurité.
</p>
