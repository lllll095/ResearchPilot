# ResearchPilot Architecture

## Phase 1 Architecture

```text
User Goal
  ↓
AgentLoop
  ↓
MockAgentPolicy
  ↓
AgentAction
  ↓
ToolRuntime
  ↓
Tool
  ↓
Observation
  ↓
TraceStore
  ↓
Final Answer
```

## Key Design

ResearchPilot separates the core Agent runtime from specific capabilities.

The core runtime includes:

- Action
- Observation
- State
- Tool
- ToolRuntime
- PermissionChecker
- ContextManager
- TraceStore
- AgentLoop

Later phases will add real LLM policy, deep research workflow, paper RAG tools, and codebase tools.
