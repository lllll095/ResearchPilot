# ResearchPilot 简历与 GitHub 展示说明

本文档用于整理 ResearchPilot 在简历、GitHub 和面试中的展示方式。

---

## 1. 项目中文名称

```text
ResearchPilot：图工作流驱动的多智能体研究助手
```

---

## 2. 项目英文名称

```text
ResearchPilot: Graph-based Multi-agent Research Assistant
```

---

## 3. 一句话项目定位

中文版：

```text
ResearchPilot 是一个面向代码理解、论文研究和多轮对话的图工作流多智能体研究助手，包含自定义 AgentLoop、ToolRuntime、Workflow、GraphWorkflowRuntime、Blackboard、Conversation Memory、Trace Report 和 Evaluation。
```

英文版：

```text
ResearchPilot is a graph-based multi-agent research assistant for codebase QA, adaptive paper research, and multi-turn interaction, built with a custom AgentLoop, ToolRuntime, deterministic workflows, GraphWorkflowRuntime, blackboard memory, trace reporting, and evaluation.
```

---

## 4. 简历项目描述：中文精简版

适合中文简历项目经历部分。

```text
ResearchPilot：图工作流驱动的多智能体研究助手

- 自主实现 AgentLoop、ToolRuntime、AgentState、Observation 和 TraceStore，支持 LLM tool-calling、工具执行、状态管理和执行轨迹记录。
- 设计 CodeWorkflowRunner 和 PaperWorkflowRunner，将代码问答、论文检索、下载、索引和证据生成封装为稳定的 deterministic workflow，降低自由 AgentLoop 的不稳定性和 token 成本。
- 实现轻量级 GraphWorkflowRuntime，支持 node、conditional edge、GraphState、visited path 和 retry loop，并构建 planner / code / paper / reviewer / writer 多智能体协作流程。
- 构建 adaptive paper research workflow：本地 RAG 证据不足时自动搜索、下载、索引论文并重新检索生成证据型答案；修复 top-k retrieval 误判证据充分和长 prompt 污染 paper search query 的问题。
- 实现 persistent conversation memory、blackboard shared state、multi-agent trace report 和 workflow evaluation，提升复杂 Agent 系统的可调试性、可复盘性和回归测试能力。
```

---

## 5. 简历项目描述：中文详细版

适合项目经历写得稍微完整一些的版本。

```text
ResearchPilot：图工作流驱动的多智能体研究助手

项目简介：
构建了一个面向代码库问答、论文研究和多轮对话的研究型 Agent 系统。项目从底层 AgentLoop 和 ToolRuntime 出发，逐步扩展出 deterministic workflow、graph-based multi-agent orchestration、blackboard memory、adaptive paper research、trace report 和 evaluation，目标是实现一个可运行、可调试、可评估、可扩展的 Agent Engineering 项目。

主要工作：
- 实现自定义 AgentLoop 运行时，支持 LLM policy、tool calling、AgentState 状态管理、Observation 记录、ToolRuntime 工具执行和 TraceStore 执行轨迹保存。
- 设计 deterministic workflow 替代完全自由的工具调用流程，构建 CodeWorkflowRunner 和 PaperWorkflowRunner，提高代码问答和论文研究任务的稳定性并降低 token 消耗。
- 实现轻量级 GraphWorkflowRuntime，支持节点、条件边、共享 GraphState、visited path、step records 和 retry loop，用于组织 planner、specialist、reviewer、writer 多智能体协作。
- 构建 adaptive paper research 流程，支持 local RAG search、evidence sufficiency check、paper download、RAG indexing、retrieval retry 和 evidence-aware answer generation。
- 修复真实 Agentic RAG 中的关键问题：top-k retrieval 不等于证据充分；本地证据不足时需要 workflow fallback；paper search query 需要与 answer question 分离，避免长 prompt 污染搜索结果。
- 实现持久化 conversation memory、blackboard shared state、multi-agent trace report 和 workflow evaluation，使复杂 Agent 系统具备可调试、可复盘和可回归测试能力。
```

---

## 6. Resume Project Description: English Version

适合英文简历。

