package com.example.syncspace.ui.screens

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.syncspace.R
import com.example.syncspace.ui.theme.SyncSpaceTheme
import com.example.syncspace.ui.theme.SyncSpaceThemeTokens

@Composable
fun OnboardingScreen(
    modifier: Modifier = Modifier,
    onLoginClick: () -> Unit = {},
    onRegisterClick: () -> Unit = {}
) {
    val colors = SyncSpaceThemeTokens.colors

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(brush = colors.onboardingGradient)
    ) {
        BoxWithConstraints(
            modifier = Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
        ) {
            val screenHeight = maxHeight
            val topSpacerHeight = if (screenHeight > 750.dp) 32.dp else 12.dp
            val middleSpacerHeight = if (screenHeight > 750.dp) 24.dp else 12.dp
            val illustrationHeight = if (screenHeight > 750.dp) 300.dp else 240.dp

            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 32.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Spacer(modifier = Modifier.height(topSpacerHeight))

                    Image(
                        painter = painterResource(id = R.drawable.img_onboarding_illustration),
                        contentDescription = "SyncSpace Illustration",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(illustrationHeight),
                        contentScale = ContentScale.Fit
                    )
                }

                Spacer(modifier = Modifier.height(middleSpacerHeight))

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Everything in Sync.",
                        fontFamily = FontFamily.SansSerif,
                        fontWeight = FontWeight.Bold,
                        fontSize = 38.sp,
                        lineHeight = 44.sp,
                        letterSpacing = (-1).sp,
                        color = Color.White,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Keep everyone on the same page. Track progress, manage shared expenses, and achieve more together.",
                        fontFamily = FontFamily.SansSerif,
                        fontWeight = FontWeight.Medium,
                        fontSize = 14.sp,
                        lineHeight = 20.sp,
                        color = colors.blue20,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(32.dp))

                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp)
                                .shadow(
                                    elevation = 8.dp,
                                    shape = RoundedCornerShape(40.dp),
                                    ambientColor = Color(0x0F232C5D),
                                    spotColor = Color(0x0F232C5D)
                                )
                                .clip(RoundedCornerShape(40.dp))
                                .background(Color.White)
                                .clickable(onClick = onLoginClick),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "Log In",
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.Medium,
                                fontSize = 14.sp,
                                color = colors.primaryNavy
                            )
                        }

                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(52.dp)
                                .shadow(
                                    elevation = 8.dp,
                                    shape = RoundedCornerShape(40.dp),
                                    ambientColor = Color(0x0F232C5D),
                                    spotColor = Color(0x0F232C5D)
                                )
                                .clip(RoundedCornerShape(40.dp))
                                .background(colors.primaryNavy)
                                .border(
                                    width = 1.dp,
                                    color = Color.White,
                                    shape = RoundedCornerShape(40.dp)
                                )
                                .clickable(onClick = onRegisterClick),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "Register",
                                fontFamily = FontFamily.SansSerif,
                                fontWeight = FontWeight.Medium,
                                fontSize = 14.sp,
                                color = Color.White
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    Text(
                        text = "By continuing you agree Terms of Services & Privacy Policy",
                        fontFamily = FontFamily.SansSerif,
                        fontWeight = FontWeight.Normal,
                        fontSize = 12.sp,
                        lineHeight = 16.sp,
                        color = colors.blue40,
                        textAlign = TextAlign.Center,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 16.dp)
                    )
                }
            }
        }
    }
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
fun OnboardingScreenPreview() {
    SyncSpaceTheme {
        OnboardingScreen()
    }
}
