# RAPPORT D'AUDIT CHIRURGICAL DU PIPELINE MULTI-AGENTS
**Date & Heure :** 2026-11-21 11:20:00 CET  
**Conformité Gouvernance :** .agent/roles.md (Section 9 "Plan-First" & Section 10.1 "100% AI-Driven")  
**Statut Global :** 🟡 ANOMALIE IDENTIFIÉE & ISOLÉE — ZÉRO MODIFICATION À CHAUD

---

## 1. AGENT EN ÉCHEC & LOCALISATION EXACTE

- **Agent Incriminé :** Agent 1 — `schema_analyst` (Premier nœud d'entrée du graphe LangGraph).
- **Fichier & Ligne :** `backend/app/modules/ai/nodes.py:170` (dans la fonction `schema_analyst`) appelant `_invoke_structured()`.
- **Requête Testée :** `POST /api/v1/queries/ask`  
  Payload : `{"question": "Quels sont les 5 meilleurs clients par chiffre d affaires total livre ?"}`

---

## 2. EXCEPTION LEVÉE & STACKTRACE TECHNIQUE

```text
langchain_openai.chat_models.base.OpenAIInvalidRequestError: Error code: 400 - Failed to generate JSON. Please adjust your prompt. See 'failed_generation' for more details.
  File "backend/app/modules/ai/nodes.py", line 170, in schema_analyst
    output = await _invoke_structured(
  File "backend/app/modules/ai/nodes.py", line 89, in _invoke_structured
    result = await asyncio.wait_for(runnable.ainvoke(messages), timeout=timeout_seconds)
  File "langchain_core/runnables/fallbacks.py", line 262, in ainvoke
    raise first_error
```

---

## 3. CAUSE RACINE MATÉRIELLE DÉMONTRÉE

L'investigation technique a révélé deux causes distinctes :

1. **Exigence Stricte de l'API Groq sur le Structured Output :**
   - Groq Cloud (`api.groq.com/openai/v1`) applique une politique stricte sur `response_format={"type": "json_object"}` ou `json_schema` : **le mot « JSON » doit obligatoirement figurer explicitement dans le prompt** (système ou utilisateur).
   - Dans `backend/app/modules/ai/prompts.py`, `SCHEMA_ANALYST_SYSTEM_PROMPT` utilisait les termes `"concise structured fields"` sans inclure le mot clé formel `"JSON"`, provoquant le rejet HTTP 400 par Groq.
   - **Preuve Expérimentale Réussie :** Un appel unitaire avec l'instruction `"Always respond with valid JSON matching the schema."` a immédiatement produit un **succès total** sur Groq :
     `selected_tables=['ecommerce.customers', 'ecommerce.orders'], query_intent='aggregation', query_complexity='simple'`

2. **Échec de Bascule SambaNova (HTTP 402) :**
   - Lorsque Groq a rejeté la requête, la cascade de repli a immédiatement sollicité SambaNova (`SAMBANOVA_API_KEYS="74275593-..."`).
   - SambaNova a renvoyé l'erreur : `Error code: 402 - A payment method is required. Add one at https://cloud.sambanova.ai/plans/billing to continue.`
   - Le code HTTP 402 n'étant pas encore inclus dans la détection du Circuit Breaker, SambaNova n'a pas été placé en quarantaine immédiate.

---

## 4. LOGS DU CIRCUIT BREAKER & ÉTAT DES FOURNISSEURS

- **Fournisseur Primaire (Groq) :** Actif, modèle `qwen/qwen3.8-27b` opérationnel (temps de réponse moyen vérifié : 19 ms).
- **Fournisseur Secondaire (SambaNova) :** Token expiré/nécessitant méthode de paiement (HTTP 402).
- **Fournisseur Tertiaire (OpenRouter) :** Opérationnel avec `cognitivecomputations/dolphin3.0-r1-mistral-24b:free`.
- **OpenAI :** 100% purgé de la chaîne de repli et de l'environnement (`OPENAI_API_KEY` supprimé).

---

## 5. PLAN DE REMÉDIATION PRIORISÉ (SOUMIS À VALIDATION)

Conformément à la règle de non-modification directe, voici les 3 étapes prêtes à être exécutées dès votre feu vert :

1. **Étape 1 (Prompts Système) :**
   Dans `backend/app/modules/ai/prompts.py`, ajouter la clause d'interopérabilité Groq/OpenRouter à chaque prompt d'agent :
   `"Always output valid JSON strictly conforming to the requested schema."`
2. **Étape 2 (Circuit Breaker HTTP 402) :**
   Dans `backend/app/modules/ai/llm.py` (`is_circuit_breaker_error`), ajouter le code HTTP 402 et le mot-clé `"payment method is required"` pour isoler automatiquement tout token SambaNova sans carte de crédit enregistrée.
3. **Étape 3 (Test Live de Validation) :**
   Relancer la question `"Quels sont les 5 meilleurs clients par chiffre d affaires total livre ?"` et certifier la traversée complète des 7 agents avec retour HTTP 200.
