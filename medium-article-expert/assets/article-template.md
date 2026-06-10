# Article Template & Skeleton

Use this skeleton as a visual guide for formatting.

```markdown
*Kicker: Tag / Series / Publication Name* (Set using small "T" subtitle button)
# Title of the Article (H1, under 12 words, benefit-driven)

![Alt text: Description of the feature image](https://unsplash.com/... or custom URL)
*Photo by [Creator Name](link_to_profile) on [Source](link_to_source) (Attributed)*

The first sentence is short, direct, and under 15 words. No throat-clearing. State the immediate tension or project scope. Use natural contractions (we're, it's, don't) to keep the voice conversational.

This is the second sentence, selling the third. The narrative flow pulls the reader forward down the Slippery Slide. Ensure one core idea per paragraph.

---

## The Unexpected Blocker (H2 Section Heading)

This section begins with the BAB (Before-After-Bridge) or ACT (Attention-Context-Takeaway) framework. Avoid qualify terms like "generally" or "somewhat".

Before writing code, explain in 1–2 sentences what the reader should look for in the snippet:

```kotlin
// Native code block, not a screenshot.
// Keep it between 10-15 lines.
class CacheManager(private val apolloClient: ApolloClient) {
    fun fetchPost(postId: String): Flow<Post> {
        return apolloClient.query(PostQuery(postId))
            .watch() // Key observation point
            .map { it.dataOrThrow }
    }
}
```

After the code block, write a single sentence highlighting the key line or technical decision:
*The watch() extension allows real-time updates to propagate automatically when cache mutations occur.*

---

## Actionable Takeaways (H2 Section Heading)

Avoid repetitive headings. Use three dots or line separators for visual eye relief. Alternate sentence lengths to vary rhythm.

*   **Takeaway One:** The bold description.
*   **Takeaway Two:** The second action item.

---

## Operational Lessons

1.  **Lesson 1:** Explaining a non-obvious engineering insight.
2.  **Lesson 2:** The second insight.

---

## Conclusion & Next Steps

This paragraph does not start with "In conclusion" or summarize what was already written. End on a forward-leaning bet or what this unlocks.

**Resources & CTA (Placed at the absolute bottom of the article)**
*   [GitHub Repository](https://github.com/...)
*   [Join our Newsletter](https://...)
```
