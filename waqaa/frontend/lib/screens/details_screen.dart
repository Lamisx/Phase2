import 'package:flutter/material.dart';

import '../widgets/shared_widgets.dart';

class DetailsScreen extends StatefulWidget {
  final GlobalKey<FormState> formKey;

  final TextEditingController usernameController;

  final TextEditingController passwordController;

  final TextEditingController confirmPasswordController;

  final VoidCallback onNext;

  final VoidCallback onBack;

  const DetailsScreen({
    super.key,

    required this.formKey,

    required this.usernameController,

    required this.passwordController,

    required this.confirmPasswordController,

    required this.onNext,

    required this.onBack,
  });

  @override
  State<DetailsScreen> createState() => _DetailsScreenState();
}

class _DetailsScreenState extends State<DetailsScreen> {
  bool hidePassword = true;

  bool hideConfirmPassword = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF2E3B46),

      body: Stack(
        children: [
          buildWaveHeader(context),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),

              child: Form(
                key: widget.formKey,

                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,

                  children: [
                    const SizedBox(height: 10),

                    buildBackButton(widget.onBack),

                    const SizedBox(height: 60),

                    const Center(
                      child: Text(
                        'تسجيل البيانات',

                        style: TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),

                    const SizedBox(height: 10),

                    const Center(
                      child: Text(
                        'إنشاء اسم المستخدم و كلمة مرور قوية باستخدام مزيج من الأحرف والأرقام والرموز',

                        textAlign: TextAlign.center,

                        style: TextStyle(
                          fontSize: 12,
                          color: Color(0xFF81C784),
                        ),
                      ),
                    ),

                    const SizedBox(height: 50),

                    // =========================
                    // USERNAME
                    // =========================
                    fieldLabel('اسم المستخدم'),

                    const SizedBox(height: 10),

                    TextFormField(
                      controller: widget.usernameController,

                      textAlign: TextAlign.right,

                      style: const TextStyle(color: Colors.white),

                      decoration: inputDecoration('ادخل اسم المستخدم'),

                      validator: (v) {
                        if (v == null || v.isEmpty) {
                          return 'اسم المستخدم مطلوب';
                        }

                        if (v.length < 3) {
                          return 'اسم المستخدم قصير';
                        }

                        return null;
                      },
                    ),

                    const SizedBox(height: 30),

                    // =========================
                    // PASSWORD
                    // =========================
                    fieldLabel('كلمة المرور'),

                    const SizedBox(height: 10),

                    TextFormField(
                      controller: widget.passwordController,

                      obscureText: hidePassword,

                      textAlign: TextAlign.right,

                      style: const TextStyle(color: Colors.white),

                      decoration: inputDecoration('ادخل كلمة المرور').copyWith(
                        suffixIcon: IconButton(
                          icon: Icon(
                            hidePassword
                                ? Icons.visibility_off
                                : Icons.visibility,

                            color: Colors.white54,
                          ),

                          onPressed: () {
                            setState(() {
                              hidePassword = !hidePassword;
                            });
                          },
                        ),
                      ),

                      validator: (v) {
                        if (v == null || v.isEmpty) {
                          return 'كلمة المرور مطلوبة';
                        }

                        if (v.length < 8) {
                          return 'كلمة المرور ضعيفة';
                        }

                        return null;
                      },
                    ),

                    const SizedBox(height: 30),

                    // =========================
                    // CONFIRM PASSWORD
                    // =========================
                    fieldLabel('تأكيد كلمة المرور'),

                    const SizedBox(height: 10),

                    TextFormField(
                      controller: widget.confirmPasswordController,

                      obscureText: hideConfirmPassword,

                      textAlign: TextAlign.right,

                      style: const TextStyle(color: Colors.white),

                      decoration: inputDecoration('ادخل تأكيد كلمة المرور')
                          .copyWith(
                            suffixIcon: IconButton(
                              icon: Icon(
                                hideConfirmPassword
                                    ? Icons.visibility_off
                                    : Icons.visibility,

                                color: Colors.white54,
                              ),

                              onPressed: () {
                                setState(() {
                                  hideConfirmPassword = !hideConfirmPassword;
                                });
                              },
                            ),
                          ),

                      validator: (v) {
                        if (v == null || v.isEmpty) {
                          return 'تأكيد كلمة المرور مطلوب';
                        }

                        if (v != widget.passwordController.text) {
                          return 'كلمات المرور غير متطابقة';
                        }

                        return null;
                      },
                    ),

                    const SizedBox(height: 70),

                    // =========================
                    // BUTTON
                    // =========================
                    SizedBox(
                      width: double.infinity,

                      height: 55,

                      child: ElevatedButton(
                        onPressed: () {
                          if (widget.formKey.currentState!.validate()) {
                            widget.onNext();
                          }
                        },

                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF3B8550),

                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(15),
                          ),
                        ),

                        child: const Text(
                          'تسجيل',

                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(height: 20),

                    const Center(
                      child: Text(
                        'بتسجيل الدخول أنت توافق على الشروط والأحكام',

                        style: TextStyle(color: Colors.white70, fontSize: 12),
                      ),
                    ),
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
