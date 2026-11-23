package com.example.syncspace.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onKeyEvent
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.syncspace.ui.components.AuthTopBar
import com.example.syncspace.ui.components.PrimaryButton
import com.example.syncspace.ui.theme.SyncSpaceTheme
import com.example.syncspace.ui.theme.SyncSpaceThemeTokens
import kotlinx.coroutines.delay

@Composable
fun VerificationCodeScreen(
    modifier: Modifier = Modifier,
    email: String = "",
    onBackClick: () -> Unit = {},
    onVerifyClick: (code: String) -> Unit = {},
    onResendCodeClick: () -> Unit = {}
) {
    val colors = SyncSpaceThemeTokens.colors
    val otpDigits = remember { mutableStateListOf("", "", "", "") }
    val focusRequesters = remember { List(4) { FocusRequester() } }
    var timeLeftSeconds by remember { mutableIntStateOf(299) }

    LaunchedEffect(Unit) {
        while (timeLeftSeconds > 0) {
            delay(1000)
            timeLeftSeconds--
        }
    }

    val timerText = String.format("%d:%02d", timeLeftSeconds / 60, timeLeftSeconds % 60)

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
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Spacer(modifier = Modifier.height(34.dp))

                        AuthTopBar(
                            title = "Verification Code",
                            onBackClick = onBackClick,
                            modifier = Modifier.padding(start = 42.dp, end = 24.dp)
                        )

                        Spacer(modifier = Modifier.height(61.dp))

                        Text(
                            text = "Verify Code",
                            fontFamily = FontFamily.SansSerif,
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 24.sp,
                            lineHeight = 32.sp,
                            color = colors.black100,
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(7.dp))

                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.padding(horizontal = 24.dp)
                        ) {
                            Text(
                                text = "Please enter the code we just sent to email",
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.Normal,
                                fontSize = 15.sp,
                                lineHeight = 20.sp,
                                color = colors.authFooterGray,
                                textAlign = TextAlign.Center
                            )

                            Text(
                                text = email.ifEmpty { "your email" },
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.SemiBold,
                                fontSize = 15.sp,
                                lineHeight = 20.sp,
                                color = colors.primaryNavy,
                                textAlign = TextAlign.Center
                            )
                        }

                        Spacer(modifier = Modifier.height(56.dp))

                        Row(
                            horizontalArrangement = Arrangement.spacedBy(20.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            otpDigits.indices.forEach { index ->
                                val digit = otpDigits[index]

                                Box(
                                    modifier = Modifier
                                        .size(55.dp)
                                        .clip(RoundedCornerShape(10.dp))
                                        .background(Color.White)
                                        .border(
                                            width = 1.dp,
                                            color = colors.primaryNavy,
                                            shape = RoundedCornerShape(10.dp)
                                        ),
                                    contentAlignment = Alignment.Center
                                ) {
                                    if (digit.isEmpty()) {
                                        Text(
                                            text = "0",
                                            fontFamily = FontFamily.SansSerif,
                                            fontWeight = FontWeight.SemiBold,
                                            fontSize = 20.sp,
                                            lineHeight = 20.sp,
                                            color = colors.otpPlaceholderGray,
                                            textAlign = TextAlign.Center
                                        )
                                    }

                                    BasicTextField(
                                        value = digit,
                                        onValueChange = { newValue ->
                                            if (newValue.length <= 1 && newValue.all { it.isDigit() }) {
                                                otpDigits[index] = newValue
                                                if (newValue.isNotEmpty() && index < 3) {
                                                    focusRequesters[index + 1].requestFocus()
                                                }
                                            }
                                        },
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .focusRequester(focusRequesters[index])
                                            .onKeyEvent { keyEvent ->
                                                if (keyEvent.key == Key.Backspace && digit.isEmpty() && index > 0) {
                                                    focusRequesters[index - 1].requestFocus()
                                                    true
                                                } else {
                                                    false
                                                }
                                            },
                                        textStyle = TextStyle(
                                            fontFamily = FontFamily.SansSerif,
                                            fontWeight = FontWeight.SemiBold,
                                            fontSize = 20.sp,
                                            lineHeight = 20.sp,
                                            color = colors.black100,
                                            textAlign = TextAlign.Center
                                        ),
                                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                        singleLine = true,
                                        cursorBrush = SolidColor(colors.primaryNavy)
                                    )
                                }
                            }
                        }
                    }

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 40.dp, bottom = 36.dp)
                            .padding(horizontal = 42.5.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = timerText,
                            fontFamily = FontFamily.SansSerif,
                            fontWeight = FontWeight.Normal,
                            fontSize = 17.sp,
                            lineHeight = 22.sp,
                            letterSpacing = (-0.4).sp,
                            color = colors.primaryNavy,
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        Row(
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Didn’t receive the code?",
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.Medium,
                                fontSize = 14.sp,
                                lineHeight = 20.sp,
                                color = colors.authFooterGray
                            )
                            Text(
                                text = " Send Again",
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.Medium,
                                fontSize = 14.sp,
                                lineHeight = 20.sp,
                                color = colors.primaryNavy,
                                modifier = Modifier.clickable(onClick = onResendCodeClick)
                            )
                        }

                        Spacer(modifier = Modifier.height(24.dp))

                        PrimaryButton(
                            text = "Verify",
                            onClick = { onVerifyClick(otpDigits.joinToString("")) }
                        )
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
fun VerificationCodeScreenPreview() {
    SyncSpaceTheme {
        VerificationCodeScreen()
    }
}
