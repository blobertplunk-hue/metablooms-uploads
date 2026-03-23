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
**Date:** _(today's date)_
**Version:** 1.0

---

## 1. Problem Statement

_What is broken, missing, or painful? Why does this matter now?_

## 2. Target Users

_Who specifically will use or benefit from this? Include any relevant segments._

| User Type | Description | Frequency of Impact |
| --------- | ----------- | ------------------- |
|           |             |                     |

## 3. Goals

_Measurable outcomes this change must achieve. Each goal should be verifiable._

- [ ] Goal 1: ...
- [ ] Goal 2: ...

## 4. Non-Goals

_Explicit exclusions — what this change will NOT do. Prevents scope creep._

- This will not ...
- Out of scope: ...

## 5. Success Metrics

_How will we know the change succeeded? Include baseline and target values._

| Metric | Baseline | Target | Measurement Method |
| ------ | -------- | ------ | ------------------ |
|        |          |        |                    |

## 6. Proposed Solution

_High-level description. Link to technical design if available._

## 7. Milestones

_Ordered delivery steps. Each milestone is independently reviewable._

| #   | Milestone | Deliverable | Done When |
| --- | --------- | ----------- | --------- |
| 1   |           |             |           |
| 2   |           |             |           |

## 8. Risks & Open Questions

| Risk / Question | Likelihood | Impact | Mitigation |
| --------------- | ---------- | ------ | ---------- |
|                 |            |        |            |

## 9. Appendix

_Links, references, related issues._

---

_After generating, ask the plan-review subagent to critique this PRD from a Staff Engineer perspective._
