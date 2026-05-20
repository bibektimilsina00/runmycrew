import React, { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, Search, Bot, FileText, Zap, Globe, Mail, GitBranch, Database, MessageSquare } from 'lucide-react'
import { TemplateCard } from '@/features/dashboard/components/template-card'
import { ChatInput } from '@/features/dashboard/components/chat-input'
import { useAuthStore } from '@/stores/auth-store'
import { useCreateWorkflow } from '@/features/dashboard/hooks/use-workflows'

const TEMPLATES = [
  {
    title: "Slack Notification Bot",
    icon: MessageSquare,
    description: "Send Slack messages when a webhook fires",
    prompt: "Build a workflow that receives a webhook trigger and sends a formatted Slack message with the webhook payload data to a channel.",
  },
  {
    title: "Web Scraper + Summarizer",
    icon: Globe,
    description: "Scrape a URL and summarize with AI",
    prompt: "Build a workflow that takes a URL from a webhook trigger, uses the Browser Use node to visit and extract content from that page, then summarizes the content using the LLM node and returns the summary.",
  },
  {
    title: "Customer Support Bot",
    icon: Bot,
    description: "Answer questions from a knowledge base",
    prompt: "Build a workflow that receives a question via webhook, searches a knowledge base for relevant context, then uses an LLM to generate a helpful answer based on that context and returns it.",
  },
  {
    title: "Scheduled Report",
    icon: Clock,
    description: "Generate and send a daily report",
    prompt: "Build a workflow with a Schedule Trigger that runs every weekday morning, calls an HTTP API to fetch data, formats it into a readable report using an LLM, and sends it via Slack.",
  },
  {
    title: "Lead Scoring",
    icon: Zap,
    description: "Score leads using AI from form submissions",
    prompt: "Build a workflow that receives lead data via webhook (name, email, company, message), uses an LLM Evaluator node to score the lead on fit and urgency from 1-10, then saves high-scoring leads and sends a Slack alert.",
  },
  {
    title: "Email to Task",
    icon: Mail,
    description: "Parse emails and create tasks",
    prompt: "Build a workflow that receives an email payload via webhook, uses an LLM to extract action items and priority from the email body, stores them as structured data, and returns the parsed tasks.",
  },
  {
    title: "RAG Q&A Pipeline",
    icon: Database,
    description: "Answer questions from your documents",
    prompt: "Build a workflow that receives a question via webhook, searches a Knowledge Base node for relevant document chunks, injects the retrieved context into an LLM prompt, and returns a grounded answer with sources.",
  },
  {
    title: "GitHub Issue Triage",
    icon: GitBranch,
    description: "Auto-label and respond to new issues",
    prompt: "Build a workflow triggered by a webhook from GitHub new issue events. Use an LLM to classify the issue type (bug, feature, question) and priority. Then use the GitHub node to add a comment with the classification and suggested next steps.",
  },
  {
    title: "Invoice Generator",
    icon: FileText,
    description: "Generate invoices from order data",
    prompt: "Build a workflow that receives order details via webhook (customer name, items, quantities, prices), uses an LLM to format a professional invoice as markdown, and sends it via Slack.",
  },
]

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const createWorkflow = useCreateWorkflow()
  const [searchQuery, setSearchQuery] = useState('')

  const firstName = user?.full_name?.split(' ')[0]

  const filteredTemplates = useMemo(() => {
    if (!searchQuery.trim()) return TEMPLATES
    const query = searchQuery.toLowerCase()
    return TEMPLATES.filter(t =>
      t.title.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    )
  }, [searchQuery])

  const handleTemplateClick = (template: typeof TEMPLATES[0]) => {
    createWorkflow.mutate(template.title, {
      onSuccess: (wf) => {
        navigate(`/workflows/${wf.id}`, { state: { autoPrompt: template.prompt } })
      },
    })
  }

  const isEmpty = filteredTemplates.length === 0

  return (
    <div className="h-full overflow-y-auto bg-[var(--bg)] custom-scrollbar">
      <div className="flex flex-col items-center px-6">

        {/* Chat Section */}
        <div className="flex flex-col items-center w-full pt-[15vh] md:pt-[25vh] lg:pt-[35vh] pb-[5vh] md:pb-[10vh]">
          <h1 className="mb-6 w-full max-w-[42rem] px-4 text-balance font-[430] font-season text-[24px] md:text-[32px] text-[var(--text-primary)] tracking-[-0.02em] text-center">
            What should we get done, {firstName || 'there'}?
          </h1>
          <ChatInput
            placeholder="Describe a workflow or search templates…"
            onChange={(val) => setSearchQuery(val)}
            onSend={(prompt) => {
              createWorkflow.mutate(undefined, {
                onSuccess: (wf) => navigate(`/workflows/${wf.id}`, { state: { autoPrompt: prompt } }),
              })
            }}
          />
        </div>

        {/* Content Grid */}
        <div className="w-full max-w-[68rem] pb-24">
          {isEmpty ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="mb-4 rounded-full bg-[var(--surface-4)] p-4">
                <Search className="size-8 text-[var(--text-muted)]" />
              </div>
              <h3 className="text-lg font-medium text-[var(--text-primary)]">No results found</h3>
              <p className="text-[var(--text-muted)]">Try adjusting your search for "{searchQuery}"</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredTemplates.map((template, i) => (
                <TemplateCard
                  key={i}
                  title={template.title}
                  icon={template.icon}
                  description={template.description}
                  onClick={() => handleTemplateClick(template)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
