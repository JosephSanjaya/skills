package com.example.agent

import ai.koog.agents.core.tools.annotations.LLMDescription
import ai.koog.agents.core.tools.annotations.Tool
import ai.koog.agents.ext.agent.reActStrategy
import ai.koog.ktor.Koog
import ai.koog.ktor.aiAgent
import ai.koog.ktor.llm
import ai.koog.prompt.dsl.prompt
import ai.koog.prompt.executor.clients.openai.OpenAIModels
import ai.koog.prompt.llm.LLMProvider
import ai.koog.prompt.executor.ollama.client.OllamaModels
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.request.receiveText
import io.ktor.server.response.respond
import io.ktor.server.routing.post
import io.ktor.server.routing.routing

@Tool
@LLMDescription("Looks up an order by id and returns status plus tracking")
fun searchOrders(orderId: String): String = "not wired"

fun Application.module() {
    install(Koog) {
        llm {
            openAI(apiKey = System.getenv("OPENAI_API_KEY") ?: error("OPENAI_API_KEY"))
            fallback {
                provider = LLMProvider.Ollama
                model = OllamaModels.Meta.LLAMA_3_2
            }
        }
        agentConfig {
            maxAgentIterations = 20
            prompt { system("You are a support assistant. Prefer tools over guessing.") }
            registerTools { tool(::searchOrders) }
        }
    }

    routing {
        post("/chat") {
            val userInput = call.receiveText()
            val harmful = llm().moderate(
                prompt("mod") { user(userInput) },
                OpenAIModels.Moderation.Omni,
            ).isHarmful
            if (harmful) {
                call.respond(HttpStatusCode.BadRequest, "rejected")
                return@post
            }
            val output = aiAgent(userInput, OpenAIModels.Chat.GPT4o)
            call.respond(HttpStatusCode.OK, output)
        }
        post("/research") {
            val q = call.receiveText()
            call.respond(HttpStatusCode.OK, aiAgent(reActStrategy(), OpenAIModels.Chat.GPT4o, q))
        }
    }
}
