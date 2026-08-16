import { test, expect, type Page } from '@playwright/test'

/**
 * End-to-end validation of FaultLens's system persistence and switching
 * (see Prompt #5 — end-to-end hardening).
 *
 * Drives the real UI with clicks/fills only — never calls internal
 * frontend functions or fakes backend responses. Requires the backend
 * (port 8000, proxied by Vite) and frontend (port 3000) to already be
 * running; see playwright.config.ts.
 *
 * Test data is explicit and uniquely identified per run (via `runId`) so
 * the suite can be re-run against the same backend database without id
 * collisions — there is no endpoint to delete a persisted system, so
 * fixtures accumulate across runs by design rather than being cleaned up.
 */

const runId = Date.now()

const systemA = {
  id: `e2e-sys-a-${runId}`,
  name: `E2E Retail A ${runId}`,
  nodes: [
    { id: 'a-gw', name: 'A Gateway', node_type: 'gateway', status: 'healthy' },
    { id: 'a-svc', name: 'A Checkout Service', node_type: 'service', status: 'healthy' },
    { id: 'a-db', name: 'A Primary Database', node_type: 'database', status: 'healthy' },
  ],
  dependencies: [
    { source: 'a-gw', target: 'a-svc', type: 'depends_on' },
    { source: 'a-svc', target: 'a-db', type: 'depends_on' },
  ],
}

const systemB = {
  id: `e2e-sys-b-${runId}`,
  name: `E2E Banking B ${runId}`,
  nodes: [
    { id: 'b-gw', name: 'B Gateway', node_type: 'gateway', status: 'healthy' },
    { id: 'b-ledger', name: 'B Ledger Service', node_type: 'service', status: 'healthy' },
    { id: 'b-db', name: 'B Ledger Database', node_type: 'database', status: 'healthy' },
  ],
  dependencies: [
    { source: 'b-gw', target: 'b-ledger', type: 'depends_on' },
    { source: 'b-ledger', target: 'b-db', type: 'depends_on' },
  ],
}

async function importSystem(page: Page, system: typeof systemA) {
  await page.getByRole('button', { name: 'Import a system architecture' }).click()
  await expect(page.locator('#import-system-title')).toBeVisible()
  await page.fill('#system-json-input', JSON.stringify(system, null, 2))
  await page.getByRole('button', { name: '⬡ Import Architecture' }).click()
  await expect(page.getByText('Architecture Analysis')).toBeVisible({ timeout: 10_000 })
  await expect(page.getByText(`Digital Twin ready — "${system.name}"`)).toBeVisible()
  await page.getByRole('button', { name: 'View Digital Twin' }).click()
}

async function activeSystemName(page: Page): Promise<string> {
  const raw = await page.locator('.app-header button[aria-label^="Active system"]').innerText()
  return raw.split('\n')[0].trim()
}

async function openSwitcher(page: Page) {
  await page.locator('.app-header button[aria-label^="Active system"]').click()
  await expect(page.locator('#system-switcher-title')).toBeVisible()
  // Wait for the async system list fetch to actually resolve before
  // asserting on its content, instead of racing it.
  await page.waitForSelector('.modal-box:has-text("dependenc")', { timeout: 5_000 })
}

test.describe('FaultLens — system persistence & switching (Prompt #5 hardening)', () => {
  test('import, experiment, reload restoration, multi-system switching, invalid-id fallback', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
    page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))

    // ── TEST A: import ──────────────────────────────────────────────────────
    await test.step('A — import a new architecture and it becomes the active system', async () => {
      await page.goto('/')
      await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })
      await importSystem(page, systemA)
      await expect.poll(() => activeSystemName(page)).toBe(systemA.name)
      await expect(page.locator('.app-sidebar')).toContainText('Total nodes')
      await expect(page.locator('.app-sidebar')).toContainText('3') // node count
      await expect(page.locator('.app-sidebar')).toContainText('A Checkout Service')
    })

    // ── TEST B: run an experiment ────────────────────────────────────────────
    await test.step('B — configure and execute a real experiment via the UI', async () => {
      await page.getByText('A Checkout Service', { exact: true }).click()
      await page.getByRole('button', { name: 'Run Experiment' }).first().click()
      await expect(page.locator('[role="dialog"]')).toBeVisible()
      await page.locator('[role="radio"]', { hasText: 'Service Down' }).click()
      await page.getByRole('button', { name: '⚡ Execute Experiment' }).click()
      await expect(page.getByText('Simulation complete').first()).toBeVisible({ timeout: 15_000 })

      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('A Checkout Service')
      await expect(page.locator('.app-sidebar')).toContainText('Service Down')
    })

    // ── TEST C: reload ────────────────────────────────────────────────────────
    await test.step('C — reload restores the active system and its history', async () => {
      await page.reload({ waitUntil: 'networkidle' })
      await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })
      await expect.poll(() => activeSystemName(page)).toBe(systemA.name)
      await expect(page.locator('.app-sidebar')).toContainText('A Checkout Service')

      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('A Checkout Service')
      await expect(page.locator('.app-sidebar')).not.toContainText('No experiments run yet')
    })

    // ── TEST D: multiple systems ─────────────────────────────────────────────
    await test.step('D — importing a second system switches context without mixing data', async () => {
      await page.locator('.sidebar-nav-item', { hasText: 'Digital Twin' }).click()
      await importSystem(page, systemB)
      await expect.poll(() => activeSystemName(page)).toBe(systemB.name)
      await expect(page.locator('.app-sidebar')).toContainText('B Ledger Service')

      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('No experiments run yet')

      await openSwitcher(page)
      await expect(page.locator('.modal-box')).toContainText(systemA.name)
      await expect(page.locator('.modal-box')).toContainText(systemB.name)
      await page.getByText(systemA.name, { exact: true }).click()

      await expect.poll(() => activeSystemName(page)).toBe(systemA.name)
      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('A Checkout Service')
      await expect(page.locator('.app-sidebar')).not.toContainText('No experiments run yet')
    })

    // ── TEST E: reload while on the second system ────────────────────────────
    await test.step('E — reload restores whichever system was active, not always the first', async () => {
      await openSwitcher(page)
      await page.getByText(systemB.name, { exact: true }).click()
      await expect.poll(() => activeSystemName(page)).toBe(systemB.name)

      await page.reload({ waitUntil: 'networkidle' })
      await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })
      await expect.poll(() => activeSystemName(page)).toBe(systemB.name)
    })

    // ── TEST F: invalid stored system id ─────────────────────────────────────
    await test.step('F — a stale/invalid stored system id falls back cleanly, no broken screen', async () => {
      await page.evaluate(() => localStorage.setItem('faultlens.activeSystemId', 'does-not-exist-anywhere'))
      await page.reload({ waitUntil: 'networkidle' })
      await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })

      // Falls back to a real, valid system (the seeded demo) rather than
      // showing an error screen or an empty Digital Twin.
      await expect(page.locator('.app-sidebar')).toContainText('Total nodes')
      const name = await activeSystemName(page)
      expect(name.length).toBeGreaterThan(0)

      const stored = await page.evaluate(() => localStorage.getItem('faultlens.activeSystemId'))
      expect(stored).not.toBe('does-not-exist-anywhere')
    })

    expect(consoleErrors, `Console errors during the run:\n${consoleErrors.join('\n')}`).toHaveLength(0)
  })
})