```text
ResearchPilot: Graph-based Multi-agent Research Assistant

- Built a custom agent runtime with AgentLoop, ToolRuntime, AgentState, Observation, and TraceStore to support LLM tool calling, state management, tool execution, and trace logging.
- Designed deterministic CodeWorkflowRunner and PaperWorkflowRunner for stable codebase QA and adaptive paper research, reducing token overhead and tool-selection instability from free-form agent loops.
- Implemented a lightweight GraphWorkflowRuntime with nodes, conditional edges, shared GraphState, visited path tracking, step records, and retry loops for planner / code / paper / reviewer / writer multi-agent orchestration.
- Developed an adaptive paper research workflow that performs local RAG search, evidence sufficiency checking, paper download, indexing, retrieval retry, and citation-aware answer generation when local evidence is insufficient.
- Improved agentic RAG reliability by separating answer questions from paper search queries, preventing long-prompt query pollution, and adding fallback logic when retrieved evidence is insufficient.
- Added persistent conversation memory, blackboard-based shared state, multi-agent trace reports, and workflow evaluation to improve debuggability, observability, and regression testing of complex agent behavior.
```

---

## 7. 英文简历更短版本

适合简历空间比较紧张时使用。

```text
ResearchPilot: Graph-based Multi-agent Research Assistant

- Built a custom agent engineering stack with AgentLoop, ToolRuntime, deterministic workflows, GraphWorkflowRuntime, blackboard memory, trace logging, and evaluation.
- Implemented graph-based multi-agent orchestration with planner, code, paper, reviewer, and writer subagents for codebase QA and adaptive paper research.
- Developed an adaptive paper research workflow with local RAG search, evidence sufficiency checking, paper download, indexing, retrieval retry, and citation-aware answer generation.
- Improved reliability by separating answer questions from search queries, adding evidence-insufficiency fallback, and supporting trace reports for debugging and workflow evaluation.
```

---

## 8. GitHub 项目首页展示文案

适合 README 开头或 GitHub 项目简介。

```text
ResearchPilot is a graph-based multi-agent research assistant for codebase understanding, adaptive paper research, and evidence-aware answer generation.

It implements a custom agent engineering stack, including AgentLoop, ToolRuntime, deterministic workflows, GraphWorkflowRuntime, blackboard-based multi-agent coordination, conversation memory, trace reporting, and evaluation.

Unlike a simple RAG demo, ResearchPilot focuses on the full agent workflow: routing, tool execution, evidence retrieval, sufficiency checking, fallback, review, traceability, and regression testing.
```

中文版本：

```text
ResearchPilot 是一个图工作流驱动的多智能体研究助手，支持代码库问答、论文研究、多轮对话、证据生成、trace report 和 workflow evaluation。

它不是一个简单 RAG demo，而是从 AgentLoop、ToolRuntime、deterministic workflow、GraphWorkflowRuntime、Blackboard Multi-agent、Conversation Memory 到 Evaluation 的完整 Agent Engineering 项目。
```

---

## 9. GitHub 项目亮点摘要

```text
项目亮点：

1. 自定义 AgentLoop 和 ToolRuntime
   实现 LLM tool-calling、状态管理、工具执行和 trace logging。

2. Deterministic Workflow
   将代码问答和论文研究封装成稳定流程，降低自由 agent loop 的不确定性。

3. Graph-based Multi-agent Orchestration
   实现 planner / code / paper / reviewer / writer 的图结构协作流程。

4. Adaptive Paper Research
   本地 RAG 证据不足时，自动搜索、下载、索引论文并重新检索生成答案。

5. Blackboard Memory
   使用共享黑板维护用户请求、session summary、recent messages、evidence sources、code files 和 report paths。

6. Trace Report and Evaluation
   支持 graph visited path、planner decision、review result、metadata preview 和 workflow regression testing。
```

---

## 10. 面试讲解中的项目亮点

面试时最值得强调这几个点：

### 10.1 不是普通 RAG demo

```text
普通 RAG demo 通常只是 document loading → retrieval → LLM answer。ResearchPilot 更关注完整 Agent 系统：planner routing、tool runtime、workflow orchestration、evidence sufficiency check、fallback、review、trace report 和 evaluation。
```

### 10.2 自己实现了 Agent 基础设施

```text
项目没有一开始直接依赖 LangGraph，而是先自己实现 AgentLoop、ToolRuntime、AgentState、Observation、TraceStore，再逐步扩展 deterministic workflow 和 GraphWorkflowRuntime。这样能体现对 Agent 底层机制的理解。
```

### 10.3 Workflow 提升稳定性

