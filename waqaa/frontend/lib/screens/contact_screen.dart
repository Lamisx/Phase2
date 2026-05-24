import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../widgets/shared_widgets.dart';
import '../services/api_service.dart';
import '../services/device_service.dart';
import '../services/crypto_service.dart';

class ContactScreen extends StatefulWidget {
  final GlobalKey<FormState> formKey;
  final TextEditingController phoneController;
  final TextEditingController emailController;
  final TextEditingController usernameController;
  final TextEditingController passwordController;
  final VoidCallback onBack;
  final VoidCallback onSubmit;
  final String sessionId;
  final String nationalId;

  const ContactScreen({
    super.key,
    required this.formKey,
    required this.phoneController,
    required this.emailController,
    required this.usernameController,
    required this.passwordController,
    required this.onBack,
    required this.onSubmit,
    required this.sessionId,
    required this.nationalId,
  });

  @override
  State<ContactScreen> createState() => _ContactScreenState();
}

class _ContactScreenState extends State<ContactScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1C2B33),
      body: Stack(
        children: [
          buildWaveHeader(context),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Form(
                key: widget.formKey,
                child: Column(
                  textDirection: TextDirection.rtl,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 10),
                    buildBackButton(widget.onBack),
                    const SizedBox(height: 30),
                    const Text(
                      'يتبع',
                      style: TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'اكمال بيانات الحساب',
                      style: TextStyle(fontSize: 13, color: Color(0xFF81C784)),
                    ),
                    const SizedBox(height: 40),

                    // =====================================================================
                    // PHONE
                    // =====================================================================
                    fieldLabel('رقم الجوال'),
                    const SizedBox(height: 10),
                    TextFormField(
                      controller: widget.phoneController,
                      keyboardType: TextInputType.phone,
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      inputFormatters: [
                        FilteringTextInputFormatter.digitsOnly,
                        LengthLimitingTextInputFormatter(10),
                      ],
                      decoration: inputDecoration(
                        'ادخل رقم الجوال (5XXXXXXXXX)',
                      ),
                      validator: (v) {
                        if (v == null || v.isEmpty) {
                          return 'رقم الجوال مطلوب';
                        }
                        if (v.length != 10) {
                          return 'رقم الجوال يجب أن يكون 10 أرقام';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 24),

                    // =====================================================================
                    // EMAIL
                    // =====================================================================
                    fieldLabel('البريد الالكتروني'),
                    const SizedBox(height: 10),
                    TextFormField(
                      controller: widget.emailController,
                      keyboardType: TextInputType.emailAddress,
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      decoration: inputDecoration('ادخل البريد الالكتروني'),
                      validator: (v) {
                        if (v == null || v.isEmpty) {
                          return 'البريد الإلكتروني مطلوب';
                        }
                        // Simple email validation
                        if (!v.contains('@')) {
                          return 'البريد الإلكتروني غير صحيح';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 50),

                    // =====================================================================
                    // SUBMIT BUTTON
                    // =====================================================================
                    buildButton('تسجيل', () async {
                      if (!widget.formKey.currentState!.validate()) {
                        return;
                      }

                      try {
                        showDialog(
                          context: context,
                          barrierDismissible: false,
                          builder: (_) =>
                              const Center(child: CircularProgressIndicator()),
                        );

                        print("\n📝 === REGISTRATION COMPLETE ===");

                        // =====================================================================
                        // VALIDATION
                        // =====================================================================
                        print("📋 Validating data...");
                        print("   National ID: ${widget.nationalId}");
                        print("   Session ID: ${widget.sessionId}");
                        print("   Username: ${widget.usernameController.text}");
                        print("   Phone: ${widget.phoneController.text}");
                        print("   Email: ${widget.emailController.text}");

                        // Check required data
                        if (widget.nationalId.isEmpty) {
                          throw Exception("National ID is empty");
                        }
                        if (widget.sessionId.isEmpty) {
                          throw Exception("Session ID is empty");
                        }

                        // =====================================================================
                        // STEP 1: CREATE ACCOUNT
                        // =====================================================================
                        print("1️⃣ Creating account...");

                        bool created = await ApiService.completeRegistration(
                          sessionId: widget.sessionId,
                          nationalId: widget.nationalId,
                          username: widget.usernameController.text,
                          password: widget.passwordController.text,
                          phone: widget.phoneController.text,
                          // ✅ With country code
                          email: widget.emailController.text,
                        );

                        if (!created) {
                          throw Exception("Account creation failed");
                        }

                        print("✅ Account created successfully");

                        // =====================================================================
                        // STEP 2: CREATE DEVICE (happens after account creation)
                        // =====================================================================
                        print("2️⃣ Creating device...");

                        final deviceId = await DeviceService.createDevice();

                        if (deviceId == null) {
                          throw Exception("Device creation failed");
                        }

                        print("✅ Device created: $deviceId");

                        // =====================================================================
                        // STEP 3: GENERATE KEYS (happens DURING REGISTRATION)
                        // =====================================================================
                        print("3️⃣ Generating cryptographic keys...");

                        final keys = await CryptoService.generateKeyPair();

                        if (keys == null || keys["publicKey"] == null) {
                          throw Exception("Key generation failed");
                        }

                        print("✅ Keys generated");

                        // =====================================================================
                        // STEP 4: REGISTER PUBLIC KEY
                        // =====================================================================
                        print("4️⃣ Registering public key...");

                        await DeviceService.registerDeviceKey(
                          deviceId: deviceId,
                          publicKey: keys["publicKey"]!,
                        );

                        print("✅ Public key registered");

                        print(
                          "📝 === REGISTRATION COMPLETE - DEVICE READY ===\n",
                        );

                        if (!mounted) return;

                        Navigator.pop(context);
                        widget.onSubmit();
                      } catch (e) {
                        if (mounted) Navigator.pop(context);

                        print("❌ Registration Error: $e");

                        showDialog(
                          context: context,
                          builder: (_) => AlertDialog(
                            title: const Text("خطأ"),
                            content: Text("حدث خطأ أثناء إنشاء الحساب:\n\n$e"),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(context),
                                child: const Text("حسناً"),
                              ),
                            ],
                          ),
                        );
                      }
                    }),

                    const SizedBox(height: 16),
                    buildFooter(),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
