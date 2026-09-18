package com.revrag.targetapp

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.revrag.targetapp.screens.DashboardScreen
import com.revrag.targetapp.screens.FeedScreen
import com.revrag.targetapp.screens.KycFormScreen
import com.revrag.targetapp.screens.ListDetailsScreen
import com.revrag.targetapp.screens.LoginScreen
import com.revrag.targetapp.screens.OtpScreen
import com.revrag.targetapp.screens.SettingsScreen
import com.revrag.targetapp.screens.SplashScreen

enum class TargetScreen {
    SPLASH,
    LOGIN,
    OTP,
    DASHBOARD,
    FEED,
    KYC,
    LIST_DETAILS,
    SETTINGS
}

@Composable
fun TargetAppNavigation(
    isDarkMode: Boolean,
    onToggleDarkMode: (Boolean) -> Unit
) {
    var currentScreen by remember { mutableStateOf(TargetScreen.SPLASH) }
    var userEmail by remember { mutableStateOf("operator@revrag.ai") }

    fun resetToInitial() {
        currentScreen = TargetScreen.SPLASH
        userEmail = "operator@revrag.ai"
    }

    when (currentScreen) {
        TargetScreen.SPLASH -> {
            SplashScreen(
                onContinue = { currentScreen = TargetScreen.LOGIN }
            )
        }
        TargetScreen.LOGIN -> {
            LoginScreen(
                onLoginSuccess = { email ->
                    userEmail = email
                    currentScreen = TargetScreen.OTP
                },
                onBack = { currentScreen = TargetScreen.SPLASH }
            )
        }
        TargetScreen.OTP -> {
            OtpScreen(
                email = userEmail,
                onOtpVerified = { currentScreen = TargetScreen.DASHBOARD },
                onBack = { currentScreen = TargetScreen.LOGIN }
            )
        }
        TargetScreen.DASHBOARD -> {
            DashboardScreen(
                onNavigateToFeed = { currentScreen = TargetScreen.FEED },
                onNavigateToKyc = { currentScreen = TargetScreen.KYC },
                onNavigateToList = { currentScreen = TargetScreen.LIST_DETAILS },
                onNavigateToSettings = { currentScreen = TargetScreen.SETTINGS },
                onLogout = { currentScreen = TargetScreen.LOGIN }
            )
        }
        TargetScreen.FEED -> {
            FeedScreen(
                onBack = { currentScreen = TargetScreen.DASHBOARD }
            )
        }
        TargetScreen.KYC -> {
            KycFormScreen(
                onBack = { currentScreen = TargetScreen.DASHBOARD }
            )
        }
        TargetScreen.LIST_DETAILS -> {
            ListDetailsScreen(
                onBack = { currentScreen = TargetScreen.DASHBOARD }
            )
        }
        TargetScreen.SETTINGS -> {
            SettingsScreen(
                isDarkMode = isDarkMode,
                onToggleDarkMode = onToggleDarkMode,
                onResetDemoData = { resetToInitial() },
                onBack = { currentScreen = TargetScreen.DASHBOARD }
            )
        }
    }
}
