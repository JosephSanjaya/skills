package com.example.compose.samples

import androidx.compose.foundation.style.Style
import androidx.compose.foundation.style.background
import androidx.compose.foundation.style.border
import androidx.compose.foundation.style.shape
import androidx.compose.foundation.style.styleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.style.rememberStyleState

/**
 * Showcase of Compose 1.11+ experimental Style API.
 * Moves visual styling out of composition phase into layout/draw.
 */
@Composable
fun StyledButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val styleState = rememberStyleState()
    Button(
        onClick = onClick,
        modifier = modifier.styleable(styleState = styleState, style = BUTTON_STYLE),
    ) {
        Text("Click Me")
    }
}

private val BUTTON_STYLE = Style {
    background(Color(0xFF6200EE))
    border(1.dp, Color(0xFF3700B3))
    shape(RoundedCornerShape(4.dp))
    
    hovered(Style {
        animate(Style {
            background(Color(0xFF7F39FB))
        })
    })
    
    pressed(Style {
        animate(Style {
            background(Color(0xFF3700B3))
        })
    })
}
