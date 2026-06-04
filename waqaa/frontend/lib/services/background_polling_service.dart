// lib/services/background_polling_service.dart
//
// خدمة الخلفية: تفحص الجلسات المعلّقة كل 10 ثوانٍ وتوقّعها تلقائياً.
//
// إذا الجوال ما يقدر يوقّع (no key for alias):
//   1. يرسل reject إلى وقاء (status → denied)
//   2. يطلق onSuspiciousActivity callback
//   3. الـ UI يعرض تنبيه للمستخدم

import 'dart:async';

import 'package:dio/dio.dart';

import 'api_service.dart';
import 'security_service.dart';

class BackgroundPollingService {
  static Timer? _timer;
  static bool _isPolling = false;
  static bool _isStarted = false;

  /// Callback تُستدعى عند نشاط مشبوه (جلسة لا يمكن توقيعها)
  /// الـ UI يستخدمها لإظهار تنبيه.
  static void Function(Map<String, dynamic> session, String reason)?
  onSuspiciousSession;

  /// Callback تُستدعى عند نجاح توقيع
  static void Function(Map<String, dynamic> session)? onSessionVerified;

  /// يبدأ الـ polling. آمن للاستدعاء أكثر من مرة (idempotent).
  static void start() {
    if (_isStarted) {
      print("⏯️ BackgroundPolling already started — skipping");
      return;
    }
    _isStarted = true;
    print("▶️ BackgroundPolling: START (every 10 seconds)");

    _checkOnce();

    _timer = Timer.periodic(const Duration(seconds: 10), (_) {
      _checkOnce();
    });
  }

  /// يوقف الـ polling (مثلاً عند logout).
  static void stop() {
    print("⏹️ BackgroundPolling: STOP");
    _timer?.cancel();
    _timer = null;
    _isStarted = false;
  }

  /// دورة فحص واحدة. نتجنّب التداخل (lock).
  static Future<void> _checkOnce() async {
    if (_isPolling) return;
    _isPolling = true;

    try {
      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) return;

      final response = await ApiService.dio.get(
        "api/verification/my-pending-sessions/",
        options: Options(
          headers: {"Authorization": "Bearer $token"},
          receiveTimeout: const Duration(seconds: 5),
          sendTimeout: const Duration(seconds: 5),
        ),
      );

      if (response.statusCode != 200) return;

      final data = response.data;
      final deviceId = data["device_id"] as String?;
      final pending = data["pending_sessions"] as List<dynamic>;

      if (deviceId == null || pending.isEmpty) return;

      print("\n🔔 BackgroundPolling: ${pending.length} pending session(s)");

      for (final session in pending) {
        await _processSession(
          deviceId: deviceId,
          session: session as Map<String, dynamic>,
        );
      }
    } catch (e) {
      if (e is DioException && e.response?.statusCode != null) {
        print("⚠️ BackgroundPolling: ${e.response?.statusCode}");
      }
    } finally {
      _isPolling = false;
    }
  }

  /// يعالج session واحدة: يوقّع لو ممكن، أو يرفض لو ما يقدر.
  static Future<void> _processSession({
    required String deviceId,
    required Map<String, dynamic> session,
  }) async {
    final sessionId = session["session_id"] as String;
    final orgId = session["organization_id"] as String;
    final orgName = session["organization_name"] as String;
    final challengeHex = session["challenge_bytes"] as String;
    final opType = session["operation_type"] as String;

    print("\n🖋️ Processing session: $sessionId");
    print("   org: $orgName ($orgId)");
    print("   operation: $opType");

    try {
      final alias = SecurityService.aliasFor(
        deviceId: deviceId,
        organizationId: orgId,
      );

      // ⚠️ فحص أمني: هل الـ key موجود في Keystore؟
      final hasKey = await SecurityService.hasKey(alias: alias);

      if (!hasKey) {
        // ❌ الجهاز ما عنده الـ key — هذا قد يكون محاولة احتيال
        print("   ⚠️ No key in Keystore for alias: $alias");
        print("   🚨 Reporting suspicious activity to backend");

        await _rejectSession(
          sessionId: sessionId,
          reason: "device_not_authorized",
        );

        // إخبار الـ UI لإظهار تنبيه
        onSuspiciousSession?.call(session, "device_not_authorized");
        return;
      }

      // ✅ عندنا الـ key — نوقّع
      final signature = await SecurityService.signChallenge(
        alias: alias,
        challengeHex: challengeHex,
      );
      print("   ✅ Signature generated");

      final token = ApiService.accessToken;
      final response = await ApiService.dio.post(
        "api/verification/sessions/$sessionId/verify-mobile/",
        data: {"signature": signature},
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      if (response.statusCode == 200) {
        final newStatus = response.data["session_status"];
        print("   ✅ Verify response: status = $newStatus");

        if (newStatus == "verified") {
          onSessionVerified?.call(session);
        }
      } else {
        print("   ❌ Verify failed: ${response.statusCode}");
      }
    } catch (e) {
      print("   ❌ Error processing session: $e");

      // محاولة rejection لو فشل التوقيع
      if (e.toString().contains("NO_KEY_FOR_ALIAS") ||
          e.toString().contains("SIGN_ERROR")) {
        await _rejectSession(
          sessionId: sessionId,
          reason: "device_not_authorized",
        );
        onSuspiciousSession?.call(session, "device_not_authorized");
      }
    }
  }

  /// يرسل rejection إلى وقاء (يحدّث session.status = denied)
  static Future<void> _rejectSession({
    required String sessionId,
    required String reason,
  }) async {
    try {
      final token = ApiService.accessToken;
      final response = await ApiService.dio.post(
        "api/verification/sessions/$sessionId/reject-mobile/",
        data: {"reason": reason},
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      if (response.statusCode == 200) {
        print("   📨 Rejection sent to backend: $reason");
      }
    } catch (e) {
      print("   ⚠️ Failed to send rejection: $e");
    }
  }
}
