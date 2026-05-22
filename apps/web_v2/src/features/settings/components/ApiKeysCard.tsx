import { useState } from 'react'
import { Key, Copy, Trash2, Plus } from 'lucide-react'
import { Card, Button, Input } from '@/shared/components'
import type { ApiKey } from '../types/settingsTypes'

interface ApiKeysCardProps {
  apiKeys: ApiKey[]
  isGenerating: boolean
  onCreateKey: (name: string) => Promise<ApiKey>
  onRevokeKey: (id: string, name: string) => void
  onCopyKey: (token: string) => void
}

export function ApiKeysCard({ apiKeys, isGenerating, onCreateKey, onRevokeKey, onCopyKey }: ApiKeysCardProps) {
  const [newKeyName, setNewKeyName] = useState('')

  const handleCreate = async () => {
    if (!newKeyName.trim()) return
    await onCreateKey(newKeyName.trim())
    setNewKeyName('')
  }

  return (
    <Card padding="lg" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1 pb-3 border-b border-border-faint">
        <h3 className="text-sm font-semibold text-text tracking-tight flex items-center gap-2">
          <Key size={14} className="text-accent" />
          <span>Developer Access Keys</span>
        </h3>
        <p className="text-xs text-text-faint">Authenticate command line agents and remote microservices.</p>
      </div>

      <div className="flex gap-3 bg-bg/50 p-3.5 border border-border-faint rounded-[10px]">
        <div className="flex-1">
          <Input
            placeholder="Enter new key description (e.g. Server CLI)..."
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            disabled={isGenerating}
          />
        </div>
        <Button variant="primary" onClick={handleCreate} loading={isGenerating}>
          <Plus size={12} className="mr-1.5" />
          Generate
        </Button>
      </div>

      <div className="flex flex-col gap-2 mt-2">
        {apiKeys.length === 0 ? (
          <div className="text-center py-6 text-xs text-text-faint border border-dashed border-border-faint rounded-[10px]">
            No API keys configured.
          </div>
        ) : (
          apiKeys.map((k) => (
            <div
              key={k.id}
              className="flex items-center justify-between gap-4 p-3 bg-bg/20 border border-border-faint hover:border-border-soft rounded-[10px] transition-colors"
            >
              <div className="flex flex-col gap-1">
                <span className="text-xs font-semibold text-text">{k.name}</span>
                <span className="font-mono text-[10px] text-text-faint bg-bg px-2 py-0.5 rounded-[4px] border border-border-faint max-w-max select-all">
                  {k.token}
                </span>
                <span className="text-[9px] text-text-dim mt-0.5">Created on {k.createdAt}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-8 w-8 p-0 justify-center"
                  onClick={() => onCopyKey(k.token)}
                  title="Copy API Token"
                >
                  <Copy size={12} />
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  className="h-8 w-8 p-0 justify-center hover:text-err"
                  onClick={() => onRevokeKey(k.id, k.name)}
                  title="Revoke API Key"
                >
                  <Trash2 size={12} />
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  )
}
