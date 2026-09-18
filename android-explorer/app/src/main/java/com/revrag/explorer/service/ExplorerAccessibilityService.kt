package com.revrag.explorer.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Bitmap
import android.graphics.Path
import android.graphics.Rect
import android.os.Build
import android.os.Bundle
import android.util.Base64
import android.util.Log
import android.view.Display
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.revrag.explorer.client.BackendClient
import com.revrag.explorer.models.NextAction
import com.revrag.explorer.models.ObservationRequest
import com.revrag.explorer.models.UIElement
import com.revrag.explorer.models.UITree
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.util.UUID
import java.util.concurrent.Executor

data class ExplorationStatus(
    val isRunning: Boolean = false,
    val step: Int = 0,
    val maxSteps: Int = 20,
    val currentScreen: String = "Idle",
    val lastAction: String = "None",
    val lastResult: String = "Ready",
    val backendUrl: String = "http://10.0.2.2:8000"
)

class ExplorerAccessibilityService : AccessibilityService() {

    private val tag = "RevRagExplorerService"
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var explorationJob: Job? = null

    val backendClient = BackendClient()

    companion object {
        var instance: ExplorerAccessibilityService? = null
            private set

        private val _statusFlow = MutableStateFlow(ExplorationStatus())
        val statusFlow: StateFlow<ExplorationStatus> = _statusFlow.asStateFlow()
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(tag, "RevRag Explorer Accessibility Service connected successfully")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Can monitor window state changes if needed
    }

    override fun onInterrupt() {
        stopExploration()
        Log.w(tag, "Explorer service interrupted")
    }

    override fun onDestroy() {
        stopExploration()
        instance = null
        super.onDestroy()
    }

    fun startExploration(backendUrl: String = "http://10.0.2.2:8000", maxSteps: Int = 20) {
        if (explorationJob?.isActive == true) return

        backendClient.baseUrl = backendUrl
        val sessionId = "session_${UUID.randomUUID().toString().take(8)}"

        _statusFlow.value = ExplorationStatus(
            isRunning = true,
            step = 0,
            maxSteps = maxSteps,
            currentScreen = "Starting...",
            lastAction = "Initializing",
            lastResult = "Started session $sessionId",
            backendUrl = backendUrl
        )

        explorationJob = serviceScope.launch {
            runExplorationLoop(sessionId, maxSteps)
        }
    }

    fun stopExploration() {
        explorationJob?.cancel()
        explorationJob = null
        _statusFlow.value = _statusFlow.value.copy(
            isRunning = false,
            lastResult = "Exploration stopped"
        )
    }

    private suspend fun runExplorationLoop(sessionId: String, maxSteps: Int) {
        var step = 0
        var previousStateId: String? = null

        while (step < maxSteps && _statusFlow.value.isRunning) {
            // 1. Settle wait
            delay(1200)

            // 2. Capture observation
            val rootNode = rootInActiveWindow
            if (rootNode == null) {
                Log.w(tag, "Step $step: rootInActiveWindow is null, retrying...")
                delay(800)
                continue
            }

            val packageName = rootNode.packageName?.toString() ?: "unknown"
            val uiTreeRoot = parseNode(rootNode)
            rootNode.recycle()

            val uiTree = UITree(
                packageName = packageName,
                activityName = packageName,
                root = uiTreeRoot
            )

            val screenshotB64 = captureScreenshotB64()

            val observation = ObservationRequest(
                sessionId = sessionId,
                step = step,
                screenshot_b64 = screenshotB64,
                ui_tree = uiTree,
                previous_state_id = previousStateId
            )

            // 3. Post to backend
            _statusFlow.value = _statusFlow.value.copy(
                step = step + 1,
                currentScreen = packageName,
                lastAction = "Observing...",
                lastResult = "Sent step $step to backend"
            )

            val responseResult = backendClient.ingestScreen(observation)
            if (responseResult.isFailure) {
                _statusFlow.value = _statusFlow.value.copy(
                    lastResult = "Error: ${responseResult.exceptionOrNull()?.message}"
                )
                delay(2000)
                continue
            }

            val response = responseResult.getOrThrow()
            previousStateId = response.stateId

            // 4. Validate and Execute Action
            val nextAction = response.nextAction
            if (nextAction.type == "null") {
                _statusFlow.value = _statusFlow.value.copy(
                    isRunning = false,
                    lastAction = "Done",
                    lastResult = "Exploration completed by orchestrator"
                )
                break
            }

            _statusFlow.value = _statusFlow.value.copy(
                lastAction = "${nextAction.type} (${nextAction.value ?: nextAction.targetElementId ?: ""})",
                lastResult = nextAction.reason
            )

            val success = executeAction(nextAction, response.elements)
            Log.i(tag, "Step $step: Executed ${nextAction.type}, success=$success")

            step++
        }

        if (_statusFlow.value.isRunning) {
            _statusFlow.value = _statusFlow.value.copy(
                isRunning = false,
                lastResult = "Reached max step limit ($maxSteps)"
            )
        }
    }

