import 'api_service.dart';

class AuthService {
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
    } catch (e) {
      print("LOGIN ERROR");

      print(e);
    }
  }
}
