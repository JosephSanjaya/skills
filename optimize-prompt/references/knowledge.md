---
name: knowledge
description: Comprehensive reference on Transformer attention constraints, positional biases, prefix caching, structured decoding, and tokenization fertility
metadata:
  type: reference
---

# Core LLM Mechanics & Prompt Optimization Theory

Comprehensive reference on Transformer constraints, positional biases, caching mechanisms, structured decoding, and tokenization dynamics.

---

## 1. Architectural Constraints of Self-Attention
*   **Softmax Normalization**: Self-attention assigns weights dynamically to all tokens in a sequence. Because attention scores must sum to exactly 1, adding extraneous tokens shrinks the denominator, leading to **Attention Dilution**.
*   **Attention Sinks**: Early tokens (often system prompts or boilerplate) dynamically absorb disproportionately high attention weights, regardless of relevance.
*   **Context Cost**: Non-essential tokens increase:
    *   **Inference Latency**: Autoregressive decoding time.
    *   **VRAM Usage**: Key-Value (KV) cache grows linearly with sequence length.
    *   **Financial Overhead**: API providers charge per token.

---

## 2. Positional Bias & Spatial Dynamics
*   **Lost-in-the-Middle Phenomenon**: Decoder-only and encoder-decoder models show high recall/comprehension at the start (Prism/Primacy bias) and end (Recency bias) of context. Recall degrades drastically in the middle.
*   **Prism Prompting (Suffix-Loading)**: Relocating formatting rules, critical constraints, and the user query to the absolute end of the prompt sequence (adjacent to output generation).
*   **Ms-PoE (Positional Hidden State Scaling)**: Dynamically scales position embeddings within attention heads to recover information in the middle of long sequences without fine-tuning.
*   **Gold Panning Bandits**: Active combinatorial context shuffling framework to dynamically order retrieval results, centering relevant documents in high-attention regions.

---

## 3. Infrastructure Caching & KV Reusability
*   **Semantic Caching**: Checks semantically similar prompts using embedding models. Bypasses LLM execution on high-similarity hits.
*   **Prefix Caching (Input Token Caching)**: Reuses pre-computed KV matrices for identical character/token prefixes. Supported by vLLM, LMCache, etc.
*   **Append-Only Imperative**: To prevent KV cache invalidation, static instructions, system definitions, schemas, and examples must go first. Dynamic, session-specific, or user-specific data must be appended at the absolute end.

---

## 4. Grammar-Based Constrained Decoding
*   **Failure of Natural Language Schemas**: Probabilistic generation frequently produces malformed JSON/XML, missing fields, or conversational noise (96%+ failure rates on complex schemas under zero constraints).
*   **Constrained Sampling (FSM)**: Compiles context-free grammars (CFG) or schemas into a Finite State Machine (FSM). During generation, logits of invalid tokens are masked to $-\infty$.
*   **Outlines & Pydantic**: Allows type-safe, validated schemas to be compiled directly into state machines for guaranteed structural correctness.

---

## 5. Multilingual Tokenization & Low-Resource Languages
*   **Tokenization Fertility**: Number of tokens required to represent a single word. Foundational tokenizers (Byte-Pair, WordPiece, SentencePiece) are biased towards English/code.
*   **Linguistic Degradation**: Low-resource languages are tokenized at the byte or character level. This increases fertility, bloats context, accelerates attention dilution, and inflates API costs.
*   **Mitigation**: Monolingual tokenizer transfer, pre-prompt transliteration, and specialized tokenization algorithms.
