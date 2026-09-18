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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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

@Composable
fun DashboardScreen(
    onNavigateToFeed: () -> Unit,
    onNavigateToKyc: () -> Unit,
    onNavigateToList: () -> Unit,
    onNavigateToSettings: () -> Unit,
    onLogout: () -> Unit
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SoftCream)
            .verticalScroll(scrollState)
            .padding(24.dp)
    ) {
        // Top Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .background(DynamicBlack, RoundedCornerShape(8.dp))
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Text(
                    text = "REVRAG // HUB",
                    color = OffWhite,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
            }

            Box(
                modifier = Modifier
                    .background(HoneyBeige, RoundedCornerShape(8.dp))
                    .border(1.dp, BorderNeutral, RoundedCornerShape(8.dp))
                    .clickable { onNavigateToSettings() }
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Text(
                    text = "SETTINGS ⚙",
                    color = DynamicBlack,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Hero Typography
        Text(
            text = "Exploration Hub",
            fontSize = 32.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = (-1.0).sp,
            color = DynamicBlack
        )

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = "Select a branch to test autonomous navigation and state tracking.",
            fontSize = 14.sp,
            color = MutedNeutral,
            lineHeight = 20.sp
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Stats Block (Editorial Grid)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .background(HoneyBeige, RoundedCornerShape(12.dp))
                    .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                    .padding(16.dp)
            ) {
                Column {
                    Text(
                        text = "DISCOVERED",
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        color = MutedNeutral,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "12",
                        fontSize = 26.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = DynamicBlack
                    )
                    Text(
                        text = "Screens mapped",
                        fontSize = 12.sp,
                        color = DynamicBlack
                    )
                }
            }

            Box(
                modifier = Modifier
                    .weight(1f)
                    .background(EggLiqueur, RoundedCornerShape(12.dp))
                    .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                    .padding(16.dp)
            ) {
                Column {
                    Text(
                        text = "ACCURACY",
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        color = MutedNeutral,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "98.4%",
                        fontSize = 26.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = ApocalypticOrange
                    )
                    Text(
                        text = "Token match",
                        fontSize = 12.sp,
                        color = DynamicBlack
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(28.dp))

        // Navigation Menu Cards
        Text(
            text = "TARGET BRANCHES",
            fontSize = 11.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold,
            color = DynamicBlack
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Branch 1: Scrollable Feed
        DashboardBranchCard(
            badge = "01 // SCROLL",
            title = "Scrollable Content Feed",
            description = "Test vertical gestures, repeated cards, and state deduplication.",
            onClick = onNavigateToFeed
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Branch 2: KYC Form
        DashboardBranchCard(
            badge = "02 // FORM",
            title = "KYC Onboarding Form",
            description = "Multi-type input verification (text, dropdown selector, radio buttons).",
            onClick = onNavigateToKyc
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Branch 3: List & Details
        DashboardBranchCard(
            badge = "03 // LIST & MODAL",
            title = "Transaction Audit List",
            description = "Inspect detail views, bottom sheet triggers, and back-navigation.",
            onClick = onNavigateToList
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Sign out row
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onLogout() }
                .padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.Center
        ) {
            Text(
                text = "← Return to Login Screen",
                fontSize = 13.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.SemiBold,
                color = MutedNeutral
            )
        }
    }
}

@Composable
fun DashboardBranchCard(
    badge: String,
    title: String,
    description: String,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(OffWhite, RoundedCornerShape(12.dp))
            .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
            .clickable { onClick() }
            .padding(18.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = badge,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = ApocalypticOrange
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = title,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    color = DynamicBlack
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = description,
                    fontSize = 13.sp,
                    color = MutedNeutral,
                    lineHeight = 18.sp
                )
            }

            Box(
                modifier = Modifier
                    .background(HoneyBeige, RoundedCornerShape(8.dp))
                    .padding(horizontal = 10.dp, vertical = 6.dp)
            ) {
                Text(
                    text = "OPEN →",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = DynamicBlack
                )
            }
        }
    }
}
