#!/usr/bin/env python3
"""
Analyze token usage patterns in conversation history or prompts.
Helps identify token-heavy sections for optimization.
"""

import json
import sys
from pathlib import Path


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (1 token ≈ 4 characters for English).
    For accurate counts, use tiktoken library.
    """
    return len(text) // 4


def analyze_file(filepath: str) -> dict:
    """Analyze token usage in a file."""
    path = Path(filepath)

    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    content = path.read_text()
    total_tokens = estimate_tokens(content)

    # Analyze by sections (markdown headers)
    sections = {}
    current_section = "preamble"
    current_content = []

    for line in content.split("\n"):
        if line.startswith("#"):
            # Save previous section
            if current_content:
                sections[current_section] = {
                    "tokens": estimate_tokens("\n".join(current_content)),
                    "lines": len(current_content),
                }
            # Start new section
            current_section = line.strip("#").strip()
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = {
            "tokens": estimate_tokens("\n".join(current_content)),
            "lines": len(current_content),
        }

    # Sort sections by token count
    sorted_sections = sorted(
        sections.items(), key=lambda x: x[1]["tokens"], reverse=True
    )

    return {
        "file": filepath,
        "total_tokens": total_tokens,
        "total_lines": len(content.split("\n")),
        "sections": sorted_sections[:10],  # Top 10 sections
        "recommendations": generate_recommendations(total_tokens, sections),
    }


def generate_recommendations(total_tokens: int, sections: dict) -> list[str]:
    """Generate optimization recommendations."""
    recommendations = []

    if total_tokens > 10000:
        recommendations.append(
            f"⚠️  Large file ({total_tokens} tokens). Consider splitting into modules."
        )

    # Find verbose sections
    for section, data in sections.items():
        if data["tokens"] > 2000:
            recommendations.append(
                f"📝 Section '{section}' is large ({data['tokens']} tokens). "
                f"Consider moving to separate reference file."
            )

    if total_tokens > 5000:
        recommendations.append(
            "💡 Use progressive disclosure: move detailed content to references/"
        )

    if total_tokens < 1000:
        recommendations.append("✅ File size is optimal for context loading")

    return recommendations


def analyze_conversation(messages: list[dict]) -> dict:
    """Analyze token usage in conversation history."""
    total_tokens = 0
    message_analysis = []

    for i, msg in enumerate(messages):
        content = msg.get("content", "")
        tokens = estimate_tokens(content)
        total_tokens += tokens

        message_analysis.append(
            {
                "index": i,
                "role": msg.get("role", "unknown"),
                "tokens": tokens,
                "cumulative": total_tokens,
            }
        )

    # Calculate history tax
    history_tax = []
    for i in range(len(messages)):
        # Each message carries all previous messages
        tax = sum(m["tokens"] for m in message_analysis[: i + 1])
        history_tax.append(tax)

    total_tax = sum(history_tax)

    return {
        "total_messages": len(messages),
        "total_tokens": total_tokens,
        "total_history_tax": total_tax,
        "average_per_message": total_tokens // len(messages) if messages else 0,
        "messages": message_analysis,
        "recommendations": generate_conversation_recommendations(
            len(messages), total_tokens, total_tax
        ),
    }


def generate_conversation_recommendations(
    num_messages: int, total_tokens: int, history_tax: int
) -> list[str]:
    """Generate conversation optimization recommendations."""
    recommendations = []

    if num_messages > 20:
        recommendations.append(
            f"⚠️  Long conversation ({num_messages} messages). "
            f"Consider resetting session."
        )

    if num_messages > 15:
        recommendations.append("💡 Use /compact to summarize conversation history")

    if history_tax > 100000:
        recommendations.append(
            f"🔥 High history tax ({history_tax:,} cumulative tokens). "
            f"Reset conversation immediately."
        )

    avg_per_message = total_tokens // num_messages if num_messages else 0
    if avg_per_message > 2000:
        recommendations.append(
            f"📊 Average message size is high ({avg_per_message} tokens). "
            f"Consider more concise prompts."
        )

    return recommendations


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_token_usage.py <file_or_conversation.json>")
        print("\nAnalyze token usage in files or conversation history.")
        print("\nExamples:")
        print("  python analyze_token_usage.py SKILL.md")
        print("  python analyze_token_usage.py conversation.json")
        sys.exit(1)

    filepath = sys.argv[1]
    path = Path(filepath)

    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # Detect file type
    if path.suffix == ".json":
        # Assume conversation history
        with open(path) as f:
            data = json.load(f)
            messages = data if isinstance(data, list) else data.get("messages", [])

        result = analyze_conversation(messages)

        print(f"\n{'=' * 60}")
        print(f"CONVERSATION ANALYSIS: {filepath}")
        print(f"{'=' * 60}\n")
        print(f"Total Messages: {result['total_messages']}")
        print(f"Total Tokens: {result['total_tokens']:,}")
        print(f"History Tax: {result['total_history_tax']:,}")
        print(f"Average per Message: {result['average_per_message']:,}")

        print(f"\n{'=' * 60}")
        print("RECOMMENDATIONS")
        print(f"{'=' * 60}\n")
        for rec in result["recommendations"]:
            print(f"  {rec}")

        print(f"\n{'=' * 60}")
        print("MESSAGE BREAKDOWN")
        print(f"{'=' * 60}\n")
        for msg in result["messages"][-10:]:  # Last 10 messages
            print(
                f"  [{msg['index']}] {msg['role']:10} "
                f"{msg['tokens']:6,} tokens "
                f"(cumulative: {msg['cumulative']:,})"
            )

    else:
        # Assume text file
        result = analyze_file(filepath)

        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"\n{'=' * 60}")
        print(f"FILE ANALYSIS: {filepath}")
        print(f"{'=' * 60}\n")
        print(f"Total Tokens: {result['total_tokens']:,}")
        print(f"Total Lines: {result['total_lines']:,}")

        print(f"\n{'=' * 60}")
        print("TOP SECTIONS BY TOKEN COUNT")
        print(f"{'=' * 60}\n")
        for section, data in result["sections"]:
            print(f"  {data['tokens']:6,} tokens | {section[:50]}")

        print(f"\n{'=' * 60}")
        print("RECOMMENDATIONS")
        print(f"{'=' * 60}\n")
        for rec in result["recommendations"]:
            print(f"  {rec}")

    print()


if __name__ == "__main__":
    main()
