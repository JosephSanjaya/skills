package com.example.agent.tools

import ai.koog.agents.core.tools.ToolRegistry
import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.core.tools.reflect.ToolSet
import ai.koog.agents.core.tools.reflect.asTools

interface OrderRepository {
    fun find(orderId: String): OrderData?
    fun updateAddress(orderId: String, address: String): Boolean
}

data class OrderData(val status: String, val trackingNumber: String)

@LLMDescription("Enterprise order tools")
class OrderTools(private val orders: OrderRepository) : ToolSet {

    @Tool
    @LLMDescription("Real-time shipping status and tracking for one order")
    fun getOrderStatus(
        @LLMDescription("10-character alphanumeric order id") orderId: String,
    ): String {
        val order = orders.find(orderId) ?: return "Order $orderId not found"
        return "Order $orderId: ${order.status}. Tracking ${order.trackingNumber}"
    }

    @Tool
    @LLMDescription("Update delivery address only if the order is not yet shipped")
    fun updateDeliveryAddress(
        @LLMDescription("10-character alphanumeric order id") orderId: String,
        @LLMDescription("Full street address including city and postal code") newAddress: String,
    ): String {
        val ok = orders.updateAddress(orderId, newAddress)
        return if (ok) "Address updated for $orderId" else "Cannot update $orderId (shipped or locked)"
    }
}

fun orderRegistry(orders: OrderRepository): ToolRegistry =
    ToolRegistry { tools(OrderTools(orders).asTools()) }
