import type { Artifact } from '../../types/artifactTypes'

export interface RendererProps {
  artifact: Artifact
  fullscreen?: boolean
}

export type ArtifactRenderer = React.FC<RendererProps>
