import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../widgets/shared_widgets.dart';

// ══════════════════════════════════════════════
//  الواجهة الثانية — اسم المستخدم وكلمة المرور
// ══════════════════════════════════════════════
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
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  String _passwordStrengthText = '';
  Color _passwordStrengthColor = Colors.transparent;

  void _checkPasswordStrength(String password) {
    if (password.isEmpty) {
      setState(() {
        _passwordStrengthText = '';
        _passwordStrengthColor = Colors.transparent;
      });
      return;
    }
    final hasUppercase = RegExp(r'[A-Z]').hasMatch(password);
    final hasLowercase = RegExp(r'[a-z]').hasMatch(password);
    final hasDigits = RegExp(r'[0-9]').hasMatch(password);
    final hasSpecialChars = RegExp(
      r'[!@#\$%^&*(),.?":{}|<>]',
    ).hasMatch(password);

    if (!(hasUppercase && hasLowercase && hasDigits && hasSpecialChars)) {
      setState(() {
        _passwordStrengthText =
            'يجب أن تحتوي على أحرف كبيرة وصغيرة وأرقام ورموز';
        _passwordStrengthColor = Colors.red;
      });
      return;
    }
    if (password.length >= 10) {
      setState(() {
        _passwordStrengthText = 'كلمة مرور قوية';
        _passwordStrengthColor = Colors.green;
      });
    } else {
      setState(() {
        _passwordStrengthText = 'كلمة مرور متوسطة';
        _passwordStrengthColor = Colors.orange;
      });
    }
  }

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
                      'تسجيل البيانات',
                      textDirection: TextDirection.rtl,
                      style: TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'إنشاء اسم المستخدم و كلمة مرور قوية باستخدام مزيج من الأحرف والأرقام والرموز',
                      textDirection: TextDirection.rtl,
                      textAlign: TextAlign.right,
                      style: TextStyle(fontSize: 12, color: Color(0xFF81C784)),
                    ),
                    const SizedBox(height: 30),
                    fieldLabel('اسم المستخدم'),
                    const SizedBox(height: 10),
                    TextFormField(
                      controller: widget.usernameController,
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.ltr,
                      inputFormatters: [
                        FilteringTextInputFormatter.deny(RegExp(r'\s')),
                        FilteringTextInputFormatter.allow(
                          RegExp(r'[a-zA-Z0-9_]'),
                        ),
                      ],
                      decoration: inputDecoration('ادخل اسم المستخدم'),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'اسم المستخدم مطلوب';
                        if (v.contains(' '))
                          return 'لا يُسمح بالمسافات في اسم المستخدم';
                        if (!RegExp(r'^[a-zA-Z0-9_]+$').hasMatch(v))
                          return 'اسم المستخدم يجب أن يكون بالإنجليزية فقط';
                        return null;
                      },
                    ),
                    const SizedBox(height: 20),
                    fieldLabel('كلمة المرور'),
                    const SizedBox(height: 10),
                    TextFormField(
                      controller: widget.passwordController,
                      obscureText: _obscurePassword,
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      onChanged: _checkPasswordStrength,
                      decoration: inputDecoration('ادخل كلمة المرور').copyWith(
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_off
                                : Icons.visibility,
                            color: Colors.white38,
                          ),
                          onPressed: () => setState(
                            () => _obscurePassword = !_obscurePassword,
                          ),
                        ),
                      ),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'كلمة المرور مطلوبة';
                        if (_passwordStrengthColor == Colors.red)
                          return 'كلمة مرور ضعيفة جداً';
                        return null;
                      },
                    ),
                    const SizedBox(height: 20),
                    fieldLabel('تأكيد كلمة المرور'),
                    const SizedBox(height: 10),
                    TextFormField(
                      controller: widget.confirmPasswordController,
                      obscureText: _obscureConfirmPassword,
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      decoration: inputDecoration('ادخل تأكيد كلمة المرور')
                          .copyWith(
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscureConfirmPassword
                                    ? Icons.visibility_off
                                    : Icons.visibility,
                                color: Colors.white38,
                              ),
                              onPressed: () => setState(
                                () => _obscureConfirmPassword =
                                    !_obscureConfirmPassword,
                              ),
                            ),
                          ),
                      validator: (v) => (v != widget.passwordController.text)
                          ? 'كلمات المرور غير متطابقة'
                          : null,
                    ),
                    if (_passwordStrengthText.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          _passwordStrengthText,
                          textDirection: TextDirection.rtl,
                          style: TextStyle(
                            color: _passwordStrengthColor,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    const SizedBox(height: 30),
                    buildButton('تسجيل', () {
                      if (widget.formKey.currentState!.validate()) {
                        widget.onNext();
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
