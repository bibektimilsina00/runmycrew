import { KeyRound } from 'lucide-react'
import { useMemo } from 'react'
import { useCredentials } from '@/features/connections/hooks/useConnections'
import { Select } from '@/shared/components'
import type { NodeDefinition, NodeProperty } from '../../../../types/editorTypes'
import { resolveCredentialTypes } from '../../utils/credential-types'

interface Props {
  prop: NodeProperty
  definition: NodeDefinition
  properties: Record<string, unknown>
  value: unknown
  onChange: (value: unknown) => void
}

export function CredentialRenderer({ prop, definition, properties, value, onChange }: Props) {
  const { data: credentials = [], isLoading } = useCredentials()
  const credentialTypes = useMemo(
    () => resolveCredentialTypes(prop, definition, properties),
    [definition, prop, properties],
  )
  const options = credentials
    .filter(c => credentialTypes.length === 0 || credentialTypes.includes(c.type))
    .map(c => ({ value: c.id, label: c.name, description: c.type, icon: <KeyRound size={13} /> }))

  return (
    <Select
      value={value !== undefined && value !== null ? String(value) : ''}
      placeholder={isLoading ? 'Loading credentials…' : 'Select credential'}
      options={options}
      onChange={onChange}
      disabled={isLoading}
    />
  )
}