```text
自由 AgentLoop 很灵活，但对于代码问答和论文研究这种结构稳定的任务，容易多花 token 或选错工具。因此我将这些任务封装成 deterministic workflow，让 Python 控制流程，LLM 只在关键生成节点发挥作用。
```

### 10.4 Graph Workflow 支持多智能体

```text
当系统需要 planner、specialist、reviewer、writer 时，简单 if/else 会变复杂。因此我实现了 GraphWorkflowRuntime，用 node 和 conditional edge 表达多智能体路径，并记录 visited path 方便 debug。
```

### 10.5 Adaptive Paper Research 解决真实问题

```text
RAG top-k 返回很多 chunk 不代表证据真的充分。ResearchPilot 中 PaperWorkflowRunner 会检查 evidence sufficiency。如果本地证据不足，或者用户明确要求搜索，就会下载论文、更新索引、重新检索并生成答案。
```

### 10.6 Query Pollution 的 Debug 经验

```text
开发中我发现如果把完整 prompt 直接传给 arXiv 搜索，会导致搜索结果严重污染。后来我把 answer_question 和 search_query 分开：前者给回答器，后者给 paper_search / paper_download。这个改动显著提高了 paper search 的稳定性。
```

### 10.7 Trace 和 Evaluation 是复杂 Agent 的关键

```text
复杂 Agent 系统出错时，问题可能来自 planner、tool input、retrieval、writer 或 reviewer。Trace report 能记录 graph path、planner decision、specialist output、review result 和 blackboard state。Evaluation 则用于修改 workflow 后做回归测试。
```

---

## 11. 面试中可以主动展示的命令

### 代码问答

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --verbose
```

输入：

```text
AgentLoop 是怎么实现的？
```

展示点：

```text
prepare → planner → code → reviewer → final
```

---

### 论文研究

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --verbose
```

输入：

```text
搜索一下并告诉我 AdaDetectGPT 是啥
```

展示点：

```text
prepare → planner → paper → reviewer → final
```

Paper workflow 内部展示：

```text
paper_research
  → paper_download
  → engineered_rag_index
  → engineered_rag_search
  → write_evidence_answer
```

---

### Trace Report

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --show-review --save-trace-report --verbose
```

展示点：

```text
graph visited path
planner decision
specialist output
reviewer result
blackboard summary
metadata preview
```

---

### Evaluation

```powershell
research-pilot eval-multi-agent
```

展示点：

```text
workflow success
graph visited nodes
planner route
reviewer output
final answer checks
```

---

## 12. 项目不足与后续计划

面试时可以主动说明：

```text
当前项目仍有一些可以继续改进的方向：

1. SubAgent Context Isolation
   当前是 shared blackboard 架构，后续可以为不同 subagent 构造 filtered context view，减少上下文污染。

2. Fast Search Answer
   当前论文研究主要走完整 PDF download + indexing + RAG answer。后续可以增加 paper_search 后直接基于 title / abstract / snippet 的快速回答模式。

3. Background Indexing
   当前 indexing 是同步执行，后续可以做后台下载和索引，实现先给 preliminary answer，再更新 full evidence report。

4. Incremental-only Indexing
   后续可以让 engineered_rag_index 明确只 index 新下载文件，避免重复处理已有论文。

5. Paper Candidate Reranking
   当前主要依赖 arXiv search，后续可以增加 LLM relevance grader 或 reranker，提高下载论文的相关性。
```

---

## 13. 最终面试定位

最后可以这样总结：

```text
ResearchPilot 的核心价值不是某一个 RAG pipeline，而是一个完整 Agent 系统的工程实现。

它展示了我对 Agent 工程关键问题的理解：如何设计 agent runtime，如何管理工具调用，如何让稳定任务走 workflow，如何用 graph 组织多智能体，如何处理 RAG 证据不足，如何避免 query pollution，如何管理多轮记忆，以及如何通过 trace report 和 evaluation 提高可调试性和可维护性。
```

---

## 14. 适合投递岗位关键词

这个项目可以对应以下岗位关键词：

```text
LLM Engineer
Agent Engineer
RAG Engineer
AI Application Engineer
Applied LLM Intern
AI Infrastructure Intern
Research Engineer Intern
```

对应技术关键词：

```text
LLM Agent
Tool Calling
AgentLoop
Workflow Orchestration
Graph Workflow
Multi-agent System
RAG
Agentic RAG
Evidence-aware Generation
Conversation Memory
Trace Logging
Evaluation
Codebase QA
Paper Research Assistant
```
