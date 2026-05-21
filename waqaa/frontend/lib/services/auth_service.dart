import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api_service.dart';

class AuthService {
  static const storage = FlutterSecureStorage();

  static Future<void> login({
    required String username,
    required String password,
  }) async {
    try {
      print("START LOGIN");

      final response = await ApiService.dio.post(
        "api/account/auth/login/",

        data: {"username": username, "password": password},
      );

      print("LOGIN SUCCESS");

      print(response.data);

      await storage.write(
        key: "access",

        value: response.data["tokens"]["access"],
      );

      await storage.write(
        key: "refresh",

        value: response.data["tokens"]["refresh"],
      );

      print("TOKENS SAVED");
    } on DioException catch (e) {
      print("LOGIN ERROR");

      print(e.response?.data);
    } catch (e) {
      print("ERROR");

      print(e);
    }
  }
}
