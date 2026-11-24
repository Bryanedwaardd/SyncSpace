package com.example.syncspace.navigation

import android.widget.Toast
import androidx.compose.animation.Crossfade
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import com.example.syncspace.network.LoginRequest
import com.example.syncspace.network.RegisterRequest
import com.example.syncspace.network.RetrofitClient
import com.example.syncspace.ui.screens.ForgotPasswordScreen
import com.example.syncspace.ui.screens.LoginScreen
import com.example.syncspace.ui.screens.OnboardingScreen
import com.example.syncspace.ui.screens.RegisterScreen
import com.example.syncspace.ui.screens.SplashScreen
import com.example.syncspace.ui.screens.VerificationCodeScreen
import kotlinx.coroutines.launch

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
    val coroutineScope = rememberCoroutineScope()

    var currentScreen by remember { mutableStateOf(Screen.Splash) }
    var userEmail by remember { mutableStateOf("") }
    var verificationSource by remember { mutableStateOf(Screen.Register) }
    var authToken by remember { mutableStateOf("") }
    var loggedInUserId by remember { mutableLongStateOf(-1L) }
    var isLoading by remember { mutableStateOf(false) }

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
                onLoginClick = { email, password ->
                    if (isLoading) return@LoginScreen
                    isLoading = true
                    coroutineScope.launch {
                        try {
                            val response = RetrofitClient.apiService.login(
                                LoginRequest(email = email.trim(), password = password)
                            )
                            if (response.isSuccessful && response.body() != null) {
                                val data = response.body()!!
                                authToken = data.token
                                loggedInUserId = data.userId
                                userEmail = data.email
                                verificationSource = Screen.Login
                                Toast.makeText(context, "Login sukses! Halo ${data.name}", Toast.LENGTH_SHORT).show()
                                currentScreen = Screen.Verification
                            } else {
                                Toast.makeText(context, "Login gagal (${response.code()}): cek email/password", Toast.LENGTH_LONG).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(context, "Koneksi error: ${e.message}", Toast.LENGTH_LONG).show()
                        } finally {
                            isLoading = false
                        }
                    }
                },
                onForgotPasswordClick = { currentScreen = Screen.ForgotPassword },
                onGoogleSignInClick = {
                    Toast.makeText(context, "Continue with Google clicked", Toast.LENGTH_SHORT).show()
                },
                onRegisterClick = { currentScreen = Screen.Register }
            )

            Screen.Register -> RegisterScreen(
                onBackClick = { currentScreen = Screen.Onboarding },
                onRegisterClick = { username, email, password ->
                    if (isLoading) return@RegisterScreen
                    isLoading = true
                    coroutineScope.launch {
                        try {
                            val response = RetrofitClient.apiService.register(
                                RegisterRequest(
                                    name = username.trim(),
                                    email = email.trim(),
                                    password = password
                                )
                            )
                            if (response.isSuccessful && response.body() != null) {
                                val data = response.body()!!
                                authToken = data.token
                                loggedInUserId = data.userId
                                userEmail = data.email
                                verificationSource = Screen.Register
                                Toast.makeText(context, "Akun ${data.name} berhasil dibuat!", Toast.LENGTH_SHORT).show()
                                currentScreen = Screen.Verification
                            } else {
                                Toast.makeText(context, "Register gagal (${response.code()})", Toast.LENGTH_LONG).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(context, "Koneksi error: ${e.message}", Toast.LENGTH_LONG).show()
                        } finally {
                            isLoading = false
                        }
                    }
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
                        Toast.makeText(
                            context,
                            "Login verified! UserID: $loggedInUserId (Token siap)",
                            Toast.LENGTH_LONG
                        ).show()
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