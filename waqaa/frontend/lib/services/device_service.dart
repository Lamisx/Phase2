import 'package:dio/dio.dart';

import 'api_service.dart';
import 'device_info_service.dart';

class DeviceService {
  // =====================================================================
  // CREATE DEVICE — يستخدم معرّفاً ثابتاً للجهاز (android.id)
  // =====================================================================
  static Future<String?> createDevice() async {
    try {
      print("\n🔧 Creating device...");

      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) {
        print("❌ ERROR: Token is null!");
        return null;
      }

      final authHeader = "Bearer $token";

      final info = await DeviceInfoService.getDeviceData();
      final platform = info["platform"] ?? "android";
      final label = info["label"] ?? "Unknown Device";
      final appInstanceId = info["app_instance_id"] ?? "fallback";

      print("📱 Platform: $platform");
      print("📱 Label: $label");
      print("📱 app_instance_id: $appInstanceId");

      final response = await ApiService.dio.post(
        "api/device/create/",
        data: {
          "platform": platform,
          "label": label,
          "app_instance_id": appInstanceId,
        },
        options: Options(headers: {"Authorization": authHeader}),
      );

      print("✅ Status: ${response.statusCode}");

      // 201: Device جديد
      if (response.statusCode == 201) {
        final deviceId = response.data["device"]["id"];
        print("✅ Device created (new): $deviceId");
        return deviceId;
      }

      // 409: Device موجود مسبقاً (idempotent)
      if (response.statusCode == 409) {
        print("ℹ️ Device already exists — using existing");
        final deviceId = response.data["device_id"];
        if (deviceId != null) return deviceId;
      }

      // 200: نادر
      if (response.statusCode == 200) {
        return response.data["device"]["id"];
      }

      print("❌ Failed: ${response.statusCode}");
      print("❌ Response: ${response.data}");
      return null;
    } catch (e) {
      print("❌ Error: $e");
      if (e is DioException) {
        print("   Status: ${e.response?.statusCode}");
        print("   Data: ${e.response?.data}");
      }
      return null;
    }
  }

  // =====================================================================
  // LIST DEVICES
  // =====================================================================
  static Future<List<Map<String, dynamic>>> listDevices() async {
    try {
      print("\n📱 Fetching devices...");

      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) return [];

      final response = await ApiService.dio.get(
        "api/device/me/",
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      if (response.statusCode == 200) {
        final List<dynamic> devicesList = response.data["devices"] ?? [];
        print("✅ Fetched ${devicesList.length} devices");
        return devicesList
            .map((d) => Map<String, dynamic>.from(d as Map))
            .toList();
      }
      return [];
    } catch (e) {
      print("❌ Error fetching devices: $e");
      return [];
    }
  }

  // =====================================================================
  // REGISTER DEVICE KEY
  //
  // ⭐ organizationId الآن parameter ديناميكي
  // (مو hardcoded). نمرّر organization المناسبة.
  // =====================================================================
  static Future<void> registerDeviceKey({
    required String deviceId,
    required String publicKey,
    required String organizationId,
  }) async {
    try {
      print("\n🔑 Registering device key...");
      print("   device: $deviceId");
      print("   org: $organizationId");

      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) {
        print("❌ ERROR: Token is null!");
        return;
      }

      final response = await ApiService.dio.post(
        "api/device/keys/register-device-key/",
        data: {
          "device_id": deviceId,
          "organization_id": organizationId,
          "public_key": publicKey,
          "key_purpose": "auth",
        },
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      print("✅ Status: ${response.statusCode}");
      print("✅ Response: ${response.data}");
    } catch (e) {
      print("❌ Error: $e");
      if (e is DioException) {
        print("   Status: ${e.response?.statusCode}");
        print("   Data: ${e.response?.data}");
      }
      rethrow; // نعيد رمي الخطأ عشان contact_screen يعرضها
    }
  }

  // =====================================================================
  // REVOKE DEVICE
  // =====================================================================
  static Future<bool> revokeDevice({required String deviceId}) async {
    try {
      print("\n🗑️ Revoking device: $deviceId");

      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) return false;

      final response = await ApiService.dio.post(
        "api/device/$deviceId/revoke/",
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      return response.statusCode == 200;
    } catch (e) {
      print("❌ Error: $e");
      return false;
    }
  }
}
