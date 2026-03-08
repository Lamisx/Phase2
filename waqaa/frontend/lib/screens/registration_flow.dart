import 'package:flutter/material.dart';
import 'id_screen.dart';
import 'details_screen.dart';
import 'contact_screen.dart';
import 'AddTrustDevice.dart';

// ══════════════════════════════════════════════
//  المنسّق الرئيسي للتسجيل (يتحكم في PageView)
// ══════════════════════════════════════════════
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
      builder: (context) => Directionality(
        textDirection: TextDirection.rtl,
        child: AlertDialog(
          backgroundColor: const Color(0xFF252A34),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          title: const Row(
            children: [
              Icon(Icons.mark_email_read, color: Color(0xFF2E8B57), size: 28),
              SizedBox(width: 10),
              Text(
                'تم الإرسال!',
                style: TextStyle(color: Colors.white, fontSize: 20),
              ),
            ],
          ),
          content: RichText(
            textDirection: TextDirection.rtl,
            text: TextSpan(
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 14,
                height: 1.6,
              ),
              children: [
                const TextSpan(
                  text: 'تم إرسال رسالة تأكيد إلى بريدك الإلكتروني\n',
                ),
                TextSpan(
                  text: _emailController.text,
                  style: const TextStyle(
                    color: Color(0xFF81C784),
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const TextSpan(
                  text:
                      '\n\nيرجى التحقق من بريدك الوارد والضغط على رابط التأكيد لإتمام التسجيل.',
                ),
              ],
            ),
          ),
          actions: [
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2E8B57),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () {
                  Navigator.of(context).pop();

                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const GenerateCodeScreen(),
                    ),
                  );
                },
                child: const Text(
                  'حسناً',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ],
        ),
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
            IdScreen(
              formKey: _idFormKey,
              idController: _idController,
              onNext: _nextPage,
            ),
            DetailsScreen(
              formKey: _detailsFormKey,
              usernameController: _usernameController,
              passwordController: _passwordController,
              confirmPasswordController: _confirmPasswordController,
              onNext: _nextPage,
              onBack: _prevPage,
            ),
            ContactScreen(
              formKey: _contactFormKey,
              phoneController: _phoneController,
              emailController: _emailController,
              onSubmit: _showConfirmationDialog,
              onBack: _prevPage,
            ),
          ],
        ),
      ),
    );
  }
}
