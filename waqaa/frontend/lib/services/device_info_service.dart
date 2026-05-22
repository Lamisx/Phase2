import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';

class DeviceInfoService {
  static Future<Map<String, String>> getDeviceData() async {
    final deviceInfo = DeviceInfoPlugin();

    if (Platform.isAndroid) {
      final android = await deviceInfo.androidInfo;

      return {
        "platform": "android",

        "label": "${android.brand} ${android.model}",

        "app_instance_id": android.id,
      };
    }

    if (Platform.isIOS) {
      final ios = await deviceInfo.iosInfo;

      return {
        "platform": "ios",

        "label": "${ios.name} ${ios.model}",

        "app_instance_id": ios.identifierForVendor ?? "ios_device",
      };
    }

    return {
      "platform": "unknown",

      "label": "Unknown Device",

      "app_instance_id": DateTime.now().millisecondsSinceEpoch.toString(),
    };
  }
}
