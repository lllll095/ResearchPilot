# ResearchPilot

ResearchPilot is a lightweight Claude Code-like agent harness for deep research, paper RAG, and codebase understanding.

This project is designed as an internship-ready Agent project. Instead of directly depending on a single orchestration framework, it first implements the core runtime of an Agent system.

## Inspired By

- Hello Agents Chapter 14: Automated Deep Research Agent
- Claude Code-style Agent Loop
- Hermes-style Tool Runtime, Memory, Trace, and Permission design
- Local Paper RAG systems

## Phase 1 Features

- Agent Loop
- Structured Agent Action
- Structured Observation
- Tool Interface
- Tool Runtime
- Permission Checker
- Context Manager
- Trace Store
- File Tools
- Note Tool
- Shell Tool with permission checks
- Mock Agent Policy
- CLI entrypoint

## Quick Start

```bash
conda create -n research-pilot python=3.10 -y
conda activate research-pilot

pip install -e .
research-pilot run "analyze this project"
```

Or:

```bash
python -m research_pilot.cli run "analyze this project"
```

## Run Tests

```bash
pip install -e ".[dev]"
pytest
```
