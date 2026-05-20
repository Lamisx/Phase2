package com.example.waqaa_mobile

import android.os.Bundle
import android.util.Base64

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine

import io.flutter.plugin.common.MethodChannel

import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.PrivateKey
import java.security.Signature

import java.security.spec.ECGenParameterSpec

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties

class MainActivity : FlutterActivity() {

    /// اسم قناة الاتصال بين Flutter و Kotlin
    private val CHANNEL = "waqaa/security"

    /// اسم المفتاح داخل Android Keystore
    private val KEY_ALIAS = "waqaa_device_key"

    override fun configureFlutterEngine(
        flutterEngine: FlutterEngine
    ) {

        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        ).setMethodCallHandler { call, result ->

            when (call.method) {

                /// Flutter طلب توليد مفاتيح
                "generateKeyPair" -> {

                    try {

                        val publicKey =
                            generateKeyPair()

                        result.success(publicKey)

                    } catch (e: Exception) {

                        result.error(
                            "KEY_ERROR",
                            e.message,
                            null
                        )
                    }
                }

                /// Flutter طلب توقيع challenge
                "signChallenge" -> {

                    try {

                        val challenge =
                            call.argument<String>(
                                "challenge"
                            ) ?: ""

                        val signature =
                            signChallenge(challenge)

                        result.success(signature)

                    } catch (e: Exception) {

                        result.error(
                            "SIGN_ERROR",
                            e.message,
                            null
                        )
                    }
                }

                else -> {
                    result.notImplemented()
                }
            }
        }
    }

    /// توليد ES256 Key Pair
    ///
    /// private key:
    /// يبقى داخل Android Keystore
    ///
    /// public key:
    /// يرجع لـ Flutter ثم للسيرفر
    private fun generateKeyPair(): String {

        val keyPairGenerator =
            KeyPairGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_EC,
                "AndroidKeyStore"
            )

        val parameterSpec =
            KeyGenParameterSpec.Builder(
                KEY_ALIAS,

                KeyProperties.PURPOSE_SIGN or
                        KeyProperties.PURPOSE_VERIFY
            )
                .setAlgorithmParameterSpec(
                    ECGenParameterSpec("secp256r1")
                )
                .setDigests(
                    KeyProperties.DIGEST_SHA256
                )
                .setUserAuthenticationRequired(false)
                .build()

        keyPairGenerator.initialize(parameterSpec)

        val keyPair =
            keyPairGenerator.generateKeyPair()

        /// هذا public key فقط
        val publicKeyBytes =
            keyPair.public.encoded

        /// نحوله Base64 عشان نرسله للسيرفر
        return Base64.encodeToString(
            publicKeyBytes,
            Base64.NO_WRAP
        )
    }

    /// توقيع challenge باستخدام private key
    ///
    /// private key لا يخرج من الجهاز
    private fun signChallenge(
        challenge: String
    ): String {

        val keyStore =
            KeyStore.getInstance(
                "AndroidKeyStore"
            )

        keyStore.load(null)

        val privateKey =
            keyStore.getKey(
                KEY_ALIAS,
                null
            ) as PrivateKey

        val signature =
            Signature.getInstance(
                "SHA256withECDSA"
            )

        signature.initSign(privateKey)

        signature.update(
            challenge.toByteArray()
        )

        val signedBytes =
            signature.sign()

        return Base64.encodeToString(
            signedBytes,
            Base64.NO_WRAP
        )
    }
}