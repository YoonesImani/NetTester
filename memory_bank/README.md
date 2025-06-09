# Memory Bank System

This directory contains the Memory Bank system, a modular, graph-based system for managing development workflows and task states.

## Directory Structure

```
memory_bank/
├── README.md           # This file
├── rules/             # Mode-specific rules and configurations
├── state/             # Current state and context information
├── graphs/            # Visual process maps and decision trees
└── logs/              # System logs and activity tracking
```

## Purpose

The Memory Bank system provides:
- Mode-specific rule management
- Just-in-time loading of relevant rules
- Visual process maps and decision trees
- State tracking and context management
- Integration with Cursor custom modes

## Modes

The system supports the following modes:
1. VAN - Initialization and setup
2. PLAN - Task planning and requirements analysis
3. CREATIVE - Design decisions and exploration
4. IMPLEMENT - Code implementation
5. QA - Technical validation and testing

Each mode has its own set of rules and processes, loaded dynamically as needed. 