export type KnownNodePropertyType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'json'
  | 'options'
  | 'credential'
  | 'key-value'
  | 'list'
  | 'messages'
  | 'schema'
  | 'file-list'
  | 'tool-selector'
  | 'skill-selector';

export type NodePropertyType = KnownNodePropertyType | (string & {});

export interface NodeProperty {
  name: string;
  label: string;
  type: NodePropertyType;
  description?: string;
  default?: any;
  required?: boolean | { field: string; value: any | any[] };
  options?: { label: string; value: any }[];
  placeholder?: string;
  condition?: any;
  credentialType?: string;
  credentialTypeByField?: { field: string; values: Record<string, string> };
  /**
   * Fields that must be non-empty before this field is enabled.
   * - Array: all listed fields must have values (AND logic)
   * - Object: `{ all?: string[]; any?: string[] }` for mixed AND/OR logic
   */
  dependsOn?: string[] | { all?: string[]; any?: string[] };
  loadOptions?: string;
  loadOptionsDependsOn?: string[];
  mode?: 'basic' | 'advanced' | 'both';
  secret?: boolean;
  visibility?: 'user-or-llm' | 'user-only' | 'hidden';
  /** Links basic and advanced variants of the same logical field */
  canonicalId?: string;
  /** Section label for visual grouping within the inspector */
  group?: string;
}

export interface NodeDefinition {
  type: string;
  name: string;
  category: 'trigger' | 'action' | 'logic' | 'ai' | 'browser' | 'integration';
  description: string;
  icon: string;
  color?: string;
  properties: NodeProperty[];
  inputs: number;
  outputs: number;
  outputsSchema?: { label: string; type: string }[];
  allowError?: boolean;
  credentialType?: string;
  allowError?: boolean;
  tools?: string[];
  operationToolMap?: Record<string, string>;
}
