// Persists only the *identifier* of the system the user was last working
// with — never the full System object. The real data always comes from the
// backend; localStorage just remembers which system_id to ask for again.
const STORAGE_KEY = 'faultlens.activeSystemId'

export function getStoredSystemId(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    // localStorage unavailable (private browsing, disabled storage, etc.) —
    // treat as "nothing stored" rather than failing the app.
    return null
  }
}

export function setStoredSystemId(id: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, id)
  } catch {
    // Non-fatal: the session simply won't survive a reload.
  }
}

export function clearStoredSystemId(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}
