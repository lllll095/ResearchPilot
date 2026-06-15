# ResearchPilot GitHub 上传前检查清单

本文档用于整理 ResearchPilot 在上传 GitHub 或展示给面试官前需要检查的内容，包括项目结构、文档完整性、环境配置、敏感信息、demo 命令和最终提交步骤。

---

## 1. 项目结构总览

ResearchPilot 当前推荐展示结构如下：

```text
ResearchPilot/
├── README.md
├── pyproject.toml
├── .gitignore
├── docs/
│   ├── project_architecture.md
│   ├── demo_cases.md
│   ├── interview_guide.md
│   ├── resume_showcase.md
│   └── github_release_checklist.md
├── eval/
│   ├── code_eval_cases.jsonl
│   ├── paper_eval_cases.jsonl
│   └── multiagent_eval_cases.jsonl
├── src/
│   └── research_pilot/
│       ├── agents/
│       ├── core/
│       ├── tools/
│       ├── workflows/
│       ├── graph/
│       ├── multiagent/
│       ├── conversation/
│       └── evaluation/
└── workspace/
    ├── documents/
    ├── reports/
    ├── traces/
    └── sessions/
```

其中最核心的是：

```text
src/research_pilot/core/
  AgentLoop、AgentState、Action、Observation、ToolRuntime、TraceStore

src/research_pilot/workflows/
  CodeWorkflowRunner、PaperWorkflowRunner、MultiAgentGraphWorkflowRunner

src/research_pilot/graph/
  GraphState、GraphNode、GraphWorkflowRunner

src/research_pilot/multiagent/
  Blackboard、SubAgent、Planner、Code、Paper、Reviewer、Writer

src/research_pilot/tools/
  code tools、paper tools、RAG tools、save tools

src/research_pilot/conversation/
  session、summary、turn memory

src/research_pilot/evaluation/
  code、paper、multi-agent evaluation
```

---

## 2. README 检查

上传前确认 README 至少包含：

```text
项目简介
项目亮点
核心架构
多智能体流程
Adaptive Paper Research
Codebase QA
Conversation Memory
Trace Report
Evaluation
常用命令
推荐 Demo
项目目录结构
当前限制
后续计划
```

README 的目标是让别人 2 分钟内明白：

```text
1. 这是一个 Agent Engineering 项目，不是普通 RAG demo。
2. 项目包含 AgentLoop、ToolRuntime、Workflow、GraphWorkflowRuntime 和 Multi-agent。
3. 项目可以实际运行代码问答和论文研究 demo。
4. 项目有 trace report 和 evaluation。
```

---

## 3. docs 文档检查

确认 `docs/` 下至少有：

```text
docs/project_architecture.md
  项目架构说明。

docs/demo_cases.md
  展示案例和命令。

docs/interview_guide.md
  面试讲解稿。

docs/resume_showcase.md
  简历和 GitHub 展示文案。

docs/github_release_checklist.md
  GitHub 上传前检查清单。
```

这些文档的作用：

```text
project_architecture.md：
  解释系统为什么这样设计。

demo_cases.md：
  告诉别人怎么跑 demo。

interview_guide.md：
  帮自己准备面试讲解。

resume_showcase.md：
  帮自己写简历 bullet。

github_release_checklist.md：
  上传前自查。
```

---

## 4. 敏感信息检查

上传 GitHub 前必须确认不要上传：

```text
.env
.env.local
.env.*
api_key
OPENAI_API_KEY
DASHSCOPE_API_KEY
TAVILY_API_KEY
任何真实 token
workspace 中下载的大量论文 PDF
运行 trace 中包含的私人信息
conversation sessions 中的私人对话
```

推荐 `.gitignore` 至少包含：

```gitignore
.env
.env.*
__pycache__/
*.pyc
.ipynb_checkpoints/

workspace/documents/papers/
workspace/reports/
workspace/traces/
workspace/sessions/
workspace/tmp/

*.log
.DS_Store
```

如果你想保留空目录，可以加 `.gitkeep`：

```text
workspace/documents/.gitkeep
workspace/reports/.gitkeep
workspace/traces/.gitkeep
workspace/sessions/.gitkeep
```

---

## 5. 当前 Git 状态检查

运行：

```powershell
git status
```

理想状态是：

```text
nothing to commit, working tree clean
```

如果有修改，先确认是否应该提交：

```powershell
git diff
```

如果确认要提交：

```powershell
git add .
git commit -m "Prepare project documentation for release"
```

---

## 6. 检查是否误提交大文件

运行：

```powershell
git status
```

重点看有没有这些文件被追踪：

```text
.pdf
.pkl
.sqlite
.chroma
.env
workspace/
```

也可以用：

```powershell
git ls-files
```

如果发现已经加入了不该提交的文件，例如：

```text
workspace/documents/papers/xxx.pdf
.env
```

先从 Git 追踪里移除，但保留本地文件：

```powershell
git rm --cached .env
git rm --cached -r workspace/documents/papers
git rm --cached -r workspace/reports
git rm --cached -r workspace/traces
git rm --cached -r workspace/sessions
```

然后提交：

```powershell
git add .gitignore
git commit -m "Remove local artifacts from version control"
```

---

## 7. 本地运行检查

上传前建议至少跑 3 个命令。

### 7.1 Import 检查

```powershell
python -c "import research_pilot; print('import ok')"
```

### 7.2 CLI 检查

```powershell
research-pilot --help
```

