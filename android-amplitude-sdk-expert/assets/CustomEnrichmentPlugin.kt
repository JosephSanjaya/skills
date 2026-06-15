package com.example.amplitude

import com.amplitude.core.Amplitude
import com.amplitude.core.events.BaseEvent
import com.amplitude.core.platform.Plugin

class CustomEnrichmentPlugin : Plugin {
    override val type: Plugin.Type = Plugin.Type.Enrichment
    override lateinit var amplitude: Amplitude

    override fun execute(event: BaseEvent): BaseEvent? {
        // 1. Event Filtering / Sampling: Drop specific events by returning null
        if (event.eventType == "SensitiveTemporaryEvent") {
            return null
        }

        // 2. PII Scrubbing: Remove sensitive data before upload
        event.eventProperties?.let { props ->
            if (props.containsKey("email")) {
                val mutableProps = props.toMutableMap()
                mutableProps.remove("email")
                event.eventProperties = mutableProps
            }
        }

        // 3. Enrichment: Append dynamic context or global properties
        if (event.eventProperties == null) {
            event.eventProperties = mutableMapOf()
        }
        val properties = event.eventProperties?.toMutableMap() ?: mutableMapOf()
        properties["custom_global_attribute"] = "verified_value"
        event.eventProperties = properties

        return event
    }
}
