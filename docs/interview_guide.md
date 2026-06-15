# ResearchPilot 面试讲解稿

本文档用于整理 ResearchPilot 项目的面试讲法，包括 2 分钟版本、5 分钟版本、10 分钟版本、常见追问和简历 bullet。

---

## 1. 一句话介绍

ResearchPilot 是一个图工作流驱动的多智能体研究助手，支持代码库问答、论文研究、多轮对话记忆、证据生成、trace report 和 evaluation。

它不是一个简单的 RAG demo，而是一个完整的 Agent Engineering 项目，包含自定义 AgentLoop、ToolRuntime、Workflow、GraphWorkflowRuntime、Blackboard Multi-agent、Conversation Memory、Adaptive Paper Research 和 Evaluation。

一句话版本：

```text
ResearchPilot is a graph-based multi-agent research assistant with a custom agent runtime, deterministic workflows, blackboard-based coordination, adaptive paper research, codebase QA, trace reporting, and workflow evaluation.
```

中文解释：

```text
ResearchPilot 是我自己实现的一个研究型 Agent 系统。它不是简单调用 LangChain 或 LangGraph，而是从底层 AgentLoop、工具执行、状态管理、工作流编排、多智能体协作、记忆、证据管理和评估都做了一遍。
```

---

## 2. 2 分钟讲法

ResearchPilot 是我做的一个 Agent Engineering 项目，目标是构建一个可以做代码理解和论文研究的多智能体研究助手。

最开始我实现了一个通用 AgentLoop，也就是传统的 tool-calling agent。它会维护 AgentState，由 LLM policy 决定下一步 action，比如调用工具或者生成最终答案，然后通过 ToolRuntime 执行工具，并把 Observation 和 Trace 保存下来。

后来我发现纯 AgentLoop 虽然灵活，但对于代码问答、论文问答这类流程比较固定的任务，稳定性和 token 成本都不是最优。所以我又抽象出了 deterministic workflow，比如 CodeWorkflowRunner 和 PaperWorkflowRunner。代码问答会固定执行 code_map、code_search、code_read、write_code_answer；论文研究会执行本地 RAG 检索、证据充分性判断、论文下载、索引、再次检索和证据型回答生成。

在此基础上，我进一步实现了一个轻量级 GraphWorkflowRuntime，用图结构来组织多智能体协作。当前主流程是 prepare、planner、code/paper/general、reviewer、retry/writer、final。Planner 负责路由，CodeSubAgent 负责代码问题，PaperSubAgent 负责论文研究，Reviewer 负责审查答案，Writer 负责兜底改写。

项目里比较核心的是 adaptive paper research。普通 RAG 经常有一个问题：top-k 检索返回了很多 chunk，但不代表证据真的能回答问题。所以我加了 evidence sufficiency check 和 post-answer fallback。如果本地证据不足，或者用户明确要求搜索，系统会自动下载论文、更新索引、重新检索，再基于证据生成回答。

此外，项目还有 conversation memory、blackboard shared state、trace report 和 evaluation。这样整个系统不只是能回答问题，还能调试、复盘和回归测试。

---

## 3. 5 分钟讲法

ResearchPilot 是一个图工作流驱动的多智能体研究助手，主要支持两个实际场景：代码库问答和论文研究。我的目标不是做一个简单 RAG demo，而是系统性学习和实现一个完整 Agent 系统从底层运行时到上层多智能体编排的工程结构。

项目可以分成三层。

第一层是 AgentLoop。它是一个通用 tool-calling loop，包含 AgentState、AgentAction、Observation、ToolRuntime 和 TraceStore。LLM policy 每一步决定是调用工具还是生成 final answer，ToolRuntime 执行工具，结果写回状态和 trace。这个层让我理解了 Agent 的基本运行机制。

第二层是 deterministic workflow。我在使用 AgentLoop 的过程中发现，自由工具调用虽然灵活，但对于一些固定任务不够稳定，而且 token 成本较高。比如代码问答通常就是先理解代码结构，再搜索相关文件，再读取文件，最后生成答案；论文问答通常也是先检索证据，再生成引用型回答。所以我把这些任务封装成确定性 workflow。

