import 'package:flutter/material.dart';

import 'id_screen.dart';
import 'contact_screen.dart';
import 'trusted_device.dart';
import 'details_screen.dart';

class RegistrationFlow extends StatefulWidget {
  const RegistrationFlow({super.key});

  @override
  State<RegistrationFlow> createState() => _RegistrationFlowState();
}

class _RegistrationFlowState extends State<RegistrationFlow> {
  int _currentPage = 0;
  String? sessionId;
  String? nationalId;

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
    _idController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  // =====================================================
  // NAVIGATION HELPERS
  // =====================================================

  void _nextPage() {
    setState(() {
      _currentPage++;
    });
  }

  void _prevPage() {
    setState(() {
      _currentPage--;
    });
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

  // =====================================================
  // ID SCREEN CALLBACK
  // =====================================================
  void _handleIdScreenNext(
    String receivedSessionId,
    String receivedNationalId,
  ) {
    print("🎯 ID Screen Callback");
    print("   SESSION: $receivedSessionId");
    print("   NATIONAL ID: $receivedNationalId");

    setState(() {
      sessionId = receivedSessionId;
      nationalId = receivedNationalId;
      print("✅ State Updated");
      print("   nationalId = $nationalId");
      print("   sessionId = $sessionId");
    });

    _nextPage();
  }

  // =====================================================
  // DETAILS SCREEN CALLBACK
  // =====================================================
  void _handleDetailsScreenNext() {
    _nextPage();
  }

  // =====================================================
  // CONTACT SCREEN CALLBACK
  // =====================================================
  void _handleContactScreenSubmit() {
    _showConfirmationDialog();
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: const Color(0xFF1E242C),
        body: IndexedStack(
          index: _currentPage,
          children: [
            // =====================================
            // PAGE 0: ID SCREEN
            // =====================================
            IdScreen(
              formKey: _idFormKey,
              idController: _idController,
              onNext: _handleIdScreenNext,
            ),

            // =====================================
            // PAGE 1: DETAILS SCREEN
            // =====================================
            DetailsScreen(
              formKey: _detailsFormKey,
              usernameController: _usernameController,
              passwordController: _passwordController,
              confirmPasswordController: _confirmPasswordController,
              onNext: _handleDetailsScreenNext,
              onBack: _prevPage,
            ),

            // =====================================
            // PAGE 2: CONTACT SCREEN
            // =====================================
            ContactScreen(
              formKey: _contactFormKey,
              phoneController: _phoneController,
              emailController: _emailController,
              usernameController: _usernameController,
              passwordController: _passwordController,
              nationalId: nationalId ?? "",
              sessionId: sessionId ?? "",
              onBack: _prevPage,
              onSubmit: _handleContactScreenSubmit,
            ),
          ],
        ),
      ),
    );
  }
}
