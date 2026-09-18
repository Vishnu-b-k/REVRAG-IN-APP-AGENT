package com.revrag.targetapp

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.revrag.explorer.ui.ExplorerControlOverlay
import com.revrag.ui.theme.RevRagTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            var isDarkMode by remember { mutableStateOf(false) }

            RevRagTheme(darkTheme = isDarkMode) {
                Box(modifier = Modifier.fillMaxSize()) {
                    // 1. Target App Screen View
                    TargetAppNavigation(
                        isDarkMode = isDarkMode,
                        onToggleDarkMode = { isDarkMode = it }
                    )

                    // 2. Floating Autonomous Explorer HUD Overlay
                    ExplorerControlOverlay(
                        modifier = Modifier.align(Alignment.BottomCenter),
                        onOpenAccessibilitySettings = {
                            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                            startActivity(intent)
                        }
                    )
                }
            }
        }
    }
}
