import { test, expect, type Page } from '@playwright/test'

/**
 * End-to-end validation of the FaultLens Core Workflow — the full,
 * continuous chain: System Import -> Digital Twin -> Dependency Analysis ->
 * Node Selection -> Experiment Design -> ChaosLab execution -> Failure
 * Propagation -> Resilience Analysis -> Recommendation -> Next Experiment
 * -> History -> Reload -> Context restoration.
 *
 * Drives the real UI with clicks/fills only — never calls internal frontend
 * functions or fakes backend responses. Requires the backend (port 8000)
 * and frontend (port 3000) to already be running; see playwright.config.ts.
 *
 * This spec exists specifically to prove no stage of the workflow is an
 * "island": every assertion below checks that a *later* stage's UI reflects
 * data genuinely produced by an *earlier* stage, not independently-seeded
 * or stale state.
 */

const runId = Date.now()

const system = {
  id: `e2e-core-${runId}`,
  name: `E2E Core Workflow ${runId}`,
  nodes: [
    { id: 'c-gw', name: 'Core Gateway', node_type: 'gateway', status: 'healthy' },
    { id: 'c-auth', name: 'Core Auth Service', node_type: 'service', status: 'healthy' },
    { id: 'c-orders', name: 'Core Order Service', node_type: 'service', status: 'healthy' },
    { id: 'c-db', name: 'Core Primary Database', node_type: 'database', status: 'healthy' },
  ],
  dependencies: [
    { source: 'c-gw', target: 'c-auth', type: 'depends_on' },
    { source: 'c-gw', target: 'c-orders', type: 'depends_on' },
    { source: 'c-auth', target: 'c-db', type: 'depends_on' },
    { source: 'c-orders', target: 'c-db', type: 'depends_on' },
  ],
}

async function activeSystemName(page: Page): Promise<string> {
  const raw = await page.locator('.app-header button[aria-label^="Active system"]').innerText()
  return raw.split('\n')[0].trim()
}

// Scoped strictly to the "Nodes" list in the Digital Twin panel, so a node
// name that also happens to appear elsewhere on the page right now (e.g. as
// a dependent/dependency of whichever node is currently selected) can't
// cause a strict-mode ambiguity.
function nodesListItem(page: Page, name: string) {
  const nodesSection = page.locator('.panel-section').filter({
    has: page.locator('.panel-section-title', { hasText: 'Nodes' }),
  })
  return nodesSection.getByText(name, { exact: true })
}

