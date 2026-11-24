package com.example.syncspace.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalInspectionMode

@Immutable
data class SyncSpaceColors(
    val primaryNavy: Color = PrimaryNavy,
    val primaryBlue: Color = PrimaryBlue,
    val primaryBlueLight: Color = PrimaryBlueLight,
    val primaryPurpleSoft: Color = PrimaryPurpleSoft,
    val blue20: Color = Blue20,
    val blue40: Color = Blue40,
    val black100: Color = Black100,
    val black60: Color = Black60,
    val black20: Color = Black20,
    val black10: Color = Black10,
    val green100: Color = Green100,
    val orTextGray: Color = OrTextGray,
    val dividerLineGray: Color = DividerLineGray,
    val authFooterGray: Color = AuthFooterGray,
    val otpPlaceholderGray: Color = OtpPlaceholderGray,
    val socialBorderBlack: Color = SocialBorderBlack,
    val socialButtonShadow: Color = SocialButtonShadow,
    val splashGradient: Brush = SplashGradient,
    val onboardingGradient: Brush = OnboardingBackgroundGradient
)

val LocalSyncSpaceColors = staticCompositionLocalOf { SyncSpaceColors() }

private val DarkColorScheme = darkColorScheme(
    primary = PrimaryNavy,
    secondary = PrimaryBlue,
    tertiary = Blue40,
    background = Color(0xFF121212),
    surface = Color(0xFF1E1E1E),
    onPrimary = Color.White,
    onSecondary = Color.White,
    onBackground = Color.White,
    onSurface = Color.White
)

private val LightColorScheme = lightColorScheme(
    primary = PrimaryNavy,
    secondary = PrimaryBlue,
    tertiary = PrimaryPurpleSoft,
    background = Color.White,
    surface = Color.White,
    onPrimary = Color.White,
    onSecondary = Color.White,
    onBackground = Black100,
    onSurface = Black100
)

@Composable
fun SyncSpaceTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val isPreview = LocalInspectionMode.current
    val colorScheme = when {
        !isPreview && dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    CompositionLocalProvider(LocalSyncSpaceColors provides SyncSpaceColors()) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = Typography,
            content = content
        )
    }
}

object SyncSpaceThemeTokens {
    val colors: SyncSpaceColors
        @Composable
        get() = LocalSyncSpaceColors.current
}
