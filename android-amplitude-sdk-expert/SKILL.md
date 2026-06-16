---
name: android-amplitude-sdk-expert
description: "Expert guide for Amplitude Android SDK integration (Kotlin/Java). Use when tracking events, configuring autocapture, managing user identity, configuring batching or EU residency, implementing custom Enrichment/Destination plugins, migrating from legacy com.amplitude:android-sdk to modern com.amplitude:analytics-android, setting up Session Replay (plugin/middleware/standalone), configuring privacy masking, or debugging SDK behavior in Android. Always use this skill for any Amplitude Android question — even if not explicitly about SDK setup. Triggers: amplitude, logEvent, track, identify, revenue, serverZone, minIdLength, migrateLegacyData, AutocaptureOption, session replay, SessionReplayPlugin, SessionReplayMiddleware, maskLevel, sampleRate, amp-mask, amp-block, com.amplitude:analytics-android."
---

# Android Amplitude SDK Expert

Configure, optimize, and migrate Amplitude SDK in Android applications.

<instructions>
Initialize modern Kotlin SDK once in Application class, configure autocapture options, use Enrichment plugins for scrubbing/sampling, set EU zone for compliance, migrate legacy SQLite data safely, and wire Session Replay via Plugin (modern SDK), Middleware (legacy SDK), or Standalone (third-party analytics).
</instructions>

## 1. Quick Decision Tree
- **API Reference (Track, Identify, Revenue, Configs)** → [references/api_reference.md](references/api_reference.md)
- **SDK Migration & Identity (Legacy to Modern, Session Management)** → [references/migration_and_identity.md](references/migration_and_identity.md)
- **Scenarios**:
  - *New Android setup* → Use Kotlin SDK initialization ([assets/AmplitudeInitializer.kt](assets/AmplitudeInitializer.kt))
  - *PII Scrubbing / Event Sampling / Event Filters* → Use custom Enrichment Plugin ([assets/CustomEnrichmentPlugin.kt](assets/CustomEnrichmentPlugin.kt))
  - *Session Replay (any variant)* → [references/api_reference.md § 5](references/api_reference.md) — Plugin (5a) / Middleware (5b) / Standalone (5c) / Privacy (5 Privacy)
  - *Legacy code scan* → Run validation script (`scripts/validate_amplitude.py`)

## 2. Fast Command Tools
Scan codebase for legacy calls, blocking code, short IDs, or incorrect properties:
```bash
python3 scripts/validate_amplitude.py <path_to_scan>
```

## 3. Clean Code Reference Implementations
- **Idiomatic SDK Initializer**: [AmplitudeInitializer.kt](assets/AmplitudeInitializer.kt)
- **PII / Filter Plugin**: [CustomEnrichmentPlugin.kt](assets/CustomEnrichmentPlugin.kt)

<constraints>
Use com.amplitude:analytics-android for new apps. Direct-boot services must not initialize SDK. All calls are main-thread safe. ID values (user/device) must be >= 5 chars unless minIdLength set. Format output using clear, concise markdown hierarchy.
</constraints>
