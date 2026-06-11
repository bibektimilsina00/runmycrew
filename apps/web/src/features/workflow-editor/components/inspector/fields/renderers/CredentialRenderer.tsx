import { useMemo } from 'react'
import { CredentialSelector } from '@/shared/components'
import { resolveCredentialTypes } from '../../utils/credential-types'
import type { RendererProps } from '../types'

export function CredentialRenderer({ prop, definition, properties, value, onChange, disabled }: RendererProps) {
  const credentialTypes = useMemo(
    () => resolveCredentialTypes(prop, definition, properties),
    [definition, prop, properties],
  )

  // If the node defines multiple acceptable credential types (e.g. OAuth or
  // API key), we use the first. Most nodes have exactly one; this matches the
  // previous behaviour and keeps the inspector contract simple.
  const credType = credentialTypes[0]
  if (!credType) {
    return (
      <p className="text-[11px] text-text-faint">
        This node does not declare a credential type.
      </p>
    )
  }

  return (
    <CredentialSelector
      credType={credType}
      value={value !== undefined && value !== null ? String(value) : ''}
      onChange={onChange}
      disabled={disabled}
    />
  )
}
