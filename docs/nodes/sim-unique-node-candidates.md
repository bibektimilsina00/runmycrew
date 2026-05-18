# Sim Unique Node Candidates

Source reference: `temp/sim`.

This list intentionally excludes most plain SaaS/API action nodes such as Slack, Discord, CRM CRUD, and simple send-message blocks. It focuses on nodes that likely need distinct runtime behavior, canvas behavior, or inspector UI.

## Highest Priority

- `agent` - LLM agent with messages, tools, model settings, memory limits, and structured output.
- Loop subflow - Sim has loop orchestration separate from normal blocks: `for`, `forEach`, `while`, and `doWhile`.
- Parallel subflow - parallel branch/subflow execution concept.
- `router_v2` - route workflow execution based on context and route descriptions.
- `condition` - explicit branching with condition editor and multiple paths.
- `human_in_the_loop` - pauses execution and resumes from human input.
- `workflow_input` - child workflow execution with input mapping to the child start schema.
- `function` - custom JavaScript/Python code execution.
- `mcp` - dynamic MCP server/tool selector with tool-specific arguments.
- `knowledge` - knowledge base/vector search operations.
- `memory`, `mem0`, `zep` - memory/session context primitives.
- `browser_use` - browser automation task runner with live session outputs.
- `stagehand` - browser extraction and agent automation.
- `guardrails` - JSON/regex/hallucination/PII validation.
- `evaluator` - AI-based scoring/evaluation of content.
- `response` - structured API response node.
- `file_v3` - read/write workspace files.
- `table` - user-defined table data.

## AI And Media

- `image_generator` - image generation with file output.
- `video_generator_v2` - video generation with provider/model-specific controls.
- `vision_v2` - image analysis.
- `tts` - text-to-speech with voice/provider controls.
- `stt_v2` - speech-to-text with diarization, timestamps, summarization, and redaction options.
- `mistral_parse_v3` - document/PDF parsing.
- `textract_v2` - document extraction/OCR.
- `reducto_v2` - document parsing.
- `thinking` - explicit thought-process instruction tool.
- `a2a` - external agent-to-agent interaction.
- `dspy` - DSPy program prediction.
- `parallel_ai` - web research/deep research.
- `perplexity` - AI search/chat.
- `devin` - autonomous coding agent integration.
- `cursor_v2` - Cursor cloud agent and artifact workflow.

## Specialized Data Nodes

These are integrations, but their UI/runtime is more specialized than simple API calls because they need query editors, schema browsing, file selectors, or vector/database-specific controls.

- `postgresql`
- `mysql`
- `mongodb`
- `redis`
- `upstash`
- `supabase`
- `dynamodb`
- `rds`
- `athena`
- `google_bigquery`
- `databricks`
- `neo4j`
- `elasticsearch`
- `pinecone`
- `qdrant`

## Trigger And IO Nodes

- `start_trigger` - unified start node for chat, manual, and API runs.
- `chat_trigger` - chat-entry workflow trigger.
- `api_trigger` - HTTP API trigger.
- `input_trigger` - structured input form trigger.
- `schedule` - scheduled trigger.
- `generic_webhook` - arbitrary webhook trigger.
- `rss` - RSS polling/trigger.
- `wait` - pause execution for a duration.
- `variables` - workflow-scoped variables.
- `logs` - query workflow execution logs.
- `note` - canvas-only annotation block.
