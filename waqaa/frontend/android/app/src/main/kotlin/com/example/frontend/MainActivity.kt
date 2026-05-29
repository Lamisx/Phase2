package com.example.waqaa_mobile

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

    // اسم قناة الاتصال بين Flutter و Kotlin
    private val CHANNEL = "waqaa/security"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        ).setMethodCallHandler { call, result ->

            when (call.method) {

                // توليد زوج مفاتيح ES256 لـ alias محدّد (لكل منظمة)
                "generateKeyPair" -> {
                    try {
                        val alias = call.argument<String>("alias")
                        if (alias.isNullOrEmpty()) {
                            result.error("ALIAS_REQUIRED", "alias is required", null)
                            return@setMethodCallHandler
                        }
                        val publicKey = generateKeyPair(alias)
                        result.success(publicKey)
                    } catch (e: Exception) {
                        result.error("KEY_ERROR", e.message, null)
                    }
                }

                // توقيع التحدّي بمفتاح alias المحدّد
                "signChallenge" -> {
                    try {
                        val alias = call.argument<String>("alias")
                        val challengeHex = call.argument<String>("challengeHex")
                        if (alias.isNullOrEmpty()) {
                            result.error("ALIAS_REQUIRED", "alias is required", null)
                            return@setMethodCallHandler
                        }
                        if (challengeHex.isNullOrEmpty()) {
                            result.error("CHALLENGE_REQUIRED", "challengeHex is required", null)
                            return@setMethodCallHandler
                        }
                        val signature = signChallenge(alias, challengeHex)
                        result.success(signature)
                    } catch (e: Exception) {
                        result.error("SIGN_ERROR", e.message, null)
                    }
                }

                // هل يوجد مفتاح لهذا الـ alias؟
                "hasKey" -> {
                    try {
                        val alias = call.argument<String>("alias") ?: ""
                        result.success(hasKey(alias))
                    } catch (e: Exception) {
                        result.error("HASKEY_ERROR", e.message, null)
                    }
                }

                else -> result.notImplemented()
            }
        }
    }

    // ============================================================
    // توليد ES256 — المفتاح الخاص يبقى داخل Android Keystore
    // المفتاح العام يُرجَّع بصيغة X509/SPKI base64 (يطابق key_format=X509)
    // ============================================================
    private fun generateKeyPair(alias: String): String {

        val keyPairGenerator = KeyPairGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_EC,
            "AndroidKeyStore"
        )

        val parameterSpec = KeyGenParameterSpec.Builder(
            alias,
            KeyProperties.PURPOSE_SIGN or KeyProperties.PURPOSE_VERIFY
        )
            .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
            .setDigests(KeyProperties.DIGEST_SHA256)
            .setUserAuthenticationRequired(false)
            .build()

        keyPairGenerator.initialize(parameterSpec)
        val keyPair = keyPairGenerator.generateKeyPair()

        // public.encoded = X509/SubjectPublicKeyInfo (DER)
        val publicKeyBytes = keyPair.public.encoded
        return Base64.encodeToString(publicKeyBytes, Base64.NO_WRAP)
    }

    // ============================================================
    // توقيع التحدّي
    // مهم: الباك يرسل challenge كـ hex string. نفكّه إلى بايتات
    // ثم نوقّع البايتات الأصلية (لا حروف الـ hex).
    // SHA256withECDSA يُخرج توقيعاً بصيغة DER — الباك يقبله.
    // ============================================================
    private fun signChallenge(alias: String, challengeHex: String): String {

        val keyStore = KeyStore.getInstance("AndroidKeyStore")
        keyStore.load(null)

        val privateKey = keyStore.getKey(alias, null) as? PrivateKey
            ?: throw IllegalStateException("NO_KEY_FOR_ALIAS")

        val signature = Signature.getInstance("SHA256withECDSA")
        signature.initSign(privateKey)

        // ← الإصلاح القاتل: نوقّع البايتات الحقيقية للتحدّي
        signature.update(hexToBytes(challengeHex))

        val signedBytes = signature.sign()
        return Base64.encodeToString(signedBytes, Base64.NO_WRAP)
    }

    // ============================================================
    private fun hasKey(alias: String): Boolean {
        if (alias.isEmpty()) return false
        val keyStore = KeyStore.getInstance("AndroidKeyStore")
        keyStore.load(null)
        return keyStore.containsAlias(alias)
    }

    // فكّ hex string إلى ByteArray
    private fun hexToBytes(hex: String): ByteArray {
        val clean = if (hex.startsWith("0x")) hex.substring(2) else hex
        require(clean.length % 2 == 0) { "Invalid hex length" }
        val out = ByteArray(clean.length / 2)
        var i = 0
        while (i < clean.length) {
            out[i / 2] = ((Character.digit(clean[i], 16) shl 4) +
                    Character.digit(clean[i + 1], 16)).toByte()
            i += 2
        }
        return out
    }
}