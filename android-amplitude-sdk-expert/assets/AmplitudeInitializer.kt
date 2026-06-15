package com.example.amplitude

import android.app.Application
import com.amplitude.android.Amplitude
import com.amplitude.android.Configuration
import com.amplitude.common.autocapture.AutocaptureOption
import com.amplitude.android.ServerZone

class AmplitudeInitializer : Application() {

    companion object {
        lateinit var amplitude: Amplitude
            private set
    }

    override fun onCreate() {
        super.onCreate()

        // Idiomatic 2026 Kotlin SDK initialization
        amplitude = Amplitude(
            Configuration(
                apiKey = "YOUR_API_KEY",
                context = applicationContext,
                serverZone = ServerZone.US, // Or ServerZone.EU for EU data residency
                flushQueueSize = 30, // Flush when queue reaches 30 events
                flushIntervalMillis = 30000, // Or every 30 seconds
                useBatch = false, // Set true for high-volume batch endpoint
                optOut = false, // Set true to disable tracking globally
                migrateLegacyData = true, // Auto-migrates from legacy SQLite
                minIdLength = 5, // Min length for userId/deviceId
                autocapture = setOf(
                    AutocaptureOption.SESSIONS,
                    AutocaptureOption.APP_LIFECYCLES,
                    AutocaptureOption.SCREEN_VIEWS,
                    AutocaptureOption.DEEP_LINKS,
                    AutocaptureOption.ELEMENT_INTERACTIONS
                )
            )
        )
    }
}
