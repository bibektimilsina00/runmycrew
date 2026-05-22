import type { FileItem } from '../types/filesTypes'

const MOCK_FILES: FileItem[] = [
  { id: 1, name: 'Q2_refund_report.pdf',        ext: 'pdf',  size: '1.2 MB', uploaded: '2h ago',  source: 'Invoice triage agent' },
  { id: 2, name: 'leads_export_may22.csv',       ext: 'csv',  size: '842 KB', uploaded: '4h ago',  source: 'Lead enrichment flow' },
  { id: 3, name: 'rfp_acme_corp.docx',           ext: 'doc',  size: '312 KB', uploaded: '1d ago',  source: 'RFP classifier agent' },
  { id: 4, name: 'metrics_digest_w20.pdf',       ext: 'pdf',  size: '2.1 MB', uploaded: '5d ago',  source: 'Weekly metrics agent' },
  { id: 5, name: 'churn_signals_export.csv',     ext: 'csv',  size: '218 KB', uploaded: '6h ago',  source: 'Churn-risk watchlist' },
  { id: 6, name: 'pipeline_data.json',           ext: 'json', size: '94 KB',  uploaded: '2d ago',  source: 'HubSpot sync' },
  { id: 7, name: 'support_export_q2.xls',        ext: 'xls',  size: '1.8 MB', uploaded: '1d ago',  source: 'Zendesk export' },
  { id: 8, name: 'brand_assets_pack.img',        ext: 'img',  size: '14.3 MB', uploaded: '3d ago', source: 'Manual upload' },
]

export const filesAPI = {
  getAll: async (): Promise<FileItem[]> => MOCK_FILES,
}
