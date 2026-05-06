import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../widgets/shared_widgets.dart';
import '../services/api_service.dart'; // ✅ مهم

// ══════════════════════════════════════════════
//  الواجهة الثالثة — رقم الجوال والبريد
// ══════════════════════════════════════════════
class ContactScreen extends StatefulWidget {
  final GlobalKey<FormState> formKey;
  final TextEditingController phoneController;
  final TextEditingController emailController;
  final VoidCallback onBack;
  final String sessionId; // ✅ مهم

  const ContactScreen({
    super.key,
    required this.formKey,
    required this.phoneController,
    required this.emailController,
    required this.onBack,
    required this.sessionId,
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
                      decoration: inputDecoration('ادخل رقم الجوال'),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'رقم الجوال مطلوب';
                        if (v.length != 10)
                          return 'رقم الجوال يجب أن يكون 10 أرقام بالضبط';
                        return null;
                      },
                    ),

                    const SizedBox(height: 24),

                    fieldLabel('البريد الالكتروني'),
                    const SizedBox(height: 10),

                    TextFormField(
                      controller: widget.emailController,
                      keyboardType: TextInputType.emailAddress,
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      decoration: inputDecoration('ادخل البريد الالكتروني'),
                      validator: (v) {
                        if (v == null || v.isEmpty)
                          return 'البريد الإلكتروني مطلوب';
                        if (!v.endsWith('@gmail.com'))
                          return 'يجب أن ينتهي البريد بـ @gmail.com';
                        return null;
                      },
                    ),

                    const SizedBox(height: 50),

                    // 🔥 زر الإرسال النهائي (إنشاء الحساب)
                    buildButton('تسجيل', () async {
                      if (!widget.formKey.currentState!.validate()) return;

                      try {
                        // ⏳ loading
                        showDialog(
                          context: context,
                          barrierDismissible: false,
                          builder: (_) =>
                              const Center(child: CircularProgressIndicator()),
                        );

                        // 🔹 1. حفظ بيانات الاتصال
                        bool contactSaved = await ApiService.setContact(
                          sessionId: widget.sessionId,
                          phone: widget.phoneController.text,
                          email: widget.emailController.text,
                        );

                        if (!contactSaved) {
                          throw Exception("فشل حفظ بيانات الاتصال");
                        }

                        // 🔹 2. إنشاء الحساب النهائي
                        bool created = await ApiService.completeRegistration(
                          widget.sessionId,
                        );

                        Navigator.pop(context);

                        if (created) {
                          showDialog(
                            context: context,
                            builder: (_) => AlertDialog(
                              title: const Text("نجاح"),
                              content: const Text("تم إنشاء الحساب بنجاح 🎉"),
                              actions: [
                                TextButton(
                                  onPressed: () {
                                    Navigator.pop(context);
                                    Navigator.popUntil(
                                      context,
                                      (route) => route.isFirst,
                                    );
                                  },
                                  child: const Text("حسناً"),
                                ),
                              ],
                            ),
                          );
                        }
                      } catch (e) {
                        Navigator.pop(context);
                        print(e);

                        showDialog(
                          context: context,
                          builder: (_) => const AlertDialog(
                            title: Text("خطأ"),
                            content: Text("حدث خطأ أثناء إنشاء الحساب"),
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
