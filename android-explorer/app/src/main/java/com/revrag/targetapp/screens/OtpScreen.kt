package com.revrag.targetapp.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.material3.OutlinedButton
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
fun OtpScreen(
    email: String,
    onOtpVerified: () -> Unit,
    onBack: () -> Unit
) {
    var otpCode by remember { mutableStateOf("123456") }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(SoftCream)
            .padding(24.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Header Bar
            Column(modifier = Modifier.padding(top = 16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .background(HoneyBeige, RoundedCornerShape(8.dp))
                            .border(1.dp, BorderNeutral, RoundedCornerShape(8.dp))
                            .padding(horizontal = 10.dp, vertical = 5.dp)
                    ) {
                        Text(
                            text = "AUTH // OTP",
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = DynamicBlack
                        )
                    }

                    Text(
                        text = "STEP 2 OF 2",
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        color = MutedNeutral
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                Text(
                    text = "Verify Code",
                    fontSize = 30.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = (-0.8).sp,
                    color = DynamicBlack
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Enter the 6-digit one-time passcode for demo verification.",
                    fontSize = 14.sp,
                    color = MutedNeutral,
                    lineHeight = 20.sp
                )
            }

            // OTP Input Card
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(OffWhite, RoundedCornerShape(12.dp))
                    .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                    .padding(20.dp)
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(EggLiqueur, RoundedCornerShape(8.dp))
                        .padding(12.dp)
                ) {
                    Text(
                        text = "DEMO MODE: Any 6-digit numeric sequence will pass.",
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.SemiBold,
                        color = DynamicBlack
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "6-DIGIT PASSCODE",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = DynamicBlack
                )
                Spacer(modifier = Modifier.height(6.dp))

                OutlinedTextField(
                    value = otpCode,
                    onValueChange = {
                        if (it.length <= 6) {
                            otpCode = it
                            errorMessage = null
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("000000", color = MutedNeutral) },
                    singleLine = true,
                    shape = RoundedCornerShape(8.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ApocalypticOrange,
                        unfocusedBorderColor = BorderNeutral,
                        focusedTextColor = DynamicBlack,
                        unfocusedTextColor = DynamicBlack
                    )
                )

                if (errorMessage != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = errorMessage ?: "",
                        color = ApocalypticOrange,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            // Actions
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 24.dp)
            ) {
                Button(
                    onClick = {
                        if (otpCode.length == 6) {
                            onOtpVerified()
                        } else {
                            errorMessage = "Passcode must be 6 digits"
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ApocalypticOrange,
                        contentColor = OffWhite
                    )
                ) {
                    Text(
                        text = "Verify Code & Enter Dashboard",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                OutlinedButton(
                    onClick = onBack,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    shape = RoundedCornerShape(12.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, BorderNeutral),
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = DynamicBlack
                    )
                ) {
                    Text(
                        text = "Back to Sign In",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }
    }
}
