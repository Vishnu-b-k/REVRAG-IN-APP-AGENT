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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
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
import com.revrag.ui.theme.EggLiqueur
import com.revrag.ui.theme.HoneyBeige
import com.revrag.ui.theme.MutedNeutral
import com.revrag.ui.theme.OffWhite
import com.revrag.ui.theme.SoftCream

data class AuditRecord(
    val id: String,
    val title: String,
    val status: String,
    val author: String,
    val date: String,
    val payloadSize: String,
    val tokensCaptured: Int
)

val auditRecords = listOf(
    AuditRecord("REC-001", "Login Screen Observation Scan", "COMPLETED", "Agent Alpha", "Sep 18, 2026", "24.2 KB", 18),
    AuditRecord("REC-002", "OTP Verification State Node", "COMPLETED", "Agent Alpha", "Sep 18, 2026", "18.6 KB", 14),
    AuditRecord("REC-003", "Dashboard Layout Token Map", "VERIFIED", "Agent Beta", "Sep 18, 2026", "45.1 KB", 28),
    AuditRecord("REC-004", "Scrollable Feed Dedup Analysis", "PENDING", "Agent Gamma", "Sep 18, 2026", "32.0 KB", 22),
    AuditRecord("REC-005", "Settings Dark Mode Extractor", "STAGED", "Agent Delta", "Sep 18, 2026", "12.8 KB", 16)
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ListDetailsScreen(
    onBack: () -> Unit
) {
    var selectedRecord by remember { mutableStateOf<AuditRecord?>(null) }
    val sheetState = rememberModalBottomSheetState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SoftCream)
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
                text = "BRANCH 03",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                color = MutedNeutral
            )
        }

        Text(
            text = "Audit Records",
            fontSize = 30.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = (-0.8).sp,
            color = DynamicBlack
        )

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = "Select any record below to inspect details in the bottom sheet modal.",
            fontSize = 14.sp,
            color = MutedNeutral
        )

        Spacer(modifier = Modifier.height(16.dp))

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(auditRecords) { record ->
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(OffWhite, RoundedCornerShape(12.dp))
                        .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                        .clickable { selectedRecord = record }
                        .padding(18.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = record.id,
                                fontSize = 11.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                color = ApocalypticOrange
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = record.title,
                                fontSize = 15.sp,
                                fontWeight = FontWeight.Bold,
                                color = DynamicBlack
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "By ${record.author} • ${record.date}",
                                fontSize = 12.sp,
                                color = MutedNeutral
                            )
                        }

                        Box(
                            modifier = Modifier
                                .background(EggLiqueur, RoundedCornerShape(6.dp))
                                .padding(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text(
                                text = record.status,
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                color = DynamicBlack
                            )
                        }
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }

    // Modal Bottom Sheet for Details (Sections 8, 9, 10)
    if (selectedRecord != null) {
        val record = selectedRecord!!
        ModalBottomSheet(
            onDismissRequest = { selectedRecord = null },
            sheetState = sheetState,
            containerColor = SoftCream,
            shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .background(DynamicBlack, RoundedCornerShape(6.dp))
                            .padding(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = record.id,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = OffWhite
                        )
                    }

                    Box(
                        modifier = Modifier
                            .background(ApocalypticOrange, RoundedCornerShape(6.dp))
                            .padding(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text(
                            text = record.status,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = OffWhite
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                Text(
                    text = record.title,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = DynamicBlack
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Metadata Details Box
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(OffWhite, RoundedCornerShape(12.dp))
                        .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                        .padding(16.dp)
                ) {
                    DetailRow(label = "AGENT / AUTHOR", value = record.author)
                    DetailRow(label = "TIMESTAMP", value = record.date)
                    DetailRow(label = "PAYLOAD SIZE", value = record.payloadSize)
                    DetailRow(label = "TOKENS CAPTURED", value = "${record.tokensCaptured} tokens")
                }

                Spacer(modifier = Modifier.height(20.dp))

                Button(
                    onClick = { selectedRecord = null },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = DynamicBlack,
                        contentColor = OffWhite
                    )
                ) {
                    Text(
                        text = "Dismiss Details Modal",
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

@Composable
fun DetailRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            fontSize = 11.sp,
            fontFamily = FontFamily.Monospace,
            color = MutedNeutral,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = value,
            fontSize = 13.sp,
            fontFamily = FontFamily.Monospace,
            color = DynamicBlack,
            fontWeight = FontWeight.SemiBold
        )
    }
}
