# Root Cause Analysis Protocol

## When to Activate RCA Mode

Trigger on: production bug, unexpected regression, repeated failure pattern, "why did X break", incident investigation, postmortem prep.

---

## Phase 0: Bias-Check Before Starting

Before touching code or logs, explicitly state your current hypothesis and run it through:

| Bias | Trap | Counter |
|------|------|---------|
| **Anchoring** | First error message = root cause | Force ≥2 alternative failure vectors before committing |
| **Confirmation** | Only read logs that support hypothesis | Actively search for disconfirming evidence |
| **Hyperbolic discounting** | Quick hotfix to unblock CI | Ask: "does this fix root cause or defer it?" |
| **Cargo cult** | "We've always handled it this way" | Verify assumption still holds against current code |

Write hypothesis explicitly: `HYPOTHESIS: [component] fails because [mechanism]`. Do not proceed until you have at least one alternative hypothesis.

---

## Phase 1: History Mining (No Bisect)

### Pickaxe Search — Find When Change Was Introduced

```bash
# Track when literal string count changed (add/remove)
git log -S "symbolName" --oneline -- path/to/dir

# Track any commit whose diff matches a pattern (more precise)
git log -G "pattern|regex" --oneline -p -- src/

# Find commits by message keyword (ticket, refactor description)
git log --grep="TICKET-123" --grep="alias" --all-match --oneline

# Combine: find change to specific symbol in specific path
git log -S "userAlias" --oneline -- app/src/main/
```

Use `-S` first (faster). Switch to `-G` when refactor preserves name but changes internal structure.

### Reconstruct Blame Chain

```bash
# Who last touched each line in a function
git blame -L <start>,<end> path/to/file

# Full context: blame + surrounding commits
git log --follow -p -- path/to/file | head -200
```

---

## Phase 2: 5 Whys Investigation

Rule: each "why" must be answered with **verifiable evidence** (log line, test, code reference).

**Template:**

| Level | Question | Answer | Evidence |
|-------|----------|--------|----------|
| Why 1 | Why did symptom occur? | | log/metric ref |
| Why 2 | Why did cause 1 happen? | | code ref |
| Why 3 | Why did cause 2 happen? | | test/config ref |
| Why 4 | Why did cause 3 happen? | | PR/commit ref |
| Why 5 | What process gap enabled this? | | process doc |

Stop when you reach a process gap (missing test, missing validation, architectural boundary violation). That's the fix target.

**Specificity rule:** Problem statement must include: what broke, when, on which device/environment, observed vs expected value. Vague = wrong root cause.

---

## Phase 3: Structural Failure Pattern Matching

Match observed failure against known patterns before writing fix:

| Pattern | Signal | Investigation |
|---------|--------|---------------|
| **Tribal knowledge erosion** | Works for one team, fails after handoff | Check ADRs, README, ArchUnit tests — does rule exist anywhere? |
| **Architectural drift** | Works in isolation, fails integrated | Run `rg "*Adapter\|*Mapper"` at boundaries — is translation layer present? |
| **Cargo cult guard** | Code checks condition that no longer applies | `git log -S "condition"` → find origin commit → verify constraint still valid |
| **State mutation race** | Flaky under load, consistent in isolation | Find dirty-row flags or transactional boundaries; check watchdog health |
| **Regression from refactor** | Broke after rename/move, not logic change | `-G "old_pattern"` across affected paths |

---

## Phase 4: Fix Classification

Before implementing, classify fix:

| Class | Definition | Action |
|-------|-----------|--------|
| **Symptomatic** | Stops error, doesn't fix root cause | Flag as tech debt, create follow-up ticket |
| **Causal** | Fixes the Why-3/4 level cause | Preferred — implement now |
| **Systemic** | Fixes the Why-5 process gap | Architectural: ArchUnit test, ADR, or pipeline gate |

Never ship only a symptomatic fix without a systemic ticket.

---

## Phase 5: Postmortem (for Production Incidents)

**Triggers:** user-visible downtime, data corruption, manual prod intervention, monitoring missed the alert.

**Blameless rule:** describe *what happened* and *how decisions were made*, not *who did what*. Use "how" questions before "why" — avoids accusatory framing.

**Agenda (90 min max):**
1. Action item review (10 min) — verify previous postmortem tickets
2. Timeline walkthrough (30 min) — reconstruct with logs + metrics
3. Core analysis (30 min) — 5 Whys → systemic root cause
4. Action items (20 min) — max 3 tickets, scheduled for next sprint

**Three-rule postmortem policy:**
1. Max 3 action items — if can't narrow, root cause not found
2. All items → tickets → next sprint (not backlog)
3. Every postmortem starts with prior action item review

Store postmortem in `docs/postmortems/YYYY-MM-DD-incident-title.md`.

---

## RCA Output Format

```markdown
## Incident: [title]

**Symptom:** [observed behavior, device/env, when]
**Hypothesis 1:** [mechanism] — [status: confirmed/refuted]
**Hypothesis 2:** [mechanism] — [status: confirmed/refuted]

### 5 Whys
| Why | Answer | Evidence |
|-----|--------|----------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 (process gap) | | |

### Fix Classification
- Symptomatic fix: [description] — ticket: [link]
- Causal fix: [description]
- Systemic fix: [ArchUnit rule / ADR / gate]

### Timeline (postmortem only)
[chronological log entries]
```

---

## Integration with Architecture Recovery

During Phase 2 (Dynamic Tracing) of context gathering, if anomaly found:
1. Switch to RCA Phase 1 (history mining) for that component
2. Run 5 Whys before concluding "broken by design"
3. Add `"rca_note"` field to `architecture.json` component entry
4. Mark component `"verified": false` until causal fix confirmed
