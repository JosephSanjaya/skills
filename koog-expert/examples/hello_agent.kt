package com.example.agent

import ai.koog.agents.core.agent.AIAgent
import ai.koog.agents.core.tools.ToolRegistry
import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.core.tools.reflect.asTools
import ai.koog.prompt.executor.clients.openai.OpenAIModels
import ai.koog.prompt.executor.llms.all.simpleOpenAIExecutor
import kotlinx.coroutines.runBlocking

class CalculatorTools {
    @Tool
    @LLMDescription("Multiplies two numbers")
    fun multiply(a: Double, b: Double): Double = a * b
}

fun main() = runBlocking {
    val apiKey = System.getenv("OPENAI_API_KEY") ?: error("OPENAI_API_KEY is not set")
    simpleOpenAIExecutor(apiKey).use { executor ->
        val agent = AIAgent(
            promptExecutor = executor,
            llmModel = OpenAIModels.Chat.GPT4oMini,
            systemPrompt = "You are a calculator. Use tools instead of mental math.",
            maxIterations = 10,
            toolRegistry = ToolRegistry { tools(CalculatorTools().asTools()) },
        )
        println(agent.run("What is 25 multiplied by 4?"))
    }
}
