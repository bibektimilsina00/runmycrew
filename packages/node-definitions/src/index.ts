import * as aiNodes from './nodes/ai'
import * as commonNodes from './nodes/common'
import * as httpNodes from './nodes/http'
import * as slackNodes from './nodes/slack'
import type { NodeDefinition } from './types'

export * from './types'
export * from './registry'

export const nodeDefinitions: NodeDefinition[] = [
  ...Object.values(aiNodes),
  ...Object.values(commonNodes),
  ...Object.values(httpNodes),
  ...Object.values(slackNodes),
].filter(d => typeof d === 'object' && 'type' in d) as NodeDefinition[]
