import { useQuery } from '@tanstack/react-query'
import type { NodeDefinition } from '@fuse/node-definitions'
import { requestJson } from '@/lib/api/client'
import { ApiNodeDefinitionListSchema, type ApiNodeDefinition } from '@/lib/api/contracts'
import { nodeKeys } from '@/hooks/nodes/keys'

function normalizeNodeDefinition(node: ApiNodeDefinition): NodeDefinition {
  return {
    ...node,
    allowError: node.allow_error,
    credentialType: node.credential_type ?? undefined,
    outputsSchema: node.outputs_schema,
    tools: node.tools ?? undefined,
    operationToolMap: node.operation_tool_map ?? undefined,
    defaultWidth: node.default_width ?? undefined,
    defaultHeight: node.default_height ?? undefined,
  }
}

export function useNodes() {
  return useQuery({
    queryKey: nodeKeys.lists(),
    queryFn: async ({ signal }) => {
      const nodes = await requestJson(ApiNodeDefinitionListSchema, {
        url: '/nodes/',
        method: 'GET',
        signal,
      })
      return nodes.map(normalizeNodeDefinition)
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
  })
}
