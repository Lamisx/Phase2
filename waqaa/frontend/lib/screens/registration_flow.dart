import 'package:flutter/material.dart';
import 'id_screen.dart';
import 'details_screen.dart';
import 'contact_screen.dart';
import 'trusted_device.dart';

class RegistrationFlow extends StatefulWidget {
  const RegistrationFlow({super.key});

  @override
  State<RegistrationFlow> createState() => _RegistrationFlowState();
}

class _RegistrationFlowState extends State<RegistrationFlow> {
  final PageController _pageController = PageController();

  final _idFormKey = GlobalKey<FormState>();
  final _detailsFormKey = GlobalKey<FormState>();
  final _contactFormKey = GlobalKey<FormState>();

  final _idController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();

  @override
  void dispose() {
    _pageController.dispose();
    _idController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  void _nextPage() {
    _pageController.nextPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _prevPage() {
    _pageController.previousPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  void _showConfirmationDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text("تم"),
        content: const Text("تم إنشاء الحساب بنجاح"),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const TrustedDevicesPage(),
                ),
              );
            },
            child: const Text("حسناً"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: const Color(0xFF1E242C),
        body: PageView(
          controller: _pageController,
          physics: const NeverScrollableScrollPhysics(),
          children: [
            /// 🔹 شاشة الهوية
            IdScreen(
              formKey: _idFormKey,
              idController: _idController,
              onNext: _nextPage,
            ),

            /// 🔹 شاشة البيانات (username/password)
            DetailsScreen(
              formKey: _detailsFormKey,
              usernameController: _usernameController,
              passwordController: _passwordController,
              confirmPasswordController: _confirmPasswordController,
              onNext: _nextPage,
              onBack: _prevPage,
            ),

            /// 🔹 شاشة الجوال والبريد (تم تعديلها)
            ContactScreen(
              formKey: _contactFormKey,
              phoneController: _phoneController,
              emailController: _emailController,
              sessionId: "", // ✅ مهم (حل الخطأ)
              onBack: _prevPage,
            ),
          ],
        ),
      ),
    );
  }
}
