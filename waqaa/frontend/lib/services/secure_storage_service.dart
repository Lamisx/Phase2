import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  static const _storage = FlutterSecureStorage();

  // ===============================
  // SAVE PRIVATE KEY
  // ===============================

  static Future<void> savePrivateKey(String privateKey) async {
    await _storage.write(key: "private_key", value: privateKey);
  }

  // ===============================
  // GET PRIVATE KEY
  // ===============================

  static Future<String?> getPrivateKey() async {
    return await _storage.read(key: "private_key");
  }
}
