"""Tests for stable screen fingerprinting and deduplication.

Covers all V-3 requirements:
- Same screen + different username → same screen ID
- Same screen + changing timestamp → same screen ID
- Different screen + similar colours → different ID
- Same screen + different modal state → distinct state
- Deterministic fingerprints across repeated runs
- Duplicate screens merge rather than multiply
"""

import copy
import pytest

from orchestrator.services.fingerprint import (
    normalise_volatile_text,
    normalise_bounds,
    canonicalise_element,
    canonicalise_tree,
    compute_fingerprint,
    compute_screen_id,
    ScreenDeduplicator,
)


# ── Fixtures ─────────────────────────────────────────────────────────

def _login_screen(username: str = "", otp: str = "", timestamp: str = "") -> dict:
    """Build a Login screen tree with optional volatile values."""
    return {
        "package_name": "com.revrag.targetapp",
        "activity_name": "com.revrag.targetapp.LoginActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "text": None,
            "content_description": None,
            "bounds": [0, 0, 1080, 2340],
            "clickable": False,
            "editable": False,
            "focusable": False,
            "children": [
                {
                    "class_name": "android.widget.TextView",
                    "text": f"Welcome back{', ' + username if username else ''}",
                    "content_description": None,
                    "bounds": [200, 550, 880, 620],
                    "clickable": False,
                    "editable": False,
                    "focusable": False,
                    "children": [],
                },
                {
                    "class_name": "android.widget.EditText",
                    "text": username or "",
                    "content_description": "Phone number",
                    "bounds": [100, 700, 980, 800],
                    "clickable": True,
                    "editable": True,
                    "focusable": True,
                    "children": [],
                },
                {
                    "class_name": "android.widget.Button",
                    "text": "Send OTP",
                    "content_description": None,
                    "bounds": [300, 870, 780, 960],
                    "clickable": True,
                    "editable": False,
                    "focusable": True,
                    "children": [],
                },
                {
                    "class_name": "android.widget.TextView",
                    "text": timestamp or "Last login: 2:30 PM",
                    "content_description": None,
                    "bounds": [200, 1020, 880, 1070],
                    "clickable": False,
                    "editable": False,
                    "focusable": False,
                    "children": [],
                },
            ],
        },
    }


def _dashboard_screen(counter: str = "12", price: str = "$45.99") -> dict:
    """Build a Dashboard screen tree with volatile counters/prices."""
    return {
        "package_name": "com.revrag.targetapp",
        "activity_name": "com.revrag.targetapp.DashboardActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "text": None,
            "content_description": None,
            "bounds": [0, 0, 1080, 2340],
            "clickable": False,
            "editable": False,
            "focusable": False,
            "children": [
                {
                    "class_name": "android.widget.TextView",
                    "text": f"Notifications: {counter}",
                    "content_description": None,
                    "bounds": [50, 100, 400, 160],
                    "clickable": False,
                    "editable": False,
                    "focusable": False,
                    "children": [],
                },
                {
                    "class_name": "android.widget.TextView",
                    "text": f"Balance: {price}",
                    "content_description": None,
                    "bounds": [50, 200, 400, 260],
                    "clickable": False,
                    "editable": False,
                    "focusable": False,
                    "children": [],
                },
                {
                    "class_name": "android.widget.Button",
                    "text": "View Feed",
                    "content_description": None,
                    "bounds": [300, 400, 780, 490],
                    "clickable": True,
                    "editable": False,
                    "focusable": True,
                    "children": [],
                },
            ],
        },
    }


def _profile_screen(name: str = "Test User", email: str = "test@example.com") -> dict:
    """Build a Profile screen (structurally different from Login/Dashboard)."""
    return {
        "package_name": "com.revrag.targetapp",
        "activity_name": "com.revrag.targetapp.ProfileActivity",
        "root": {
            "class_name": "android.widget.FrameLayout",
            "text": None,
            "content_description": None,
            "bounds": [0, 0, 1080, 2340],
            "clickable": False,
            "editable": False,
            "focusable": False,
            "children": [
                {
                    "class_name": "android.widget.ImageView",
                    "text": None,
                    "content_description": "Profile Photo",
                    "bounds": [340, 100, 740, 500],
                    "clickable": False,
                    "editable": False,
                    "focusable": False,
                    "children": [],
                },
                {
                    "class_name": "android.widget.TextView",
                    "text": name,
                    "content_description": None,
                    "bounds": [200, 550, 880, 620],
                    "clickable": False,
                    "editable": False,
                    "focusable": False,
                    "children": [],
                },
                {
                    "class_name": "android.widget.TextView",
                    "text": email,
                    "content_description": None,
                    "bounds": [200, 650, 880, 710],
                    "clickable": False,
                    "editable": False,
                    "focusable": False,
                    "children": [],
                },
            ],
        },
    }


