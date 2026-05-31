import 'package:dio/dio.dart';

class ApiService {
  // =====================================================
  // BASE URL
  // =====================================================

  static const String baseUrl = "http://192.168.68.105:8000/";
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
    required String sessionId,

    required String nationalId,

    required String username,

    required String password,

    required String phone,

    required String email,
  }) async {
    try {
      final response = await dio.post(
        "api/account/auth/register/complete/",

        data: {
          "session_id": sessionId,
          "national_id": nationalId,

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
      print("❌ COMPLETE REGISTRATION ERROR");

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

  // ============================================================
  // ADD THESE TWO METHODS to api_service.dart
  // (داخل class ApiService، أضيفي قبل القوس الأخير })
  // ============================================================
  //
  // لا تحتاج أي استيرادات إضافية — Dio موجود أصلاً.
  // التوكن مرفق تلقائياً في dio.options.headers بعد login.

  // =====================================================
  // GENERATE DELEGATION CODE  (A يولّد رمز لإعطائه لـ B)
  // =====================================================
  //
  // Response من الباك:
  //   { "code": "847291", "expires_in": 300, "expires_at": "..." }
  //
  static Future<Map<String, dynamic>> generateDelegationCode() async {
    try {
      final response = await dio.post("api/account/delegations/generate-code/");

      if (response.statusCode == 201) {
        return {
          "code": response.data["code"]?.toString() ?? "",
          "expires_in": response.data["expires_in"] ?? 300,
          "expires_at": response.data["expires_at"]?.toString() ?? "",
        };
      }

      throw Exception("Failed to generate code: ${response.statusCode}");
    } catch (e) {
      print("❌ generateDelegationCode error: $e");
      if (e is DioException) {
        print("STATUS: ${e.response?.statusCode}");
        print("DATA: ${e.response?.data}");
      }
      rethrow;
    }
  }

  // =====================================================
  // ACCEPT DELEGATION CODE  (B يدخل الرمز اللي حصل عليه من A)
  // =====================================================
  //
  // Response من الباك (نجاح):
  //   {
  //     "message": "DELEGATION_ACCEPTED",
  //     "delegation": {
  //       "owner_username": "rawan",
  //       "delegated_username": "layan",
  //       ...
  //     }
  //   }
  //
  // يُرجع owner_username (اسم الشخص اللي فوّضك) لعرضه في رسالة النجاح.
  //
  static Future<String> acceptDelegationCode({required String code}) async {
    try {
      final response = await dio.post(
        "api/account/delegations/accept-code/",
        data: {"code": code.trim()},
      );

      if (response.statusCode == 201) {
        // اسم صاحب الحساب اللي فوّضك (للعرض في رسالة النجاح)
        final ownerUsername =
            response.data["delegation"]?["owner_username"]?.toString() ??
            "صاحب الحساب";
        return ownerUsername;
      }

      // أخطاء معالجة (الباك يرجّع 400 مع رسالة واضحة)
      if (response.statusCode == 400) {
        print("🔍 BACKEND 400 RESPONSE: ${response.data}"); // ← أضيفي هذا السطر
        final errorMsg = _extractDelegationError(response.data);
        throw Exception(errorMsg);
      }

      throw Exception("Failed: ${response.statusCode}");
    } catch (e) {
      print("❌ acceptDelegationCode error: $e");
      if (e is DioException) {
        print("STATUS: ${e.response?.statusCode}");
        print("DATA: ${e.response?.data}");
        // استخرج رسالة الخطأ من response لو موجودة
        if (e.response?.data is Map) {
          final msg = _extractDelegationError(e.response!.data);
          throw Exception(msg);
        }
      }
      rethrow;
    }
  }

  // مساعدة: يستخرج رسالة الخطأ من response الباك
  static String _extractDelegationError(dynamic data) {
    if (data is Map) {
      // {"code": ["Invalid or already used code."]}
      if (data["code"] is List && (data["code"] as List).isNotEmpty) {
        return data["code"][0].toString();
      }
      if (data["code"] is String) return data["code"];
      if (data["detail"] != null) return data["detail"].toString();
    }
    return "رمز غير صحيح";
  }
  // ============================================================
  // ADD these methods to api_service.dart
  // (داخل class ApiService، قبل القوس الأخير })
  // ============================================================
  //
  // تستخدمان للحسابات المرتبطة:
  //   getReceivedDelegations  → جلب التفويضات اللي استلمها المستخدم
  //   revokeMyDelegation      → إلغاء تفويض من جانب المُفوَّض

  // =====================================================
  // GET RECEIVED DELEGATIONS  (B يجلب من فوّضوه)
  // =====================================================
  //
  // Response من الباك:
  //   {
  //     "count": 2,
  //     "delegations": [
  //       {
  //         "id": "...",
  //         "owner_username": "rawan",
  //         "delegated_username": "layan",
  //         "delegated_display_name": "Layan",
  //         "status": "active",
  //         ...
  //       },
  //       ...
  //     ]
  //   }
  //
  static Future<List<Map<String, dynamic>>> getReceivedDelegations() async {
    try {
      final response = await dio.get("api/account/delegations/received/");

      if (response.statusCode == 200) {
        final List<dynamic> list = response.data["delegations"] ?? [];
        return list.cast<Map<String, dynamic>>();
      }

      throw Exception("Failed: ${response.statusCode}");
    } catch (e) {
      print("❌ getReceivedDelegations error: $e");
      if (e is DioException) {
        print("STATUS: ${e.response?.statusCode}");
        print("DATA: ${e.response?.data}");
      }
      rethrow;
    }
  }

  // =====================================================
  // REVOKE MY DELEGATION  (B يلغي تفويضه عن A)
  // =====================================================
  //
  // delegationId = id من response getReceivedDelegations
  //
  static Future<void> revokeMyDelegation({required String delegationId}) async {
    try {
      final response = await dio.delete(
        "api/account/delegations/$delegationId/revoke-as-delegated/",
      );

      if (response.statusCode != 200) {
        throw Exception("Failed: ${response.statusCode}");
      }
    } catch (e) {
      print("❌ revokeMyDelegation error: $e");
      if (e is DioException) {
        print("STATUS: ${e.response?.statusCode}");
        print("DATA: ${e.response?.data}");
      }
      rethrow;
    }
  }
}
