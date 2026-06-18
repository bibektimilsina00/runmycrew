import { useState } from 'react'
import {
  Zap, Plus, MoreHorizontal, Trash2, ChevronRight,
  Settings, Play, Copy, Star, FileText,
  Workflow, Filter, Webhook, Clock, Hand, Search, Terminal,
} from 'lucide-react'
import {
  Button, Input, Badge, Divider, Spinner, Avatar, StatusDot,
  Checkbox, Toggle, Textarea, Select, Chip, FormField,
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem, DropdownSeparator,
  Tabs, TabsList, TabsTrigger, TabsContent,
  Tooltip, Card, Modal, Empty, ThemeToggle, Skeleton, SkeletonText, SkeletonCard,
  useToast,
  type SelectOption,
} from '@/shared/components'
import { AuthForm } from '@/features/auth/components/AuthForm'

function CardHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col gap-1 pb-3.5 border-b border-border-faint mb-4">
      <h3 className="text-sm font-semibold text-text tracking-tight">{title}</h3>
      {description && <p className="text-xs text-text-faint font-normal">{description}</p>}
    </div>
  )
}

const triggerOptions: SelectOption[] = [
  { value: 'webhook',  label: 'Webhook',  icon: <Webhook size={13} />, description: 'Triggered by HTTP request' },
  { value: 'schedule', label: 'Schedule', icon: <Clock size={13} />,   description: 'Runs on a cron schedule' },
  { value: 'manual',   label: 'Manual',   icon: <Hand size={13} />,    description: 'Triggered manually' },
]

