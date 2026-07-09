import { MarkdownRenderer } from './MarkdownRenderer'
import { CodeRenderer } from './CodeRenderer'
import { ImageRenderer } from './ImageRenderer'
import { UrlPreviewRenderer } from './UrlPreviewRenderer'
import { IframeRenderer } from './IframeRenderer'
import { HtmlRenderer } from './HtmlRenderer'
import { FileRenderer } from './FileRenderer'
import { AudioRenderer } from './AudioRenderer'
import { VideoRenderer } from './VideoRenderer'
import { JsonRenderer } from './JsonRenderer'
import { TableRenderer } from './TableRenderer'
import { ChartRenderer } from './ChartRenderer'
import { CitationRenderer } from './CitationRenderer'
import { PdfRenderer } from './PdfRenderer'
import type { ArtifactRenderer } from './types'
import type { Artifact } from '../../types/artifactTypes'

const REGISTRY: Record<string, ArtifactRenderer> = {
  markdown: MarkdownRenderer,
  code: CodeRenderer,
  image: ImageRenderer,
  url_preview: UrlPreviewRenderer,
  iframe: IframeRenderer,
  html: HtmlRenderer,
  file: FileRenderer,
  audio: AudioRenderer,
  video: VideoRenderer,
  json: JsonRenderer,
  table: TableRenderer,
  chart: ChartRenderer,
  citation: CitationRenderer,
  pdf: PdfRenderer,
}

interface ArtifactViewProps {
  artifact: Artifact
  fullscreen?: boolean
}

export function ArtifactView({ artifact, fullscreen }: ArtifactViewProps) {
  const Cmp = REGISTRY[artifact.type] ?? JsonRenderer
  return <Cmp artifact={artifact} fullscreen={fullscreen} />
}
