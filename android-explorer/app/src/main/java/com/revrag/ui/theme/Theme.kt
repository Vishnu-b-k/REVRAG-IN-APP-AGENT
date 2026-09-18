package com.revrag.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.dp
import androidx.core.view.WindowCompat

// Modest corner radii adhering to skill.md section 8
val RevRagShapes = Shapes(
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp)
)

private val LightColorScheme = lightColorScheme(
    primary = ApocalypticOrange,
    onPrimary = OffWhite,
    primaryContainer = HoneyBeige,
    onPrimaryContainer = DynamicBlack,
    secondary = EggLiqueur,
    onSecondary = DynamicBlack,
    background = SoftCream,
    onBackground = DynamicBlack,
    surface = OffWhite,
    onSurface = DynamicBlack,
    surfaceVariant = HoneyBeige,
    onSurfaceVariant = DynamicBlack,
    outline = BorderNeutral
)

private val DarkColorScheme = darkColorScheme(
    primary = ApocalypticOrange,
    onPrimary = OffWhite,
    primaryContainer = DynamicBlack,
    onPrimaryContainer = HoneyBeige,
    secondary = EggLiqueur,
    onSecondary = DynamicBlack,
    background = DynamicBlack,
    onBackground = OffWhite,
    surface = DynamicBlack,
    onSurface = OffWhite,
    surfaceVariant = DynamicBlack,
    onSurfaceVariant = HoneyBeige,
    outline = MutedNeutral
)

@Composable
fun RevRagTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = DynamicBlack.toArgb()
            window.navigationBarColor = DynamicBlack.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        shapes = RevRagShapes,
        content = content
    )
}