export function Showcase() {
  const { toast } = useToast()
  const [checked1, setChecked1]   = useState(false)
  const [checked2, setChecked2]   = useState(true)
  const [toggled1, setToggled1]   = useState(false)
  const [toggled2, setToggled2]   = useState(true)
  const [chip, setChip]           = useState('all')
  const [trigger, setTrigger]     = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [btnLoading, setBtnLoading]   = useState(false)
  const [authTab, setAuthTab]         = useState<'login' | 'register'>('login')

  function simulateLoad() {
    setBtnLoading(true)
    setTimeout(() => {
      setBtnLoading(false)
      toast('Workflow published successfully', { variant: 'ok', description: 'Version v1.0.2 is now active.' })
    }, 1800)
  }

  return (
    <div className="fixed inset-0 bg-bg text-text overflow-y-auto z-10">
      {/* Background Dot Grid */}
      <div className="dot-grid" />

      {/* Main Container */}
      <div className="relative max-w-6xl mx-auto px-6 py-8 md:px-10 md:py-12 flex flex-col gap-8 z-10">

        {/* Top Navbar Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-bg2/50 backdrop-blur-md border border-border-faint rounded-[10px] p-4 shadow-panel">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-[8px] bg-text text-bg flex items-center justify-center shadow-sm">
              <Zap size={15} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold tracking-tight text-text">Fuse Design System</span>
                <Badge variant="accent" className="text-[10px] px-1.5 py-0.2">v2.0</Badge>
              </div>
              <p className="text-xs text-text-faint">Premium operations dashboard component playground</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Sync State Mockup */}
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-text-mute bg-bg border border-border-faint px-3 py-1.5 rounded-[8px]">
              <StatusDot status="ok" size="sm" />
              <span>System Synced</span>
            </div>

            {/* Search Mockup */}
            <div className="relative hidden lg:flex items-center w-48 h-8 bg-bg border border-border-faint rounded-[8px] px-2.5 text-text-faint text-xs hover:border-border-soft transition-colors cursor-text">
              <Search size={12} className="mr-1.5" />
              <span>Search components...</span>
              <span className="kbd ml-auto">⌘K</span>
            </div>

            <Divider vertical className="h-6 hidden sm:block" />

            <ThemeToggle />
          </div>
        </header>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

          {/* LEFT/MAIN COLUMN (SPAN 2) */}
          <div className="lg:col-span-2 flex flex-col gap-6">

            {/* Card 1: Interactive Forms & Inputs */}
            <Card padding="lg" className="flex flex-col gap-4">
              <CardHeader
                title="Form Controls & Inputs"
                description="Flexible schema-driven field elements with integrated validation states."
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField label="Workflow name" required hint="Give your workflow a unique name">
                  <Input placeholder="Stripe Refund Approvals" />
                </FormField>

                <FormField label="Trigger Source" hint="Select the initial ingestion point">
                  <Select
                    options={triggerOptions}
                    value={trigger}
                    onChange={setTrigger}
                    placeholder="Select starting point…"
                  />
                </FormField>

                <FormField label="Receiver Email Address" error="Please enter a valid developer email">
                  <Input error placeholder="developer@fuse.dev" />
                </FormField>

                <FormField label="Private API Key" success="Key verified by SecurityService">
                  <Input success placeholder="sk_live_51Ny..." />
                </FormField>
              </div>

              <FormField label="Execution Payload Schema" hint="Define variables to forward to the Celery executor.">
                <Textarea placeholder='{\n  "refund_id": "{{trigger.payload.id}}",\n  "reason": "Customer request"\n}' rows={4} className="font-mono text-xs" />
              </FormField>

              <div className="flex flex-col gap-3.5 pt-2">
                <p className="mono-label text-text-faint">Interactive Checkboxes</p>
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <Checkbox
                    checked={checked1}
                    onChange={e => setChecked1(e.target.checked)}
                    label="Enable email notifications"
                  />
                  <Checkbox
                    checked={checked2}
                    onChange={e => setChecked2(e.target.checked)}
                    label="Auto-retry tasks on failure"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-3.5 pt-2">
                <p className="mono-label text-text-faint">Toggle Switches</p>
                <div className="flex flex-col sm:flex-row gap-6">
                  <div className="flex items-center gap-2.5">
                    <Toggle checked={toggled1} onChange={e => setToggled1(e.target.checked)} />
                    <span className="text-xs text-text-mute font-medium">
                      Debug Logs: <strong className="text-text">{toggled1 ? 'ON' : 'OFF'}</strong>
                    </span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Toggle checked={toggled2} onChange={e => setToggled2(e.target.checked)} />
                    <span className="text-xs text-text-mute font-medium">
                      Production Mode: <strong className="text-text">{toggled2 ? 'ON' : 'OFF'}</strong>
                    </span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Card: Authentication Module Showcase */}
            <Card padding="lg" className="flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3">
                <CardHeader
                  title="Authentication Module Showcase"
                  description="Stateful Login and Registration forms utilizing our custom-styled shared UI elements."
                />
                <div className="flex gap-2 self-start sm:self-center bg-bg p-1 border border-border-faint rounded-[8px]">
                  <Button
                    variant={authTab === 'login' ? 'primary' : 'secondary'}
                    size="sm"
                    className="h-8 py-1 text-xs"
                    onClick={() => setAuthTab('login')}
                  >
                    Login Form
                  </Button>
                  <Button
                    variant={authTab === 'register' ? 'primary' : 'secondary'}
                    size="sm"
                    className="h-8 py-1 text-xs"
                    onClick={() => setAuthTab('register')}
                  >
                    Register Form
                  </Button>
                </div>
              </div>

              <div className="flex justify-center items-center py-8 px-4 bg-bg border border-border-faint rounded-[12px] min-h-[460px] relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-tr from-bg/10 via-surface/5 to-text/2 opacity-20 pointer-events-none" />
                <div className="w-full max-w-[400px] z-10">
                  <AuthForm mode={authTab === 'login' ? 'login' : 'signup'} />
                </div>
              </div>
            </Card>


            {/* Card 2: Interactive Tabs & Panel State */}
            <Card padding="lg">
              <CardHeader
                title="Navigation & Server State Tabs"
                description="Zustand-powered state transitions with fade-in animations and status sub-panels."
              />

              <Tabs defaultValue="overview">
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="runs">
                    <span className="flex items-center gap-1.5">
                      Runs <Badge variant="default" className="text-[10px] px-1 py-0 h-4">12</Badge>
                    </span>
                  </TabsTrigger>
                  <TabsTrigger value="logs">Logs</TabsTrigger>
                  <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="pt-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-4 rounded-[8px] bg-bg border border-border-faint flex flex-col gap-1">
                      <span className="text-xs text-text-mute">Last Executed</span>
                      <span className="text-sm font-semibold text-text">2 minutes ago</span>
                    </div>
                    <div className="p-4 rounded-[8px] bg-bg border border-border-faint flex flex-col gap-1">
                      <span className="text-xs text-text-mute">Average Duration</span>
                      <span className="text-sm font-semibold text-text">410ms</span>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="runs" className="pt-4">
                  <div className="border border-border-faint rounded-[8px] overflow-hidden bg-bg">
                    {[
                      { id: "run-e2a1", time: "10:01:03", state: "ok" as const, desc: "Completed successfully" },
                      { id: "run-9c2b", time: "09:44:12", state: "err" as const, desc: "Task failed at StripeAPI Node" },
                      { id: "run-4a92", time: "08:15:30", state: "ok" as const, desc: "Completed successfully" },
                    ].map((r, i) => (
                      <div key={r.id} className={`flex items-center justify-between p-3 text-xs ${i !== 0 ? 'border-t border-border-faint' : ''}`}>
                        <div className="flex items-center gap-2">
                          <StatusDot status={r.state} size="sm" />
                          <span className="font-mono text-text-mute">{r.id}</span>
                          <span className="text-text-faint">{r.desc}</span>
                        </div>
                        <span className="text-text-faint font-mono">{r.time}</span>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="logs" className="pt-4">
                  <div className="p-4 rounded-[8px] bg-bg border border-border-faint font-mono text-xs text-text-mute leading-relaxed">
                    <div className="flex items-center gap-1 text-text-faint">
                      <Terminal size={12} />
                      <span>Console output:</span>
                    </div>
                    <p className="mt-2 text-text-mute">
                      <span className="text-text-dim">[10:01:03]</span> Triggering workflow 'Stripe Approvals'<br />
                      <span className="text-text-dim">[10:01:04]</span> Fetching account details from Stripe API...<br />
                      <span className="text-ok">[10:01:04]</span> Fetch returned 200 OK (240ms)<br />
                      <span className="text-text-dim">[10:01:05]</span> Dispatched email notification to admin<br />
                      <span className="text-text-dim">[10:01:05]</span> Execution complete. Status: SUCCESS
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="settings" className="pt-4">
                  <div className="p-4 rounded-[8px] bg-bg border border-border-faint flex flex-col gap-3">
                    <FormField label="Concurrency Limit">
                      <Select
                        options={[
                          { value: '1', label: '1 concurrent execution' },
                          { value: '5', label: '5 concurrent executions' },
                          { value: '10', label: '10 concurrent executions' },
                        ]}
                        value="5"
                        onChange={() => {}}
                      />
                    </FormField>
                  </div>
                </TabsContent>
              </Tabs>
            </Card>

            {/* Card 3: Dashboard Layout Templates */}
            <Card padding="lg" className="flex flex-col gap-4">
              <CardHeader
                title="Dashboard Card Templates"
                description="Premium composite card designs implementing standard headers, avatars, status tags, and details."
              />

              <div className="flex flex-col gap-3">
                {/* slack digest card */}
                <Card padding="md" className="flex flex-col sm:flex-row sm:items-center gap-4 bg-bg/60">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <Avatar name="Slack Digest" size="md" className="bg-surface border border-border-faint text-text" />
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-text truncate">Daily Slack Summary</span>
                        <Badge variant="ok" dot>Active</Badge>
                      </div>
                      <span className="text-xs text-text-faint truncate">Dispatches to #marketing-leads · Mon-Fri at 9:00 AM</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                    <div className="flex items-center gap-1">
                      <StatusDot status="ok" size="sm" />
                      <span className="text-xs text-text-mute font-mono">Last run: 9:00 AM</span>
                    </div>
                    <Divider vertical className="h-4" />
                    <Dropdown>
                      <DropdownTrigger>
                        <Button variant="icon-sm"><MoreHorizontal size={13} /></Button>
                      </DropdownTrigger>
                      <DropdownContent>
                        <DropdownItem leftIcon={<Play size={13} />}>Trigger now</DropdownItem>
                        <DropdownItem leftIcon={<Settings size={13} />}>Edit configuration</DropdownItem>
                        <DropdownSeparator />
                        <DropdownItem leftIcon={<Trash2 size={13} />} variant="danger">Disable</DropdownItem>
                      </DropdownContent>
                    </Dropdown>
                  </div>
                </Card>

                {/* empty templates */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-bg/40 border border-border-faint rounded-[12px] p-6 text-center flex flex-col items-center justify-center">
                    <Empty
                      icon={<Workflow size={16} />}
                      title="No Connected Tables"
                      description="Create data tables to query."
                      action={<Button variant="secondary" size="sm" leftIcon={<Plus />}>Add Table</Button>}
                    />
                  </div>

                  <div className="bg-bg/40 border border-border-faint rounded-[12px] p-6 text-center flex flex-col items-center justify-center">
                    <Empty
                      icon={<Filter size={16} />}
                      title="No Executed Runs"
                      description="Triggers will appear here."
                    />
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* RIGHT COLUMN (SPAN 1) */}
          <div className="lg:col-span-1 flex flex-col gap-6">

            {/* Card 4: Buttons Playground */}
            <Card padding="lg" className="flex flex-col gap-4">
              <CardHeader
                title="Buttons Playground"
                description="Theme-aware button variants and sizing options matching the mockup style."
              />

              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <span className="mono-label text-text-faint">Variants</span>
                  <div className="flex flex-col gap-2">
                    <Button variant="primary" leftIcon={<Play size={13} className="fill-current" />} loading={btnLoading} onClick={simulateLoad}>
                      Publish changes
                    </Button>
                    <Button variant="secondary" leftIcon={<Plus size={13} />}>
                      Create new node
                    </Button>
                    <Button variant="outline" leftIcon={<Copy size={13} />}>
                      Clone workflow
                    </Button>
                    <Button variant="ghost" leftIcon={<Settings size={13} />}>
                      Workspace settings
                    </Button>
                    <Button variant="danger" leftIcon={<Trash2 size={13} />}>
                      Delete workflow
                    </Button>
                  </div>
                </div>

                <Divider />

                <div className="flex flex-col gap-2">
                  <span className="mono-label text-text-faint">Sizes & States</span>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button variant="secondary" size="sm" leftIcon={<Plus size={12} />}>Add</Button>
                    <Button variant="primary" size="sm">Save</Button>
                    <Button variant="outline" size="sm">Export</Button>
                    <Button disabled size="sm">Disabled</Button>
                  </div>
                </div>

                <Divider />

                <div className="flex flex-col gap-2">
                  <span className="mono-label text-text-faint">Icon Buttons</span>
                  <div className="flex items-center gap-2">
                    <Button variant="icon"><MoreHorizontal size={15} /></Button>
                    <Button variant="icon-sm"><ChevronRight size={13} /></Button>
                    <Button variant="icon-sm" className="rounded-full"><Settings size={13} /></Button>
                  </div>
                </div>
              </div>
            </Card>

            {/* Card 5: Indicators & Badges */}
            <Card padding="lg" className="flex flex-col gap-4">
              <CardHeader
                title="Indicators & Badges"
                description="Status elements indicating run loop states, task logs, and categorization."
              />

              <div className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <span className="mono-label text-text-faint">Badges</span>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="ok" dot>Active</Badge>
                    <Badge variant="warn" dot>Degraded</Badge>
                    <Badge variant="err" dot>Failed</Badge>
                    <Badge variant="accent">Running</Badge>
                    <Badge variant="draft" dot>Draft</Badge>
                    <Badge variant="default">Paused</Badge>
                  </div>
                </div>

                <Divider />

                <div className="flex flex-col gap-2">
                  <span className="mono-label text-text-faint">StatusDot Legend</span>
                  <div className="grid grid-cols-2 gap-3 bg-bg/50 border border-border-faint rounded-[8px] p-3">
                    {(['ok', 'warn', 'err', 'run', 'draft'] as const).map(s => (
                      <div key={s} className="flex items-center gap-2">
                        <StatusDot status={s} size="md" />
                        <span className="text-xs text-text-mute capitalize font-medium">{s === 'run' ? 'Running' : s}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <Divider />

                <div className="flex flex-col gap-2">
                  <span className="mono-label text-text-faint">Segmented Chips</span>
                  <div className="flex flex-wrap gap-1.5">
                    {['All', 'Active', 'Draft', 'Failed'].map(v => (
                      <Chip
                        key={v}
                        active={chip === v.toLowerCase()}
                        onClick={() => setChip(v.toLowerCase())}
                      >
                        {v}
                      </Chip>
                    ))}
                  </div>
                </div>

                <Divider />

                <div className="flex flex-col gap-2">
                  <span className="mono-label text-text-faint">Avatars & Spinners</span>
                  <div className="flex items-center gap-3">
                    <Avatar name="Alice Chen" size="sm" />
                    <Avatar name="Bob Tanner" size="md" />
                    <Avatar name="Fuse System" size="lg" />
                    <Divider vertical className="h-5" />
                    <Spinner size="xs" />
                    <Spinner size="sm" />
                    <Spinner size="md" />
                  </div>
                </div>
              </div>
            </Card>

            {/* Card 6: Interactive Modals, Dropdowns & Toasts */}
            <Card padding="lg" className="flex flex-col gap-4">
              <CardHeader
                title="Overlays & Triggers"
                description="Triggers for dropdown selections, toast notifications, modals, and tooltips."
              />

              <div className="flex flex-col gap-3">
                <span className="mono-label text-text-faint">Dropdown Options</span>
                <div className="flex flex-wrap gap-2.5">
                  <Dropdown>
                    <DropdownTrigger>
                      <Button variant="secondary" rightIcon={<ChevronRight size={12} className="rotate-90" />}>
                        Configure actions
                      </Button>
                    </DropdownTrigger>
                    <DropdownContent>
                      <DropdownItem leftIcon={<Copy size={13} />} shortcut="⌘D">Duplicate Node</DropdownItem>
                      <DropdownItem leftIcon={<Star size={13} />}>Pin to Library</DropdownItem>
                      <DropdownItem leftIcon={<Settings size={13} />}>Advanced Settings</DropdownItem>
                      <DropdownSeparator />
                      <DropdownItem leftIcon={<Trash2 size={13} />} variant="danger">Remove Node</DropdownItem>
                    </DropdownContent>
                  </Dropdown>
                </div>

                <Divider />

                <span className="mono-label text-text-faint">Toast Notifications</span>
                <div className="grid grid-cols-2 gap-2">
                  <Button variant="secondary" size="sm" onClick={() => toast('Fetching variables...')}>Default</Button>
                  <Button variant="outline" size="sm" onClick={() => toast('Pipeline ready', { variant: 'ok', description: 'Agent prompt is verified.' })}>Success</Button>
                  <Button variant="outline" size="sm" onClick={() => toast('Rate limit approaching', { variant: 'warn', description: 'Usage is at 88%.' })}>Warning</Button>
                  <Button variant="danger" size="sm" onClick={() => toast('Compile failed', { variant: 'err', description: 'Invalid syntax at line 4.' })}>Error</Button>
                </div>

                <Divider />

                <span className="mono-label text-text-faint">Modal Dialogs</span>
                <div className="flex items-center gap-2">
                  <Button variant="secondary" size="sm" leftIcon={<FileText size={12} />} onClick={() => setModalOpen(true)}>Edit Modal</Button>
                  <Button variant="danger" size="sm" leftIcon={<Trash2 size={12} />} onClick={() => setConfirmOpen(true)}>Delete Modal</Button>
                </div>

                <Divider />

                <span className="mono-label text-text-faint">Tooltips (Hover)</span>
                <div className="flex items-center gap-2">
                  <Tooltip content="Instantly trigger a manual run" side="top">
                    <Button variant="secondary" size="sm">Hover top</Button>
                  </Tooltip>
                  <Tooltip content="Delete this connection" side="bottom">
                    <Button variant="danger" size="sm">Hover bottom</Button>
                  </Tooltip>
                </div>
              </div>
            </Card>

            {/* Card 7: Loaders & Skeletons */}
            <Card padding="lg" className="flex flex-col gap-4">
              <CardHeader
                title="Loading Skeletons"
                description="Skeleton components used for initial load states."
              />

              <div className="flex flex-col gap-4">
                <SkeletonCard />
                <div className="flex flex-col gap-2">
                  <Skeleton className="h-4 w-2/3" />
                  <SkeletonText lines={2} />
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Footer info */}
        <footer className="text-center py-4 border-t border-border-faint mt-4">
          <p className="text-xs text-text-dim">Fuse Design System · Built with Tailwind CSS and Vanilla CSS variables</p>
        </footer>
      </div>

      {/* Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Edit Workflow Configuration"
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button variant="primary" size="sm" onClick={() => setModalOpen(false)}>Save changes</Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <FormField label="Workflow Name"><Input defaultValue="Daily Slack Summary" /></FormField>
          <FormField label="Description" hint="Shown in the workflow list."><Textarea defaultValue="Dispatches to #marketing-leads · Mon-Fri at 9:00 AM" rows={3} /></FormField>
          <FormField label="Ingestion Trigger"><Select options={triggerOptions} value={trigger} onChange={setTrigger} placeholder="Select starting point…" /></FormField>
          <div className="flex items-center justify-between py-1 border-t border-border-faint mt-2 pt-3">
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-semibold text-text">Enable notifications</span>
              <span className="text-[10px] text-text-faint">Sends an email on failed runs</span>
            </div>
            <Toggle checked={toggled2} onChange={e => setToggled2(e.target.checked)} />
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title="Confirm Deletion"
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setConfirmOpen(false)}>Cancel</Button>
            <Button variant="danger" size="sm" onClick={() => setConfirmOpen(false)}>Yes, delete workflow</Button>
          </>
        }
      >
        <p className="text-sm font-normal text-text-mute leading-relaxed">
          Are you sure you want to permanently delete <strong className="text-text font-semibold">Daily Slack Summary</strong> and all its execution history? This operation cannot be undone.
        </p>
      </Modal>
    </div>
  )
}
