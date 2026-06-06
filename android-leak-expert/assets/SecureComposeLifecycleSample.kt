package com.example.sdk.sample

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.coroutines.flow.StateFlow

/**
 * Compose screen demonstrating leak-free state collection and listener registration.
 */
@Composable
fun SecureComposeScreen(
    stateFlow: StateFlow<String>,
    onBatteryChanged: (isCharging: Boolean) -> Unit
) {
    // 1. collectAsStateWithLifecycle cancels collection when app goes into the background
    val uiState by stateFlow.collectAsStateWithLifecycle()

    // Render screen state
    Text(text = uiState)

    // 2. Register a system listener safely
    SystemBatteryReceiver(onBatteryChanged = onBatteryChanged)
}

/**
 * Custom BroadcastReceiver helper that registers/unregisters symmetrically with composition lifecycle.
 */
@Composable
fun SystemBatteryReceiver(
    onBatteryChanged: (isCharging: Boolean) -> Unit
) {
    val context = LocalContext.current

    // Wrap callback in rememberUpdatedState to ensure the active listener always has the latest logic
    // without triggering DisposableEffect registration/unregistration churn.
    val currentOnBatteryChanged by rememberUpdatedState(onBatteryChanged)

    // Symmetrically register and unregister BroadcastReceiver
    DisposableEffect(context) {
        val filter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context?, intent: Intent?) {
                val status = intent?.getIntExtra("status", -1) ?: -1
                val isCharging = status == 2 || status == 5 // 2: Charging, 5: Full
                currentOnBatteryChanged(isCharging)
            }
        }

        context.registerReceiver(receiver, filter)

        // Tear down hook executed when Composable leaves the UI tree
        onDispose {
            context.unregisterReceiver(receiver)
        }
    }
}
