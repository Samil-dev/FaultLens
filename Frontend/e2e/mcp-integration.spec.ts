import { test, expect } from '@playwright/test'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const execFileAsync = promisify(execFile)

// Resolve paths relative to this file, not to whatever directory
// `npx playwright test` happened to be invoked from.
const THIS_FILE_DIR = path.dirname(fileURLToPath(import.meta.url)) // .../Frontend/e2e
const BACKEND_DIR = path.resolve(THIS_FILE_DIR, '..', '..', 'Backend')
const PYTHON_EXE = path.join(BACKEND_DIR, 'venv', 'Scripts', 'python.exe')

/**
 * Validates FaultLens's real, observable IBM Bob / MCP integration status
 * in the UI — the header's "IBM BOB" indicator (Frontend/src/components/
 * layout/IBMBobMcpStatus.tsx), backed by GET /api/mcp/status.
 *
 * The strongest part of this spec actually spawns a real MCP client
 * (Backend/scripts/mcp_demo_client.py) as a subprocess — using the real
 * `mcp` SDK, the same command/args/cwd shape .bob/mcp.json declares — to
 * call FaultLens's MCP tools exactly as an external Bob agent would, then
 * confirms the browser UI reflects that real activity. This is not a
 * simulated connection: it's a genuine MCP protocol round-trip, driven from
 * outside the browser, verified through the real UI polling loop.
 *
 * Requires both dev servers already running (see playwright.config.ts) and
 * a working Backend/venv (see Backend/scripts/mcp_demo_client.py's docstring).
 */

const runId = Date.now()

test.describe('FaultLens — IBM Bob / MCP integration status', () => {
  test('the header shows a real IBM Bob indicator, never a fabricated "Connected" claim', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
    page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err.message}`))

    await page.goto('/')
    await expect(page.getByText('FAULTLENS', { exact: true })).toBeVisible({ timeout: 15_000 })

    const bobIndicator = page.locator('.app-header').getByText('IBM BOB', { exact: true })

    await test.step('the indicator is present and shows one of the honest, real states', async () => {
      await expect(bobIndicator).toBeVisible({ timeout: 15_000 })
      // Whatever state it starts in (depends on this shared dev database's
      // prior activity), it must be one of the real, defined states — never
      // a bare "Connected" that this architecture can't actually promise.
      const validStates = ['MCP checking…', 'MCP unavailable', 'Bob not connected', 'MCP active', 'MCP available']
      const statusText = await page.locator('.app-header').getByText(/MCP checking…|MCP unavailable|Bob not connected|MCP active|MCP available/).innerText()
      expect(validStates).toContain(statusText)
    })

    await test.step('a real MCP client call updates the indicator to "MCP active"', async () => {
      const systemId = `e2e-mcp-status-${runId}`

      // Spawns app.mcp.server as a real subprocess and talks to it over the
      // real MCP stdio protocol — see the script's own docstring. This is
      // not a call into FaultLens's REST API; it's an independent MCP
      // client process, exactly like an external Bob agent would be.
      await execFileAsync(
        PYTHON_EXE,
        ['scripts/mcp_demo_client.py', systemId],
        { cwd: BACKEND_DIR, timeout: 20_000 },
      )

      // The header polls GET /api/mcp/status every 10s — poll.toPass gives
      // it room to pick up the real activity we just generated.
      await expect(async () => {
        const statusText = await page.locator('.app-header').getByText(/MCP active|MCP available/).innerText()
        expect(statusText).toBe('MCP active')
      }).toPass({ timeout: 15_000, intervals: [1_000] })
    })

    expect(consoleErrors, `Console errors during the run:\n${consoleErrors.join('\n')}`).toHaveLength(0)
  })
})
