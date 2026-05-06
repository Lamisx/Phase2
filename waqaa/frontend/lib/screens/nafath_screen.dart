import 'dart:math';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'contact_screen.dart'; // ✅ تعديل مهم
import 'trusted_device.dart';
import 'details_screen.dart';

class NafathScreen extends StatefulWidget {
  final bool isLogin;
  final String sessionId;
  final String nationalId;

  const NafathScreen({
    super.key,
    this.isLogin = false,
    required this.sessionId,
    required this.nationalId,
  });

  @override
  State<NafathScreen> createState() => _NafathScreenState();
}

class _NafathScreenState extends State<NafathScreen> {
  int requestNumber = 0;

  @override
  void initState() {
    super.initState();
    generateRequestNumber();
    verifyNafath();
  }

  void generateRequestNumber() {
    final random = Random();
    requestNumber = random.nextInt(90) + 10;
  }

  // 🔹 التحقق من نفاذ
  Future<void> verifyNafath() async {
    try {
      final verified = await ApiService.verifyNafath(
        sessionId: widget.sessionId,
        nationalId: widget.nationalId,
      );

      if (!mounted) return;

      if (verified) {
        if (widget.isLogin) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const TrustedDevicesPage()),
          );
        } else {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => ContactScreen(
                formKey: GlobalKey<FormState>(),
                phoneController: TextEditingController(),
                emailController: TextEditingController(),
                sessionId: widget.sessionId,
                onBack: () => Navigator.pop(context),
              ),
            ),
          );
        }
      } else {
        showError();
      }
    } catch (e) {
      if (!mounted) return;
      showError();
    }
  }

  void showError() {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("خطأ"),
        content: const Text("فشل التحقق من نفاذ"),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: const Text("رجوع"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF314048),
      body: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              "جاري التحقق عبر نفاذ...",
              style: TextStyle(color: Colors.white, fontSize: 18),
            ),
            const SizedBox(height: 20),
            Text(
              "$requestNumber",
              style: const TextStyle(
                fontSize: 60,
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 30),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
