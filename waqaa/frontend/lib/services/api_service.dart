import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = "http://10.0.2.2:8000/api";

  // 🔹 إنشاء session (start registration)
  static Future<String> startRegistration(String nationalId) async {
    final url = Uri.parse('$baseUrl/accounts/start-registration/');

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"national_id": nationalId}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data["session_id"];
    } else {
      throw Exception("Error: ${response.body}");
    }
  }

  static Future<bool> verifyNafath({
    required String sessionId,
    required String nationalId,
  }) async {
    final url = Uri.parse('$baseUrl/accounts/verify-nafath/');

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"session_id": sessionId, "national_id": nationalId}),
    );

    return response.statusCode == 200;
  }

  static Future<bool> setCredentials({
    required String sessionId,
    required String username,
    required String password,
  }) async {
    final url = Uri.parse('$baseUrl/accounts/set-credentials/');

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "session_id": sessionId,
        "username": username,
        "password": password,
      }),
    );

    return response.statusCode == 200;
  }

  static Future<bool> setContact({
    required String sessionId,
    required String phone,
    required String email,
  }) async {
    final url = Uri.parse('$baseUrl/accounts/set-contact/');

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "session_id": sessionId,
        "phone": phone,
        "email": email,
      }),
    );

    return response.statusCode == 200;
  }

  static Future<bool> completeRegistration(String sessionId) async {
    final url = Uri.parse('$baseUrl/accounts/complete-registration/');

    final response = await http.post(
      url,
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"session_id": sessionId}),
    );

    return response.statusCode == 200;
  }
}