CodeWorkflowRunner 的流程是 code_map、code_search、code_read、write_code_answer。PaperWorkflowRunner 则包含 paper_answer、paper_collect 和 paper_research 三种模式。其中 paper_research 是 local-first adaptive workflow，会先查本地 RAG，如果证据不足，或者用户明确要求搜索，就自动调用 paper_download 下载论文，再调用 engineered_rag_index 更新索引，再检索和生成答案。

第三层是 GraphWorkflowRuntime。我实现了一个轻量级图运行时，用来组织多智能体协作。它支持 graph node、conditional edge、visited nodes、GraphState、step records 和 max_steps。当前 multi-agent workflow 是 prepare 到 planner，再到 code、paper 或 general specialist，然后进入 reviewer。如果 reviewer 判断答案不充分，可以进入 retry 或 writer fallback，最后生成 final answer。

多智能体部分采用 blackboard-style 架构。PlannerSubAgent 负责判断任务类型，CodeSubAgent 包装 CodeWorkflowRunner，PaperSubAgent 包装 PaperWorkflowRunner，GeneralSubAgent 处理普通问题，ReviewerSubAgent 审查答案，WriterSubAgent 负责改写。Blackboard 中保存 user_request、session summary、recent messages、evidence sources、code files、report paths 和 notes。

这个项目中我解决过一个很典型的 Agentic RAG 问题：本地 RAG 即使没有真正相关证据，也会返回 top-k chunks。如果 workflow 只看返回数量，就会误判证据充分。为了解决这个问题，我做了几层改进：首先 PaperSubAgent 默认走 adaptive paper_research，而不是只走 local paper_answer；其次把 answer_question 和 search_query 分离，避免把长 prompt 传给 arXiv 搜索；第三加入 evidence sufficiency check；第四加入 post-answer fallback，如果 answer writer 明确说证据不足，workflow 会回退到下载、索引、重新检索和重新回答。

项目还支持 conversation memory。多轮 chat 中，当前用户消息直接传给 graph runner，历史上下文通过 session 进入 blackboard。这样可以避免把完整历史拼进当前问题导致 planner 路由污染。

最后，我还做了 trace report 和 evaluation。Trace report 可以记录 graph visited path、planner decision、specialist output、reviewer result、blackboard summary 和 metadata。Evaluation 用来检查 code、paper、multi-agent workflow 的关键行为，避免每次改 routing 或 workflow 后出现回归问题。

所以这个项目的价值不是某个单点模型能力，而是完整展示了一个 Agent 系统在工程上如何组织工具、状态、记忆、工作流、多智能体协作、证据和评估。

---

## 4. 10 分钟讲法

### 4.1 项目背景

我做 ResearchPilot 的初衷是系统学习 Agent 工程。相比只做一个 RAG demo，我希望自己实现一个更完整的 agent harness，覆盖从底层 tool-calling runtime 到上层 multi-agent orchestration 的完整流程。

所以项目一开始不是直接用 LangGraph，而是先自己实现 AgentLoop、ToolRuntime、AgentState、Observation、TraceStore 等基础组件。后面再逐步引入 workflow、multi-agent、graph runtime、memory、evaluation 和 trace report。

---

### 4.2 第一阶段：AgentLoop

最早的版本是一个通用 AgentLoop。它的流程是：

```text
User Goal
  → AgentState
  → LLMAgentPolicy decides action
  → ToolRuntime executes tool
  → Observation is stored
  → loop continues
  → final answer
```

这里我实现了几个核心对象：

```text
AgentState：保存用户目标、历史步骤、final answer、evidence store。
AgentAction：表示 LLM 的下一步动作，比如 tool_call 或 final_answer。
Observation：保存工具执行结果。
ToolRuntime：根据 tool name 找到具体工具并执行。
TraceStore：把每一步 action 和 observation 保存下来。
```

