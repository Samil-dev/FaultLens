import { test, expect, type Page } from '@playwright/test'

/**
 * FaultLens hardening coverage (robustness pass): system-switch data
 * isolation, and import-time architecture validation surfacing clean
 * errors to the user instead of raw JSON or silent acceptance.
 *
 * Drives the real UI with clicks/fills only — never calls internal
 * frontend functions or fakes backend responses. Requires the backend
 * (port 8000, proxied by Vite) and frontend (port 3000) to already be
 * running; see playwright.config.ts.
 */

const runId = Date.now()

const systemA = {
  id: `e2e-hard-a-${runId}`,
  name: `E2E Hardening A ${runId}`,
  nodes: [
    { id: 'ha-gw', name: 'HA Gateway', node_type: 'gateway', status: 'healthy' },
    { id: 'ha-svc', name: 'HA Checkout Service', node_type: 'service', status: 'healthy' },
    { id: 'ha-db', name: 'HA Primary Database', node_type: 'database', status: 'healthy' },
  ],
  dependencies: [
    { source: 'ha-gw', target: 'ha-svc', type: 'depends_on' },
    { source: 'ha-svc', target: 'ha-db', type: 'depends_on' },
  ],
}

const systemB = {
  id: `e2e-hard-b-${runId}`,
  name: `E2E Hardening B ${runId}`,
  nodes: [
    { id: 'hb-gw', name: 'HB Gateway', node_type: 'gateway', status: 'healthy' },
    { id: 'hb-ledger', name: 'HB Ledger Service', node_type: 'service', status: 'healthy' },
  ],
  dependencies: [
    { source: 'hb-gw', target: 'hb-ledger', type: 'depends_on' },
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

function nodesListItem(page: Page, name: string) {
  const nodesSection = page.locator('.panel-section').filter({
    has: page.locator('.panel-section-title', { hasText: 'Nodes' }),
  })
  return nodesSection.getByText(name, { exact: true })
}

test.describe('FaultLens — hardening: system-switch isolation', () => {
  test('switching systems clears the previous system\'s result, recommendation, and comparison state', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
    page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))

    await page.goto('/')
    await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })

    await test.step('run a full experiment on System A, producing a result and a recommendation', async () => {
      await importSystem(page, systemA)
      await nodesListItem(page, 'HA Checkout Service').click()
      await page.getByRole('button', { name: 'Run Experiment' }).first().click()
      await expect(page.locator('[role="dialog"]')).toBeVisible()
      await page.locator('[role="radio"]', { hasText: 'Service Down' }).click()
      await page.getByRole('button', { name: '⚡ Execute Experiment' }).click()
      await expect(page.getByText('Simulation complete').first()).toBeVisible({ timeout: 15_000 })

      // The RightPanel is now showing System A's real result.
      await expect(page.locator('.app-right-panel')).toContainText('HA Checkout Service')
      await expect(page.locator('.app-right-panel')).toContainText('Resilience Score')
    })

    await test.step('import System B and confirm none of System A\'s result data is still visible', async () => {
      await importSystem(page, systemB)

      // Landed back on the Digital Twin, with System B's own topology —
      // not System A's node or result.
      await expect(page.locator('.app-sidebar')).toContainText('HB Ledger Service')
      await expect(page.locator('.app-sidebar')).not.toContainText('HA Checkout Service')

      // The RightPanel must have reset to its idle state — System A's
      // resilience score, target node, and AI analysis must not leak
      // through into System B's (experiment-less) session.
      await expect(page.locator('.app-right-panel')).not.toContainText('HA Checkout Service')
      await expect(page.locator('.app-right-panel')).not.toContainText('Resilience Score')
      await expect(page.locator('.app-right-panel')).toContainText('Run a chaos experiment')

      // History for System B must be genuinely empty, not A's history
      // relabeled.
      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('No experiments run yet')
      await expect(page.locator('.app-sidebar')).not.toContainText('HA Checkout Service')
    })

    await test.step('Compare Scenarios for System B has no trace of System A\'s runs', async () => {
      await page.locator('.sidebar-nav-item', { hasText: 'Compare Scenarios' }).click()
      await expect(page.locator('.app-sidebar')).not.toContainText('HA Checkout Service')
    })

    expect(consoleErrors, `Console errors during the run:\n${consoleErrors.join('\n')}`).toHaveLength(0)
  })
})

test.describe('FaultLens — hardening: import validation surfaces clean errors', () => {
  test('a dependency referencing a nonexistent node shows a clear, readable error', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })

    await page.getByRole('button', { name: 'Import a system architecture' }).click()
    await expect(page.locator('#import-system-title')).toBeVisible()

    const invalidSystem = {
      id: `e2e-hard-bad-target-${runId}`,
      name: 'Invalid Dependency Target System',
      nodes: [{ id: 'only-node', name: 'Only Node', node_type: 'service' }],
      dependencies: [{ source: 'only-node', target: 'does-not-exist', type: 'depends_on' }],
    }
    await page.fill('#system-json-input', JSON.stringify(invalidSystem, null, 2))
    await page.getByRole('button', { name: '⬡ Import Architecture' }).click()

    // A real, readable error — not a raw {"detail": [...]} JSON dump, and
    // not silent acceptance of a corrupt architecture.
    const errorText = page.locator('.modal-box').locator('text=does-not-exist')
    await expect(errorText).toBeVisible({ timeout: 10_000 })
    const fullText = await page.locator('.modal-box').innerText()
    expect(fullText).not.toContain('"detail"')
    expect(fullText).not.toContain('{"')

    // The invalid architecture must never have been accepted as the
    // active system.
    await expect(page.getByText('Digital Twin ready', { exact: false })).not.toBeVisible()
  })

  test('an empty architecture is rejected with a clear error, not silently accepted', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })

    await page.getByRole('button', { name: 'Import a system architecture' }).click()
    await expect(page.locator('#import-system-title')).toBeVisible()

    const emptySystem = {
      id: `e2e-hard-empty-${runId}`,
      name: 'Empty Architecture System',
      nodes: [],
      dependencies: [],
    }
    await page.fill('#system-json-input', JSON.stringify(emptySystem, null, 2))
    await page.getByRole('button', { name: '⬡ Import Architecture' }).click()

    await expect(page.getByText('at least one node')).toBeVisible({ timeout: 10_000 })
    await expect(page.getByText('Digital Twin ready', { exact: false })).not.toBeVisible()
  })
})