    private fun parseNode(node: AccessibilityNodeInfo): UIElement {
        val rect = Rect()
        node.getBoundsInScreen(rect)
        val bounds = listOf(rect.left, rect.top, rect.right, rect.bottom)

        val children = mutableListOf<UIElement>()
        for (i in 0 until node.childCount) {
            val child = node.getChild(i)
            if (child != null) {
                children.add(parseNode(child))
                child.recycle()
            }
        }

        return UIElement(
            className = node.className?.toString() ?: "android.view.View",
            text = node.text?.toString(),
            contentDescription = node.contentDescription?.toString(),
            bounds = bounds,
            clickable = node.isClickable,
            focusable = node.isFocusable,
            editable = node.isEditable,
            enabled = node.isEnabled,
            selected = node.isSelected,
            checked = if (node.isCheckable) node.isChecked else null,
            children = children
        )
    }

    private suspend fun captureScreenshotB64(): String {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            return kotlinx.coroutines.suspendCancellableCoroutine { continuation ->
                takeScreenshot(
                    Display.DEFAULT_DISPLAY,
                    applicationContext.mainExecutor,
                    object : TakeScreenshotCallback {
                        override fun onSuccess(screenshotResult: ScreenshotResult) {
                            val bitmap = Bitmap.wrapHardwareBuffer(
                                screenshotResult.hardwareBuffer,
                                screenshotResult.colorSpace
                            )?.copy(Bitmap.Config.ARGB_8888, false)

                            if (bitmap != null) {
                                val out = ByteArrayOutputStream()
                                bitmap.compress(Bitmap.CompressFormat.PNG, 80, out)
                                val b64 = Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP)
                                continuation.resume(b64) {}
                            } else {
                                continuation.resume(createDummyScreenshotB64()) {}
                            }
                        }

                        override fun onFailure(errorCode: Int) {
                            Log.w(tag, "takeScreenshot failed with code $errorCode")
                            continuation.resume(createDummyScreenshotB64()) {}
                        }
                    }
                )
            }
        }
        return createDummyScreenshotB64()
    }

    private fun createDummyScreenshotB64(): String {
        // Minimal 1x1 PNG fallback if screenshot API is restricted
        val bmp = Bitmap.createBitmap(16, 16, Bitmap.Config.ARGB_8888)
        val out = ByteArrayOutputStream()
        bmp.compress(Bitmap.CompressFormat.PNG, 100, out)
        return Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP)
    }

    private fun executeAction(action: NextAction, elements: List<com.revrag.explorer.models.ScreenElement>): Boolean {
        return when (action.type) {
            "tap" -> {
                val elem = elements.find { it.id == action.targetElementId }
                if (elem != null && elem.bounds.size >= 4) {
                    val x = (elem.bounds[0] + elem.bounds[2]) / 2f
                    val y = (elem.bounds[1] + elem.bounds[3]) / 2f
                    dispatchTapGesture(x, y)
                } else {
                    // Tap center of screen
                    dispatchTapGesture(540f, 960f)
                }
            }
            "type_text" -> {
                val text = action.value ?: "demo text"
                val root = rootInActiveWindow ?: return false
                val focused = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
                val targetNode = focused ?: findFirstEditableNode(root)
                if (targetNode != null) {
                    val args = Bundle().apply {
                        putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
                    }
                    val res = targetNode.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
                    targetNode.recycle()
                    root.recycle()
                    res
                } else {
                    root.recycle()
                    false
                }
            }
            "scroll" -> {
                dispatchScrollGesture()
            }
            "back" -> {
                performGlobalAction(GLOBAL_ACTION_BACK)
            }
            else -> false
        }
    }

    private fun findFirstEditableNode(node: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        if (node.isEditable) return node
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            val found = findFirstEditableNode(child)
            if (found != null) return found
            child.recycle()
        }
        return null
    }

    private fun dispatchTapGesture(x: Float, y: Float): Boolean {
        val path = Path().apply { moveTo(x, y) }
        val stroke = GestureDescription.StrokeDescription(path, 0, 100)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()
        return dispatchGesture(gesture, null, null)
    }

    private fun dispatchScrollGesture(): Boolean {
        // Swipe upwards to scroll down
        val path = Path().apply {
            moveTo(540f, 1500f)
            lineTo(540f, 600f)
        }
        val stroke = GestureDescription.StrokeDescription(path, 0, 300)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()
        return dispatchGesture(gesture, null, null)
    }
}
