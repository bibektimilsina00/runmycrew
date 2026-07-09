import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute, PublicRoute } from '@/shared/components'
import { useReportBugShortcut } from '@/shared/observability/useReportBugShortcut'
import { AppLayout, EditorLayout } from '@/shared/layouts'
import { APP_ROUTES } from '@/shared/constants/routes'
import { Login, Register, ForgotPassword, ResetPassword } from '@/features/auth'
import { Dashboard } from '@/features/dashboard'
import { Settings } from '@/features/settings'
import { Showcase } from '@/features/showcase'
import { Automations } from '@/features/automations'
import { Loops } from '@/features/loops'
import { Templates, TemplateDetail, MyTemplates } from '@/features/templates'
import { Runs } from '@/features/runs'
import { Schedules } from '@/features/schedules'
import { Logs } from '@/features/logs'
import { Tables } from '@/features/tables'
import { Files } from '@/features/files'
import { Knowledge, KnowledgeDetail, KnowledgeDocumentView } from '@/features/knowledge'
import { Skills, SkillEditor } from '@/features/skills'
import { Personas } from '@/features/personas'
import { WorkflowEditor } from '@/features/workflow-editor'
import { Variables } from '@/features/variables'
import { Connections } from '@/features/connections'
import { WorkspaceSettings, InviteAccept } from '@/features/workspaces'

export default function App() {
  useReportBugShortcut()
  return (
    <BrowserRouter>
      <Routes>
        {/* Public auth pages */}
        <Route element={<PublicRoute />}>
          <Route path={APP_ROUTES.LOGIN} element={<Login />} />
          <Route path={APP_ROUTES.REGISTER} element={<Register />} />
          <Route path={APP_ROUTES.FORGOT_PASSWORD} element={<ForgotPassword />} />
          <Route path={APP_ROUTES.RESET_PASSWORD} element={<ResetPassword />} />
        </Route>

        {/* Protected app pages */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path={APP_ROUTES.DASHBOARD} element={<Dashboard />} />
            <Route path={APP_ROUTES.SETTINGS} element={<Settings />} />
            <Route path={APP_ROUTES.AUTOMATIONS} element={<Automations />} />
            <Route path={APP_ROUTES.LOOPS} element={<Loops />} />
            <Route path={APP_ROUTES.PERSONAS} element={<Personas />} />
            <Route path={APP_ROUTES.TEMPLATES} element={<Templates />} />
            <Route path="/templates/mine" element={<MyTemplates />} />
            <Route path="/templates/:slug" element={<TemplateDetail />} />
            <Route path={APP_ROUTES.RUNS} element={<Runs />} />
            <Route path={APP_ROUTES.SCHEDULES} element={<Schedules />} />
            <Route path={APP_ROUTES.LOGS} element={<Logs />} />
            <Route path={APP_ROUTES.TABLES} element={<Tables />} />
            <Route path={APP_ROUTES.FILES} element={<Files />} />
            <Route path={APP_ROUTES.KNOWLEDGE} element={<Knowledge />} />
            <Route path="/knowledge/:id" element={<KnowledgeDetail />} />
            <Route path="/knowledge/:id/documents/:docId" element={<KnowledgeDocumentView />} />
            <Route path={APP_ROUTES.SKILLS} element={<Skills />} />
            <Route path={APP_ROUTES.SKILL_NEW} element={<SkillEditor />} />
            <Route path="/skills/:id" element={<SkillEditor />} />
            <Route path={APP_ROUTES.VARIABLES} element={<Variables />} />
            <Route path={APP_ROUTES.CONNECTIONS} element={<Connections />} />
            <Route path={APP_ROUTES.WORKSPACE_SETTINGS} element={<WorkspaceSettings />} />
          </Route>
        </Route>

        {/* Public invite accept — needs auth check inside the page */}
        <Route path="/invites/:token" element={<InviteAccept />} />

        {/* Workflow editor — app sidebar via EditorLayout, full-bleed canvas + right panel */}
        <Route element={<ProtectedRoute />}>
          <Route element={<EditorLayout />}>
            <Route path="/workflows/:id" element={<WorkflowEditor />} />
            {/* Crews reuse the workflow editor but load/save/run via /crews */}
            <Route path="/crews/:id" element={<WorkflowEditor entity="crew" />} />
          </Route>
        </Route>

        {/* Showcase page - public but using AppLayout */}
        <Route element={<AppLayout />}>
          <Route path={APP_ROUTES.SHOWCASE} element={<Showcase />} />
        </Route>

        {/* Redirects */}
        <Route path="/" element={<Navigate to={APP_ROUTES.DASHBOARD} replace />} />
        <Route path="*" element={<Navigate to={APP_ROUTES.DASHBOARD} replace />} />
      </Routes>
    </BrowserRouter>
  )
}