这个阶段的重点是理解 Agent 的基本运行机制：模型不是直接一次性回答，而是在状态和工具之间循环决策。

---

### 4.3 第二阶段：ToolRuntime 和工具层

工具层统一由 ToolRuntime 管理。工具包括代码工具、论文工具、RAG 工具和保存工具。

比如：

```text
code_map
code_search
code_read
write_code_answer

paper_search
paper_download
engineered_rag_index
engineered_rag_search
write_evidence_answer

save_report
save_note
```

每个工具都有统一输入输出，输出 Observation。这样上层不需要关心工具内部细节，只需要通过 ToolRuntime 调用工具。

这也是后面 workflow 和 graph workflow 能复用同一套工具层的基础。

---

### 4.4 第三阶段：从 AgentLoop 到 Workflow

在实践中我发现，完全自由的 AgentLoop 有两个问题。

第一是稳定性。比如代码问答其实很适合固定流程：先 code_map，再 code_search，再 code_read，再 write_code_answer。让 LLM 每一步自由选工具，反而可能选错或者多花 token。

第二是成本。AgentLoop 每一步都要把 tool specs、history、state 给模型看，token 消耗比较大。Workflow 可以把流程控制交给 Python，只在关键生成环节调用 LLM。

所以我实现了 deterministic workflow。

CodeWorkflowRunner 的流程是：

```text
code_map
  → code_search
  → code_read
  → write_code_answer
```

PaperWorkflowRunner 包含：

```text
paper_answer：基于已有索引论文回答
paper_collect：搜索下载论文并更新索引
paper_research：自适应论文研究流程
```

---

### 4.5 第四阶段：Adaptive Paper Research

论文研究是项目中最重要的 workflow。

最初的问题是：如果只做本地 RAG，那么当本地索引没有相关论文时，系统仍然可能返回 top-k chunks。这些 chunks 数量很多，但不一定真正回答问题。

所以我把 paper_research 设计成 local-first adaptive workflow：

```text
local engineered_rag_search
  → evidence sufficiency check
  → if insufficient or force search:
        paper_download
        engineered_rag_index
        engineered_rag_search
  → write_evidence_answer
  → if answer says evidence insufficient:
        fallback download / index / search / answer
  → save_report
```

这里有几个关键设计点。

第一，区分 local_answer 和 adaptive_research。如果用户明确说“基于已有论文”，系统只用本地索引；如果用户说“搜索一下”“找论文”，系统会强制下载新论文。

第二，区分 answer_question 和 search_query。answer_question 可以保留用户原话、planner rewritten request 和回答要求；但 search_query 必须短而干净，比如 `AdaDetectGPT adaptive DetectGPT AI-generated text detection`。否则如果把长 prompt 传给 arXiv，会导致搜索结果严重污染。

第三，加入 evidence insufficiency fallback。如果 writer 生成答案时明确说“retrieved evidence does not contain direct information”，workflow 会把这当成信号，回退到下载、索引和重新检索。

这个设计解决了普通 RAG 中很常见的问题：top-k retrieval 不等于 evidence sufficient。

---

### 4.6 第五阶段：GraphWorkflowRuntime

当系统有了代码 workflow、论文 workflow 和普通 fallback 后，我进一步实现了 GraphWorkflowRuntime，用图结构组织多智能体流程。

GraphWorkflowRuntime 支持：

```text
GraphState
GraphNode
FunctionGraphNode
conditional edge
default edge
visited nodes
step records
max steps
final answer
```

当前 multi-agent graph 是：

```text
prepare
  → planner
  → code / paper / general
  → reviewer
  → final / retry / writer
```

相比简单 if/else，graph runtime 更适合表达复杂 agent 流程，也更容易 debug，因为每个节点和边都可以记录下来。

---

### 4.7 第六阶段：SubAgent 和 Blackboard

multi-agent 系统中，我把角色抽象成 SubAgent。

当前有：

```text
PlannerSubAgent
CodeSubAgent
PaperSubAgent
GeneralSubAgent
ReviewerSubAgent
WriterSubAgent
```

