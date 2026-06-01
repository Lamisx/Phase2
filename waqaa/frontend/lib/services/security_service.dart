import 'package:flutter/services.dart';

/// مسؤول عن التواصل بين Flutter و Android Native (MainActivity.kt)
/// لاستخدام Android Keystore بشكل صحيح.
///
/// الـ private_key يبقى **داخل Keystore** (hardware-backed لو متاح)
/// ولا يمكن استخراجه أبداً.
class SecurityService {
  /// قناة الاتصال مع Kotlin (نفس اسم القناة في MainActivity.kt)
  static const MethodChannel _channel = MethodChannel('waqaa/security');

  /// ============================================================
  /// Helper: نبني alias فريد لكل (device, organization).
  ///
  /// كل (جهاز + مؤسسة) عندها keypair خاص. الـ alias يعرّف الـ keypair
  /// داخل Keystore.
  /// ============================================================
  static String aliasFor({
    required String deviceId,
    required String organizationId,
  }) {
    return "waqaa_${deviceId}_$organizationId";
  }

  /// ============================================================
  /// توليد ES256 keypair داخل Android Keystore.
  ///
  /// المفتاح الخاص يبقى داخل الجهاز ولا يمكن استخراجه أبداً.
  /// يرجع الـ public_key بتنسيق X509/SubjectPublicKeyInfo
  /// مكوّد base64 (نفس ما يقبله الباك).
  /// ============================================================
  static Future<String> generateKeyPair({required String alias}) async {
    print("🔐 Generating ES256 keypair in Keystore for alias: $alias");

    final publicKey = await _channel.invokeMethod("generateKeyPair", {
      "alias": alias,
    });

    print(
      "✅ Keypair generated. Public key (first 30 chars): ${publicKey.substring(0, 30)}...",
    );
    return publicKey as String;
  }

  /// ============================================================
  /// توقيع challenge باستخدام private_key من Keystore.
  ///
  /// challengeHex = الـ challenge من الباك كـ hex string.
  /// نوقّع البايتات الفعلية (مو حروف الـ hex).
  /// ============================================================
  static Future<String> signChallenge({
    required String alias,
    required String challengeHex,
  }) async {
    print("🖋️ Signing challenge with alias: $alias");
    print("   challengeHex: ${challengeHex.substring(0, 16)}...");

    final signature = await _channel.invokeMethod("signChallenge", {
      "alias": alias,
      "challengeHex": challengeHex,
    });

    print(
      "✅ Signature (first 30 chars): ${(signature as String).substring(0, 30)}...",
    );
    return signature;
  }

  /// ============================================================
  /// هل يوجد keypair لهذا الـ alias في Keystore؟
  /// ============================================================
  static Future<bool> hasKey({required String alias}) async {
    final result = await _channel.invokeMethod("hasKey", {"alias": alias});
    return result as bool;
  }
}
