import type { NodeDefinition, NodeProperty } from '../../../types/editorTypes'

export function resolveCredentialTypes(
  prop: NodeProperty,
  definition: NodeDefinition,
  properties: Record<string, unknown>,
): string[] {
  if (Array.isArray(prop.credentialType)) return prop.credentialType
  if (prop.credentialType) return [prop.credentialType]

  const dynamic = prop.credentialTypeByField
  if (dynamic) {
    const fieldValue = properties[dynamic.field]
    const credentialType = typeof fieldValue === 'string' ? dynamic.values[fieldValue] : undefined
    return credentialType ? [credentialType] : []
  }

  if (definition.credentialType) return [definition.credentialType]
  return []
}
