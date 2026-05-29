
export type ExecutionStatus = 'running' | 'completed' | 'failed' | null

export const useNodeExecutionStatus = (_nodeId: string): ExecutionStatus => null
