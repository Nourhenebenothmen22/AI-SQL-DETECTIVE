import { expect, test } from "@playwright/test";

test.describe("AI SQL Detective — End-to-End Workbench, Security, SSE, Analytics & History", () => {
  test("loads live schema explorer and executes read-only SQL with EXPLAIN JSON inspection", async ({
    page,
  }) => {
    await page.goto("/");

    // Verify shell chrome, preconfigured read-only connection, and live API/DB status
    await expect(page.getByRole("heading", { name: "SQL Detective Workbench" })).toBeVisible();
    await expect(page.getByLabel("Database connection")).toHaveValue("ecommerce_demo");
    await expect(page.getByText("READ-ONLY", { exact: true })).toBeVisible();
    await expect(page.getByText(/API OK · DB connected/i)).toBeVisible({ timeout: 10_000 });

    // Live PostgreSQL catalog introspection displays ecommerce tables & filters cleanly
    await expect(page.getByText("Schema Explorer")).toBeVisible();
    await expect(page.getByRole("button", { name: "orders", exact: true })).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByRole("button", { name: "customers", exact: true })).toBeVisible();

    await page.getByLabel("Filter tables and columns").fill("inventory");
    await expect(page.getByRole("button", { name: "inventory", exact: true })).toBeVisible();
    await page.getByLabel("Filter tables and columns").fill("");

    // Execute the default read-only SQL query against live PostgreSQL 16
    await page.getByRole("button", { name: "Run Read-Only" }).click();

    // Verify Results table renders real aggregated rows and supports accessible sorting
    const resultsRegion = page.getByRole("region", { name: /PostgreSQL query results table/i });
    await expect(resultsRegion).toBeVisible({ timeout: 10_000 });
    await expect(resultsRegion.getByRole("cell", { name: "retail" })).toBeVisible();
    await expect(resultsRegion.getByRole("cell", { name: "vip" })).toBeVisible();
    await expect(resultsRegion.getByRole("cell", { name: "wholesale" })).toBeVisible();

    const segmentHeader = resultsRegion.getByRole("columnheader", { name: "segment" });
    await segmentHeader.getByRole("button", { name: "segment" }).click();
    await expect(segmentHeader).toHaveAttribute("aria-sort", "ascending");

    // Verify deterministic Security & Review tab shows PASSED
    await page.getByRole("tab", { name: /Security & Review/i }).click();
    await expect(page.getByText("Independent Security Gate (Deterministic)")).toBeVisible();
    await expect(page.getByText("PASSED", { exact: true })).toBeVisible();

    // Verify Optimization tab displays EXPLAIN (FORMAT JSON) plan metrics
    await page.getByRole("tab", { name: /Optimization/i }).click();
    await expect(page.getByText("Root Plan Node")).toBeVisible();
    await expect(page.getByText("Estimated Total Cost")).toBeVisible();
    await page.getByRole("button", { name: "Inspect JSON" }).click();
    await expect(page.locator("pre code").filter({ hasText: '"Plan"' })).toBeVisible();
  });

  test("blocks destructive SQL via deterministic Security Gate and surfaces violations", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByText(/API OK · DB connected/i)).toBeVisible({ timeout: 10_000 });

    // Wait for Monaco editor textarea to mount, replace content with destructive SQL
    const monacoEditor = page.locator(".monaco-editor").first();
    await expect(monacoEditor).toBeVisible({ timeout: 15_000 });
    await monacoEditor.click();
    await page.keyboard.press("ControlOrMeta+A");
    await page.keyboard.type("DROP TABLE ecommerce.orders;");

    await page.getByRole("button", { name: "Run Read-Only" }).click();

    // Security & Review tab activates automatically and displays BLOCKED violation
    await expect(page.getByText("BLOCKED", { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(
      page.getByText(/Only read-only SELECT queries are permitted|SQL syntax could not be parsed safely/i),
    ).toBeVisible();
  });

  test("streams 6-stage SSE workflow progress and separate parallel Optimization Agent panel", async ({
    page,
  }) => {
    // Deterministic SSE fixture honoring roles.md QA boundary (no live LLM flakiness in E2E)
    const ssePayload = [
      'event: stage_started\ndata: {"stage":"schema_analyst","label":"Schema Analyst","attempt":1,"timestamp":"2026-11-18T08:00:00Z"}\n\n',
      'event: stage_completed\ndata: {"stage":"schema_analyst","label":"Schema Analyst","status":"completed","attempt":1,"duration_ms":120,"summary":"Selected 2 table(s): ecommerce.orders, ecommerce.customers"}\n\n',
      'event: stage_started\ndata: {"stage":"sql_generator","label":"SQL Generator","attempt":1,"timestamp":"2026-11-18T08:00:00Z"}\n\n',
      'event: stage_completed\ndata: {"stage":"sql_generator","label":"SQL Generator","status":"completed","attempt":1,"duration_ms":210,"summary":"Generated candidate PostgreSQL SELECT query"}\n\n',
      'event: stage_started\ndata: {"stage":"query_reviewer","label":"Query Reviewer","attempt":1,"timestamp":"2026-11-18T08:00:00Z"}\n\n',
      'event: stage_completed\ndata: {"stage":"query_reviewer","label":"Query Reviewer","status":"completed","attempt":1,"duration_ms":150,"summary":"Semantic review approved"}\n\n',
      'event: stage_started\ndata: {"stage":"security_gate","label":"Security Gate","attempt":1,"timestamp":"2026-11-18T08:00:00Z"}\n\n',
      'event: stage_completed\ndata: {"stage":"security_gate","label":"Security Gate","status":"completed","attempt":1,"duration_ms":4,"summary":"Passed 6 deterministic AST checks (LIMIT 200)"}\n\n',
      'event: stage_started\ndata: {"stage":"sql_executor","label":"SQL Executor","attempt":1,"timestamp":"2026-11-18T08:00:00Z"}\n\n',
      'event: stage_completed\ndata: {"stage":"sql_executor","label":"SQL Executor","status":"completed","attempt":1,"duration_ms":8.4,"summary":"Returned 3 row(s) in 8.4ms"}\n\n',
      'event: optimization_started\ndata: {"stage":"optimization_agent","timestamp":"2026-11-18T08:00:01Z"}\n\n',
      'event: stage_started\ndata: {"stage":"result_explainer","label":"Result Explainer","attempt":1,"timestamp":"2026-11-18T08:00:01Z"}\n\n',
      'event: optimization_completed\ndata: {"stage":"optimization_agent","status":"completed","duration_ms":190,"recommendation_count":1,"recommendations":[{"severity":"warning","category":"indexing","title":"Composite index on orders(status, customer_id)","detail":"Seq Scan observed on ecommerce.orders.","suggestion":"Add composite B-tree index on (status, customer_id).","suggested_sql_or_index":"CREATE INDEX ix_orders_status_customer ON ecommerce.orders (status, customer_id);"}]}\n\n',
      'event: stage_completed\ndata: {"stage":"result_explainer","label":"Result Explainer","status":"completed","attempt":1,"duration_ms":180,"summary":"Generated grounded explanation of query results"}\n\n',
      'event: final_result\ndata: {"run_id":null,"connection_id":"ecommerce_demo","question":"Delivered revenue by segment","selected_tables":["ecommerce.orders","ecommerce.customers"],"ambiguities":[],"candidate_sql":"SELECT c.segment, COUNT(*) AS orders FROM ecommerce.orders o JOIN ecommerce.customers c ON c.id = o.customer_id GROUP BY c.segment","validated_sql":"SELECT c.segment, COUNT(*) AS orders FROM ecommerce.orders AS o JOIN ecommerce.customers AS c ON c.id = o.customer_id GROUP BY c.segment LIMIT 200","generation_rationale":"Counts orders grouped by customer segment.","assumptions":["Includes all statuses."],"review_status":"approved","review_notes":["Valid join key and GROUP BY."],"security_status":"passed","security_violations":[],"security_checks":[{"rule":"readonly_root","passed":true,"detail":"Read-only SELECT root verified."}],"enforced_limit":200,"limit_was_injected":true,"limit_was_clamped":false,"execution_status":"success","columns":["segment","orders"],"rows":[{"segment":"retail","orders":9100},{"segment":"vip","orders":1950},{"segment":"wholesale","orders":950}],"row_count":3,"was_truncated":false,"execution_time_ms":8.4,"execution_error":null,"explanation":{"summary":"Retail leads with 9,100 orders.","key_findings":["Retail represents the largest segment."],"caveats":[],"suggested_chart":"bar"},"explain_plan":[{"Plan":{"Node Type":"Aggregate","Total Cost":310.5}}],"plan_summary":{"root_node_type":"Aggregate","startup_cost":290.0,"total_cost":310.5,"estimated_rows":3,"plan_width":32,"node_types":["Aggregate","Seq Scan"],"has_sort":false,"has_nested_loop":false,"has_hash_join":false,"findings":[]},"optimization_status":"completed","optimizations":[{"severity":"warning","category":"indexing","title":"Composite index on orders(status, customer_id)","detail":"Seq Scan observed on ecommerce.orders.","suggestion":"Add composite B-tree index on (status, customer_id).","suggested_sql_or_index":"CREATE INDEX ix_orders_status_customer ON ecommerce.orders (status, customer_id);"}],"warnings":[],"stages":[]}\n\n',
    ].join("");

    await page.route("**/api/v1/queries/ask/stream", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: ssePayload,
      });
    });

    await page.goto("/");
    await page.getByLabel("Ask in Natural Language").fill("Delivered revenue by segment");
    await page.getByRole("button", { name: "Ask Detective" }).click();

    // Primary stepper displays strictly the 6 ordered stages
    await expect(page.getByText("Agent Execution Pipeline (6 Stages)")).toBeVisible();
    for (const label of [
      "1. Schema Analyst",
      "2. SQL Generator",
      "3. Query Reviewer",
      "4. Security Gate",
      "5. SQL Executor",
      "6. Result Explainer",
    ]) {
      await expect(page.getByText(label)).toBeVisible();
    }

    // Results tab renders returned rows
    await expect(page.getByRole("cell", { name: "9100" })).toBeVisible();

    // AI Explanation tab renders grounded summary
    await page.getByRole("tab", { name: /AI Explanation/i }).click();
    await expect(page.getByText("Retail leads with 9,100 orders.")).toBeVisible();

    // Optimization panel renders parallel Optimization Agent output separately
    await page.getByRole("tab", { name: /Optimization/i }).click();
    await expect(page.getByText("Composite index on orders(status, customer_id)")).toBeVisible();
    await expect(page.getByText(/Advisory Recommendation \(Not Auto-Executed\)/i)).toBeVisible();
  });

  test("navigates to Analytics (all 5 charts) and History with Workbench reload", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByText(/API OK · DB connected/i)).toBeVisible({ timeout: 10_000 });

    // Navigate to Analytics via sidebar
    await page.getByRole("link", { name: "Analytics" }).click();
    await expect(page).toHaveURL(/\/analytics$/);
    await expect(page.getByRole("heading", { name: "Query & Database Analytics" })).toBeVisible();

    // Verify all 5 Recharts figures and live ecommerce catalog stats render
    for (const chartTitle of [
      "Execution Latency Trends",
      "Query Status Distribution",
      "Query Activity Over Time",
      "Recent Query Comparisons",
      "PostgreSQL Table Statistics",
    ]) {
      await expect(page.getByRole("heading", { name: new RegExp(chartTitle) })).toBeVisible({
        timeout: 10_000,
      });
    }
    await expect(page.getByRole("cell", { name: "order_items" })).toBeVisible();

    // Navigate to History via sidebar and reload a real recorded run into Workbench
    await page.getByRole("link", { name: "History" }).click();
    await expect(page).toHaveURL(/\/history$/);
    await expect(page.getByRole("heading", { name: "Query History" })).toBeVisible();

    const firstOpenLink = page.getByRole("link", { name: /Open run .* in Workbench/i }).first();
    await expect(firstOpenLink).toBeVisible({ timeout: 10_000 });
    await firstOpenLink.click();
    await expect(page).toHaveURL(/\/\?runId=/);
    await expect(page.getByRole("heading", { name: "SQL Detective Workbench" })).toBeVisible();
  });

  test("navigates to EvalOps Benchmark, displays KPIs, and inspects golden case diff", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByText(/API OK · DB connected/i)).toBeVisible({ timeout: 10_000 });

    // Navigate to EvalOps via sidebar
    await page.getByRole("link", { name: "EvalOps" }).click();
    await expect(page).toHaveURL(/\/evals$/);
    await expect(
      page.getByRole("heading", { name: "AI Model Evaluation & EvalOps Benchmark" }),
    ).toBeVisible();

    // Verify key KPI cards render
    await expect(page.getByText("Execution Accuracy (EX)", { exact: true })).toBeVisible();
    await expect(page.getByText("Valid AST Rate (VAST)")).toBeVisible();
    await expect(page.getByText("Golden Suite Size")).toBeVisible();

    // Filter by difficulty
    await page.getByRole("button", { name: /^Easy/i }).click();
    await expect(page.getByText("golden_01")).toBeVisible();

    // Open Diff accordion
    await page.getByRole("button", { name: "Diff" }).first().click();
    await expect(page.getByText(/Canonical Ground Truth SQL/i)).toBeVisible();
  });
});
