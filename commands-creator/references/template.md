# Command template + frontmatter reference

## Canonical skeleton

Copy, then delete every optional line that does not apply. Order of blocks is fixed so all commands read alike.

```markdown
---
description: <Verb-first, what + when, ≤200 chars>
argument-hint: "<required> [optional]"          # only if body reads $ARGUMENTS/$N
allowed-tools: Bash(git diff *), Bash(git log *) # only if !`cmd` injection or pre-approval needed
disable-model-invocation: true                   # only if side effects (push, deploy, send, delete)
---

<context>
- Branch: !`git branch --show-current`
- Changes: !`git diff --stat HEAD`
</context>

<instructions>
Goal: <one sentence outcome>.
Input: $ARGUMENTS = <shape>. Empty → <default | ask once>.
Skills: invoke Skill `<name>` for <sub-task>. Missing → do inline.
Scope: <what NOT to touch>.
</instructions>

<step id="1" label="<Gather>">
<1-4 imperative lines>
</step>

<step id="2" label="<Act>">
...
</step>

<step id="3" label="<Verify>">
<concrete check: command to run, condition to confirm>
</step>

<output>
<exact shape of final reply: sections, table columns, or file path + summary>
</output>
```

Drop `<context>` when nothing is worth pre-injecting. Steps: 3–6. Each step ≤5 lines.

## Frontmatter fields (command files in `.claude/commands/`)

Claude Code silently ignores unknown or misspelled fields, so stick to this list. `name` and `paths` are skill-only; a command's name is its filename (subdir = namespace shown in `/help`, not part of the name).

| Field | Use |
|---|---|
| `description` | Shown in `/` menu; also how Claude decides to auto-run it. Recommended always. |
| `when_to_use` | Extra trigger phrases, appended to description. |
| `argument-hint` | Autocomplete hint, e.g. `"[issue-number] [--draft]"`. Quote it (brackets are YAML). |
| `arguments` | Named positionals, e.g. `arguments: file format` → `$file`, `$format`. |
| `allowed-tools` | Tools pre-approved for this turn. Required for `!`cmd`` injection. Scope narrowly: `Bash(gh pr *)`. |
| `disable-model-invocation` | `true` = only the user can run it. Use for anything with side effects. |
| `model` | Pin model (e.g. `claude-haiku-4-5-20251001` for cheap mechanical commands). |
| `effort` | Reasoning effort override. |
| `context: fork` + `agent` | Run in a subagent (e.g. `agent: Explore` for read-only research); keeps main context clean. |
| `hooks` | Command-scoped hooks. Rare. |

## Argument substitution

- `$ARGUMENTS` — whole string.
- `$ARGUMENTS[0]` / `$0`, `$1` … — space-split positionals.
- `@path/to/file` in body — inlines file content.
- `!`cmd`` or a ```` ```! ```` fenced block — runs before Claude sees the prompt; output replaces it.

## Patterns worth copying

- **Parse-then-branch input**: `Input: $ARGUMENTS = mr=<url> | mr=<iid> project=<path>. Parse first.`
- **Parallel gather**: `<step id="1" parallel="true">` + "Call in one message: A, B, C".
- **Hard stop**: `If <precondition fails>: report <X> and stop.` Fail fast beats guessing.
- **Scope fence**: "Only changed lines. Do not audit unrelated code."
