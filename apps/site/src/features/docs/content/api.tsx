import type { DocContent } from './index'

/**
 * API reference pages. Facts (paths, auth, fields) mirror the live FastAPI
 * routers under apps/api — base prefix /api/v1, JWT + fuse_live_ API keys,
 * optional X-Workspace-ID.
 */
export const API: Record<string, DocContent> = {
  'api/auth': {
    toc: [
      { id: 'base-url', label: 'Base URL' },
      { id: 'schemes', label: 'Auth schemes' },
      { id: 'login', label: 'Email + password' },
      { id: 'api-keys', label: 'API keys' },
      { id: 'workspace', label: 'Workspace header' },
      { id: 'errors', label: 'Errors' },
    ],
    body: (
      <>
        <h1>Authentication</h1>
        <p className="lead">
          Every RunMyCrew API request is authenticated and scoped to a
          workspace. Use a JWT for user sessions or a <code>fuse_live_</code>{' '}
          API key for programmatic access.
        </p>

        <h2 id="base-url">Base URL</h2>
        <p>
          All endpoints live under the <code>/api/v1</code> prefix. On the
          hosted product the base URL is{' '}
          <code>https://api.runmycrew.com/api/v1</code>; self-hosted it is
          whatever host your API service runs on. The OpenAPI schema is served
          at <code>/api/v1/openapi.json</code>, and a public health probe at{' '}
          <code>GET /health</code>.
        </p>

        <h2 id="schemes">Auth schemes</h2>
        <p>The API accepts three credential forms:</p>
        <ul>
          <li>
            <strong>JWT bearer</strong> — <code>Authorization: Bearer &lt;jwt&gt;</code>.
            Minted by <code>/auth/login</code>; the token subject is the user
            email.
          </li>
          <li>
            <strong>API key header</strong> — <code>x-api-key: fuse_live_…</code>.
          </li>
          <li>
            <strong>API key bearer</strong> —{' '}
            <code>Authorization: Bearer fuse_live_…</code>. Keys are matched by
            SHA-256 hash, never stored in plaintext.
          </li>
        </ul>

        <h2 id="login">Email + password</h2>
        <p>Register, then exchange credentials for a token.</p>
        <pre>
          <code>{`# Create an account
POST /api/v1/auth/register
{ "email": "ada@acme.com", "password": "your-password", "full_name": "Ada" }

# Log in → { access_token, token_type: "bearer" }
POST /api/v1/auth/login
{ "email": "ada@acme.com", "password": "your-password" }

# Use the token
GET /api/v1/auth/me
Authorization: Bearer <access_token>`}</code>
        </pre>
        <p>
          Password reset is a two-step flow:{' '}
          <code>POST /auth/forgot-password</code> emails a token,{' '}
          <code>POST /auth/reset-password</code> consumes it. Social sign-in
          (Google, GitHub, Microsoft) is a browser redirect at{' '}
          <code>/auth/&#123;provider&#125;/start</code> and only mints an
          internal JWT — there is no third-party OAuth token endpoint for the
          API.
        </p>

        <h2 id="api-keys">API keys</h2>
        <p>
          For servers and scripts, create a long-lived key instead of storing
          a password. Manage keys under <code>/api-keys</code> (JWT-auth):
        </p>
        <pre>
          <code>{`POST /api/v1/api-keys
{ "name": "CI pipeline" }

# → the plaintext token is returned ONCE:
{ "id": "...", "name": "CI pipeline", "key_preview": "fuse_live_…abcd", "token": "fuse_live_…" }`}</code>
        </pre>
        <p>
          Store <code>token</code> immediately — it is never shown again. List
          keys with <code>GET /api-keys</code> and revoke with{' '}
          <code>DELETE /api-keys/&#123;id&#125;</code>.
        </p>

        <h2 id="workspace">Workspace header</h2>
        <p>
          Data endpoints are workspace-scoped. Pass{' '}
          <code>X-Workspace-ID: &lt;uuid&gt;</code> to target a specific
          workspace. The header is optional — when omitted, the API resolves
          your default/personal workspace.
        </p>

        <h2 id="errors">Errors</h2>
        <p>
          The API uses standard status codes: <code>401</code> for a missing or
          invalid credential, <code>403</code> when your role lacks edit rights
          on the workspace, <code>404</code> for an unknown resource, and{' '}
          <code>422</code> for a schema validation error (with a field-level
          detail array).
        </p>
      </>
    ),
  },

  'api/workflows': {
    toc: [
      { id: 'model', label: 'The workflow object' },
      { id: 'list', label: 'List & read' },
      { id: 'create', label: 'Create' },
      { id: 'update', label: 'Update & version' },
      { id: 'run', label: 'Run' },
      { id: 'lifecycle', label: 'Toggle, duplicate, delete' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          API
        </p>
        <h1>Workflows</h1>
        <p className="lead">
          Create, read, update, run and version workflows. All endpoints sit
          under <code>/api/v1/workflows</code> and require auth plus a
          workspace.
        </p>

        <h2 id="model">The workflow object</h2>
        <p>
          A workflow is a named graph. The <code>graph</code> holds{' '}
          <code>&#123; nodes, edges &#125;</code>; <code>kind</code> is{' '}
          <code>automation</code> (default) or <code>crew</code>.
        </p>
        <pre>
          <code>{`{
  "id": "uuid",
  "name": "Urgent issues → Slack",
  "graph": { "nodes": [...], "edges": [...] },
  "kind": "automation",
  "is_active": true,
  "workspace_id": "uuid",
  "created_at": "...",
  "updated_at": "..."
}`}</code>
        </pre>

        <h2 id="list">List &amp; read</h2>
        <pre>
          <code>{`GET  /api/v1/workflows/                 # list (optional ?kind=)
GET  /api/v1/workflows/with-stats       # + status, run count, last/next run
GET  /api/v1/workflows/{workflow_id}    # one workflow`}</code>
        </pre>

        <h2 id="create">Create</h2>
        <p>
          <code>name</code> is required; <code>graph</code> defaults to empty.
          Returns <code>201</code> with the created workflow.
        </p>
        <pre>
          <code>{`POST /api/v1/workflows/
{
  "name": "Daily standup digest",
  "description": "Summarise GitHub activity to Slack",
  "graph": { "nodes": [...], "edges": [...] },
  "kind": "automation"
}`}</code>
        </pre>

        <h2 id="update">Update &amp; version</h2>
        <p>
          <code>PUT /workflows/&#123;id&#125;</code> replaces the workflow. When
          the graph changes, RunMyCrew auto-snapshots the previous version so
          you can roll back:
        </p>
        <pre>
          <code>{`GET  /api/v1/workflows/{id}/versions
POST /api/v1/workflows/{id}/versions/{version_id}/restore`}</code>
        </pre>

        <h2 id="run">Run</h2>
        <p>
          Trigger a manual run. Optionally override the graph or pass input
          data. Returns the new execution id — poll it via the{' '}
          <a href="/docs/api/runs">Runs API</a>.
        </p>
        <pre>
          <code>{`POST /api/v1/workflows/{workflow_id}/run
{ "input_data": { "issue": 4821 } }

# → { "execution_id": "uuid" }`}</code>
        </pre>

        <h2 id="lifecycle">Toggle, duplicate, delete</h2>
        <pre>
          <code>{`PATCH  /api/v1/workflows/{id}/toggle      # flip is_active
POST   /api/v1/workflows/{id}/duplicate   # deep copy
DELETE /api/v1/workflows/{id}             # 204
PATCH  /api/v1/workflows/batch            # reorder / move between folders`}</code>
        </pre>
      </>
    ),
  },

  'api/runs': {
    toc: [
      { id: 'model', label: 'The execution object' },
      { id: 'list', label: 'List runs' },
      { id: 'detail', label: 'Run detail' },
      { id: 'control', label: 'Rerun, cancel, resume' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          API
        </p>
        <h1>Runs</h1>
        <p className="lead">
          Every workflow run is an <em>execution</em> with a status, the input
          that started it, the output it produced, and a step-by-step log.
          Endpoints live under <code>/api/v1/executions</code>.
        </p>

        <h2 id="model">The execution object</h2>
        <pre>
          <code>{`{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "success | running | failed | cancelled",
  "trigger_type": "manual | schedule | webhook | ...",
  "input_data": { ... },
  "output_data": { ... },
  "started_at": "...",
  "finished_at": "...",
  "logs": [ { node, status, output, duration_ms }, ... ]
}`}</code>
        </pre>

        <h2 id="list">List runs</h2>
        <pre>
          <code>{`# Runs for one workflow
GET /api/v1/executions/?workflow_id={uuid}

# Runs across the workspace (paginated + filterable)
GET /api/v1/executions/all?limit=50&offset=0&status=failed
# → { executions, total, limit, offset }`}</code>
        </pre>

        <h2 id="detail">Run detail</h2>
        <p>
          Fetch one execution including its full <code>logs</code> array — the
          same data the <a href="/docs/replay">run inspector</a> renders.
        </p>
        <pre>
          <code>{`GET /api/v1/executions/{execution_id}`}</code>
        </pre>

        <h2 id="control">Rerun, cancel, resume</h2>
        <pre>
          <code>{`POST /api/v1/executions/{id}/rerun    # replay with the original input
POST /api/v1/executions/{id}/cancel   # stop a running execution
POST /api/v1/executions/{id}/resume   # continue a paused run
{ "token": "<resume-token>", "input": { ... } }`}</code>
        </pre>
        <p>
          <strong>Resume</strong> is used by human-in-the-loop steps: a paused
          run emits a one-time <code>token</code>; posting it back (no other
          auth required — the token is the secret) continues the run with the
          supplied input.
        </p>
      </>
    ),
  },
}
