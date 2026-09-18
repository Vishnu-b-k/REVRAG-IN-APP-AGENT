import time
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from orchestrator.models.observation import ObservationRequest, UITree, UIElement
from orchestrator.services.screen_ingestion import ingest_screen
from orchestrator.services.pack_builder import finalize_pack
from orchestrator.services.session import session_store
from orchestrator.providers.mock import MockLLMProvider
from orchestrator.models.knowledge_pack import KnowledgePack

router = APIRouter(prefix="/simulate", tags=["simulate"])

class SimulationStep(BaseModel):
    step: int
    screen_id: str
    is_new_screen: bool
    description: str
    action_type: str
    action_target: Optional[str] = None
    action_reason: str = ""

class SimulationResponse(BaseModel):
    session_id: str
    total_steps: int
    screens_discovered: int
    steps: list[SimulationStep]
    knowledge_pack: KnowledgePack

SCREENS_DATA = [
    # Login
    {
        "package_name": "com.revrag.demoapp",
        "activity_name": "com.revrag.demoapp.LoginActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "bounds": [0, 0, 1080, 2340], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "text": None, "content_description": None,
            "children": [
                {"class_name": "android.widget.ImageView", "text": None, "content_description": "App Logo", "bounds": [340, 200, 740, 500], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "Welcome to DemoApp", "content_description": None, "bounds": [200, 550, 880, 620], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.EditText", "text": "", "content_description": "Phone number", "bounds": [100, 700, 980, 800], "clickable": True, "focusable": True, "editable": True, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Send OTP", "content_description": None, "bounds": [300, 870, 780, 960], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "By continuing you agree to our Terms of Service", "content_description": None, "bounds": [150, 1020, 930, 1070], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []}
            ]
        }
    },
    # OTP
    {
        "package_name": "com.revrag.demoapp",
        "activity_name": "com.revrag.demoapp.OTPActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "bounds": [0, 0, 1080, 2340], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "text": None, "content_description": None,
            "children": [
                {"class_name": "android.widget.TextView", "text": "Enter OTP", "content_description": None, "bounds": [200, 400, 880, 470], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "We sent a 6-digit code to +91 98765 43210", "content_description": None, "bounds": [150, 490, 930, 540], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.EditText", "text": "", "content_description": "OTP code", "bounds": [200, 600, 880, 700], "clickable": True, "focusable": True, "editable": True, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Verify", "content_description": None, "bounds": [300, 780, 780, 870], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Resend OTP", "content_description": None, "bounds": [300, 930, 780, 1000], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []}
            ]
        }
    },
    # Dashboard
    {
        "package_name": "com.revrag.demoapp",
        "activity_name": "com.revrag.demoapp.DashboardActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "bounds": [0, 0, 1080, 2340], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "text": None, "content_description": None,
            "children": [
                {"class_name": "android.widget.TextView", "text": "Dashboard", "content_description": None, "bounds": [50, 50, 400, 110], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "Welcome back, User!", "content_description": None, "bounds": [50, 130, 600, 180], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "View Feed", "content_description": None, "bounds": [50, 300, 520, 390], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Profile", "content_description": None, "bounds": [560, 300, 1030, 390], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "KYC Form", "content_description": None, "bounds": [50, 450, 520, 540], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Settings", "content_description": None, "bounds": [560, 450, 1030, 540], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "3 new notifications", "content_description": None, "bounds": [50, 600, 500, 650], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []}
            ]
        }
    },
    # Profile
    {
        "package_name": "com.revrag.demoapp",
        "activity_name": "com.revrag.demoapp.ProfileActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "bounds": [0, 0, 1080, 2340], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "text": None, "content_description": None,
            "children": [
                {"class_name": "android.widget.ImageView", "text": None, "content_description": "Profile Photo", "bounds": [340, 100, 740, 500], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "Test User", "content_description": None, "bounds": [200, 550, 880, 620], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "testuser@example.com", "content_description": None, "bounds": [200, 650, 880, 710], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "+91 98765 43210", "content_description": None, "bounds": [200, 740, 880, 800], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Edit Profile", "content_description": None, "bounds": [300, 870, 780, 960], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Logout", "content_description": None, "bounds": [300, 1020, 780, 1110], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []}
            ]
        }
    },
    # Settings
    {
        "package_name": "com.revrag.demoapp",
        "activity_name": "com.revrag.demoapp.SettingsActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "bounds": [0, 0, 1080, 2340], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "text": None, "content_description": None,
            "children": [
                {"class_name": "android.widget.TextView", "text": "Settings", "content_description": None, "bounds": [50, 50, 400, 110], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Switch", "text": "Dark Mode", "content_description": None, "bounds": [50, 200, 1030, 280], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": False, "children": []},
                {"class_name": "android.widget.Switch", "text": "Notifications", "content_description": None, "bounds": [50, 320, 1030, 400], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": True, "children": []},
                {"class_name": "android.widget.Button", "text": "Change Language", "content_description": None, "bounds": [50, 460, 1030, 550], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.Button", "text": "Privacy Policy", "content_description": None, "bounds": [50, 600, 1030, 690], "clickable": True, "focusable": True, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []},
                {"class_name": "android.widget.TextView", "text": "Version 2.1.0", "content_description": None, "bounds": [50, 2200, 400, 2260], "clickable": False, "focusable": False, "editable": False, "enabled": True, "selected": False, "checked": None, "children": []}
            ]
        }
    }
]

@router.post("/run", response_model=SimulationResponse)
async def run_simulation():
    session_id = f"sim-{int(time.time())}"
    session = session_store.get_or_create(session_id)
    provider = MockLLMProvider()
    
    b64_img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    steps_res = []
    prev_state_id = None
    
    for step_idx, screen_data in enumerate(SCREENS_DATA):
        ui_tree = UITree(**screen_data)
        req = ObservationRequest(
            session_id=session_id,
            step=step_idx,
            screenshot_b64=b64_img,
            ui_tree=ui_tree,
            previous_state_id=prev_state_id
        )
        
        ingest_res = await ingest_screen(req, session, provider)
        prev_state_id = ingest_res.state_id
        
        steps_res.append(SimulationStep(
            step=step_idx,
            screen_id=ingest_res.screen_id,
            is_new_screen=ingest_res.is_new_screen,
            description=ingest_res.description,
            action_type=ingest_res.next_action.type.value if ingest_res.next_action else "null",
            action_target=ingest_res.next_action.target_element_id if ingest_res.next_action else None,
            action_reason=ingest_res.next_action.reason if ingest_res.next_action else ""
        ))
        
    pack = finalize_pack(session)
    
    # Patch screenshot URLs — map screen IDs to actual Target App screenshots
    # These are real renders of the android-explorer Compose screens
    SCREENSHOT_MAP = {
        "scr_6edf4f0a": "/screenshots/scr_login_app.jpg",      # LoginActivity
        "scr_d2988000": "/screenshots/scr_otp_app.jpg",         # OTPActivity
        "scr_8ecc448b": "/screenshots/scr_dashboard_app.jpg",   # DashboardActivity
        "scr_dc2459da": "/screenshots/scr_profile_app.jpg",     # ProfileActivity
        "scr_6c94648c": "/screenshots/scr_settings_app.jpg",    # SettingsActivity
    }
    for screen in pack.screens:
        screen.screenshot_url = SCREENSHOT_MAP.get(screen.id, "/screenshots/scr_dashboard_app.jpg")
    
    return SimulationResponse(
        session_id=session_id,
        total_steps=len(steps_res),
        screens_discovered=pack.scan_metadata.screens_discovered,
        steps=steps_res,
        knowledge_pack=pack
    )