它们之间通过 Blackboard 共享状态。Blackboard 里有：

```text
user_request
session_summary
recent_messages
recent_turn_memories
code_files
evidence_sources
report_paths
notes
metadata
```

这里要区分 Tool 和 SubAgent：

```text
Tool 是具体动作，比如下载论文、搜索代码、读取文件。
SubAgent 是角色节点，比如规划、代码问答、论文研究、审查、重写。
```

SubAgent 不直接重复实现工具能力，而是包装已有 workflow 或 AgentLoop。

---

### 4.8 第七阶段：Conversation Memory

为了支持多轮对话，我加入了 session memory，包括：

```text
session store
recent messages
session summary
turn memory
evidence carryover
report path carryover
```

这里有一个关键修复：在 graph multi-agent chat 中，当前用户消息应该直接作为 user_request 传给 graph runner，而不是把历史上下文拼成 contextual_input 后传进去。历史上下文应该通过 session 进入 blackboard。

这样可以避免 planner 被长历史污染，导致当前路由判断不准。

---

### 4.9 第八阶段：Trace Report 和 Evaluation

复杂 agent 系统最重要的问题之一是可调试性。所以我实现了 trace report。

Trace report 可以记录：

```text
graph visited path
step records
planner decision
specialist output
reviewer result
retry path
writer output
blackboard summary
metadata preview
```

这样如果系统出错，可以判断是 planner 路由错、tool input 错、RAG 证据不足，还是 writer 生成问题。

另外我还做了 evaluation，包括：

```text
eval-code
eval-paper
eval-multi-agent
```

用来做回归测试，检查 workflow 是否成功、answer 是否包含关键术语、graph visited nodes 是否存在、reviewer 是否运行等。

---

### 4.10 项目总结

ResearchPilot 最终形成了一个完整的 agent engineering stack：

```text
AgentLoop
ToolRuntime
Deterministic Workflow
GraphWorkflowRuntime
Blackboard Multi-agent
Conversation Memory
Adaptive Paper Research
Codebase QA
Evidence-aware Answer Generation
Trace Report
Evaluation
```

它的重点不是某个 prompt 或某个现成框架，而是展示了一个真实 agent 系统中如何处理工具调用、流程稳定性、多智能体协作、证据充分性、上下文记忆、debug 和 evaluation。

---

## 5. 常见面试追问

### Q1：为什么不直接用 LangGraph？

可以回答：

```text
这个项目的目标之一是学习 Agent 系统底层机制，所以我先自己实现了一个轻量级 GraphWorkflowRuntime。它支持 node、conditional edge、GraphState、visited nodes、step records 和 max_steps。这样我能更清楚地理解 LangGraph 这类框架背后的核心思想。

当然，如果是生产系统，后续完全可以把这个 graph runtime 替换成 LangGraph。我的实现重点是理解原理和验证架构设计。
```

---

### Q2：AgentLoop 和 Workflow 有什么区别？

可以回答：

```text
AgentLoop 更灵活，让 LLM 每一步自由决定调用哪个工具，适合开放式任务。但它 token 成本高，稳定性也较差。

Workflow 是固定流程，由 Python 控制工具调用顺序，比如代码问答固定执行 code_map、code_search、code_read、write_code_answer。它更稳定、更省 token，也更容易评估。

ResearchPilot 的设计是混合式：开放任务保留 AgentLoop，稳定任务用 Workflow，复杂多智能体流程用 GraphWorkflow。
```

---

### Q3：为什么要做 Graph Workflow？

可以回答：

```text
当系统里有 planner、code specialist、paper specialist、reviewer、writer 时，简单 if/else 会越来越乱。Graph workflow 可以把每个角色变成 node，把路由和 retry 变成 edge。

这样流程更清晰，也能记录 visited path。比如一次任务可能走 prepare → planner → paper → reviewer → final。如果 reviewer 不通过，也可以走 retry 或 writer fallback。
```

---

### Q4：PaperSubAgent 和 paper workflow 是什么关系？

可以回答：

