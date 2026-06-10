# ResearchPilot Interview Guide

## 1. How to introduce the project

ResearchPilot is a lightweight Claude Code-like Agent Harness for deep research, Paper RAG, and codebase understanding.

Instead of directly building a demo on top of an existing orchestration framework, I first implemented the core runtime myself, including the Agent Loop, Action schema, Observation schema, Tool Runtime, Permission Layer, Context Manager, and Trace Store.

## 2. Why not directly use LangGraph?

LangGraph is useful for graph-based orchestration, but the goal of this project is to understand and implement the core mechanism behind Agent systems.

The project can later provide a LangGraph backend, but the core logic is framework-independent.

## 3. What does Phase 1 demonstrate?

Phase 1 demonstrates:

- The Agent Loop can run.
- Tools can be registered and executed.
- Tool outputs are returned as Observations.
- Permission checks are applied.
- Execution traces are saved.
- CLI can trigger the harness.
