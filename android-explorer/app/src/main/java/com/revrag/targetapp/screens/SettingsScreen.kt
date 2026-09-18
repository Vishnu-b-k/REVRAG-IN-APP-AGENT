package com.revrag.targetapp.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.revrag.ui.theme.ApocalypticOrange
import com.revrag.ui.theme.BorderNeutral
import com.revrag.ui.theme.DynamicBlack
import com.revrag.ui.theme.HoneyBeige
import com.revrag.ui.theme.MutedNeutral
import com.revrag.ui.theme.OffWhite
import com.revrag.ui.theme.SoftCream

@Composable
fun SettingsScreen(
    isDarkMode: Boolean,
    onToggleDarkMode: (Boolean) -> Unit,
    onResetDemoData: () -> Unit,
    onBack: () -> Unit
) {
    var orchestratorUrl by remember { mutableStateOf("http://10.0.2.2:8000") }
    var resetBannerMessage by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(if (isDarkMode) DynamicBlack else SoftCream)
            .padding(horizontal = 24.dp)
    ) {
        // Navigation Bar
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 24.dp, bottom = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .background(HoneyBeige, RoundedCornerShape(8.dp))
                    .border(1.dp, BorderNeutral, RoundedCornerShape(8.dp))
                    .clickable { onBack() }
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Text(
                    text = "← BACK TO HUB",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = DynamicBlack
                )
            }

            Text(
                text = "CONFIG // PREFS",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                color = MutedNeutral
            )
        }

        Text(
            text = "App Settings",
            fontSize = 30.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = (-0.8).sp,
            color = if (isDarkMode) OffWhite else DynamicBlack
        )

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = "Toggle visual themes to verify design extraction mode detection.",
            fontSize = 14.sp,
            color = MutedNeutral
        )

        Spacer(modifier = Modifier.height(20.dp))

        // Settings Container
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(if (isDarkMode) DynamicBlack else OffWhite, RoundedCornerShape(12.dp))
                .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                .padding(20.dp)
        ) {
            // Theme Switch Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "DARK THEME MODE",
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        color = if (isDarkMode) OffWhite else DynamicBlack
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = if (isDarkMode) "Dynamic Black (#151314) active" else "Soft Cream & Honey active",
                        fontSize = 13.sp,
                        color = MutedNeutral
                    )
                }

                Switch(
                    checked = isDarkMode,
                    onCheckedChange = { onToggleDarkMode(it) },
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = OffWhite,
                        checkedTrackColor = ApocalypticOrange,
                        uncheckedThumbColor = DynamicBlack,
                        uncheckedTrackColor = HoneyBeige
                    )
                )
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Orchestrator URL
            Text(
                text = "ORCHESTRATOR BACKEND URL",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = if (isDarkMode) OffWhite else DynamicBlack
            )
            Spacer(modifier = Modifier.height(6.dp))
            OutlinedTextField(
                value = orchestratorUrl,
                onValueChange = { orchestratorUrl = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(8.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = ApocalypticOrange,
                    unfocusedBorderColor = BorderNeutral,
                    focusedTextColor = if (isDarkMode) OffWhite else DynamicBlack,
                    unfocusedTextColor = if (isDarkMode) OffWhite else DynamicBlack
                )
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Reset Data Action (Phase T-4 requirement)
            Button(
                onClick = {
                    onResetDemoData()
                    resetBannerMessage = "✓ Demo state reset to initial Splash/Login state."
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = HoneyBeige,
                    contentColor = DynamicBlack
                )
            ) {
                Text(
                    text = "Reset Demo State to Initial",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            if (resetBannerMessage != null) {
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = resetBannerMessage ?: "",
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.SemiBold,
                    color = ApocalypticOrange
                )
            }
        }
    }
}
