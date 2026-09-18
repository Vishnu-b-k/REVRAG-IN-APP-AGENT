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
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
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

data class FeedItem(
    val id: String,
    val title: String,
    val category: String,
    val timestamp: String,
    val summary: String,
    val tag: String
)

val sampleFeed = listOf(
    FeedItem(
        id = "EVT-101",
        title = "Accessibility Tree Stream Stabilized",
        category = "SYSTEM PIPELINE",
        timestamp = "10:42 AM",
        summary = "Android accessibility node snapshot mapped without race conditions. Dynamic bounds normalized across coordinate spaces.",
        tag = "CRITICAL"
    ),
    FeedItem(
        id = "EVT-102",
        title = "Editorial Palette Token Extractor",
        category = "DESIGN TOKENS",
        timestamp = "10:40 AM",
        summary = "Detected brand surfaces: Apocalyptic Orange (#DF5E39) alongside Honey Beige and Dynamic Black. 0 gradients identified.",
        tag = "DESIGN"
    ),
    FeedItem(
        id = "EVT-103",
        title = "Backtracking Frontier Updated",
        category = "EXPLORATION",
        timestamp = "10:38 AM",
        summary = "Branch 2 completed all interactable actions. Backtracking to Dashboard node via system back gesture.",
        tag = "AUTONOMOUS"
    ),
    FeedItem(
        id = "EVT-104",
        title = "Compacted Pack Compression: 84%",
        category = "KNOWLEDGE PACK",
        timestamp = "10:35 AM",
        summary = "Volatile timestamp nodes pruned from canonical state graph. Preserved all semantic buttons, form fields, and journeys.",
        tag = "COMPACT"
    ),
    FeedItem(
        id = "EVT-105",
        title = "Rebuild HTML Spec Generated",
        category = "RECONSTRUCTION",
        timestamp = "10:30 AM",
        summary = "Reconstructed Login and Dashboard screens from pack alone. 100% token fidelity achieved on layout hierarchy.",
        tag = "VERIFIED"
    ),
    FeedItem(
        id = "EVT-106",
        title = "Multi-step Flow Completed",
        category = "ORCHESTRATOR",
        timestamp = "10:25 AM",
        summary = "End-to-end journey from Splash -> Login -> OTP verified successfully without human intervention.",
        tag = "STAGE DEMO"
    )
)

@Composable
fun FeedScreen(
    onBack: () -> Unit
) {
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
                text = "BRANCH 01",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                color = MutedNeutral
            )
        }

        // Title
        Text(
            text = "Activity Feed",
            fontSize = 30.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = (-0.8).sp,
            color = DynamicBlack
        )

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = "Scroll through repeated items to test vertical scroll actions.",
            fontSize = 14.sp,
            color = MutedNeutral
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Scrollable List
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            itemsIndexed(sampleFeed) { index, item ->
                FeedCard(item = item, index = index)
            }

            item {
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

@Composable
fun FeedCard(item: FeedItem, index: Int) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(OffWhite, RoundedCornerShape(12.dp))
            .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
            .padding(18.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .background(EggLiqueur, RoundedCornerShape(6.dp))
                        .padding(horizontal = 8.dp, vertical = 3.dp)
                ) {
                    Text(
                        text = item.category,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        color = DynamicBlack
                    )
                }

                Text(
                    text = item.timestamp,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    color = MutedNeutral
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = item.title,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = DynamicBlack
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = item.summary,
                fontSize = 13.sp,
                color = MutedNeutral,
                lineHeight = 18.sp
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "ID: ${item.id}",
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    color = MutedNeutral
                )

                Box(
                    modifier = Modifier
                        .background(
                            if (index % 2 == 0) ApocalypticOrange else DynamicBlack,
                            RoundedCornerShape(6.dp)
                        )
                        .padding(horizontal = 8.dp, vertical = 3.dp)
                ) {
                    Text(
                        text = item.tag,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold,
                        color = OffWhite
                    )
                }
            }
        }
    }
}
