package com.example.agent

import ai.koog.agents.core.dsl.builder.strategy
import ai.koog.agents.core.dsl.extension.HistoryCompressionStrategy
import ai.koog.agents.core.dsl.extension.ReceivedToolResults
import ai.koog.agents.core.dsl.extension.nodeExecuteTools
import ai.koog.agents.core.dsl.extension.nodeLLMCompressHistory
import ai.koog.agents.core.dsl.extension.nodeLLMRequest
import ai.koog.agents.core.dsl.extension.nodeLLMSendToolResults
import ai.koog.agents.core.dsl.extension.onTextMessage
import ai.koog.agents.core.dsl.extension.onToolCalls
import ai.koog.prompt.executor.clients.openai.OpenAIModels

private const val MAX_MESSAGES = 12

val supportStrategy = strategy<String, String>("customer_support") {
    val callLLM by nodeLLMRequest()
    val executeTools by nodeExecuteTools(parallel = true)
    val sendResults by nodeLLMSendToolResults()
    val compress by nodeLLMCompressHistory<ReceivedToolResults>(
        strategy = HistoryCompressionStrategy.FromLastNMessages(6),
        retrievalModel = OpenAIModels.Chat.GPT4oMini,
        preserveMemory = true,
    )

    edge(nodeStart forwardTo callLLM)
    edge(callLLM forwardTo executeTools onToolCalls { true })
    edge(callLLM forwardTo nodeFinish onTextMessage { true })

    edge(executeTools forwardTo compress onCondition {
        llm.readSession { prompt.messages.size > MAX_MESSAGES }
    })
    edge(executeTools forwardTo sendResults onCondition {
        llm.readSession { prompt.messages.size <= MAX_MESSAGES }
    })
    edge(compress forwardTo sendResults)

    edge(sendResults forwardTo executeTools onToolCalls { true })
    edge(sendResults forwardTo nodeFinish onTextMessage { true })
}
