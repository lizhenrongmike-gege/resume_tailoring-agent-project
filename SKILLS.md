# Available Skills

This document lists all available skills that can be invoked using the Skill tool.

## Skills List

### keybindings-help
Use when the user wants to customize keyboard shortcuts, rebind keys, add chord bindings, or modify `~/.claude/keybindings.json`.

**Examples:** "rebind ctrl+s", "add a chord shortcut", "change the submit key", "customize keybindings"

---

### humanizer
Remove signs of AI-generated writing from text. Use when editing or reviewing text to make it sound more natural and human-written.

Based on Wikipedia's comprehensive "Signs of AI writing" guide. Detects and fixes patterns including:
- Inflated symbolism
- Promotional language
- Superficial -ing analyses
- Vague attributions
- Em dash overuse
- Rule of three
- AI vocabulary words
- Negative parallelisms
- Excessive conjunctive phrases

---

### frontend-design:frontend-design
Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications.

Generates creative, polished code that avoids generic AI aesthetics.

---

### superpowers:using-git-worktrees
Use when starting feature work that needs isolation from current workspace or before executing implementation plans.

Creates isolated git worktrees with smart directory selection and safety verification.

---

### superpowers:test-driven-development
Use when implementing any feature or bugfix, before writing implementation code.

---

### superpowers:systematic-debugging
Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes.

---

### superpowers:using-superpowers
Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions.

---

### superpowers:dispatching-parallel-agents
Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies.

---

### superpowers:executing-plans
Use when you have a written implementation plan to execute in a separate session with review checkpoints.

---

### superpowers:finishing-a-development-branch
Use when implementation is complete, all tests pass, and you need to decide how to integrate the work.

Guides completion of development work by presenting structured options for merge, PR, or cleanup.

---

### superpowers:brainstorming
**You MUST use this before any creative work** - creating features, building components, adding functionality, or modifying behavior.

Explores user intent, requirements and design before implementation.

---

### superpowers:writing-plans
Use when you have a spec or requirements for a multi-step task, before touching code.

---

### superpowers:requesting-code-review
Use when completing tasks, implementing major features, or before merging to verify work meets requirements.

---

### superpowers:receiving-code-review
Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable.

Requires technical rigor and verification, not performative agreement or blind implementation.

---

### superpowers:writing-skills
Use when creating new skills, editing existing skills, or verifying skills work before deployment.

---

### superpowers:verification-before-completion
Use when about to claim work is complete, fixed, or passing, before committing or creating PRs.

Requires running verification commands and confirming output before making any success claims; evidence before assertions always.

---

### superpowers:subagent-driven-development
Use when executing implementation plans with independent tasks in the current session.
