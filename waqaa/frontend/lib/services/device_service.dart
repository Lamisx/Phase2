import 'package:dio/dio.dart';

import 'api_service.dart';

class DeviceService {
  static Future<void> registerDeviceKey({
    required String deviceId,
    required String organizationId,
    required String publicKey,
  }) async {
    try {
      print("START REGISTER");

      final response = await ApiService.dio.post(
        "api/device/keys/register-device-key/",
        data: {
          "device_id": deviceId,

          "organization_id": organizationId,

          "public_key": publicKey,

          "algorithm": "ES256",

          "key_format": "X509",

          "key_purpose": "auth",
        },
      );

      print("REGISTER SUCCESS");

      print(response.data);
    } catch (e) {
      print("REGISTER ERROR");

      print(e);
    }
  }
}
