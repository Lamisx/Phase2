import 'package:dio/dio.dart';

import 'api_service.dart';
import 'device_info_service.dart';

class DeviceService {
  // =====================================================================
  // CREATE DEVICE
  //
  // يستخدم DeviceInfoService.getDeviceData() عشان يجيب معرّف ثابت للجهاز
  // (android.id أو ios.identifierForVendor) بدل timestamp متغيّر.
  //
  // كذا الباك idempotent: نفس الجهاز = نفس app_instance_id =
  // نفس Device في DB، حتى لو استدعينا createDevice أكثر من مرة.
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

      // ⭐ نستخدم معلومات الجهاز الحقيقية (معرّف ثابت)
      final info = await DeviceInfoService.getDeviceData();
      final platform = info["platform"] ?? "android";
      final label = info["label"] ?? "Unknown Device";
      final appInstanceId = info["app_instance_id"] ?? "fallback";

      print("📱 Platform: $platform");
      print("📱 Label: $label");
      print("📱 app_instance_id: $appInstanceId  (ثابت لهذا الجهاز)");

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
      print("✅ Response: ${response.data}");

      // Case 1: جهاز جديد أُنشئ
      if (response.statusCode == 201) {
        final deviceId = response.data["device"]["id"];
        print("✅ Device created (new): $deviceId");
        return deviceId;
      }

      // Case 2: الجهاز موجود مسبقاً (idempotent) — الباك يرجّع 409 + device_id
      if (response.statusCode == 409) {
        print("ℹ️ Device already exists (409 CONFLICT) — using existing");
        String? deviceId;
        try {
          deviceId = response.data["device_id"];
        } catch (e) {
          print("⚠️ Could not extract device_id from 409 response");
          print("Response data: ${response.data}");
          return null;
        }
        if (deviceId != null) {
          print("✅ Using existing device: $deviceId");
          return deviceId;
        }
      }

      // Case 3: 200 (نادرة، لكن نتعامل معها)
      if (response.statusCode == 200) {
        final deviceId = response.data["device"]["id"];
        print("✅ Device created: $deviceId");
        return deviceId;
      }

      print("❌ Failed: ${response.statusCode}");
      print("❌ Error: ${response.data}");
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
      if (token == null || token.isEmpty) {
        print("❌ ERROR: Token is null!");
        return [];
      }

      final authHeader = "Bearer $token";

      final response = await ApiService.dio.get(
        "api/device/me/",
        options: Options(headers: {"Authorization": authHeader}),
      );

      print("✅ Status: ${response.statusCode}");
      print("✅ Response: ${response.data}");

      if (response.statusCode == 200) {
        final List<dynamic> devicesList = response.data["devices"] ?? [];
        print("✅ Fetched ${devicesList.length} devices");
        return devicesList
            .map((device) => Map<String, dynamic>.from(device as Map))
            .toList();
      } else {
        print("❌ Failed to fetch devices: ${response.statusCode}");
        return [];
      }
    } catch (e) {
      print("❌ Error fetching devices: $e");
      if (e is DioException) {
        print("   Status: ${e.response?.statusCode}");
        print("   Data: ${e.response?.data}");
      }
      return [];
    }
  }

  // =====================================================================
  // REGISTER DEVICE KEY  (passkey العام)
  // =====================================================================
  static Future<void> registerDeviceKey({
    required String deviceId,
    required String publicKey,
  }) async {
    try {
      print("\n🔑 Registering device key...");

      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) {
        print("❌ ERROR: Token is null!");
        return;
      }

      final authHeader = "Bearer $token";

      final response = await ApiService.dio.post(
        "api/device/keys/register-device-key/",
        data: {
          "device_id": deviceId,
          "organization_id": "550e8400-e29b-41d4-a716-446655440000",
          "public_key": publicKey,
          "key_purpose": "auth",
        },
        options: Options(headers: {"Authorization": authHeader}),
      );

      print("✅ Status: ${response.statusCode}");
      print("✅ Response: ${response.data}");
    } catch (e) {
      print("❌ Error: $e");
      if (e is DioException) {
        print("   Status: ${e.response?.statusCode}");
        print("   Data: ${e.response?.data}");
      }
    }
  }

  // =====================================================================
  // REVOKE DEVICE
  // =====================================================================
  static Future<bool> revokeDevice({required String deviceId}) async {
    try {
      print("\n🗑️ Revoking device: $deviceId");

      final token = ApiService.accessToken;
      if (token == null || token.isEmpty) {
        print("❌ ERROR: Token is null!");
        return false;
      }

      final response = await ApiService.dio.post(
        "api/device/$deviceId/revoke/",
        options: Options(headers: {"Authorization": "Bearer $token"}),
      );

      print("✅ Status: ${response.statusCode}");
      print("✅ Response: ${response.data}");

      return response.statusCode == 200;
    } catch (e) {
      print("❌ Error revoking device: $e");
      if (e is DioException) {
        print("   Status: ${e.response?.statusCode}");
        print("   Data: ${e.response?.data}");
      }
      return false;
    }
  }
}
