import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../widgets/shared_widgets.dart';
import '../services/api_service.dart'; // ✅ مهم
import 'nafath_screen.dart';

// ══════════════════════════════════════════════
//  الواجهة الأولى — رقم الهوية
// ══════════════════════════════════════════════
class IdScreen extends StatefulWidget {
  final GlobalKey<FormState> formKey;
  final TextEditingController idController;

  const IdScreen({
    super.key,
    required this.formKey,
    required this.idController,
  });

  @override
  State<IdScreen> createState() => _IdScreenState();
}

class _IdScreenState extends State<IdScreen> {
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
                    buildBackButton(() => Navigator.pop(context)),
                    const SizedBox(height: 60),

                    const Center(
                      child: Text(
                        'تسجيل حساب جديد',
                        textDirection: TextDirection.rtl,
                        style: TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),

                    const SizedBox(height: 50),

                    fieldLabel('رقم الهوية'),
                    const SizedBox(height: 10),

                    TextFormField(
                      controller: widget.idController,
                      keyboardType: TextInputType.number,
                      textAlign: TextAlign.right,
                      textDirection: TextDirection.rtl,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      decoration: inputDecoration('ادخل رقم الهوية'),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'رقم الهوية مطلوب';
                        if (v.length != 10)
                          return 'رقم الهوية يجب أن يكون 10 أرقام بالضبط';
                        return null;
                      },
                    ),

                    const SizedBox(height: 120),

                    // 🔴 زر تسجيل بعد الربط
                    buildButton('تسجيل', () async {
                      if (widget.formKey.currentState!.validate()) {
                        final nationalId = widget.idController.text;

                        try {
                          // ⏳ عرض loading
                          showDialog(
                            context: context,
                            barrierDismissible: false,
                            builder: (_) => const Center(
                              child: CircularProgressIndicator(),
                            ),
                          );

                          // 🔹 إرسال الهوية للباك اند
                          String sessionId = await ApiService.startRegistration(
                            nationalId,
                          );

                          // ❌ إغلاق loading
                          Navigator.pop(context);

                          // ✅ الانتقال لصفحة نفاذ
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => NafathScreen(
                                sessionId: sessionId,
                                nationalId: nationalId,
                              ),
                            ),
                          );
                        } catch (e) {
                          Navigator.pop(context);
                          print("ERROR: $e");
                        }
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
