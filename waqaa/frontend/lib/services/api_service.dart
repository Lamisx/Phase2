import 'package:dio/dio.dart';

class ApiService {
  static const String baseUrl = "http://192.168.8.97:8000/"; //192.168.174.1

  static final Dio dio = Dio(
    BaseOptions(
      baseUrl: baseUrl,
      headers: {"Content-Type": "application/json"},
    ),
  );
}
