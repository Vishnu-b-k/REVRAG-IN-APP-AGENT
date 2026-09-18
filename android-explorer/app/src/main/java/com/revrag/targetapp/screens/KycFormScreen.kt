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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
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
import com.revrag.ui.theme.EggLiqueur
import com.revrag.ui.theme.HoneyBeige
import com.revrag.ui.theme.MutedNeutral
import com.revrag.ui.theme.OffWhite
import com.revrag.ui.theme.SoftCream

@Composable
fun KycFormScreen(
    onBack: () -> Unit
) {
    var fullName by remember { mutableStateOf("Vishnu B.K.") }
    var idType by remember { mutableStateOf("Passport") }
    var annualTier by remember { mutableStateOf("Tier 1: < $50K") }
    var showDialog by remember { mutableStateOf(false) }

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(SoftCream)
            .verticalScroll(scrollState)
            .padding(horizontal = 24.dp)
    ) {
        // Top Nav
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
                text = "BRANCH 02",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                color = MutedNeutral
            )
        }

        Text(
            text = "KYC Verification",
            fontSize = 30.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = (-0.8).sp,
            color = DynamicBlack
        )

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = "Multi-input form with text, selectable pills, and modal submission.",
            fontSize = 14.sp,
            color = MutedNeutral
        )

        Spacer(modifier = Modifier.height(20.dp))

        // Form Container Card
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(OffWhite, RoundedCornerShape(12.dp))
                .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                .padding(20.dp)
        ) {
            // Field 1: Full Name
            Text(
                text = "FULL LEGAL NAME",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = DynamicBlack
            )
            Spacer(modifier = Modifier.height(6.dp))
            OutlinedTextField(
                value = fullName,
                onValueChange = { fullName = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(8.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = ApocalypticOrange,
                    unfocusedBorderColor = BorderNeutral,
                    focusedTextColor = DynamicBlack,
                    unfocusedTextColor = DynamicBlack
                )
            )

            Spacer(modifier = Modifier.height(18.dp))

            // Field 2: Document Type Selection
            Text(
                text = "IDENTIFICATION TYPE",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = DynamicBlack
            )
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf("Passport", "National ID", "Driver License").forEach { type ->
                    val isSelected = idType == type
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .background(
                                if (isSelected) ApocalypticOrange else EggLiqueur,
                                RoundedCornerShape(8.dp)
                            )
                            .border(
                                1.dp,
                                if (isSelected) ApocalypticOrange else BorderNeutral,
                                RoundedCornerShape(8.dp)
                            )
                            .clickable { idType = type }
                            .padding(vertical = 10.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = type,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (isSelected) OffWhite else DynamicBlack
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Field 3: Expected Tier
            Text(
                text = "ESTIMATED TRANSACTION VOLUME",
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                color = DynamicBlack
            )
            Spacer(modifier = Modifier.height(8.dp))
            listOf("Tier 1: < $50K", "Tier 2: $50K - $250K", "Tier 3: > $250K").forEach { tier ->
                val isSelected = annualTier == tier
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 6.dp)
                        .background(
                            if (isSelected) HoneyBeige else SoftCream,
                            RoundedCornerShape(8.dp)
                        )
                        .border(
                            1.dp,
                            if (isSelected) ApocalypticOrange else BorderNeutral,
                            RoundedCornerShape(8.dp)
                        )
                        .clickable { annualTier = tier }
                        .padding(horizontal = 14.dp, vertical = 12.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = tier,
                            fontSize = 13.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                            color = DynamicBlack
                        )
                        if (isSelected) {
                            Text(
                                text = "✓ ACTIVE",
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace,
                                fontWeight = FontWeight.Bold,
                                color = ApocalypticOrange
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Submit Button
            Button(
                onClick = { showDialog = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ApocalypticOrange,
                    contentColor = OffWhite
                )
            ) {
                Text(
                    text = "Submit Verification Form",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        Spacer(modifier = Modifier.height(40.dp))
    }

    // Modal Confirmation Dialog (Required by Section 3: Dialog/Bottom Sheet discoverable)
    if (showDialog) {
        AlertDialog(
            onDismissRequest = { showDialog = false },
            confirmButton = {
                Button(
                    onClick = {
                        showDialog = false
                        onBack()
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ApocalypticOrange,
                        contentColor = OffWhite
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Confirm & Return", fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                Button(
                    onClick = { showDialog = false },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = HoneyBeige,
                        contentColor = DynamicBlack
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Cancel")
                }
            },
            title = {
                Text(
                    text = "Confirm KYC Submission",
                    fontWeight = FontWeight.Bold,
                    color = DynamicBlack
                )
            },
            text = {
                Text(
                    text = "Verification data for '$fullName' ($idType) has been staged for processing.",
                    color = MutedNeutral,
                    fontSize = 14.sp
                )
            },
            containerColor = OffWhite,
            shape = RoundedCornerShape(12.dp)
        )
    }
}
