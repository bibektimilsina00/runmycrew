import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import type { Variable } from '../types/variablesTypes'

interface Props { items: Variable[] }

export function VariablesTable({ items }: Props) {
  const [reveal, setReveal] = useState<Record<number, boolean>>({})

  return (
    <div className="panel">
      <div className="table table-vars">
        <div className="table-head">
          <span>Key</span>
          <span>Value</span>
          <span>Scope</span>
          <span>Updated</span>
          <span></span>
        </div>
        {items.map(v => (
          <div key={v.id} className="table-row">
            <span className="row-name mono">{v.key}</span>
            <span className="var-val">
              <span className="row-mono">
                {v.plain || reveal[v.id] ? v.val : v.val.replace(/[^·]/g, '•')}
              </span>
              {!v.plain && (
                <button
                  className="reveal-btn"
                  onClick={e => { e.stopPropagation(); setReveal(r => ({ ...r, [v.id]: !r[v.id] })) }}
                >
                  {reveal[v.id] ? <Icons.EyeOff /> : <Icons.Eye />}
                </button>
              )}
            </span>
            <span className="row-owner">{v.scope}</span>
            <span className="row-mono">{v.updated}</span>
            <span className="caret"><Icons.CaretRight /></span>
          </div>
        ))}
      </div>
    </div>
  )
}
