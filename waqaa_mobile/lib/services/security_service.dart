import 'package:flutter/services.dart';

/// مسؤول عن التواصل بين Flutter و Android Native
/// عشان ننفذ:
/// - توليد المفاتيح
/// - التوقيع
/// - استخدام Android Keystore
class SecurityService {
  /// قناة الاتصال مع Kotlin
  static const MethodChannel _channel = MethodChannel('waqaa/security');

  /// توليد ES256 Key Pair داخل Android Keystore
  ///
  /// يرجع:
  /// public key فقط
  ///
  /// private key يبقى داخل الجهاز وغير قابل للاستخراج
  static Future<String> generateKeyPair() async {
    final publicKey = await _channel.invokeMethod("generateKeyPair");

    return publicKey;
  }

  /// توقيع challenge باستخدام private key
  ///
  /// السيرفر يرسل challenge
  /// الجهاز يوقعه
  /// ثم نرجع signature للسيرفر
  static Future<String> signChallenge(String challenge) async {
    final signature = await _channel.invokeMethod("signChallenge", {
      "challenge": challenge,
    });

    return signature;
  }
}
