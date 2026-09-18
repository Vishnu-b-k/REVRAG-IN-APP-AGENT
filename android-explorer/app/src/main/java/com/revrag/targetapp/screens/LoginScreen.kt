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
import androidx.compose.ui.text.input.PasswordVisualTransformation
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
fun LoginScreen(
    onLoginSuccess: (email: String) -> Unit,
    onBack: () -> Unit
) {
    var email by remember { mutableStateOf("agent.explorer@revrag.ai") }
    var password by remember { mutableStateOf("demo1234") }
    var errorText by remember { mutableStateOf<String?>(null) }

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
                            text = "AUTH // LOGIN",
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = DynamicBlack
                        )
                    }

                    Text(
                        text = "STEP 1 OF 2",
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        color = MutedNeutral
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                Text(
                    text = "Operator Sign In",
                    fontSize = 30.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = (-0.8).sp,
                    color = DynamicBlack
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Authenticate the exploration instance to access workspace screens.",
                    fontSize = 14.sp,
                    color = MutedNeutral,
                    lineHeight = 20.sp
                )
            }

            // Input Fields Card
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(OffWhite, RoundedCornerShape(12.dp))
                    .border(1.dp, BorderNeutral, RoundedCornerShape(12.dp))
                    .padding(20.dp)
            ) {
                Text(
                    text = "EMAIL ADDRESS",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = DynamicBlack
                )
                Spacer(modifier = Modifier.height(6.dp))
                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it; errorText = null },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("operator@revrag.ai", color = MutedNeutral) },
                    singleLine = true,
                    shape = RoundedCornerShape(8.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ApocalypticOrange,
                        unfocusedBorderColor = BorderNeutral,
                        focusedTextColor = DynamicBlack,
                        unfocusedTextColor = DynamicBlack
                    )
                )

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "PASSWORD",
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    color = DynamicBlack
                )
                Spacer(modifier = Modifier.height(6.dp))
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it; errorText = null },
                    modifier = Modifier.fillMaxWidth(),
                    placeholder = { Text("••••••••", color = MutedNeutral) },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    shape = RoundedCornerShape(8.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ApocalypticOrange,
                        unfocusedBorderColor = BorderNeutral,
                        focusedTextColor = DynamicBlack,
                        unfocusedTextColor = DynamicBlack
                    )
                )

                if (errorText != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = errorText ?: "",
                        color = ApocalypticOrange,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            // Action Buttons
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 24.dp)
            ) {
                Button(
                    onClick = {
                        if (email.isBlank()) {
                            errorText = "Please enter an email address"
                        } else {
                            onLoginSuccess(email)
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
                        text = "Continue to OTP Verification",
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
