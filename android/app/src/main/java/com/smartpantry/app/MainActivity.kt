
package com.smartpantry.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.smartpantry.app.ui.theme.SmartPantryTheme
import com.smartpantry.app.ui.session.SessionGate

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            SmartPantryTheme {
                SessionGate()
            }
        }
    }
}
