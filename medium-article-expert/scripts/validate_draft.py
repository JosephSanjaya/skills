#!/usr/bin/env python3
import sys
import os
import re

# Banned lists of words/phrases (AI slop indicators)
BANNED_WORDS = {
    "verbs": [
        "delve", "delving", "leverage", "utilize", "facilitate", 
        "elucidate", "ascertain", "endeavor", "commence", "underscore"
    ],
    "adjectives": [
        "transformative", "groundbreaking", "revolutionary", "seamless", 
        "robust", "cutting-edge", "comprehensive", "nuanced", "holistic", 
        "pivotal", "commendable"
    ],
    "nouns": [
        "tapestry", "realm", "landscape", "ecosystem", "testament", 
        "journey", "paradigm shift"
    ],
    "transitions": [
        "furthermore", "moreover", "additionally", "consequently", 
        "indeed", "in conclusion", "ultimately", "in summary", "overall"
    ],
    "phrases": [
        "it's worth noting that", "it goes without saying", "at the end of the day", 
        "moving forward", "in today's fast-paced world", "honest(ly)?", 
        "here's the breakdown", "let me be direct", "here's what nobody tells you"
    ]
}

QUALIFIERS = [
    "a bit", "sort of", "generally", "probably", "somewhat", 
    "in a sense", "a little bit", "kind of", "fairly", "rather", "quite"
]

EMPTY_CLOSERS = [
    r"\bultimately\b", r"\bin conclusion\b", r"\boverall\b", 
    r"\bin summary\b", r"\bby understanding these\b", r"\bby leveraging these\b"
]

def analyze_file(file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
        
    print(f"Analyzing {os.path.basename(file_path)}...")
    print("=" * 60)
    
    issues_found = 0
    
    # 1. Banned words check
    print("\n[1] Checking Banned Words (AI Slop)...")
    content_lower = content.lower()
    for cat, words in BANNED_WORDS.items():
        found_in_cat = []
        for word in words:
            # Use word boundaries for words, but literal check for phrases
            pattern = rf"\b{word}\b" if " " in word or cat == "phrases" else rf"\b{word}s?\b"
            matches = re.findall(pattern, content_lower)
            if matches:
                found_in_cat.append(f"'{word}' (x{len(matches)})")
                issues_found += len(matches)
        if found_in_cat:
            print(f"  ✗ Found banned {cat}: {', '.join(found_in_cat)}")
        else:
            print(f"  ✓ No banned {cat} found.")

    # 2. Qualifiers check
    print("\n[2] Checking Qualifiers...")
    found_qualifiers = []
    for qual in QUALIFIERS:
        pattern = rf"\b{qual}\b"
        matches = re.findall(pattern, content_lower)
        if matches:
            found_qualifiers.append(f"'{qual}' (x{len(matches)})")
            issues_found += len(matches)
    if found_qualifiers:
        print(f"  ✗ Found qualifiers: {', '.join(found_qualifiers)}")
    else:
        print(f"  ✓ No qualifiers found.")

    # 3. Empty Closers at Paragraph End
    print("\n[3] Checking Empty Closers...")
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    found_closers = 0
    for idx, p in enumerate(paragraphs):
        lines = p.splitlines()
        if not lines:
            continue
        last_line = lines[-1].strip().lower()
        for pattern in EMPTY_CLOSERS:
            if re.search(pattern, last_line):
                # Print snippet
                print(f"  ✗ Paragraph {idx+1} ends with empty closer matching '{pattern}':")
                print(f"    Snippet: \"... {lines[-1][-50:]}\"")
                found_closers += 1
                issues_found += 1
    if found_closers == 0:
        print("  ✓ No empty paragraph closers found.")

    # 4. Semicolons check
    print("\n[4] Checking Semicolons...")
    semicolon_count = content.count(";")
    if semicolon_count > 0:
        print(f"  ✗ Found {semicolon_count} semicolons. Replace with periods/shorter sentences.")
        issues_found += semicolon_count
    else:
        print("  ✓ No semicolons found.")

    # 5. Punctuation placements
    print("\n[5] Checking Punctuation Rules...")
    # Commas or periods outside quotation marks (e.g. ", or ". instead of ," or .")
    # Matches word/punctuation followed by quotation mark and then comma or period
    outside_pattern = re.compile(r'["\'][\.,]')
    inside_wrong_pattern = re.compile(r'[\.,]["\']') # Correct in US, check for opposite to warn
    # Let's search for space before colons (e.g. "term : definition")
    space_colon_matches = re.findall(r'\s+:', content)
    
    punctuation_issues = 0
    if space_colon_matches:
        print(f"  ✗ Found {len(space_colon_matches)} instances of space before colons (e.g., 'word :').")
        punctuation_issues += len(space_colon_matches)
        issues_found += len(space_colon_matches)
        
    # Quotation rules: we prefer punctuation inside quotes (e.g., ." or ,")
    outside_matches = re.findall(r'(\w+["\'][\.,])', content)
    if outside_matches:
        print(f"  ✗ Found {len(outside_matches)} instances of punctuation outside quotation marks (e.g., {', '.join(outside_matches[:5])}).")
        punctuation_issues += len(outside_matches)
        issues_found += len(outside_matches)
        
    if punctuation_issues == 0:
        print("  ✓ Punctuation looks correct.")

    # 6. Sentence Rhythm Analysis (Consecutive same-length sentences)
    print("\n[6] Checking Sentence Rhythm Variation...")
    # Split paragraphs and sentences
    sentence_pattern = re.compile(r'[^.!?]+[.!?]')
    rhythm_issues = 0
    for idx, p in enumerate(paragraphs):
        # Skip markdown structural blocks (tables, code, lists)
        if p.startswith("|") or p.startswith("```") or p.startswith("-") or p.startswith("*") or p.startswith("#"):
            continue
            
        sentences = sentence_pattern.findall(p)
        if len(sentences) < 3:
            continue
            
        lengths = []
        for s in sentences:
            words = [w for w in s.strip().split() if w.isalnum()]
            lengths.append(len(words))
            
        # Check for 3 consecutive sentences of similar length (e.g., diff <= 3)
        for i in range(len(lengths) - 2):
            len1, len2, len3 = lengths[i], lengths[i+1], lengths[i+2]
            # Symmetrical medium range check (e.g. all 7-13 words)
            if (7 <= len1 <= 13) and (7 <= len2 <= 13) and (7 <= len3 <= 13):
                print(f"  ✗ Paragraph {idx+1} has 3 consecutive flat medium-length sentences: {len1}, {len2}, {len3} words.")
                rhythm_issues += 1
                issues_found += 1
                break
            # Or all long sentences (e.g., 22+ words)
            elif len1 >= 22 and len2 >= 22 and len3 >= 22:
                print(f"  ✗ Paragraph {idx+1} has 3 consecutive long sentences: {len1}, {len2}, {len3} words.")
                rhythm_issues += 1
                issues_found += 1
                break
                
    if rhythm_issues == 0:
        print("  ✓ Sentence rhythm variation looks healthy.")

    print("=" * 60)
    if issues_found > 0:
        print(f"ANALYSIS COMPLETE: Found {issues_found} issues that need addressing.")
    else:
        print("ANALYSIS COMPLETE: Perfect! No issues found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_draft.py <path_to_draft.md>")
        sys.exit(1)
    analyze_file(sys.argv[1])
