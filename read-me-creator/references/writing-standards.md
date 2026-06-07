# Writing Standards Reference

## Google Standard
- One idea per sentence; split compound sentences
- Remove filler: "at this point in time" → "now", "is able to" → "can", "in order to" → "to"
- Active voice; present tense for instructions
- Define acronyms on first use

## Microsoft Standard
- Warm but crisp; everyday words, not less technical
- Focus on user intent before writing
- Call out frustrating steps honestly
- No ALL CAPS text (screen reader reads individual letters)

## Formatting Conventions

| Element | Format | Example |
|---------|--------|---------|
| Commands | backticks | `npm install` |
| UI elements | **bold** | Select **Save** |
| File names | backticks | `config.json` |
| Key combos | **bold + plus** | **Ctrl+Alt+Del** |
| Placeholders | angle brackets | `<version>` |
| Env vars | ALL_CAPS backticks | `DATABASE_URL` |

## Anti-Patterns to Avoid
- "simply", "easily", "just" — patronizing
- "Hello World" examples — demonstrate real value instead
- Color as sole meaning carrier — add `*` or text indicator
- Step count >12 in a single doc — split to linked doc
- Passive voice in instructions: "the user should" → "you"
- Missing prerequisites ("silent blockers")

## Accessibility
- Alt-text: describe intent + context, not just content; <125 chars
- Don't start alt-text with "image of" or "picture of"
- High contrast: black on white preferred
- Structural headings H1→H2→H3 (never skip levels)
