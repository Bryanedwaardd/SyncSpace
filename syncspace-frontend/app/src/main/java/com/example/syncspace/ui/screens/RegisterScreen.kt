package com.example.syncspace.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.syncspace.ui.components.AuthTopBar
import com.example.syncspace.ui.components.AuthUnderlineTextField
import com.example.syncspace.ui.components.GoogleSignInButton
import com.example.syncspace.ui.components.OrDivider
import com.example.syncspace.ui.components.PrimaryButton
import com.example.syncspace.ui.theme.SyncSpaceTheme
import com.example.syncspace.ui.theme.SyncSpaceThemeTokens

@Composable
fun RegisterScreen(
    modifier: Modifier = Modifier,
    onBackClick: () -> Unit = {},
    onRegisterClick: (email: String) -> Unit = {},
    onGoogleSignInClick: () -> Unit = {},
    onLoginClick: () -> Unit = {}
) {
    val colors = SyncSpaceThemeTokens.colors
    var email by remember { mutableStateOf("") }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.White)
    ) {
        BoxWithConstraints(
            modifier = Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .imePadding()
        ) {
            val minScreenHeight = maxHeight

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .defaultMinSize(minHeight = minScreenHeight),
                    verticalArrangement = Arrangement.SpaceBetween
                ) {
                    Column(modifier = Modifier.fillMaxWidth()) {
                        Spacer(modifier = Modifier.height(34.dp))

                        AuthTopBar(
                            title = "Register",
                            onBackClick = onBackClick,
                            modifier = Modifier.padding(start = 42.dp, end = 24.dp)
                        )

                        Spacer(modifier = Modifier.height(28.dp))

                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 28.dp)
                        ) {
                            AuthUnderlineTextField(
                                label = "GMAIL",
                                value = email,
                                onValueChange = { email = it },
                                placeholder = "Enter your gmail",
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                                isValid = email.isNotEmpty(),
                                showClearIcon = true
                            )

                            Spacer(modifier = Modifier.height(16.dp))

                            AuthUnderlineTextField(
                                label = "USERNAME",
                                value = username,
                                onValueChange = { username = it },
                                placeholder = "Enter your username",
                                isValid = username.isNotEmpty(),
                                showClearIcon = true
                            )

                            Spacer(modifier = Modifier.height(16.dp))

                            AuthUnderlineTextField(
                                label = "PASSWORD",
                                value = password,
                                onValueChange = { password = it },
                                placeholder = "Enter your password",
                                visualTransformation = PasswordVisualTransformation(),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                                isValid = password.isNotEmpty(),
                                showClearIcon = false
                            )
                        }
                    }

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 40.dp, bottom = 36.dp)
                            .padding(horizontal = 42.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            PrimaryButton(
                                text = "Register",
                                onClick = { onRegisterClick(email) }
                            )

                            OrDivider()

                            GoogleSignInButton(onClick = onGoogleSignInClick)
                        }

                        Spacer(modifier = Modifier.height(20.dp))

                        Row(
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Already have an account?",
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.Medium,
                                fontSize = 16.sp,
                                lineHeight = 20.sp,
                                color = colors.authFooterGray
                            )
                            Text(
                                text = " Login",
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.Medium,
                                fontSize = 16.sp,
                                lineHeight = 20.sp,
                                color = colors.primaryNavy,
                                modifier = Modifier.clickable(onClick = onLoginClick)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
fun RegisterScreenPreview() {
    SyncSpaceTheme {
        RegisterScreen()
    }
}
