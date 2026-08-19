import { useEffect, useState } from 'react'
import { fetchMcpStatus } from '../../services/api'
import type { McpActivity } from '../../types/api'

// A tool call this recent is shown as "active" rather than merely "available" —
// long enough to stay visible through a short demo pause, short enough that
// it never implies a persistent live connection that stdio MCP doesn't have.
const ACTIVE_WINDOW_SECONDS = 120

type State =
  | { kind: 'loading' }
  | { kind: 'unavailable' }
  | { kind: 'no_activity' }
  | { kind: 'active'; activity: McpActivity }
  | { kind: 'idle'; activity: McpActivity }

function formatAgo(seconds: number): string {
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  return `${hours}h ago`
}

/**
 * Shows the real, observable state of FaultLens's MCP integration with IBM
 * Bob — never a fabricated "Connected" badge. MCP runs over a separate
 * stdio subprocess with no channel back to this REST API's process, so
 * there is no live socket-style connection status to report. What this
 * shows instead is honestly scoped: whether the MCP server code is present
 * in this backend, and the most recent *real* MCP tool call recorded (if
 * any) — genuine evidence of Bob having used FaultLens, not a guess.
 */
export function IBMBobMcpStatus() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const res = await fetchMcpStatus()
        if (cancelled) return
        const { server_available, last_activity } = res.data
        if (!server_available) {
          setState({ kind: 'unavailable' })
        } else if (!last_activity) {
          setState({ kind: 'no_activity' })
        } else if (last_activity.seconds_ago < ACTIVE_WINDOW_SECONDS) {
          setState({ kind: 'active', activity: last_activity })
        } else {
          setState({ kind: 'idle', activity: last_activity })
        }
      } catch {
        if (!cancelled) setState({ kind: 'unavailable' })
      }
    }

    void poll()
    const id = setInterval(poll, 10_000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  const dotColor =
    state.kind === 'active' ? 'var(--color-healthy)' :
    state.kind === 'idle' ? 'var(--color-degraded)' :
    'var(--text-muted)'

  const label =
    state.kind === 'loading' ? 'Checking…' :
    state.kind === 'unavailable' ? 'MCP unavailable' :
    state.kind === 'no_activity' ? 'Not connected' :
    state.kind === 'active' ? 'Active via MCP' :
    'MCP available'

  const detail =
    state.kind === 'active' || state.kind === 'idle'
      ? `${state.activity.tool_name} · ${formatAgo(state.activity.seconds_ago)}`
      : state.kind === 'no_activity'
      ? 'No MCP activity recorded'
      : undefined

  const title =
    state.kind === 'no_activity'
      ? 'IBM Bob connects to FaultLens through MCP (.bob/mcp.json). No MCP client has called a FaultLens tool yet. See docs/ai-integration.md.'
      : state.kind === 'unavailable'
      ? 'The MCP server module could not be verified as available in this backend.'
      : `Real MCP integration status — see docs/ai-integration.md.${detail ? ` Last call: ${detail}.` : ''}`

  return (
    <div
      style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 8 }}
      title={title}
      aria-label={`IBM Bob MCP status: ${label}${detail ? `, ${detail}` : ''}`}
    >
      <span
        aria-hidden="true"
        style={{
          width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
          background: dotColor,
          animation: state.kind === 'active' ? 'blink 1.2s ease infinite' : undefined,
        }}
      />
      <span style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)', letterSpacing: '0.04em' }}>
          IBM BOB
        </span>
        <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>
          {label}
        </span>
      </span>
    </div>
  )
}
