package com.example.compose.samples

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.movableContentOf
import androidx.compose.ui.Modifier

/**
 * Idiomatic Slot API component showing:
 * - Proper parameter ordering (Required -> Modifier -> Optional -> Trailing Content)
 * - Restricting child layout rules via scoped slots (RowScope/ColumnScope)
 * - Proper usage of [movableContentOf] to preserve state across layout changes
 */
@Composable
fun AdaptiveHeaderCard(
    title: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    horizontalAlignment: Boolean = true,
    actionSlot: @Composable (RowScope.() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val rememberedAction = actionSlot?.let {
        remember(it) { movableContentOf { Row { it() } } }
    }

    Surface(modifier = modifier) {
        Column {
            if (horizontalAlignment) {
                Row {
                    rememberedAction?.invoke()
                }
            } else {
                Column {
                    rememberedAction?.invoke()
                }
            }
            content()
        }
    }
}
