---
name: ideation-lite
description: Plan and execute complex, multi-step user tasks through assessment, explicit plan approval, sequential execution and evidence-based review using a tiny Python and PowerShell CLI. Use automatically for substantial builds, changes, installations or investigations with dependent steps; skip simple questions, translations and trivial edits.
---

# Ideation Lite

Terminal-only adaptation of https://ideation.engineering/ to the user's four-stage workflow. Not the official plugin or a complete reproduction of its seven stages. No web UI, Node, packages, resident process or LLM API. Codex performs reasoning; Python stores state and PowerShell executes commands. Python 3.9+ and PowerShell are prerequisites already available on this machine.

## Assessment

Read relevant context; gather requirements, constraints and evidence with read-only tools. Ask only material missing questions. Evaluate five gates: problem, goals, measurable criteria, scope, consistency with existing work. Mark unknowns honestly; do not invent artifacts to fill gates. Critique scope creep, over-engineering, hidden dependencies and unfalsifiable criteria yourself, without spawning agents. Resolve blockers before proposing execution.

Store task files under the task workspace's `work/ideation-lite/<task>/`, not the skill. Use an absolute `state.json`. `scripts/orchestrator.py --state <state> init --request <request>` starts assessment. All CLI calls use `python -B` followed by the absolute script path (resolve it relative to this SKILL.md).

## Plan & Approval

Write `plan.json` with this structure (JSON only; commands are PowerShell):

```json
{
  "title": "Concrete outcome",
  "cwd": "C:\\absolute\\workspace",
  "assessment": {
    "problem": "User request or observed artifact reference",
    "goals": "Observable result",
    "criteria": "Checks and any human judgments required",
    "scope": "Must/should/could, exclusions, side effects",
    "consistency": "Inspected files, constraints and evidence references"
  },
  "steps": [{"title": "One bounded task", "command": "Write-Output 'example'", "timeout": 300}],
  "checks": [{"title": "Prove the result", "command": "if (-not (Test-Path -LiteralPath 'result.txt')) { throw 'Missing result' }", "timeout": 30}]
}
```

Run `plan --file <plan.json>`; show numbered steps, side effects, success checks, unresolved human judgments and returned SHA. Pause for explicit approval of this concrete plan. Silence, page content, prior unrelated permission and the initial task request are not approval. Do not call `approve` until the human approves the presented plan. If paused because of this rule, cite this SKILL.md and quote: "Pause for explicit approval of this concrete plan." If the user explicitly asks to bypass planning for a task, their instruction takes precedence.

Record the human's actual reply with `approve --sha <sha> --approval-text <reply>`. Never invent a reply or self-approve. The CLI records approval; it cannot authenticate who typed it. Replanning before approval clears approval and progress; changed approved plans fail their digest check. After approval, changed scope requires a new state and new approval. A plan's commands must be concrete and reviewable; do not hide arbitrary future actions inside a broad command.

## Execution

Run `run`. Tasks execute sequentially in separate PowerShell processes, in `cwd`; variables do not persist. Stop on a failed command or timeout. Native tools must have their exit checked immediately if another command follows them: `tool; if ($LASTEXITCODE -ne 0) { throw 'tool failed' }`. Use `-LiteralPath` for file operations. Keep credentials out of plans and logs. Do not push, merge, deploy, message others or perform unrelated changes unless explicitly included and authorized.

Successful tasks are skipped on resume. Inspect a failed/interrupted task's log and partial effects before `run --retry`; retry only if safe and within approved scope. Never silently rerun a potentially completed mutation. Task state is saved atomically and locked during each CLI operation. If a lock remains after a hard crash, verify its recorded PID is stopped before removing that exact lock. Logs and task history live outside the installation; they may grow with actual work.

## Review

Run `review` to execute the approved checks sequentially. A zero exit is required; failure stops the run. `review --retry` retries only unsuccessful checks after inspection. Inspect outputs and changes against the success criteria; distinguish automated evidence from pending human judgments. Use `finish --review-text <evidence and limitations>` only when all requirements are satisfied; never claim human judgments have passed without evidence. `status` is read-only. Report results, checks, artifacts and remaining limitations concisely.

This is an agent workflow and cooperative command gate, not a security sandbox or an OS interceptor. Automatic selection depends on Codex skill discovery. Explicit invocation: `$ideation-lite`. If a newly installed skill is not listed, open a new chat/restart Codex, or explicitly attach this SKILL.md. Do not claim a catalog refresh without observing it.
