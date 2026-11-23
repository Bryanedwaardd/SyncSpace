package com.example.syncspace.navigation

import android.widget.Toast
import androidx.compose.animation.Crossfade
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import com.example.syncspace.ui.screens.ForgotPasswordScreen
import com.example.syncspace.ui.screens.LoginScreen
import com.example.syncspace.ui.screens.OnboardingScreen
import com.example.syncspace.ui.screens.RegisterScreen
import com.example.syncspace.ui.screens.SplashScreen
import com.example.syncspace.ui.screens.VerificationCodeScreen

enum class Screen {
    Splash,
    Onboarding,
    Login,
    Register,
    Verification,
    ForgotPassword
}

@Composable
fun AppNavigation() {
    val context = LocalContext.current
    var currentScreen by remember { mutableStateOf(Screen.Splash) }
    var userEmail by remember { mutableStateOf("") }
    var verificationSource by remember { mutableStateOf(Screen.Register) }

    Crossfade(targetState = currentScreen, label = "screen_transition") { screen ->
        when (screen) {
            Screen.Splash -> SplashScreen(
                onTimeout = { currentScreen = Screen.Onboarding }
            )

            Screen.Onboarding -> OnboardingScreen(
                onLoginClick = { currentScreen = Screen.Login },
                onRegisterClick = { currentScreen = Screen.Register }
            )

            Screen.Login -> LoginScreen(
                onBackClick = { currentScreen = Screen.Onboarding },
                onLoginClick = { email ->
                    userEmail = email
                    verificationSource = Screen.Login
                    currentScreen = Screen.Verification
                },
                onForgotPasswordClick = { currentScreen = Screen.ForgotPassword },
                onGoogleSignInClick = {
                    Toast.makeText(context, "Continue with Google clicked", Toast.LENGTH_SHORT).show()
                },
                onRegisterClick = { currentScreen = Screen.Register }
            )

            Screen.Register -> RegisterScreen(
                onBackClick = { currentScreen = Screen.Onboarding },
                onRegisterClick = { email ->
                    userEmail = email
                    verificationSource = Screen.Register
                    currentScreen = Screen.Verification
                },
                onGoogleSignInClick = {
                    Toast.makeText(context, "Continue with Google clicked", Toast.LENGTH_SHORT).show()
                },
                onLoginClick = { currentScreen = Screen.Login }
            )

            Screen.Verification -> VerificationCodeScreen(
                email = userEmail,
                onBackClick = { currentScreen = verificationSource },
                onVerifyClick = {
                    if (verificationSource == Screen.Register) {
                        Toast.makeText(context, "Registration verified! Please log in.", Toast.LENGTH_SHORT).show()
                        currentScreen = Screen.Login
                    } else {
                        Toast.makeText(context, "Login verified! Welcome to SyncSpace.", Toast.LENGTH_LONG).show()
                    }
                },
                onResendCodeClick = {
                    Toast.makeText(context, "Verification code resent!", Toast.LENGTH_SHORT).show()
                }
            )

            Screen.ForgotPassword -> ForgotPasswordScreen(
                onBackClick = { currentScreen = Screen.Login },
                onSendResetLinkClick = {
                    Toast.makeText(context, "Reset link sent! Please check your email.", Toast.LENGTH_SHORT).show()
                    currentScreen = Screen.Login
                },
                onLoginClick = { currentScreen = Screen.Login }
            )
        }
    }
}
