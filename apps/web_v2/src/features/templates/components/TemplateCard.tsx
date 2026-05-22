import { Icons } from '@/shared/components/icons'
import type { Template } from '../types/templatesTypes'

interface Props { template: Template }

export function TemplateCard({ template }: Props) {
  return (
    <div className="inspo-card">
      <div className={`inspo-art ${template.bg}`}>
        <div className="index">{template.idx}</div>
        <div className="inspo-mock">
          <div className="bar" />
          <div className="body-mock" />
        </div>
        <div className="label">{template.label}</div>
      </div>
      <div className="inspo-meta">
        <div className="inspo-meta-title">{template.title}</div>
        <div className="inspo-meta-row">
          <span><Icons.Flow /> {template.kind}</span>
          <span>{template.steps} steps</span>
        </div>
      </div>
    </div>
  )
}
