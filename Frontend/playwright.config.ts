import { defineConfig } from '@playwright/test'

// FaultLens E2E suite. Requires BOTH dev servers already running:
//   Backend:  cd Backend  && venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
//   Frontend: cd Frontend && npm run dev
// Not auto-started here on purpose — the backend is a separate Python
// process (venv-dependent), so wiring it into this Node-only config would
// couple frontend tooling to a Python interpreter path. Run `npm run
// test:e2e` once both are up.
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  fullyParallel: false, // tests intentionally share backend-persisted state within a file
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    viewport: { width: 1920, height: 1080 },
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
})
