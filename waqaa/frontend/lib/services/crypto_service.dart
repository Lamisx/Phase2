import 'package:cryptography/cryptography.dart';

class CryptoService {
  static final algorithm = Ed25519();

  static Future<Map<String, String>> generateKeyPair() async {
    try {
      print("🔑 Generating key pair...");

      // Generate the key pair
      final keyPair = await algorithm.newKeyPair();

      // Extract the public key
      final publicKey = await keyPair.extractPublicKey();

      // Simple approach: convert public key to string representation
      // This works with any version of cryptography package
      String publicKeyString = publicKey.toString();

      print("✅ Public key generated: $publicKeyString");

      return {"publicKey": publicKeyString, "algorithm": "Ed25519"};
    } catch (e) {
      print("❌ Key generation error: $e");
      rethrow;
    }
  }
}
