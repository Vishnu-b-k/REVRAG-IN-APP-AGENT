package com.revrag.explorer.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
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
import com.revrag.explorer.service.ExplorerAccessibilityService
import com.revrag.ui.theme.ApocalypticOrange
import com.revrag.ui.theme.BorderNeutral
import com.revrag.ui.theme.DynamicBlack
import com.revrag.ui.theme.EggLiqueur
import com.revrag.ui.theme.HoneyBeige
import com.revrag.ui.theme.MutedNeutral
import com.revrag.ui.theme.OffWhite

@Composable
fun ExplorerControlOverlay(
    modifier: Modifier = Modifier,
    onOpenAccessibilitySettings: () -> Unit
) {
    val status by ExplorerAccessibilityService.statusFlow.collectAsState()
    var isExpanded by remember { mutableStateOf(false) }

    val serviceConnected = ExplorerAccessibilityService.instance != null

    Box(
        modifier = modifier
            .fillMaxWidth()
            .padding(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(DynamicBlack, RoundedCornerShape(12.dp))
                .border(1.dp, if (status.isRunning) ApocalypticOrange else BorderNeutral, RoundedCornerShape(12.dp))
                .padding(14.dp)
        ) {
            // Header row with toggle
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { isExpanded = !isExpanded },
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .background(if (status.isRunning) ApocalypticOrange else HoneyBeige, RoundedCornerShape(6.dp))
                            .padding(horizontal = 8.dp, vertical = 3.dp)
                    ) {
                        Text(
                            text = if (status.isRunning) "RUNNING" else "AGENT HUD",
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = if (status.isRunning) OffWhite else DynamicBlack
                        )
                    }

                    Spacer(modifier = Modifier.width(8.dp))

                    Text(
                        text = "Step ${status.step}/${status.maxSteps}",
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        color = OffWhite,
                        fontWeight = FontWeight.SemiBold
                    )
                }

                Text(
                    text = if (isExpanded) "▲ COLLAPSE" else "▼ EXPAND",
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    color = EggLiqueur
                )
            }

            AnimatedVisibility(visible = isExpanded) {
                Column(modifier = Modifier.fillMaxWidth().padding(top = 12.dp)) {
                    // Accessibility Service Status Warning if not enabled
                    if (!serviceConnected) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(ApocalypticOrange, RoundedCornerShape(8.dp))
                                .clickable { onOpenAccessibilitySettings() }
                                .padding(10.dp)
                        ) {
                            Text(
                                text = "⚠ Accessibility Service Disabled. Tap here to enable RevRag Explorer in Settings.",
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                color = OffWhite
                            )
                        }
                        Spacer(modifier = Modifier.height(10.dp))
                    }

                    // Metadata Status Box
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(OffWhite, RoundedCornerShape(8.dp))
                            .padding(10.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "LAST ACTION:",
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                color = MutedNeutral,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = status.lastAction,
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                color = DynamicBlack,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Spacer(modifier = Modifier.height(4.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "RESULT:",
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                color = MutedNeutral,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = status.lastResult.take(32),
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                color = DynamicBlack
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Action Button (Start / Stop)
                    if (status.isRunning) {
                        Button(
                            onClick = {
                                ExplorerAccessibilityService.instance?.stopExploration()
                            },
                            modifier = Modifier.fillMaxWidth().height(42.dp),
                            shape = RoundedCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = HoneyBeige,
                                contentColor = DynamicBlack
                            )
                        ) {
                            Text(
                                text = "Stop Exploration",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    } else {
                        Button(
                            onClick = {
                                if (serviceConnected) {
                                    ExplorerAccessibilityService.instance?.startExploration()
                                } else {
                                    onOpenAccessibilitySettings()
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(42.dp),
                            shape = RoundedCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = ApocalypticOrange,
                                contentColor = OffWhite
                            )
                        ) {
                            Text(
                                text = if (serviceConnected) "Start Autonomous Exploration" else "Enable Accessibility Service",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    }
}
