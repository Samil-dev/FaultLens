import { useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts'
import { useStore } from '../../store/experimentStore'
import type { MetricComparison } from '../../types/api'

// Mirrors the fixed "healthy" baseline in Backend/app/services/metrics_service.py
// (get_node_metrics, simulated_status == "healthy"). Every before/after snapshot
// starts from this baseline, so before = BASELINE and after = BASELINE + delta.
const HEALTHY_BASELINE = { cpu_usage: 35, memory_usage: 55, latency_ms: 40, error_rate: 0.2 }

type MetricKey = 'cpu_usage' | 'memory_usage' | 'latency_ms' | 'error_rate'

const METRICS: { key: MetricKey; deltaKey: keyof MetricComparison; label: string; unit: string }[] = [
  { key: 'cpu_usage',    deltaKey: 'cpu_usage_delta',    label: 'CPU',        unit: '%'  },
  { key: 'memory_usage', deltaKey: 'memory_usage_delta', label: 'Memory',     unit: '%'  },
  { key: 'latency_ms',   deltaKey: 'latency_delta_ms',   label: 'Latency',    unit: 'ms' },
  { key: 'error_rate',   deltaKey: 'error_rate_delta',   label: 'Error Rate', unit: '%'  },
]

export function MetricsPanel() {
  const { lastResult, system } = useStore()
  const [metric, setMetric] = useState<MetricKey>('cpu_usage')

  if (!lastResult) {
    return (
      <div className="empty-state">
        <span className="empty-icon">📈</span>
        <span>Run an experiment to see before/after metric charts here.</span>
      </div>
    )
  }

  const active = METRICS.find((m) => m.key === metric)!

  const rows = lastResult.comparisons
    .map((c) => {
      const delta = c[active.deltaKey] as number
      const before = HEALTHY_BASELINE[active.key]
      const after = before + delta
      return {
        id: c.node_id,
        name: system.nodes.find((n) => n.id === c.node_id)?.name ?? c.node_id,
        before: Math.round(before * 10) / 10,
        after: Math.round(after * 10) / 10,
        delta,
      }
    })
    // Impacted nodes first, unaffected nodes collapse to the bottom.
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))

  const impacted = rows.filter((r) => Math.abs(r.delta) > 0.01)
  const shown = impacted.length > 0 ? impacted : rows.slice(0, 5)

  return (
    <div className="panel-section">
      <p className="panel-section-title">Before / After Metrics</p>

      <div style={{ display: 'flex', gap: 4, marginBottom: 10, flexWrap: 'wrap' }}>
        {METRICS.map((m) => (
          <button
            key={m.key}
            type="button"
            onClick={() => setMetric(m.key)}
            className="btn btn-ghost btn-sm"
            style={{
              borderColor: metric === m.key ? 'var(--accent)' : 'var(--border-bright)',
              color: metric === m.key ? 'var(--accent)' : 'var(--text-secondary)',
              background: metric === m.key ? 'var(--accent-dim)' : 'transparent',
            }}
          >
            {m.label}
          </button>
        ))}
      </div>

      {shown.length === 0 ? (
        <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>No metric data for this run.</p>
      ) : (
        <ResponsiveContainer width="100%" height={Math.max(120, shown.length * 34)}>
          <BarChart data={shown} layout="vertical" margin={{ top: 4, right: 12, bottom: 4, left: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={80}
              tick={{ fill: 'var(--text-secondary)', fontSize: 10 }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: 'var(--bg-elevated)' }}
              contentStyle={{
                background: 'var(--bg-panel)',
                border: '1px solid var(--border-bright)',
                borderRadius: 6,
                fontSize: 11,
              }}
              labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
              formatter={(value, name) => [`${value}${active.unit}`, String(name)]}
            />
            <Bar dataKey="before" name="Before" fill="var(--border-bright)" radius={[0, 3, 3, 0]} barSize={9} />
            <Bar dataKey="after" name="After" radius={[0, 3, 3, 0]} barSize={9}>
              {shown.map((r) => (
                <Cell
                  key={r.id}
                  fill={
                    Math.abs(r.delta) < 0.01
                      ? 'var(--color-healthy)'
                      : r.delta > 0
                      ? 'var(--color-failed)'
                      : 'var(--color-recovering)'
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}

      <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--border-bright)', display: 'inline-block' }} />
          Before
        </span>
        <span style={{ fontSize: 10, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--color-failed)', display: 'inline-block' }} />
          After (worse)
        </span>
      </div>
    </div>
  )
}