```text
PaperSubAgent 是 graph workflow 里的角色节点，负责处理论文相关任务。它本身不直接实现下载、索引和检索，而是包装 PaperWorkflowRunner。

PaperWorkflowRunner 里有 paper_answer、paper_collect 和 paper_research 三种模式。PaperSubAgent 会根据用户意图选择合适模式。比如用户说只用已有论文，就走 paper_answer；用户说搜索一下，就走 adaptive paper_research。
```

---

### Q5：你怎么解决 RAG 检索不到真正相关证据的问题？

可以回答：

```text
普通 top-k retrieval 有一个问题：即使没有真正相关的文档，也会返回最相似的 k 个 chunk。因此返回数量不等于证据充分。

我做了几层处理。第一，paper_research 里有 evidence sufficiency check，不只看数量，也看 query anchor 是否覆盖。第二，如果用户明确要求搜索，直接 force download，不只查本地。第三，如果 answer writer 明确说 retrieved evidence does not contain direct information，workflow 会触发 post-answer fallback，重新下载、索引、检索和回答。
```

---

### Q6：为什么要区分 answer_question 和 search_query？

可以回答：

```text
这是我实际 debug 中发现的问题。最开始我把完整的 prompt 传给 paper_download，里面包含 Original user request、Planner rewritten request 和 workflow instruction。结果 arXiv 搜索被污染，下载了完全不相关的论文。

后来我把 answer_question 和 search_query 分开。answer_question 给最终回答器，可以保留上下文和指令；search_query 只给 paper_search 或 paper_download，必须短而干净，比如 AdaDetectGPT adaptive DetectGPT AI-generated text detection。这样搜索质量明显稳定。
```

---

### Q7：Conversation Memory 怎么做的？

可以回答：

```text
我实现了 session store、recent messages、session summary 和 turn memory。多轮对话时，系统会保存历史消息和摘要。

在 graph multi-agent 模式里，我做了一个重要设计：当前用户消息直接作为 user_request 传给 graph runner，历史上下文通过 session 进入 blackboard。这样 planner 判断当前意图时不会被长历史污染。
```

---

### Q8：Trace Report 有什么作用？

可以回答：

```text
复杂 agent 系统很容易出错，而且出错原因可能在 planner、tool input、retrieval、writer 或 reviewer。Trace report 可以记录 graph visited path、planner decision、specialist output、reviewer result、blackboard summary 和 metadata。

这样我可以快速定位问题。例如之前 paper search 效果差，我就是通过日志发现 paper_download 收到的是长 prompt，而不是干净 search query。
```

---

### Q9：Evaluation 怎么做？

可以回答：

```text
我给 code、paper 和 multi-agent workflow 都准备了 evaluation cases。它们会检查 workflow 是否成功、final answer 是否包含关键术语、graph visited nodes 是否存在、planner 是否路由正确、reviewer 是否运行等。

这不是严格学术评测，而是工程上的 regression testing。目的是每次修改 routing、workflow 或 tool input 后，能快速发现系统是否退化。
```

---

### Q10：这个项目最大的收获是什么？

可以回答：

```text
最大的收获是理解了 Agent 项目真正难的不是单次 LLM 调用，而是系统工程：如何组织工具，如何管理状态，如何设计稳定 workflow，如何处理上下文污染，如何判断证据是否充分，如何做失败回退，如何 debug 和 evaluation。

比如 adaptive paper research 里，RAG 返回 top-k 不代表证据充分；paper search query 不能直接用长 prompt；multi-agent 必须记录 trace，否则很难定位问题。这些都是实际工程中才会遇到的问题。
```

---

## 6. 简历 Bullet 中文版

可以写：

