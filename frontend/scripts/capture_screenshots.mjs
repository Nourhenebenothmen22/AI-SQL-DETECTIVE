import { chromium } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.resolve(__dirname, '../../docs/screenshots');

async function capture() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 920 },
    deviceScaleFactor: 2,
    colorScheme: 'dark',
  });

  const page = await context.newPage();

  console.log('1. Capturing Workbench...');
  await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // Click on order_items table in schema explorer to expand its columns
  try {
    const orderItemsButton = page.locator('button:has-text("order_items")').first();
    if (await orderItemsButton.isVisible()) {
      await orderItemsButton.click();
      await page.waitForTimeout(500);
    }
  } catch (e) {
    console.log('Could not expand order_items:', e.message);
  }

  // Type and run a query to show live results table
  try {
    const exampleButton = page.locator('button:has-text("Top 10 products")').first();
    if (await exampleButton.isVisible()) {
      await exampleButton.click();
      await page.waitForTimeout(2500);
    }
  } catch (e) {
    console.log('Example click note:', e.message);
  }

  await page.screenshot({ path: path.join(outputDir, '01_workbench_overview.png') });

  // 2. Workbench Query Results & Schema Explorer with tables
  console.log('2. Capturing Workbench with expanded tables...');
  try {
    const ordersButton = page.locator('button:has-text("orders")').first();
    if (await ordersButton.isVisible()) {
      await ordersButton.click();
      await page.waitForTimeout(500);
    }
  } catch (e) {
    console.log('Orders click note:', e.message);
  }
  await page.screenshot({ path: path.join(outputDir, '02_workbench_schema_and_editor.png') });

  // 3. Analytics Page
  console.log('3. Capturing Analytics...');
  await page.goto('http://localhost:3000/analytics', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(outputDir, '03_analytics_dashboard.png') });

  // 4. EvalLaps Page
  console.log('4. Capturing EvalLaps...');
  await page.goto('http://localhost:3000/evallaps', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outputDir, '04_evallaps_finops_overview.png') });

  // Scroll down a bit to capture stage charts and load balancing visual
  await page.evaluate(() => window.scrollBy(0, 450));
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(outputDir, '05_evallaps_telemetry_and_stages.png') });

  // 5. EvalOps / Evals Page
  console.log('5. Capturing EvalOps...');
  await page.goto('http://localhost:3000/evals', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(outputDir, '06_evalops_benchmarks.png') });

  // 6. History Page
  console.log('6. Capturing History...');
  await page.goto('http://localhost:3000/history', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(outputDir, '07_history_ledger.png') });

  await browser.close();
  console.log('All screenshots captured successfully in docs/screenshots/');
}

capture().catch((err) => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
