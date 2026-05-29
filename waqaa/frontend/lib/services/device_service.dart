import 'dart:io';
import 'package:device_info_plus/device_info_plus.dart';
import 'api_service.dart';

import 'package:dio/dio.dart';

class DeviceService {
  static Future<String?> createDevice() async {
    try {
      print("\n🔧 Creating device...");

      // GET TOKEN EXPLICITLY
      final token = ApiService.accessToken;
      print("📌 Token: $token");

      if (token == null || token.isEmpty) {
        print("❌ ERROR: Token is null!");
        return null;
      }

      // BUILD AUTH HEADER
      final authHeader = "Bearer $token";
      print("📌 Authorization: $authHeader");

      // =====================================================================
      // DETECT PLATFORM AUTOMATICALLY
      // =====================================================================
      String platform = "android";
      String deviceLabel = "Unknown Device";

      if (Platform.isIOS) {
        platform = "ios";
        try {
          final deviceInfo = DeviceInfoPlugin();
          final iosInfo = await deviceInfo.iosInfo;
          deviceLabel = "${iosInfo.model} (iOS)";
          print("📱 Detected iOS: $deviceLabel");
        } catch (e) {
          deviceLabel = "iPhone";
          print("⚠️ Could not get iOS device info: $e");
        }
      } else if (Platform.isAndroid) {
        platform = "android";
        try {
          final deviceInfo = DeviceInfoPlugin();
          final androidInfo = await deviceInfo.androidInfo;
          deviceLabel = "${androidInfo.model} (Android)";
          print("📱 Detected Android: $deviceLabel");
        } catch (e) {
          deviceLabel = "Android Device";
          print("⚠️ Could not get Android device info: $e");
        }
      }

      // MAKE REQUEST WITH EXPLICIT HEADER
      final response = await ApiService.dio.post(
        "api/device/create/",

        data: {
          "platform": platform,
          "label": deviceLabel,
          "app_instance_id":
              "waqaa_device_${DateTime.now().millisecondsSinceEpoch}",
        },

        // EXPLICITLY PASS TOKEN
        options: Options(headers: {"Authorization": authHeader}),
      );

      print("✅ Status: ${response.statusCode}");
      print("✅ Response: ${response.data}");

      // =====================
      // HANDLE DIFFERENT RESPONSES
      // =====================

      // Case 1: Device created successfully (201)
      if (response.statusCode == 201) {
        final deviceId = response.data["device"]["id"];
        print("✅ Device created: $deviceId");
        return deviceId;
      }

      // Case 2: Device already exists (409) - THIS IS OK!
      if (response.statusCode == 409) {
        print("ℹ️ Device already exists (409 CONFLICT)");

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

      // Case 3: Success but different status code
      if (response.statusCode == 200) {
        final deviceId = response.data["device"]["id"];
        print("✅ Device created: $deviceId");
        return deviceId;
      }

      // Case 4: Any other response is a failure
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
  // LIST DEVICES - CORRECT ENDPOINT: /api/device/me/
  // =====================================================================
  static Future<List<Map<String, dynamic>>> listDevices() async {
    try {
      print("\n📱 Fetching devices...");

      // GET TOKEN EXPLICITLY
      final token = ApiService.accessToken;

      if (token == null || token.isEmpty) {
        print("❌ ERROR: Token is null!");
        return [];
      }

      final authHeader = "Bearer $token";

      // ✅ CORRECT ENDPOINT
      final response = await ApiService.dio.get(
        "api/device/me/",
        options: Options(headers: {"Authorization": authHeader}),
      );

      print("✅ Status: ${response.statusCode}");
      print("✅ Response: ${response.data}");

      if (response.statusCode == 200) {
        // Parse devices from response
        final List<dynamic> devicesList = response.data["devices"] ?? [];

        print("✅ Fetched ${devicesList.length} devices");

        // Convert to List<Map<String, dynamic>>
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

  static Future<void> registerDeviceKey({
    required String deviceId,

    required String publicKey,
  }) async {
    try {
      print("\n🔑 Registering device key...");

      // GET TOKEN EXPLICITLY
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

        // EXPLICITLY PASS TOKEN
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
}
