---
name: prd
description: Generate a structured Product Requirements Document (PRD) for a feature or change. Provide a brief description as the argument. Based on Aakash Gupta's PRD template.
argument-hint: "[feature description]"
allowed-tools: Read, Glob, Grep
---

Generate a structured PRD for: **$ARGUMENTS**

## PRD Template

Produce a document with the following sections. Be specific and measurable. Do not use vague language.

---

# PRD: $ARGUMENTS

**Status:** Draft
**Author:** Claude Code
**Date:** *(today's date)*
**Version:** 1.0

---

## 1. Problem Statement

*What is broken, missing, or painful? Why does this matter now?*

## 2. Target Users

*Who specifically will use or benefit from this? Include any relevant segments.*

| User Type | Description | Frequency of Impact |
|-----------|-------------|---------------------|
| | | |

## 3. Goals

*Measurable outcomes this change must achieve. Each goal should be verifiable.*

- [ ] Goal 1: ...
- [ ] Goal 2: ...

## 4. Non-Goals

*Explicit exclusions — what this change will NOT do. Prevents scope creep.*

- This will not ...
- Out of scope: ...

## 5. Success Metrics

*How will we know the change succeeded? Include baseline and target values.*

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|--------------------|
| | | | |

## 6. Proposed Solution

*High-level description. Link to technical design if available.*

## 7. Milestones

*Ordered delivery steps. Each milestone is independently reviewable.*

| # | Milestone | Deliverable | Done When |
|---|-----------|-------------|-----------|
| 1 | | | |
| 2 | | | |

## 8. Risks & Open Questions

| Risk / Question | Likelihood | Impact | Mitigation |
|-----------------|------------|--------|-----------|
| | | | |

## 9. Appendix

*Links, references, related issues.*

---

*After generating, ask the plan-review subagent to critique this PRD from a Staff Engineer perspective.*