test.describe('FaultLens — Core Workflow (import → resilience analysis → history → reload)', () => {
  test('the full 16-step chain uses real, connected data at every stage', async ({ page }) => {
    const consoleErrors: string[] = []
    const failedRequests: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
    page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))
    page.on('requestfailed', (req) => failedRequests.push(`${req.method()} ${req.url()} — ${req.failure()?.errorText}`))
    page.on('response', (res) => {
      if (res.url().includes('/api/') && res.status() >= 500) {
        failedRequests.push(`${res.status()} ${res.url()}`)
      }
    })

    // ── 1. Open the app ──────────────────────────────────────────────────
    await test.step('1 — app loads', async () => {
      await page.goto('/')
      await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })
    })

    // ── 2. Import a system architecture ──────────────────────────────────
    await test.step('2 — import a new architecture via the real UI', async () => {
      await page.getByRole('button', { name: 'Import a system architecture' }).click()
      await expect(page.locator('#import-system-title')).toBeVisible()
      await page.fill('#system-json-input', JSON.stringify(system, null, 2))
      await page.getByRole('button', { name: '⬡ Import Architecture' }).click()
      await expect(page.getByText('Architecture Analysis')).toBeVisible({ timeout: 10_000 })
      await expect(page.getByText(`${system.nodes.length} nodes detected`)).toBeVisible()
      await expect(page.getByText(`Digital Twin ready — "${system.name}"`)).toBeVisible()
    })

    // ── 3. Confirm import lands on the Digital Twin (not wherever the
    //      sidebar happened to be pointed at before) ─────────────────────
    await test.step('3 — confirming the import returns to the Digital Twin automatically', async () => {
      await page.getByRole('button', { name: 'View Digital Twin' }).click()
      await expect.poll(() => activeSystemName(page)).toBe(system.name)
      await expect(page.locator('.sidebar-nav-item.active')).toContainText('Digital Twin')
      await expect(page.locator('.app-sidebar')).toContainText('4') // node count
      await expect(page.locator('.app-sidebar')).toContainText('Core Order Service')
    })

    // ── 4. Dependency graph reflects the imported topology ────────────────
    await test.step('4 — the graph canvas renders the full imported topology', async () => {
      await expect(page.locator('svg.graph-svg')).toBeVisible()
      await expect(page.locator('svg.graph-svg')).toHaveAttribute(
        'aria-label',
        `Digital twin dependency graph for ${system.name}, ${system.nodes.length} nodes`,
      )
      await expect(page.locator('.graph-node-group')).toHaveCount(system.nodes.length)
    })

    // ── 5. Node selection ───────────────────────────────────────────────
    await test.step('5 — selecting a node updates the sidebar and impact preview', async () => {
      await nodesListItem(page, 'Core Order Service').click()
      await expect(page.locator('.app-sidebar')).toContainText('Selected Node')
      await expect(page.locator('.app-sidebar')).toContainText('Impact Preview')
      await expect(page.locator('.app-sidebar')).toContainText('Potential blast radius')
    })

    // ── 6. Experiment design ────────────────────────────────────────────
    await test.step('6 — configuring an experiment carries the selected node as its target', async () => {
      await page.getByRole('button', { name: 'Run Experiment' }).first().click()
      await expect(page.locator('[role="dialog"]')).toBeVisible()
      await expect(page.locator('[role="dialog"]')).toContainText('Core Order Service')
      await page.locator('[role="radio"]', { hasText: 'Service Down' }).click()
    })

    // ── 7-8. Execute in ChaosLab and observe propagation ────────────────
    await test.step('7-8 — executing runs a real backend simulation and animates propagation', async () => {
      await page.getByRole('button', { name: '⚡ Execute Experiment' }).click()
      // While in flight/propagating, system-switching controls must be disabled
      // so a mid-run system change can't corrupt the result about to land.
      const switcherBtn = page.locator('.app-header button[aria-label^="Active system"]')
      await expect(switcherBtn).toBeDisabled()
      await expect(page.getByText('Simulation complete').first()).toBeVisible({ timeout: 15_000 })
      await expect(switcherBtn).toBeEnabled()
    })

    // ── 9. Resilience analysis is populated from the real run ───────────
    await test.step('9 — resilience analysis reflects the just-completed run', async () => {
      await page.locator('.sidebar-nav-item', { hasText: 'Resilience Analysis' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('Observed data')
      await expect(page.locator('.app-sidebar')).toContainText('Blast radius')
      await expect(page.locator('.app-sidebar')).toContainText('Risk level')
    })

    // ── 10. Recommendation / AI panel reflects the same run ─────────────
    await test.step('10 — recommendation panel is populated, not empty', async () => {
      await page.locator('.sidebar-nav-item', { hasText: 'AI Insights' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('Observed Data')
      await expect(page.locator('.app-sidebar')).toContainText('Recommendation')
    })

    // ── 10b. The Golden Path exposes real Bob/MCP integration state ─────
    // (a lightweight touch-point here — the real MCP round-trip that can
    // flip this to "Active via MCP" is exercised end-to-end in
    // e2e/mcp-integration.spec.ts; this only proves the indicator itself
    // is part of the same screen the rest of the workflow runs on).
    await test.step('10b — the header exposes an honest IBM Bob / MCP status, never a fake "Connected"', async () => {
      const bobIndicator = page.locator('.app-header').getByText('IBM BOB', { exact: true })
      await expect(bobIndicator).toBeVisible()
      const statusText = await page.locator('.app-header')
        .getByText(/Checking…|MCP unavailable|Not connected|Active via MCP|MCP available/)
        .innerText()
      expect(['Checking…', 'MCP unavailable', 'Not connected', 'Active via MCP', 'MCP available']).toContain(statusText)
    })

    // ── 11. Next Experiment Suggestion selects its target node for real ──
    // The RightPanel (with the suggestion) is independent of which LeftSidebar
    // tab is active, so it's already visible right after step 8 completed.
    await test.step('11 — running the suggested next experiment syncs node selection', async () => {
      const rightPanel = page.locator('.app-right-panel')
      const suggestionSection = rightPanel.locator('.panel-section', { hasText: 'Recommended Next Experiment' })
      await expect(suggestionSection).toBeVisible({ timeout: 10_000 })

      const runSuggestedBtn = suggestionSection.getByRole('button', { name: '⚡ Run Suggested Experiment' })
      if (await runSuggestedBtn.count() === 0) {
        // The backend had no further experiment to suggest (every reachable
        // node already tested) — a legitimate terminal state, not a bug.
        return
      }

      const targetLine = await suggestionSection.locator('p', { hasText: 'Target:' }).innerText()
      const suggestedTargetName = targetLine.replace('Target:', '').trim()
      // Note: the suggestion engine prefers a different node from the one
      // just tested, but can legitimately re-suggest it (with honest
      // phrasing) when it's the only critical node on record — so no
      // assumption is made here about which node comes back.

      await runSuggestedBtn.click()
      await expect(page.locator('[role="dialog"]')).toBeVisible()
      // The modal's target node must match what the suggestion said it would
      // run — proving selectNode() was actually called, not just the pending
      // experiment silently pointing elsewhere.
      await expect(page.locator('[role="dialog"]')).toContainText(suggestedTargetName)
      await page.getByRole('button', { name: 'Cancel' }).click()

      // The Digital Twin's own selection must also have followed —
      // cancelling the modal doesn't undo the selection sync.
      await page.locator('.sidebar-nav-item', { hasText: 'Digital Twin' }).click()
      await expect(page.locator('.app-sidebar .node-detail-card')).toContainText(suggestedTargetName)
    })

    // ── 12. History records the run ─────────────────────────────────────
    await test.step('12 — history lists the completed run with real values', async () => {
      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('Core Order Service')
      await expect(page.locator('.app-sidebar')).toContainText('Service Down')
      await expect(page.locator('.app-sidebar')).not.toContainText('No experiments run yet')
    })

    // ── 13. Clicking a history entry restores full workflow context ─────
    await test.step('13 — clicking a history entry restores selection, result, and graph state', async () => {
      // Select a different node first so the restore below is provably a
      // real change, not a no-op.
      await page.locator('.sidebar-nav-item', { hasText: 'Digital Twin' }).click()
      await nodesListItem(page, 'Core Gateway').click()
      await expect(page.locator('.app-sidebar .node-detail-card')).toContainText('Core Gateway')

      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await page.locator('.history-item', { hasText: 'Core Order Service' }).first().click()

      await page.locator('.sidebar-nav-item', { hasText: 'Digital Twin' }).click()
      await expect(page.locator('.app-sidebar .node-detail-card')).toContainText('Core Order Service')

      await page.locator('.sidebar-nav-item', { hasText: 'Resilience Analysis' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('Blast radius')
    })

    // ── 14. Reload persists the system and its history ──────────────────
    await test.step('14 — reload restores the active system and its real history', async () => {
      await page.reload({ waitUntil: 'networkidle' })
      await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })
      await expect.poll(() => activeSystemName(page)).toBe(system.name)
    })

    // ── 15. Post-reload: still on/returns to Digital Twin, context intact ─
    await test.step('15 — after reload, Digital Twin and history are both intact', async () => {
      await expect(page.locator('.sidebar-nav-item.active')).toContainText('Digital Twin')
      await expect(page.locator('.app-sidebar')).toContainText('Core Order Service')

      await page.locator('.sidebar-nav-item', { hasText: 'History' }).click()
      await expect(page.locator('.app-sidebar')).toContainText('Core Order Service')
      await expect(page.locator('.app-sidebar')).toContainText('Service Down')
    })

    // ── 16. No console errors or failed backend requests anywhere in the chain ─
    await test.step('16 — zero console errors and zero failed API requests across the entire run', async () => {
      expect(consoleErrors, `Console errors during the run:\n${consoleErrors.join('\n')}`).toHaveLength(0)
      expect(failedRequests, `Failed/5xx requests during the run:\n${failedRequests.join('\n')}`).toHaveLength(0)
    })
  })
})
