import 'package:dio/dio.dart';

class ApiService {
  static const String baseUrl = "http://192.168.8.53:8000";

  static final Dio dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      headers: {"Content-Type": "application/json"},
    ),
  );
}
