# ResearchPilot Project Specification

## 1. Project Goal

ResearchPilot aims to build a lightweight Agent Harness that supports deep research, local Paper RAG, and codebase understanding.

The project first implements a framework-independent Agent runtime:

- Agent Loop
- Action and Observation
- Tool Interface
- Tool Runtime
- Permission Check
- Trace Store
- Context Manager
- Memory Store

## 2. Why This Project

Many Agent projects only demonstrate framework usage. ResearchPilot focuses on the core mechanism behind Agent systems:

- How an Agent loop works
- How tools are registered and executed
- How observations are returned to the Agent
- How permission checks protect the runtime
- How traces are saved for debugging and evaluation
- How RAG and code tools can be plugged into a unified harness

## 3. Phase 1 MVP

Phase 1 includes:

- A mock Agent that emits predefined actions
- A tool runtime that executes registered tools
- File listing tool
- File reading tool
- Note saving tool
- Safe shell command tool
- Permission checks
- Trace logging
- CLI entrypoint

## 4. Later Phases

Phase 2: Connect a real LLM-based action policy.

Phase 3: Implement a Deep Research Agent inspired by Hello Agents Chapter 14.

Phase 4: Integrate Paper RAG Agent.

Phase 5: Implement Codebase Agent.

Phase 6: Add memory, context compression, and evaluation.

Phase 7: Prepare GitHub README, examples, docs, and interview guide.