def _login_with_dialog() -> dict:
    """Login screen with an extra modal dialog overlay."""
    tree = _login_screen()
    tree["root"]["children"].append({
        "class_name": "android.widget.FrameLayout",
        "text": None,
        "content_description": "Dialog overlay",
        "bounds": [100, 500, 980, 1500],
        "clickable": False,
        "editable": False,
        "focusable": False,
        "children": [
            {
                "class_name": "android.widget.TextView",
                "text": "Are you sure?",
                "content_description": None,
                "bounds": [200, 600, 880, 660],
                "clickable": False,
                "editable": False,
                "focusable": False,
                "children": [],
            },
            {
                "class_name": "android.widget.Button",
                "text": "Confirm",
                "content_description": None,
                "bounds": [300, 700, 500, 780],
                "clickable": True,
                "editable": False,
                "focusable": True,
                "children": [],
            },
        ],
    })
    return tree


# ── Test: Volatile Text Normalisation ────────────────────────────────

class TestVolatileText:
    """Verify volatile values are normalised to placeholders."""

    def test_otp_normalised(self):
        assert normalise_volatile_text("1234") == "<OTP>"
        assert normalise_volatile_text("987654") == "<OTP>"

    def test_timestamp_normalised(self):
        result = normalise_volatile_text("Last login: 2:30 PM")
        assert "<TIME>" in result

    def test_date_normalised(self):
        result = normalise_volatile_text("Created on 2026-09-18")
        assert "<DATE>" in result

    def test_price_normalised(self):
        assert "<PRICE>" in normalise_volatile_text("$45.99")
        assert "<PRICE>" in normalise_volatile_text("₹1,234")

    def test_phone_normalised(self):
        assert "<PHONE>" in normalise_volatile_text("+91 98765 43210")

    def test_email_normalised(self):
        assert "<EMAIL>" in normalise_volatile_text("test@example.com")

    def test_greeting_normalised(self):
        assert "<GREETING>" in normalise_volatile_text("Welcome back, Vishnu")
        assert "<GREETING>" in normalise_volatile_text("Hello User")

    def test_stable_text_unchanged(self):
        assert normalise_volatile_text("Send OTP") == "Send OTP"
        assert normalise_volatile_text("View Feed") == "View Feed"

    def test_none_returns_none(self):
        assert normalise_volatile_text(None) is None


# ── Test: Coordinate Bucketing ───────────────────────────────────────

class TestCoordinateBucketing:
    """Verify small pixel shifts don't change the fingerprint."""

    def test_small_shift_same_bucket(self):
        assert normalise_bounds([102, 703, 978, 802]) == normalise_bounds([100, 700, 980, 800])

    def test_large_shift_different_bucket(self):
        assert normalise_bounds([100, 700, 980, 800]) != normalise_bounds([300, 700, 980, 800])


# ── Test: Same Screen, Different Username → Same ID ──────────────────

class TestSameScreenDifferentUser:
    """Same Login screen with different user-entered text should fingerprint the same."""

    def test_different_usernames_same_fingerprint(self):
        fp1 = compute_fingerprint(_login_screen(username="Vishnu"))
        fp2 = compute_fingerprint(_login_screen(username="Amogh"))
        fp3 = compute_fingerprint(_login_screen(username="Slaven"))
        assert fp1 == fp2 == fp3

    def test_different_usernames_same_screen_id(self):
        id1 = compute_screen_id(compute_fingerprint(_login_screen(username="Vishnu")))
        id2 = compute_screen_id(compute_fingerprint(_login_screen(username="Maniarasan")))
        assert id1 == id2


# ── Test: Same Screen, Changing Timestamp → Same ID ──────────────────

