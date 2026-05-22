import 'package:dio/dio.dart';

class ApiService {
  // =====================================================
  // BASE URL
  // =====================================================

  static const String baseUrl = "http://192.168.8.97:8000/";
  static String? accessToken;

  // =====================================================
  // DIO
  // =====================================================

  static final Dio dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      headers: {"Content-Type": "application/json"},
      validateStatus: (status) {
        // Don't throw exception for any status code < 500
        // This allows us to handle 409 manually
        return status != null && status < 500;
      },
    ),
  );

  // =====================================================
  // LOGIN - Extract token from nested structure
  // =====================================================
  static Future<void> login({
    required String username,
    required String password,
  }) async {
    try {
      print("\n🔐 === LOGIN START ===");
      print("Username: $username");

      final response = await dio.post(
        "api/account/auth/login/",
        data: {"username": username, "password": password},
      );

      print("Response Status: ${response.statusCode}");
      print("Response Data: ${response.data}");

      if (response.statusCode != 200) {
        throw Exception("Login failed: ${response.statusCode}");
      }

      // =====================
      // GET TOKEN FROM NESTED STRUCTURE
      // =====================
      // Backend returns: response.data["tokens"]["access"]

      String? token;

      try {
        token = response.data["tokens"]["access"];
      } catch (e) {
        print("❌ Error accessing tokens.access: $e");
      }

      if (token == null || token.isEmpty) {
        print("❌ Token not found in response!");
        print("Full response: ${response.data}");
        throw Exception(
          "No access token found. Expected: response.data['tokens']['access']",
        );
      }

      // =====================
      // SAVE TOKEN GLOBALLY
      // =====================
      accessToken = token;
      print("✅ Token saved: ${token.substring(0, 20)}...");

      // SET AUTHORIZATION HEADER GLOBALLY
      dio.options.headers["Authorization"] = "Bearer $token";
      print("✅ Authorization header set: Bearer ${token.substring(0, 20)}...");

      print("🔐 === LOGIN SUCCESS ===\n");
    } catch (e) {
      print("❌ Login Error: $e\n");
      accessToken = null;
      rethrow;
    }
  }

  // =====================================================
  // START REGISTRATION
  // =====================================================

  static Future<Response> startRegistration({
    required String nationalId,
  }) async {
    return await dio.post(
      "api/account/auth/register/start/",

      data: {"national_id": nationalId},
    );
  }

  // =====================================================
  // VERIFY IDENTITY
  // =====================================================

  static Future<Response> verifyIdentity({required String sessionId}) async {
    return await dio.post(
      "api/account/auth/register/verify-identity/",

      data: {"session_id": sessionId},
    );
  }

  // =====================================================
  // VERIFY NAFATH
  // =====================================================

  static Future<bool> verifyNafath({
    required String sessionId,
    required String nationalId,
  }) async {
    try {
      final response = await dio.post(
        "api/account/auth/register/verify-identity/",

        data: {"session_id": sessionId},
      );

      return response.statusCode == 200;
    } catch (e) {
      print(e);

      return false;
    }
  }

  // =====================================================
  // SET CONTACT
  // =====================================================

  static Future<bool> setContact({
    required String sessionId,
    required String phone,
    required String email,
  }) async {
    return true;
  }

  // =====================================================
  // COMPLETE REGISTRATION
  // =====================================================

  static Future<bool> completeRegistration({
    required String username,

    required String password,

    required String phone,

    required String email,
  }) async {
    try {
      final response = await dio.post(
        "api/account/auth/register/complete/",

        data: {
          "username": username,

          "display_name": username,

          "password": password,

          "phone": phone,

          "email": email,
        },
      );

      print("Registration Response: ${response.data}");

      if (response.statusCode == 201) {
        // ALSO extract token from registration response
        // Backend returns: response.data["tokens"]["access"]
        try {
          final token = response.data["tokens"]["access"];
          accessToken = token;
          dio.options.headers["Authorization"] = "Bearer $token";
          print("✅ Token saved from registration");
        } catch (e) {
          print("⚠️ Could not extract token from registration: $e");
        }
      }

      return response.statusCode == 201;
    } catch (e) {
      if (e is DioException) {
        print("STATUS CODE:");
        print(e.response?.statusCode);

        print("RESPONSE DATA:");
        print(e.response?.data);
      }

      print(e);

      return false;
    }
  }

  static Future<Response> getMe() async {
    return await dio.get(
      "api/account/me/",

      options: Options(headers: {"Authorization": "Bearer $accessToken"}),
    );
  }
}
