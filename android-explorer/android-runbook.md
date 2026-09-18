# 📱 RevRag Android Explorer — Demo Runbook

Quick reference guide for running the Android Target App & Autonomous Explorer for live hackathon demonstrations.

---

## 1. Opening in Android Studio

1. Launch **Android Studio**.
2. Select **Open** and navigate to:
   ```
   /Users/slaven/Downloads/hackathon/REVRAG-IN-APP-AGENT/android-explorer
   ```
3. Allow Gradle to sync. (The project uses Android Gradle Plugin 8.5.2, Kotlin 2.0.0, and Compose Material3).
4. Select a virtual device with **Android 12+ (API 31–34)** or connect a physical device via USB debugging.
5. Click **Run 'app'** (Green play button).

---

## 2. Enabling the Accessibility Service

To allow the autonomous agent to observe and click UI elements automatically:

1. When the app launches, you will see the **AGENT HUD** at the bottom.
2. Tap the warning pill: `"⚠ Accessibility Service Disabled. Tap here to enable RevRag Explorer"`.
3. In Android Settings → **Accessibility**:
   - Scroll to **Downloaded apps / Installed services**.
   - Select **RevRag In-App Autonomous Explorer**.
   - Toggle **Use RevRag In-App Autonomous Explorer** to **ON**.
   - Confirm permissions (Observe screen & perform gestures).
4. Return to the RevRag Target App. The HUD will now indicate ready status.

---

## 3. Connecting to the FastAPI Orchestrator

1. Start the backend orchestrator on your host machine:
   ```bash
   cd /Users/slaven/Downloads/hackathon/REVRAG-IN-APP-AGENT
   python -m orchestrator.main
   ```
2. The Android app defaults to `http://10.0.2.2:8000` (the standard Android Emulator IP for localhost).
3. If using a **physical device over Wi-Fi**, open **Settings ⚙** in the app and set the IP to your Mac's LAN IP (e.g. `http://192.168.1.50:8000`).

---

## 4. Running the Autonomous Exploration Demo

1. Open the **AGENT HUD** by tapping **EXPAND**.
2. Tap **Start Autonomous Exploration**.
3. **Observation Loop**:
   - The service captures the `AccessibilityNodeInfo` UI tree and screenshot.
   - It posts the data to `POST /ingest-screen`.
   - The backend LLM/policy returns the next action (`tap`, `type_text`, `scroll`, `back`).
   - The accessibility service executes the action and waits 1.2s for UI stabilization.
   - Repeats across branches (Splash → Login → OTP → Dashboard → Feed → KYC → Details).

---

## 5. Offline / Standalone Mock Mode

If the backend server is not running during a quick test, the explorer automatically falls back to deterministic local mock heuristics:
- Explores clickable elements automatically.
- Inputs demo credentials.
- Navigates through branches without crashing or getting stuck.

---

## 6. Resetting to Initial State

To re-run the demo from scratch:
1. Navigate to **Dashboard** → **SETTINGS ⚙**.
2. Tap **"Reset Demo State to Initial"**.
3. Or clear app storage in Android App Info settings.
