---
name: android-amplitude-sdk-expert
description: "Expert guide for Amplitude Android SDK integration (Kotlin/Java). Use when tracking events, configuring autocapture, managing user identity, configuring batching or EU residency, implementing custom Enrichment/Destination plugins, migrating from legacy com.amplitude:android-sdk (com.amplitude.api) to modern com.amplitude:analytics-android (com.amplitude.android), or debugging SDK behavior in Android. Triggers: amplitude, logEvent, amplitude track, identify, revenue, serverZone, minIdLength, migrateLegacyData, AutocaptureOption, AndroidLifecyclePlugin, session replay plugin, com.amplitude:analytics-android."
---

# Android Amplitude SDK Expert

Configure, optimize, and migrate Amplitude SDK in Android applications.

<instructions>
Initialize modern Kotlin SDK once in Application class, configure autocapture options, use Enrichment plugins for scrubbing/sampling, set EU zone for compliance, and migrate legacy SQLite data safely.
</instructions>

## 1. Quick Decision Tree
- **API Reference (Track, Identify, Revenue, Configs)** → [references/api_reference.md](references/api_reference.md)
- **SDK Migration & Identity (Legacy to Modern, Session Management)** → [references/migration_and_identity.md](references/migration_and_identity.md)
- **Scenarios**:
  - *New Android setup* → Use Kotlin SDK initialization ([assets/AmplitudeInitializer.kt](assets/AmplitudeInitializer.kt))
  - *PII Scrubbing / Event Sampling / Event Filters* → Use custom Enrichment Plugin ([assets/CustomEnrichmentPlugin.kt](assets/CustomEnrichmentPlugin.kt))
  - *Session Replay* → Section 5 of [references/api_reference.md](references/api_reference.md#5-session-replay)
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
