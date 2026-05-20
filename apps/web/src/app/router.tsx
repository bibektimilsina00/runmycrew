import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute, PublicRoute } from '@/app/route-guards'
import { MainLayout } from '@/layouts/MainLayout'
import Editor from '@/features/workflow-editor/Editor'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { SettingsLayout } from '@/features/settings/layouts/SettingsLayout'
import { GeneralSettings } from '@/features/settings/pages/GeneralSettings'
import { IntegrationsSettings } from '@/features/settings/pages/IntegrationsSettings'
import { BYOKSettings } from '@/features/settings/pages/BYOKSettings'
import { CopilotKeysSettings } from '@/features/settings/pages/CopilotKeysSettings'
import { SecretsSettings } from '@/features/settings/pages/SecretsSettings'
import { CustomToolsSettings, SkillsSettings, MCPToolsSettings } from '@/features/settings/pages/ToolSettings'
import { FuseKeysSettings } from '@/features/settings/pages/FuseKeysSettings'
import { MCPServersSettings } from '@/features/settings/pages/MCPServersSettings'
import { RecentlyDeletedSettings } from '@/features/settings/pages/RecentlyDeletedSettings'
import { KnowledgePage } from '@/features/knowledge/KnowledgePage'
import { WorkflowsPage } from '@/features/workflows/WorkflowsPage'
import { ExecutionsPage } from '@/features/executions/ExecutionsPage'
import { ExecutionDetailPage } from '@/features/executions/ExecutionDetailPage'
import LoginPage from '@/features/auth/login-page'
import SignupPage from '@/features/auth/signup-page'
import ResetPasswordPage from '@/features/auth/reset-password-page'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    ),
  },
  {
    path: '/signup',
    element: (
      <PublicRoute>
        <SignupPage />
      </PublicRoute>
    ),
  },
  {
    path: '/reset-password',
    element: (
      <PublicRoute>
        <ResetPasswordPage />
      </PublicRoute>
    ),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'workflows',
        element: <WorkflowsPage />,
      },
      {
        path: 'executions',
        element: <ExecutionsPage />,
      },
      {
        path: 'executions/:executionId',
        element: <ExecutionDetailPage />,
      },
      {
        path: 'kb',
        element: <KnowledgePage />,
      },
      {
        path: 'workflows/:id',
        element: <Editor />,
      },
      {
        path: 'settings',
        element: <SettingsLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="general" replace />,
          },
          {
            path: 'general',
            element: <GeneralSettings />,
          },
          {
            path: 'integrations',
            element: <IntegrationsSettings />,
          },
          {
            path: 'byok',
            element: <BYOKSettings />,
          },
          {
            path: 'copilot-keys',
            element: <CopilotKeysSettings />,
          },
          {
            path: 'secrets',
            element: <SecretsSettings />,
          },
          {
            path: 'custom-tools',
            element: <CustomToolsSettings />,
          },
          {
            path: 'skills',
            element: <SkillsSettings />,
          },
          {
            path: 'mcp-tools',
            element: <MCPToolsSettings />,
          },
          {
            path: 'keys',
            element: <FuseKeysSettings />,
          },
          {
            path: 'mcp-servers',
            element: <MCPServersSettings />,
          },
          {
            path: 'deleted',
            element: <RecentlyDeletedSettings />,
          },
        ],
      },
    ],
  },
])
