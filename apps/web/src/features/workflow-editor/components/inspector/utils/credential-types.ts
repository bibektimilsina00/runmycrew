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
    // Fall back to the driving field's declared default — a fresh node
    // hasn't persisted `provider: "openai"` yet, and without this the
    // selector rendered as "no credential type" until the user re-picked
    // the provider.
    const fieldValue =
      properties[dynamic.field] ??
      definition.properties.find(p => p.name === dynamic.field)?.default
    const credentialType = typeof fieldValue === 'string' ? dynamic.values[fieldValue] : undefined
    return credentialType ? [credentialType] : []
  }

  if (definition.credentialType) return [definition.credentialType]
  return []
}
