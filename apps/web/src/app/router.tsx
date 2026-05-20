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
import { TeamSettingsPage } from '@/features/workspaces/TeamSettingsPage'
import { InviteAcceptPage } from '@/features/workspaces/InviteAcceptPage'
import { RouteError } from '@/components/ErrorBoundary'

export const router = createBrowserRouter([
  {
    path: '/login',
    errorElement: <RouteError />,
    element: (
      <PublicRoute>
        <LoginPage />
      </PublicRoute>
    ),
  },
  {
    path: '/signup',
    errorElement: <RouteError />,
    element: (
      <PublicRoute>
        <SignupPage />
      </PublicRoute>
    ),
  },
  {
    path: '/reset-password',
    errorElement: <RouteError />,
    element: (
      <PublicRoute>
        <ResetPasswordPage />
      </PublicRoute>
    ),
  },
  {
    path: '/',
    errorElement: <RouteError />,
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
        path: 'invites/:token',
        element: <InviteAcceptPage />,
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
        errorElement: <RouteError />,
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
            path: 'team',
            element: <TeamSettingsPage />,
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
