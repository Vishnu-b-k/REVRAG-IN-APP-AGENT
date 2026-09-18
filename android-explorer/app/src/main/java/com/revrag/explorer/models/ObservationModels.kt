package com.revrag.explorer.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UIElement(
    @SerialName("class_name") val className: String,
    val text: String? = null,
    @SerialName("content_description") val contentDescription: String? = null,
    val bounds: List<Int>, // [left, top, right, bottom]
    val clickable: Boolean = false,
    val focusable: Boolean = false,
    val editable: Boolean = false,
    val enabled: Boolean = true,
    val selected: Boolean = false,
    val checked: Boolean? = null,
    val children: List<UIElement> = emptyList()
)

@Serializable
data class UITree(
    @SerialName("package_name") val packageName: String,
    @SerialName("activity_name") val activityName: String? = null,
    val root: UIElement
)

@Serializable
data class ObservationRequest(
    @SerialName("session_id") val sessionId: String,
    val step: Int,
    @SerialName("screenshot_b64") val screenshotB64: String,
    @SerialName("ui_tree") val uiTree: UITree,
    @SerialName("previous_state_id") val previousStateId: String? = null
)

@Serializable
data class ScreenElement(
    val id: String,
    val role: String,
    val label: String,
    val bounds: List<Int>,
    val actions: List<String> = emptyList()
)

@Serializable
data class NextAction(
    val type: String, // "tap", "scroll", "type_text", "back", "null"
    @SerialName("target_element_id") val targetElementId: String? = null,
    val value: String? = null,
    val reason: String = "",
    val confidence: Float = 0f
)

@Serializable
data class CandidateAction(
    val type: String,
    @SerialName("target_element_id") val targetElementId: String? = null,
    val value: String? = null,
    val reason: String = "",
    val confidence: Float = 0f
)

@Serializable
data class IngestScreenResponse(
    @SerialName("screen_id") val screenId: String,
    @SerialName("state_id") val stateId: String,
    @SerialName("is_new_screen") val isNewScreen: Boolean = false,
    val description: String = "",
    val elements: List<ScreenElement> = emptyList(),
    @SerialName("candidate_actions") val candidateActions: List<CandidateAction> = emptyList(),
    @SerialName("next_action") val nextAction: NextAction
)
