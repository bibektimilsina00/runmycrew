import Link from 'next/link'
import type { DocContent } from './index'

/**
 * Connections group — OAuth integrations, inbound webhooks, custom apps,
 * API keys. Webhook paths + API-key facts mirror the triggers/webhooks
 * routers; provider list mirrors the OAuth config.
 */
export const CONNECTIONS: Record<string, DocContent> = {
  oauth: {
    toc: [
      { id: 'what', label: 'What is a connection?' },
      { id: 'connect', label: 'Connecting an app' },
      { id: 'providers', label: 'Supported providers' },
      { id: 'security', label: 'Security & tokens' },
      { id: 'reconnect', label: 'Expiry & reconnect' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Connections
        </p>
        <h1>OAuth integrations</h1>
        <p className="lead">
          A <strong>connection</strong> is an authorized link to an external
          app. Authorize once; every workflow in the workspace can then read
          from and write to that app — no API keys to copy around.
        </p>

        <h2 id="what">What is a connection?</h2>
        <p>
          When you add an integration, RunMyCrew runs the provider’s OAuth flow
          and stores the resulting tokens (encrypted) against your workspace.
          Trigger and action nodes reference the connection by id, so
          credentials never live inside a workflow graph.
        </p>

        <h2 id="connect">Connecting an app</h2>
        <ol>
          <li>Open <strong>Connections</strong> in the sidebar, or click <em>Connect app</em> on the dashboard.</li>
          <li>Pick a provider and approve the scopes in the provider’s consent screen.</li>
          <li>You’re redirected back — the connection shows <strong>OK</strong> and is ready to use in any node.</li>
        </ol>

        <h2 id="providers">Supported providers</h2>
        <p>Connectable over OAuth today:</p>
        <ul>
          <li><strong>Google</strong> — Gmail, Calendar, Sheets, Drive.</li>
          <li><strong>Slack</strong> — messages, channels, users.</li>
          <li><strong>GitHub</strong> — issues, PRs, Actions.</li>
          <li><strong>Notion</strong> — databases and pages.</li>
          <li><strong>Linear</strong> — issues and projects.</li>
          <li><strong>Microsoft</strong> — 365 / Outlook.</li>
          <li><strong>Discord</strong> — channels and bots.</li>
          <li><strong>Meta</strong> — Ads and lead forms.</li>
          <li>Plus Asana, HubSpot, Calendly, Zoom, Box, Dropbox, DocuSign and LinkedIn.</li>
        </ul>
        <p>
          Self-hosting? Each provider needs its own client id/secret — see the{' '}
          <Link href="/docs/env">Environment reference</Link>.
        </p>

        <h2 id="security">Security &amp; tokens</h2>
        <p>
          Tokens are encrypted at rest with your workspace’s Fernet{' '}
          <code>ENCRYPTION_KEY</code> and decrypted only at execution time. A
          connection is scoped to the workspace it was created in; it is never
          shared across workspaces.
        </p>

        <h2 id="reconnect">Expiry &amp; reconnect</h2>
        <p>
          RunMyCrew refreshes access tokens automatically using the stored
          refresh token. If a provider revokes access or a refresh fails, the
          connection is marked <strong>needs attention</strong> and any workflow
          that depends on it surfaces the error — reconnect in one click to
          restore it.
        </p>
      </>
    ),
  },

  webhooks: {
    toc: [
      { id: 'what', label: 'Inbound webhooks' },
      { id: 'generic', label: 'Generic webhook' },
      { id: 'signed', label: 'Signed webhooks' },
      { id: 'test', label: 'Listen for a test event' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Connections
        </p>
        <h1>Webhooks</h1>
        <p className="lead">
          Start a workflow the instant something happens in another system.
          Add a <strong>Webhook</strong> trigger and RunMyCrew gives you a URL
          to paste into the source app.
        </p>

        <h2 id="what">Inbound webhooks</h2>
        <p>
          Every webhook trigger has a stable URL under{' '}
          <code>/api/v1/webhooks/…</code>. The full request — body, headers,
          query — is captured and becomes the trigger’s output payload, ready
          to reference in downstream nodes.
        </p>

        <h2 id="generic">Generic webhook</h2>
        <p>Any source can POST to a user-defined path:</p>
        <pre>
          <code>{`POST /api/v1/webhooks/{your-path}

# Check the URL and whether a workflow is listening:
GET  /api/v1/webhooks/{your-path}/info`}</code>
        </pre>

        <h2 id="signed">Signed webhooks</h2>
        <p>
          For untrusted senders, require an HMAC signature. Mint a secret,
          configure it on the sender, and RunMyCrew verifies every request:
        </p>
        <pre>
          <code>{`POST /api/v1/webhooks/utils/generate-secret          # mint a signing secret

# GitHub-scoped receiver (verifies the X-Hub-Signature):
POST /api/v1/webhooks/github/{workflow_id}

# Provider-manifest receiver (GitLab, Twilio, …):
POST /api/v1/webhooks/{provider}/{workflow_id}/{node_id}`}</code>
        </pre>
        <p>Requests that fail signature verification are rejected before the workflow runs.</p>

        <h2 id="test">Listen for a test event</h2>
        <p>
          While editing, click <em>Listen</em> on a webhook trigger to capture
          the next real event as a fixture — then build the rest of the
          workflow against a concrete payload instead of guessing its shape.
        </p>
      </>
    ),
  },

  'custom-apps': {
    toc: [
      { id: 'when', label: 'When to use' },
      { id: 'http', label: 'The HTTP node' },
      { id: 'creds', label: 'Stored credentials' },
      { id: 'publish', label: 'Publishing an app' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Connections
        </p>
        <h1>Custom apps</h1>
        <p className="lead">
          Not every service has a first-class integration — and that’s fine.
          Any REST or GraphQL API is reachable with the HTTP node plus a stored
          credential.
        </p>

        <h2 id="when">When to use</h2>
        <p>
          Use a custom integration when the app you need isn’t in the{' '}
          <Link href="/docs/oauth">provider list</Link>, or when you need an
          endpoint the managed integration doesn’t expose yet.
        </p>

        <h2 id="http">The HTTP node</h2>
        <p>
          The HTTP request action calls any URL with a method, headers, query
          and JSON body, and returns the parsed response for downstream nodes.
          Reference earlier node outputs anywhere in the request:
        </p>
        <pre>
          <code>{`POST https://api.example.com/v1/tickets
Authorization: Bearer {{secrets.EXAMPLE_TOKEN}}
{ "title": "{{trigger.issue.title}}", "priority": "high" }`}</code>
        </pre>

        <h2 id="creds">Stored credentials</h2>
        <p>
          Don’t paste secrets into the graph. Store them as workspace{' '}
          <strong>secrets</strong> (encrypted at rest) and reference them as{' '}
          <code>&#123;&#123;secrets.NAME&#125;&#125;</code> — the value is
          injected only at run time and never rendered in logs.
        </p>

        <h2 id="publish">Publishing an app</h2>
        <p>
          A finished workflow can be published as a shareable public app with
          its own URL, so teammates or customers can run it with a form instead
          of opening the editor. Public apps run under per-workspace spend and
          concurrency caps you control.
        </p>
      </>
    ),
  },

  'api-keys': {
    toc: [
      { id: 'what', label: 'What API keys are for' },
      { id: 'create', label: 'Create a key' },
      { id: 'use', label: 'Using a key' },
      { id: 'rotate', label: 'Rotate & revoke' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Connections
        </p>
        <h1>API keys</h1>
        <p className="lead">
          API keys let servers, CI jobs and scripts call the RunMyCrew API
          without a user login. Keys are prefixed <code>fuse_live_</code> and
          scoped to your account.
        </p>

        <h2 id="what">What API keys are for</h2>
        <p>
          Use a key to trigger workflows, read runs, or manage resources from
          your own code. For calling <em>other</em> apps from inside a workflow,
          use <Link href="/docs/oauth">connections</Link> instead.
        </p>

        <h2 id="create">Create a key</h2>
        <pre>
          <code>{`POST /api/v1/api-keys
{ "name": "CI pipeline" }

# → token shown ONCE:
{ "key_preview": "fuse_live_…abcd", "token": "fuse_live_…" }`}</code>
        </pre>

        <h2 id="use">Using a key</h2>
        <p>Send it as a header — either works:</p>
        <pre>
          <code>{`x-api-key: fuse_live_…
# or
Authorization: Bearer fuse_live_…`}</code>
        </pre>
        <p>
          See the full <Link href="/docs/api/auth">Authentication</Link>{' '}
          reference for workspace scoping.
        </p>

        <h2 id="rotate">Rotate &amp; revoke</h2>
        <p>
          Keys are stored as SHA-256 hashes — the plaintext can’t be recovered,
          so treat the one-time <code>token</code> like a password. List keys
          with <code>GET /api-keys</code> and revoke instantly with{' '}
          <code>DELETE /api-keys/&#123;id&#125;</code>. Rotate by creating a new
          key, switching your clients over, then deleting the old one.
        </p>
      </>
    ),
  },
}