```text
ResearchPilot：图工作流驱动的多智能体研究助手
- 自主实现 AgentLoop、ToolRuntime、AgentState、Observation 和 TraceStore，支持 LLM tool-calling、工具执行、状态管理和执行轨迹记录。
- 设计 CodeWorkflowRunner 和 PaperWorkflowRunner，将代码问答、论文检索、下载、索引和证据生成封装为稳定的 deterministic workflows，降低自由 AgentLoop 的不稳定性和 token 成本。
- 实现轻量级 GraphWorkflowRuntime，支持 node、conditional edge、GraphState、visited path 和 retry loop，并构建 planner / code / paper / reviewer / writer 多智能体协作流程。
- 构建 adaptive paper research workflow：本地 RAG 证据不足时自动搜索、下载、索引论文并重新检索生成证据型答案；修复 top-k retrieval 误判证据充分和长 prompt 污染 paper search query 的问题。
- 实现 persistent conversation memory、blackboard shared state、multi-agent trace report 和 workflow evaluation，提升复杂 Agent 系统的可调试性、可复盘性和回归测试能力。
```

---

## 7. 简历 Bullet 英文版

可以写：

```text
ResearchPilot: Graph-based Multi-agent Research Assistant
- Built a custom agent runtime with AgentLoop, ToolRuntime, AgentState, Observation, and TraceStore to support LLM tool calling, state management, tool execution, and trace logging.
- Designed deterministic CodeWorkflowRunner and PaperWorkflowRunner for stable codebase QA and adaptive paper research, reducing token overhead and tool-selection instability from free-form agent loops.
- Implemented a lightweight GraphWorkflowRuntime with nodes, conditional edges, shared GraphState, visited path tracking, and retry loops for planner / code / paper / reviewer / writer multi-agent orchestration.
- Developed an adaptive paper research workflow that performs local RAG search, evidence sufficiency checking, paper download, indexing, retrieval retry, and citation-aware answer generation when local evidence is insufficient.
- Added persistent conversation memory, blackboard-based shared state, multi-agent trace reports, and workflow evaluation to improve debuggability, observability, and regression testing of complex agent behavior.
```

---

## 8. 面试中最推荐展示的三个点

### 8.1 Graph multi-agent workflow

展示命令：

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --verbose
```

输入：

```text
AgentLoop 是怎么实现的？
```

讲解重点：

```text
展示 planner → code → reviewer → final 的路径。
说明不是纯 prompt，而是 graph workflow。
```

---

### 8.2 Adaptive paper research

展示命令：

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --verbose
```

输入：

```text
搜索一下并告诉我 AdaDetectGPT 是啥
```

讲解重点：

```text
展示 PaperSubAgent 调用 paper_research。
展示 paper_download、engineered_rag_index、engineered_rag_search、write_evidence_answer。
说明如何处理本地证据不足和 search_query 清洗。
```

---

### 8.3 Trace report

展示命令：

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --show-review --save-trace-report --verbose
```

讲解重点：

```text
展示 graph visited path、planner decision、reviewer result、blackboard summary。
说明复杂 Agent 系统必须可观察、可调试。
```

---

## 9. 项目不足和改进方向

面试中如果被问到不足，可以主动说：

```text
当前项目还有几个可以继续改进的方向。

第一，subagent 目前是 shared blackboard 架构，还没有做到完全 message isolation。后续可以给每个 subagent 构造 filtered context view。

第二，paper search 主要依赖 arXiv API，候选排序还可以更强。后续可以加 reranker 或 LLM paper relevance grader。

第三，indexing 目前是同步执行，后续可以做 fast search answer 和 background indexing。

第四，incremental-only indexing 还可以进一步优化，让系统每次只 index 新下载文件，而不是重复处理已有论文。
```

这样回答会显得你很清楚项目边界，而不是盲目吹项目。

---

## 10. 最终项目定位

最终可以这样定位 ResearchPilot：

```text
ResearchPilot 是一个用于学习和展示 Agent Engineering 能力的完整项目。它从底层 AgentLoop 和 ToolRuntime 出发，逐步构建 deterministic workflow、graph-based multi-agent orchestration、blackboard shared state、conversation memory、adaptive paper research、trace report 和 evaluation。

这个项目体现的是我对 Agent 系统工程的理解：Agent 不只是让 LLM 调工具，更重要的是流程设计、状态管理、上下文控制、证据验证、失败回退、可观测性和评估。
```
