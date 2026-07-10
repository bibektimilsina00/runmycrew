import { useMemo } from 'react'
import { CredentialSelector } from '@/shared/components'
import { resolveCredentialTypes } from '../../utils/credential-types'
import type { RendererProps } from '../types'

export function CredentialRenderer({ prop, definition, properties, value, onChange, disabled }: RendererProps) {
  const credentialTypes = useMemo(
    () => resolveCredentialTypes(prop, definition, properties),
    [definition, prop, properties],
  )

  if (credentialTypes.length === 0) {
    return (
      <p className="rounded-[7px] border border-dashed border-border-faint px-2.5 py-2 text-[11px] text-text-faint">
        {prop.credentialTypeByField
          ? 'No stored credential type for this provider — the workspace default key is used.'
          : 'This node does not declare a credential type.'}
      </p>
    )
  }

  return (
    <CredentialSelector
      credType={credentialTypes.length === 1 ? credentialTypes[0] : credentialTypes}
      value={value !== undefined && value !== null ? String(value) : ''}
      onChange={onChange}
      disabled={disabled}
    />
  )
}
