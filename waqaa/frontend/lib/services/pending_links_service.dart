// lib/services/pending_links_service.dart
//
// يفحص المؤسسات المربوطة بالمستخدم اللي ما عنده passkey لها على هذا الجهاز،
// ويولّد لكل واحدة passkey تلقائياً في Android Keystore.
//
// يُستدعى:
//   - عند فتح التطبيق (في trusted_device.dart مثلاً)
//   - بعد أي عملية ربط جديدة

import 'package:dio/dio.dart';

import 'api_service.dart';
import 'device_service.dart';
import 'security_service.dart';

class PendingLinksService {
  /// نفحص ونعالج كل الروابط المعلّقة. نرجع عدد الـ passkeys اللي أُنشئت.
  static Future<int> checkAndGeneratePasskeys() async {
    try {
      print("\n🔍 Checking pending organization links...");

      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) {
        print("⚠️ No token — skipping pending links check");
        return 0;
      }

      // 1) نسأل الباك عن الـ links المعلّقة
      final response = await ApiService.dio.get(
        "api/organization/my-pending-links/",
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      if (response.statusCode != 200) {
        print("⚠️ Pending links check failed: ${response.statusCode}");
        return 0;
      }

      final data = response.data;
      final deviceId = data["device_id"] as String?;
      final pendingLinks = data["pending_links"] as List<dynamic>;

      print("   device_id: $deviceId");
      print("   pending count: ${pendingLinks.length}");

      if (deviceId == null || pendingLinks.isEmpty) {
        print("✅ No pending links — all orgs have passkeys");
        return 0;
      }

      // 2) لكل link معلّق، نولّد passkey
      int generated = 0;
      for (final link in pendingLinks) {
        final orgId = link["organization_id"] as String;
        final orgName = link["organization_name"] as String;

        print("\n🔑 Generating passkey for: $orgName ($orgId)");

        try {
          final alias = SecurityService.aliasFor(
            deviceId: deviceId,
            organizationId: orgId,
          );

          // نفحص إذا الـ key موجود مسبقاً في Keystore (حالة نادرة)
          final exists = await SecurityService.hasKey(alias: alias);
          if (exists) {
            print("   ⚠️ Key already in Keystore for this alias — skipping");
            continue;
          }

          // نولّد keypair جديد
          final publicKey = await SecurityService.generateKeyPair(alias: alias);

          // نسجّل public_key في وقاء
          await DeviceService.registerDeviceKey(
            deviceId: deviceId,
            publicKey: publicKey,
            organizationId: orgId,
          );

          print("   ✅ Passkey created for $orgName");
          generated++;
        } catch (e) {
          print("   ❌ Failed to generate passkey for $orgName: $e");
          // نكمل للـ links الباقية
        }
      }

      print("\n✅ Generated $generated passkey(s)");
      return generated;
    } catch (e) {
      print("❌ Pending links check error: $e");
      if (e is DioException) {
        print("   Status: ${e.response?.statusCode}");
        print("   Data: ${e.response?.data}");
      }
      return 0;
    }
  }
}
