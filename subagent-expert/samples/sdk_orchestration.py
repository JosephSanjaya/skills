#!/usr/bin/env python3
"""Example demonstrating programmatic subagent orchestration using the Claude Agent SDK."""

import asyncio
from typing import AsyncGenerator, Protocol, TypedDict
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query


class AgentProgress(TypedDict):
    """Schema for tracking subagent progress."""

    active_agents: int
    messages_processed: str
    workflow_completion: str
    coordination_efficiency: str


class LogMessage(Protocol):
    """Protocol defining the structure of messages returned by the SDK query stream."""

    @property
    def result(self) -> str:
        """Returns the result string of the message."""
        ...


async def run_orchestration(prompt_text: str) -> AsyncGenerator[str, None]:
    """Orchestrates a parallel security audit using the Claude Agent SDK."""
    options = ClaudeAgentOptions(
        # Pass 'Agent' in allowed_tools to auto-approve subagent spawning
        allowed_tools=["Read", "Grep", "Glob", "Agent"],
        agents={
            "auth-reviewer": AgentDefinition(
                description=(
                    "Expert authentication security auditor. "
                    "Use to scan JWT, sessions, and authorization logic."
                ),
                prompt=(
                    "You are a security auditor. Analyze the target auth files "
                    "and output a structured vulnerability report. Read-only."
                ),
                tools=["Read", "Grep", "Glob"],
                model="sonnet",
            ),
            "dependency-scanner": AgentDefinition(
                description=(
                    "Dependency vulnerability scanner. "
                    "Use to scan lockfiles and manifest files."
                ),
                prompt=(
                    "You are a dependency auditor. Scan manifests and lockfiles "
                    "for outdated or insecure packages. Suggest patch versions."
                ),
                tools=["Read", "Grep", "Glob"],
                model="haiku",
            ),
        },
    )

    # Stream results from the query
    async for message in query(prompt=prompt_text, options=options):
        # Using PEP 695 / Protocol interface to safely print results
        if hasattr(message, "result") and isinstance(message, LogMessage):
            yield message.result


async def main() -> None:
    """Main execution entry point."""
    prompt = (
        "Perform a security audit on our authentication module. "
        "First, use the auth-reviewer to check JWT logic. "
        "Then, use the dependency-scanner to check our manifest lockfiles."
    )

    print("Starting programmatic orchestration...")
    async for chunk in run_orchestration(prompt):
        print(chunk, end="", flush=True)
    print("\nOrchestration completed.")


if __name__ == "__main__":
    asyncio.run(main())
