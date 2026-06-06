package com.example.sdk.sample

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Message
import androidx.appcompat.app.AppCompatActivity
import java.lang.ref.WeakReference

/**
 * Showcase safe Android Handler implementation without context memory leaks.
 */
class SecureActivity : AppCompatActivity() {

    // Safe instance of Handler
    private val safeHandler = IncomingHandler(this)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Post a delayed message (leaky in standard inner classes, safe here)
        val msg = Message.obtain().apply { what = MSG_UPDATE_UI }
        safeHandler.sendMessageDelayed(msg, 10000L) // 10s delay
    }

    override fun onDestroy() {
        // Deterministic Teardown: clear all pending messages/callbacks in the message queue
        safeHandler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    // Static nested class in Kotlin (no 'inner' keyword) does not hold implicit reference to outer class
    private class IncomingHandler(activity: SecureActivity) : Handler(Looper.getMainLooper()) {
        
        // Wrap activity context in WeakReference to allow garbage collection if activity is destroyed
        private val weakActivity = WeakReference(activity)

        override fun handleMessage(msg: Message) {
            val activity = weakActivity.get()
            
            // Validate context is still alive before updating UI
            if (activity != null && !activity.isFinishing && !activity.isDestroyed) {
                when (msg.what) {
                    MSG_UPDATE_UI -> {
                        // Execute UI updates safely
                        activity.updateUserInterface()
                    }
                }
            }
        }
    }

    private fun updateUserInterface() {
        // UI updates here
    }

    companion object {
        private const val MSG_UPDATE_UI = 1
    }
}