class TestSameScreenDifferentTimestamp:
    """Same screen with different timestamps should fingerprint the same."""

    def test_different_timestamps_same_fingerprint(self):
        fp1 = compute_fingerprint(_login_screen(timestamp="Last login: 2:30 PM"))
        fp2 = compute_fingerprint(_login_screen(timestamp="Last login: 5:45 AM"))
        fp3 = compute_fingerprint(_login_screen(timestamp="Last login: 11:59 PM"))
        assert fp1 == fp2 == fp3


# ── Test: Different Screen, Similar Colours → Different ID ───────────

class TestDifferentScreenDifferentId:
    """Structurally different screens should get different IDs even if visual style is similar."""

    def test_login_vs_dashboard(self):
        fp_login = compute_fingerprint(_login_screen())
        fp_dash = compute_fingerprint(_dashboard_screen())
        assert fp_login != fp_dash

    def test_login_vs_profile(self):
        fp_login = compute_fingerprint(_login_screen())
        fp_profile = compute_fingerprint(_profile_screen())
        assert fp_login != fp_profile

    def test_dashboard_vs_profile(self):
        fp_dash = compute_fingerprint(_dashboard_screen())
        fp_profile = compute_fingerprint(_profile_screen())
        assert fp_dash != fp_profile


# ── Test: Same Screen + Modal → Distinct State ───────────────────────

class TestModalState:
    """A dialog overlay changes the tree structure → distinct fingerprint."""

    def test_login_with_dialog_differs(self):
        fp_plain = compute_fingerprint(_login_screen())
        fp_dialog = compute_fingerprint(_login_with_dialog())
        assert fp_plain != fp_dialog


# ── Test: Determinism ────────────────────────────────────────────────

class TestDeterminism:
    """Fingerprints must be identical across repeated runs."""

    def test_repeated_runs_same_fingerprint(self):
        for _ in range(10):
            fp = compute_fingerprint(_login_screen())
            assert fp == compute_fingerprint(_login_screen())

    def test_dashboard_deterministic(self):
        fps = [compute_fingerprint(_dashboard_screen(counter=str(i), price=f"${i}.99"))
               for i in range(5)]
        assert len(set(fps)) == 1  # all the same despite different counters/prices


# ── Test: Deduplicator ───────────────────────────────────────────────

class TestScreenDeduplicator:
    """ScreenDeduplicator should merge duplicate screens."""

    def test_first_observation_is_new(self):
        dedup = ScreenDeduplicator()
        screen_id, fp, is_new = dedup.process(_login_screen())
        assert is_new is True
        assert screen_id.startswith("scr_")

    def test_second_same_screen_is_not_new(self):
        dedup = ScreenDeduplicator()
        dedup.process(_login_screen(username="Vishnu"))
        _, _, is_new = dedup.process(_login_screen(username="Amogh"))
        assert is_new is False

    def test_duplicates_counted(self):
        dedup = ScreenDeduplicator()
        dedup.process(_login_screen())
        dedup.process(_login_screen(username="A"))
        dedup.process(_login_screen(username="B"))
        assert dedup.duplicates_merged == 2

    def test_different_screens_both_new(self):
        dedup = ScreenDeduplicator()
        _, _, new1 = dedup.process(_login_screen())
        _, _, new2 = dedup.process(_dashboard_screen())
        _, _, new3 = dedup.process(_profile_screen())
        assert new1 is True
        assert new2 is True
        assert new3 is True
        assert dedup.duplicates_merged == 0

    def test_merge_stats(self):
        dedup = ScreenDeduplicator()
        dedup.process(_login_screen())
        dedup.process(_login_screen(username="X"))
        dedup.process(_dashboard_screen())
        dedup.process(_dashboard_screen(counter="99"))

        stats = dedup.get_stats()
        assert stats["unique_screens"] == 2
        assert stats["duplicates_merged"] == 2

    def test_volatile_dashboard_counters_merge(self):
        """Dashboard with different notification counts and prices should merge."""
        dedup = ScreenDeduplicator()
        dedup.process(_dashboard_screen(counter="5", price="$10.00"))
        _, _, is_new = dedup.process(_dashboard_screen(counter="42", price="$999.99"))
        assert is_new is False
