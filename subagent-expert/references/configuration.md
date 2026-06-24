# Subagent Configuration, SDKs, & Parameters

Configure subagents for strict isolation and least-privilege tool access.

## 1. Deployment Methods

### A. Filesystem-Based (Project or Global)
Save as Markdown file with YAML frontmatter in `.claude/agents/*.md` (project) or `~/.claude/agents/*.md` (global).
```markdown
---
name: security-auditor
description: "Audits codebase for security issues. Triggers: security audit, check vulnerabilities."
tools: Read, Glob, Grep
model: sonnet
isolation: worktree
maxTurns: 10
---
You are a senior security auditor. Scan target files for OWASP Top 10 issues.
```

### B. Programmatic SDK Definitions (2026 Latest APIs)
Define programmatically inside parent agent script. Pass `Agent` in `allowedTools` to auto-approve subagent spawning.

#### Python SDK
`pip install claude-agent-sdk`
```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    async for message in query(
        prompt="Audit auth module",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Agent"],
            agents={
                "security-auditor": AgentDefinition(
                    description="Expert security reviewer. Triggers on vulnerability checks.",
                    prompt="Scan code for security flaws.",
                    tools=["Read", "Grep", "Glob"],
                    model="sonnet"
                )
            }
        )
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

#### TypeScript SDK
`npm install @anthropic-ai/claude-agent-sdk`
```typescript
import { query } from "@anthropic-ai/claude-agent-sdk";

async function main() {
    for await (const message of query({
        prompt: "Audit auth module",
        options: {
            allowedTools: ["Read", "Grep", "Glob", "Agent"],
            agents: {
                "security-auditor": {
                    description: "Expert security reviewer. Triggers on vulnerability checks.",
                    prompt: "Scan code for security flaws.",
                    tools: ["Read", "Grep", "Glob"],
                    model: "sonnet"
                }
            }
        }
    })) {
        if ("result" in message) console.log(message.result);
    }
}
main();
```

### C. CLI Temporary Overrides
Pass JSON to CLI using `--agents` flag:
```bash
claude --agents '{"quick-auditor": {"description": "Quick audit.", "prompt": "Audit style.", "tools": ["Read"], "model": "haiku"}}'
```

## 2. Precedence Hierarchy

Model resolution and configuration priority:
1. **Environment Override**: `CLAUDE_CODE_SUBAGENT_MODEL` env var.
2. **Invocation Overrides**: Parameters passed at runtime via API/CLI.
3. **YAML Frontmatter / SDK object**: Properties declared in the configuration.
4. **Parent Context**: Inherited from the calling parent session.

## 3. Configuration Parameters Reference

| Field | Type | Options / Constraints |
| :--- | :--- | :--- |
| `name` | string | Lowercase-kebab-case. Unique. |
| `description` | string | Action-oriented trigger prompt. Very critical for auto-selection. |
| `tools` | array | Least-privilege allowlist. If omitted, inherits all parent tools. |
| `disallowedTools` | array | Specifically blocked tools (e.g. `Edit`, `Write`, `Bash`). |
| `model` | string | `opus` (reasoning), `sonnet` (coding), `haiku` (fast/docs), `inherit` (default). |
| `isolation` | string | `worktree` (spawns in temp git worktree to prevent conflicts), `none` (default). |
| `permissionMode` | string | `auto` (auto-classify), `default` (prompt user), `acceptEdits` (auto-write), `dontAsk` (auto-deny on prompt), `bypassPermissions` (dangerous, skips confirmation). |
| `maxTurns` | number | Hard turn limit. Critical to prevent infinite loops (recommend `10-15`). |
| `background` | boolean | `true` runs as non-blocking background task. |
| `memory` | string | `project` (persist project insight), `user` (global user), `local`, `None`. |
