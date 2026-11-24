package com.example.syncspace.ui.theme

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color

val PrimaryNavy = Color(0xFF211C84)
val PrimaryBlue = Color(0xFF4D55CC)
val PrimaryBlueLight = Color(0xFF6168D0)
val PrimaryPurpleSoft = Color(0xFF7F7BD5)

val Blue20 = Color(0xFFD7D9FF)
val Blue40 = Color(0xFFAFB4FF)

val Black100 = Color(0xFF040415)
val Black60 = Color(0xFF686873)
val Black20 = Color(0xFFCDCDD0)
val Black10 = Color(0xFFEAECF0)
val Green100 = Color(0xFF3BA935)

val OrTextGray = Color(0xFFB1B1B1)
val DividerLineGray = Color(0xFFD9D9D9)
val AuthFooterGray = Color(0xBD4B5563)
val OtpPlaceholderGray = Color(0x474B5563)
val SocialBorderBlack = Color(0xFF000000)
val SocialButtonShadow = Color(0x12232C5D)

val SplashGradient = Brush.horizontalGradient(
    colors = listOf(PrimaryBlue, PrimaryBlueLight)
)

val OnboardingBackgroundGradient = Brush.linearGradient(
    colorStops = arrayOf(
        0.0f to PrimaryBlue,
        0.254f to PrimaryBlue,
        0.746f to PrimaryPurpleSoft,
        1.0f to PrimaryPurpleSoft
    ),
    start = Offset(0f, 0f),
    end = Offset.Infinite
)
