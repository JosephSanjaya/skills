#!/usr/bin/env python3
"""
Compress prompts using various techniques:
- Remove filler words
- Symbolic shorthand conversion
- Whitespace optimization
"""

import sys
import re
from pathlib import Path
from typing import Dict, List

# Filler words to remove
FILLER_WORDS = {
    'please', 'kindly', 'certainly', 'absolutely', 'definitely',
    'basically', 'actually', 'literally', 'really', 'very',
    'just', 'simply', 'quite', 'rather', 'somewhat',
    'perhaps', 'maybe', 'possibly', 'probably'
}

# Verbose phrases and their concise replacements
PHRASE_REPLACEMENTS = {
    r'\bI would like you to\b': '',
    r'\bCould you please\b': '',
    r'\bI need you to\b': '',
    r'\bPlease help me\b': '',
    r'\bI want you to\b': '',
    r'\bin order to\b': 'to',
    r'\bdue to the fact that\b': 'because',
    r'\bfor the purpose of\b': 'for',
    r'\bat this point in time\b': 'now',
    r'\bin the event that\b': 'if',
    r'\bwith regard to\b': 'regarding',
    r'\bin spite of the fact that\b': 'although',
    r'\buntil such time as\b': 'until',
}

# LTL-style symbolic replacements
SYMBOLIC_REPLACEMENTS = {
    r'\bCreate a new\b': '!new',
    r'\bImplement\b': '!impl',
    r'\bRefactor\b': '!refactor',
    r'\bOptimize\b': '!optimize',
    r'\bFix the bug\b': '!fix',
    r'\bAdd tests\b': '#test',
    r'\bTypeScript\b': '#ts',
    r'\bJavaScript\b': '#js',
    r'\bPython\b': '#py',
    r'\baccessibility\b': '#a11y',
    r'\bperformance\b': '#perf',
    r'\bsecurity\b': '#sec',
}

def remove_filler_words(text: str) -> str:
    """Remove common filler words."""
    words = text.split()
    filtered = [w for w in words if w.lower() not in FILLER_WORDS]
    return ' '.join(filtered)

def replace_verbose_phrases(text: str) -> str:
    """Replace verbose phrases with concise alternatives."""
    for pattern, replacement in PHRASE_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def apply_symbolic_shorthand(text: str, aggressive: bool = False) -> str:
    """Apply symbolic shorthand replacements."""
    if not aggressive:
        return text
    
    for pattern, replacement in SYMBOLIC_REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def optimize_whitespace(text: str) -> str:
    """Optimize whitespace without losing readability."""
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    # Remove spaces around punctuation
    text = re.sub(r' ([.,;:!?])', r'\1', text)
    # Remove multiple newlines (keep max 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing whitespace
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    return text.strip()

def remove_pleasantries(text: str) -> str:
    """Remove conversational pleasantries (Caveman mode)."""
    pleasantries = [
        r"I hope this helps!?",
        r"Let me know if you (?:need|have) .*",
        r"Feel free to .*",
        r"Don't hesitate to .*",
        r"I'd be happy to .*",
        r"Certainly!?",
        r"Absolutely!?",
        r"Sure thing!?",
        r"No problem!?",
        r"You're welcome!?",
    ]
    
    for pattern in pleasantries:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text

def compress_prompt(
    text: str,
    remove_fillers: bool = True,
    concise_phrases: bool = True,
    symbolic: bool = False,
    caveman: bool = False,
    optimize_ws: bool = True
) -> Dict:
    """
    Compress prompt using specified techniques.
    
    Returns dict with original, compressed text, and stats.
    """
    original = text
    original_tokens = len(original) // 4  # Rough estimate
    
    if remove_fillers:
        text = remove_filler_words(text)
    
    if concise_phrases:
        text = replace_verbose_phrases(text)
    
    if symbolic:
        text = apply_symbolic_shorthand(text, aggressive=True)
    
    if caveman:
        text = remove_pleasantries(text)
    
    if optimize_ws:
        text = optimize_whitespace(text)
    
    compressed_tokens = len(text) // 4
    reduction = ((original_tokens - compressed_tokens) / original_tokens * 100) if original_tokens > 0 else 0
    
    return {
        "original": original,
        "compressed": text,
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "reduction_percent": reduction,
        "techniques": {
            "remove_fillers": remove_fillers,
            "concise_phrases": concise_phrases,
            "symbolic": symbolic,
            "caveman": caveman,
            "optimize_whitespace": optimize_ws
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python compress_prompt.py <file_or_text> [options]")
        print("\nOptions:")
        print("  --no-fillers      Don't remove filler words")
        print("  --no-phrases      Don't replace verbose phrases")
        print("  --symbolic        Apply symbolic shorthand (LTL-style)")
        print("  --caveman         Remove pleasantries (Caveman mode)")
        print("  --no-whitespace   Don't optimize whitespace")
        print("\nExamples:")
        print("  python compress_prompt.py prompt.txt")
        print("  python compress_prompt.py prompt.txt --symbolic --caveman")
        print('  python compress_prompt.py "Please create a new function"')
        sys.exit(1)
    
    # Parse arguments
    input_text = sys.argv[1]
    remove_fillers = "--no-fillers" not in sys.argv
    concise_phrases = "--no-phrases" not in sys.argv
    symbolic = "--symbolic" in sys.argv
    caveman = "--caveman" in sys.argv
    optimize_ws = "--no-whitespace" not in sys.argv
    
    # Read input
    path = Path(input_text)
    if path.exists():
        text = path.read_text()
    else:
        text = input_text
    
    # Compress
    result = compress_prompt(
        text,
        remove_fillers=remove_fillers,
        concise_phrases=concise_phrases,
        symbolic=symbolic,
        caveman=caveman,
        optimize_ws=optimize_ws
    )
    
    # Output results
    print(f"\n{'='*60}")
    print("PROMPT COMPRESSION RESULTS")
    print(f"{'='*60}\n")
    print(f"Original Tokens:    {result['original_tokens']:,}")
    print(f"Compressed Tokens:  {result['compressed_tokens']:,}")
    print(f"Reduction:          {result['reduction_percent']:.1f}%")
    
    print(f"\n{'='*60}")
    print("TECHNIQUES APPLIED")
    print(f"{'='*60}\n")
    for technique, enabled in result['techniques'].items():
        status = "✓" if enabled else "✗"
        print(f"  {status} {technique.replace('_', ' ').title()}")
    
    print(f"\n{'='*60}")
    print("ORIGINAL")
    print(f"{'='*60}\n")
    print(result['original'][:500])
    if len(result['original']) > 500:
        print("\n... (truncated)")
    
    print(f"\n{'='*60}")
    print("COMPRESSED")
    print(f"{'='*60}\n")
    print(result['compressed'])
    print()

if __name__ == "__main__":
    main()
