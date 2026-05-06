import 'dart:convert';
import 'package:http/http.dart' as http;

// عنوان السيرفر — نغيره لما ننشر المشروع
const String baseUrl = "http://127.0.0.1:8000";

// API Key الخاص بالمنظمة — يجي من الـ Backend
const String apiKey = "ضع_الـ_API_KEY_هنا";

// الهيدر الأساسي لكل الطلبات
Map<String, String> getHeaders() {
  return {"Content-Type": "application/json", "X-API-KEY": apiKey};
}

// ===========================
// دالة تسجيل الدخول
// ===========================
Future<Map<String, dynamic>> login(String nationalId, String password) async {
  final response = await http.post(
    Uri.parse("$baseUrl/api/accounts/login/"),
    headers: getHeaders(),
    body: jsonEncode({"national_id": nationalId, "password": password}),
  );

  return jsonDecode(response.body);
}