### 7.3 多智能体基础检查

```powershell
research-pilot chat --multi-agent --show-graph --show-plan
```

推荐输入：

```text
RAG 和 Agent 的区别是什么？
```

预期可以正常进入：

```text
prepare → planner → general → final
```

---

## 8. 推荐 Demo 检查

上传前建议确认下面三个 demo 至少能跑通。

### Demo 1：代码库问答

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --verbose
```

输入：

```text
AgentLoop 是怎么实现的？
```

预期路径：

```text
prepare → planner → code → reviewer → final
```

---

### Demo 2：论文研究

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --verbose
```

输入：

```text
搜索一下并告诉我 AdaDetectGPT 是啥
```

预期路径：

```text
prepare → planner → paper → reviewer → final
```

预期 PaperWorkflow 内部包含：

```text
paper_download
engineered_rag_index
engineered_rag_search
write_evidence_answer
```

---

### Demo 3：Trace Report

```powershell
research-pilot chat --multi-agent --show-graph --show-plan --show-review --save-trace-report --verbose
```

输入：

```text
AgentLoop 是怎么实现的？
```

预期生成 trace report，并能看到：

```text
graph visited path
planner decision
specialist output
reviewer result
blackboard summary
```

---

## 9. Evaluation 检查

上传前建议跑：

```powershell
research-pilot eval-code
```

```powershell
research-pilot eval-paper
```

```powershell
research-pilot eval-multi-agent
```

如果某些 eval 依赖本地论文索引或 API，可以在 README 里说明：

```text
部分 paper evaluation 需要先配置 API key 或构建本地论文索引。
```

---

## 10. 环境说明检查

README 或安装说明里应写清楚：

```text
Python 版本
conda 环境
pip install -e .
需要配置哪些 API key
如何运行 CLI
如何运行 demo
```

推荐写法：

```powershell
conda create -n research-pilot python=3.10
conda activate research-pilot
pip install -e .
```

如果有开发依赖：

```powershell
pip install -e ".[dev]"
```

---

## 11. API Key 说明

不要在仓库中放真实 API key。

可以提供 `.env.example`：

```text
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini

DASHSCOPE_API_KEY=your_dashscope_key
TAVILY_API_KEY=your_tavily_key
```

实际 `.env` 必须在 `.gitignore` 中。

---

## 12. GitHub 上传步骤

如果本地还没有远程仓库：

```powershell
git init
git add .
git commit -m "Initial commit"
```

在 GitHub 新建空仓库后，复制远程地址，例如：

```powershell
git remote add origin https://github.com/your-name/research-pilot.git
git branch -M main
git push -u origin main
```

如果已经有远程仓库：

```powershell
git remote -v
git push
```

如果 push 失败，先看报错：

```text
authentication failed
remote rejected
large file
non-fast-forward
```

常见解决：

```powershell
git pull --rebase origin main
git push
```

如果是大文件问题，先移除大文件并更新 `.gitignore`。

---

## 13. GitHub 首页展示建议

GitHub repo 首页建议突出这句话：

```text
ResearchPilot is a graph-based multi-agent research assistant built from a custom AgentLoop, ToolRuntime, deterministic workflows, GraphWorkflowRuntime, blackboard memory, trace reports, and evaluation.
```

中文版本：

```text
ResearchPilot 是一个图工作流驱动的多智能体研究助手，从底层 AgentLoop、ToolRuntime 到 Workflow、GraphWorkflowRuntime、Blackboard、Conversation Memory、Trace Report 和 Evaluation 都进行了完整实现。
```

---

## 14. 推荐截图或录屏内容

可以准备 3 张截图：

```text
1. chat --multi-agent 的 graph path
2. paper_research 的 tool steps
3. trace report 内容
```

也可以准备一个短录屏：

```text
先运行代码问答 demo；
再运行论文研究 demo；
最后打开 trace report。
```

---

## 15. 最终上传前 Checklist

上传前逐项检查：

```text
[ ] README.md 已更新
[ ] docs/project_architecture.md 已完成
[ ] docs/demo_cases.md 已完成
[ ] docs/interview_guide.md 已完成
[ ] docs/resume_showcase.md 已完成
[ ] docs/github_release_checklist.md 已完成
[ ] .gitignore 已包含 .env 和 workspace 本地产物
[ ] 没有真实 API key
[ ] 没有提交大量 PDF 或 vectorstore 文件
[ ] research-pilot --help 能运行
[ ] chat --multi-agent demo 能运行
[ ] code demo 能运行
[ ] paper demo 能运行
[ ] trace report 能生成
[ ] git status 干净
[ ] 已 push 到 GitHub
```

---

## 16. 最终提交命令

```powershell
git status
git add README.md docs/
git commit -m "Finalize project documentation"
git push
```

如果只提交当前文档：

```powershell
git add docs\github_release_checklist.md
git commit -m "Add GitHub release checklist"
```

---

## 17. 项目最终状态说明

当以上内容完成后，ResearchPilot 就可以作为一个比较完整的简历项目展示。

它体现的能力包括：

```text
Agent runtime implementation
Tool calling infrastructure
Workflow orchestration
Graph-based multi-agent system
Agentic RAG
Adaptive paper research
Codebase QA
Conversation memory
Trace logging
Evaluation
Debugging and reliability engineering
```

这已经足够支撑一个 LLM Agent / RAG / AI Application Engineer 方向的项目经历。
