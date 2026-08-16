import { useRef, useState, type DragEvent } from 'react'
import { useStore, DEMO_SYSTEM } from '../../store/experimentStore'
import { createSystem, fetchExperimentHistory } from '../../services/api'
import type { System } from '../../types/api'

type Stage = 'editing' | 'submitting' | 'success'

export function ImportSystemModal() {
  const { systemImportOpen, setSystemImportOpen, setSystem, setExperimentHistory } = useStore()

  const [jsonText, setJsonText] = useState('')
  const [stage, setStage] = useState<Stage>('editing')
  const [error, setError] = useState<string | null>(null)
  const [imported, setImported] = useState<System | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!systemImportOpen) return null

  function reset() {
    setJsonText('')
    setStage('editing')
    setError(null)
    setImported(null)
  }

  function close() {
    setSystemImportOpen(false)
    reset()
  }

  function loadFile(file: File) {
    setError(null)
    if (!file.name.toLowerCase().endsWith('.json')) {
      setError('Only .json files are supported.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => setJsonText(String(reader.result ?? ''))
    reader.onerror = () => setError('Could not read the file.')
    reader.readAsText(file)
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) loadFile(file)
  }

  function loadDemoSystem() {
    setJsonText(JSON.stringify(DEMO_SYSTEM, null, 2))
    setError(null)
  }

  async function handleImport() {
    setError(null)

    let parsed: unknown
    try {
      parsed = JSON.parse(jsonText)
    } catch (err) {
      setError(`Invalid JSON: ${err instanceof Error ? err.message : 'could not parse'}`)
      return
    }

    if (
      typeof parsed !== 'object' || parsed === null ||
      !('nodes' in parsed) || !('dependencies' in parsed) ||
      !('id' in parsed) || !('name' in parsed)
    ) {
      setError('This does not look like a FaultLens System: expected "id", "name", "nodes", and "dependencies".')
      return
    }

    setStage('submitting')
    try {
      const response = await createSystem(parsed as System)
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? 'The backend rejected this architecture.')
      }

      setImported(response.data)
      setSystem(response.data)
      setStage('success')

      try {
        const history = await fetchExperimentHistory(response.data.id)
        setExperimentHistory(history)
      } catch {
        setExperimentHistory([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed.')
      setStage('editing')
    }
  }

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && close()}>
      <div
        className="modal-box"
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-system-title"
        style={{ width: 560 }}
      >
        <div className="modal-title" id="import-system-title">
          ⬡ Import System Architecture
        </div>

        {stage === 'success' && imported ? (
          <>
            <div style={{
              background: 'rgba(63,185,80,0.08)', border: '1px solid rgba(63,185,80,0.25)',
              borderRadius: 'var(--radius-md)', padding: '12px 14px', marginBottom: 16,
            }}>
              <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-healthy)', marginBottom: 8 }}>
                Architecture Analysis
              </p>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 2 }}>
                <div>✓ {imported.nodes.length} node{imported.nodes.length === 1 ? '' : 's'} detected</div>
                <div>✓ {imported.dependencies.length} dependenc{imported.dependencies.length === 1 ? 'y' : 'ies'} detected</div>
                <div>✓ Dependency graph validated (no cycles)</div>
                <div>✓ Digital Twin ready — "{imported.name}"</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={close}>
                View Digital Twin
              </button>
            </div>
          </>
        ) : (
          <>
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              style={{
                border: `1px dashed ${dragOver ? 'var(--accent)' : 'var(--border-bright)'}`,
                background: dragOver ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                borderRadius: 'var(--radius-md)',
                padding: '14px',
                marginBottom: 12,
                textAlign: 'center',
                transition: 'all var(--transition)',
              }}
            >
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>
                Drag a <code className="mono">.json</code> file here, paste it below, or
              </p>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => fileInputRef.current?.click()}>
                  Choose file…
                </button>
                <button type="button" className="btn btn-ghost btn-sm" onClick={loadDemoSystem}>
                  Load demo system
                </button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                style={{ display: 'none' }}
                onChange={(e) => e.target.files?.[0] && loadFile(e.target.files[0])}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="system-json-input">
                Architecture Source (JSON)
              </label>
              <textarea
                id="system-json-input"
                className="form-input mono"
                style={{ minHeight: 160, resize: 'vertical', lineHeight: 1.5 }}
                placeholder={'{\n  "id": "sys-my-system",\n  "name": "My System",\n  "nodes": [...],\n  "dependencies": [...]\n}'}
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
                spellCheck={false}
              />
            </div>

            <p style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 16 }}>
              FaultLens accepts a system definition as JSON — the same shape returned by{' '}
              <code className="mono">GET /api/systems</code>: an id, a name, a list of nodes, and a list of
              dependencies. Validation (unique node ids, no dependency cycles) is performed by the backend.
            </p>

            {error && (
              <div style={{
                background: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.25)',
                borderRadius: 'var(--radius-md)', padding: '8px 12px', marginBottom: 16,
                fontSize: 11, color: 'var(--color-failed)',
              }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={close} disabled={stage === 'submitting'}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleImport}
                disabled={stage === 'submitting' || jsonText.trim().length === 0}
              >
                {stage === 'submitting'
                  ? (<><span className="spinner" style={{ width: 11, height: 11, borderWidth: 1.5 }} /> Analyzing…</>)
                  : '⬡ Import Architecture'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
