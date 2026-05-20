import { addEdge } from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import { LOOP_DIMS } from './loop-utils';

export class CanvasEngine {
  static onConnect(params: Connection, edges: Edge[]): Edge[] {
    const isError = params.sourceHandle === 'error';
    return addEdge({
      ...params,
      type: 'smoothstep',
      animated: false,
      style: isError
        ? { stroke: '#ff4d4f', strokeWidth: 2 }
        : { stroke: 'var(--workflow-edge, #555)', strokeWidth: 2 },
    } as any, edges);
  }

  static createNode(type: string, position: { x: number, y: number }, definition?: any): Node {
    const properties: Record<string, any> = {};

    if (definition) {
      definition.properties.forEach((prop: any) => {
        if (prop.default !== undefined) {
          properties[prop.name] = prop.default;
        }
      });
    }

    const defaultWidth = definition?.defaultWidth
    const defaultHeight = definition?.defaultHeight
    const isLoop = type === 'logic.loop'

    // Loop nodes store width/height in data (Sim pattern) + ReactFlow style
    const loopData = isLoop
      ? { width: defaultWidth ?? LOOP_DIMS.DEFAULT_WIDTH, height: defaultHeight ?? LOOP_DIMS.DEFAULT_HEIGHT }
      : {}

    return {
      id: `${type}-${Date.now()}`,
      type,
      position,
      ...(defaultWidth ? { width: defaultWidth } : {}),
      ...(defaultHeight ? { height: defaultHeight } : {}),
      style: (defaultWidth || defaultHeight)
        ? { width: defaultWidth, height: defaultHeight }
        : undefined,
      data: {
        label: '',
        properties,
        ...loopData,
      },
    };
  }

  static validateConnection(connection: Connection): boolean {
    // Basic cycle detection or port validation
    return connection.source !== connection.target;
  }
}
