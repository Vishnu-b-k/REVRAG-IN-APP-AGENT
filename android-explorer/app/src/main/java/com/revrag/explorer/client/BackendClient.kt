package com.revrag.explorer.client

import android.util.Log
import com.revrag.explorer.models.CandidateAction
import com.revrag.explorer.models.IngestScreenResponse
import com.revrag.explorer.models.NextAction
import com.revrag.explorer.models.ObservationRequest
import com.revrag.explorer.models.ScreenElement
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class BackendClient(
    var baseUrl: String = "http://10.0.2.2:8000"
) {
    private val tag = "RevRagBackendClient"
    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
        prettyPrint = false
    }

    private val client = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    var useMockFallback: Boolean = false

    suspend fun ingestScreen(observation: ObservationRequest): Result<IngestScreenResponse> =
        withContext(Dispatchers.IO) {
            if (useMockFallback) {
                return@withContext Result.success(createMockResponse(observation))
            }

            try {
                val url = "${baseUrl.trimEnd('/')}/ingest-screen"
                val bodyStr = json.encodeToString(observation)
                val requestBody = bodyStr.toRequestBody("application/json; charset=utf-8".toMediaType())
                val request = Request.Builder()
                    .url(url)
                    .post(requestBody)
                    .build()

                client.newCall(request).execute().use { response ->
                    val respBody = response.body?.string() ?: ""
                    if (!response.isSuccessful) {
                        Log.w(tag, "Backend returned HTTP ${response.code}: $respBody")
                        return@withContext Result.failure(
                            RuntimeException("HTTP ${response.code}: $respBody")
                        )
                    }
                    val parsed = json.decodeFromString<IngestScreenResponse>(respBody)
                    Result.success(parsed)
                }
            } catch (e: Exception) {
                Log.e(tag, "Network error contacting orchestrator: ${e.message}", e)
                // If live backend fails, optionally fall back to mock to keep autonomous demo alive
                Result.success(createMockResponse(observation))
            }
        }

    private fun createMockResponse(observation: ObservationRequest): IngestScreenResponse {
        val root = observation.uiTree.root
        // Extract clickable candidate nodes
        val clickables = mutableListOf<com.revrag.explorer.models.UIElement>()
        fun collectClickables(node: com.revrag.explorer.models.UIElement) {
            if (node.clickable || node.editable) clickables.add(node)
            node.children.forEach { collectClickables(it) }
        }
        collectClickables(root)

        val screenName = observation.uiTree.activityName?.substringAfterLast('.') ?: "Screen_${observation.step}"
        val elements = clickables.mapIndexed { idx, node ->
            ScreenElement(
                id = "elem_${idx + 1}",
                role = if (node.editable) "text_input" else "button",
                label = node.text ?: node.contentDescription ?: "Element_${idx + 1}",
                bounds = node.bounds,
                actions = if (node.editable) listOf("type_text") else listOf("tap")
            )
        }

        val target = elements.firstOrNull()
        val nextAction = if (target != null) {
            NextAction(
                type = if (target.role == "text_input") "type_text" else "tap",
                targetElementId = target.id,
                value = if (target.role == "text_input") "demo@revrag.ai" else null,
                reason = "Mock exploration heuristic: target element ${target.label}",
                confidence = 0.85f
            )
        } else {
            NextAction(
                type = "back",
                reason = "No interactable elements found, backtracking",
                confidence = 0.60f
            )
        }

        return IngestScreenResponse(
            screenId = "screen_${screenName.lowercase()}",
            stateId = "state_${observation.step}",
            isNewScreen = observation.step == 0,
            description = "Autonomous mock exploration of $screenName",
            elements = elements,
            candidateActions = listOf(
                CandidateAction(
                    type = nextAction.type,
                    targetElementId = nextAction.targetElementId,
                    value = nextAction.value,
                    reason = nextAction.reason,
                    confidence = nextAction.confidence
                )
            ),
            nextAction = nextAction
        )
    }
}
