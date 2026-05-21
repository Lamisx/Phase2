import 'package:dio/dio.dart';

class ApiService {
  // =====================================================
  // BASE URL
  // =====================================================

  static const String baseUrl = "http://192.168.8.97:8000/";

  // =====================================================
  // DIO
  // =====================================================

  static final Dio dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      headers: {"Content-Type": "application/json"},
    ),
  );

  // =====================================================
  // LOGIN
  // =====================================================

  static Future<Response> login({
    required String username,
    required String password,
  }) async {
    return await dio.post(
      "api/account/auth/login/",

      data: {"username": username, "password": password},
    );
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

      print(response.data);

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
}
