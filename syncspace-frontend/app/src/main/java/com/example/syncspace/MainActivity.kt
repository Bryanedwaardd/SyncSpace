package com.example.syncspace

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.example.syncspace.navigation.AppNavigation
import com.example.syncspace.ui.theme.SyncSpaceTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SyncSpaceTheme {
                AppNavigation()
            }
        }
    }
}
