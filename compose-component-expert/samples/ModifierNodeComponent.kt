package com.example.compose.samples

import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.ContentDrawScope
import androidx.compose.ui.node.DrawModifierNode
import androidx.compose.ui.node.ModifierNodeElement
import androidx.compose.ui.platform.InspectorInfo

/**
 * Idiomatic Modifier.Node implementation replacing legacy composed {}.
 * Consists of an extension builder, a stateless Element, and a stateful Node.
 */
fun Modifier.highlightBorder(color: Color): Modifier =
    this.then(HighlightBorderElement(color))

private data class HighlightBorderElement(
    val color: Color,
) : ModifierNodeElement<HighlightBorderNode>() {
    override fun create(): HighlightBorderNode = HighlightBorderNode(color)

    override fun update(node: HighlightBorderNode) {
        node.updateColor(color)
    }

    override fun InspectorInfo.inspectableProperties() {
        name = "highlightBorder"
        properties["color"] = color
    }
}

private class HighlightBorderNode(
    private var color: Color,
) : Modifier.Node(), DrawModifierNode {

    fun updateColor(newColor: Color) {
        if (color != newColor) {
            color = newColor
            invalidateDraw() // Request redraw with new color
        }
    }

    override fun ContentDrawScope.draw() {
        // Draw the highlight border
        drawRect(color = color)
        // Draw the actual layout node content
        drawContent()
    }
}
