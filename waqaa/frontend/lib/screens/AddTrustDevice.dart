// lib/screens/AddTrustDevice.dart
//
// شاشة التفويض — بين شخصين (A يفوّض B):
//
//   البطاقة 1 (للمستخدم A):  "إنشاء رمز تسجيل" → "توليد الرمز"
//     يولّد رمز 6 أرقام صالح 5 دقائق، يعرضه في dialog كبير
//     مع عدّاد تنازلي وزر نسخ. A يعطي الرمز لـ B شفهياً.
//
//   البطاقة 2 (للمستخدم B):  "أدخل الرمز من جهاز آخر"
//     B يضغط → ينفتح dialog بحقل إدخال 6 خانات → يدخل الرمز
//     → ينجح → رسالة "تم تفويضك من [اسم A]".

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/api_service.dart';

class GenerateCodeScreen extends StatefulWidget {
  const GenerateCodeScreen({super.key});

  @override
  State<GenerateCodeScreen> createState() => _GenerateCodeScreenState();
}

class _GenerateCodeScreenState extends State<GenerateCodeScreen> {
  bool _generating = false;
  bool _accepting = false;

  Future<void> _generateCode() async {
    setState(() => _generating = true);
    try {
      final result = await ApiService.generateDelegationCode();
      if (!mounted) return;
      await _showCodeDialog(
        code: result["code"] as String,
        expiresIn: result["expires_in"] as int,
      );
    } catch (e) {
      _snack("تعذّر توليد الرمز: ${_cleanError(e)}");
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  Future<void> _enterCode() async {
    final code = await _showEnterCodeDialog();
    if (code == null || code.length != 6) return;

    setState(() => _accepting = true);
    try {
      final ownerUsername = await ApiService.acceptDelegationCode(code: code);
      if (!mounted) return;
      await _showSuccessDialog(ownerUsername);
    } catch (e) {
      _snack("فشل قبول الرمز: ${_cleanError(e)}");
    } finally {
      if (mounted) setState(() => _accepting = false);
    }
  }

  Future<void> _showCodeDialog({
    required String code,
    required int expiresIn,
  }) async {
    return showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) =>
          _CodeDisplayDialog(code: code, expiresInSeconds: expiresIn),
    );
  }

  Future<String?> _showEnterCodeDialog() async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (ctx) => Directionality(
        textDirection: TextDirection.rtl,
        child: AlertDialog(
          backgroundColor: const Color(0xFF344A52),
          title: const Text(
            "أدخل الرمز",
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                "اطلب الرمز من الشخص الذي يفوّضك",
                style: TextStyle(color: Colors.white70, fontSize: 13),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                maxLength: 6,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(6),
                ],
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  letterSpacing: 12,
                  fontWeight: FontWeight.bold,
                ),
                decoration: const InputDecoration(
                  counterText: "",
                  hintText: "000000",
                  hintStyle: TextStyle(
                    color: Colors.white24,
                    letterSpacing: 12,
                  ),
                  enabledBorder: UnderlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF23AB49)),
                  ),
                  focusedBorder: UnderlineInputBorder(
                    borderSide: BorderSide(color: Color(0xFF23AB49), width: 2),
                  ),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text(
                "إلغاء",
                style: TextStyle(color: Colors.white70),
              ),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF3B8550),
              ),
              onPressed: () {
                final c = controller.text.trim();
                if (c.length != 6) return;
                Navigator.pop(ctx, c);
              },
              child: const Text("تأكيد", style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showSuccessDialog(String ownerUsername) async {
    return showDialog(
      context: context,
      builder: (ctx) => Directionality(
        textDirection: TextDirection.rtl,
        child: AlertDialog(
          backgroundColor: const Color(0xFF344A52),
          title: const Text(
            "تم بنجاح 🎉",
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          content: Text(
            "أصبحت الآن مفوّضاً عن حساب $ownerUsername",
            style: const TextStyle(color: Colors.white70, fontSize: 14),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pop(context); // العودة لشاشة الأجهزة
              },
              child: const Text(
                "حسناً",
                style: TextStyle(color: Color(0xFF23AB49)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _snack(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  String _cleanError(dynamic e) {
    return e.toString().replaceFirst("Exception: ", "");
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: const Color(0xFF314048),
        appBar: AppBar(
          backgroundColor: const Color(0xFF314048),
          elevation: 0,
          centerTitle: true,
          automaticallyImplyLeading: false,
          leading: Directionality(
            textDirection: TextDirection.ltr,
            child: IconButton(
              icon: const Icon(Icons.arrow_forward, color: Color(0xFF3B8550)),
              onPressed: () => Navigator.pop(context),
            ),
          ),
          title: const Text(
            "إضافة جهاز موثوق",
            style: TextStyle(
              color: Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w600,
            ),
          ),
          bottom: const PreferredSize(
            preferredSize: Size.fromHeight(2),
            child: Divider(thickness: 2, height: 2, color: Color(0xFF23AB49)),
          ),
        ),
        body: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 30),
          child: Column(
            children: [
              _Card(
                icon: Icons.smartphone,
                title: "إنشاء رمز تسجيل",
                description: "إنشاء رمز آمن لتفويض شخص آخر بحسابك.",
                buttonText: "توليد الرمز",
                loading: _generating,
                onPressed: _generateCode,
              ),
              const SizedBox(height: 40),
              Row(
                children: const [
                  Expanded(
                    child: Divider(color: Color(0xFF23AB49), thickness: 1),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 14),
                    child: Text(
                      "أو",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Divider(color: Color(0xFF23AB49), thickness: 1),
                  ),
                ],
              ),
              const SizedBox(height: 40),
              _Card(
                icon: Icons.smartphone_outlined,
                title: "أدخل الرمز من شخص آخر",
                description: "هل لديك رمز تفويض؟ أدخله هنا لربط حسابك بحسابهم.",
                buttonText: "إدخال الرمز",
                loading: _accepting,
                onPressed: _enterCode,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Card extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;
  final String buttonText;
  final bool loading;
  final VoidCallback onPressed;

  const _Card({
    required this.icon,
    required this.title,
    required this.description,
    required this.buttonText,
    required this.loading,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF536976),
        borderRadius: BorderRadius.circular(14),
        boxShadow: const [
          BoxShadow(color: Colors.black45, blurRadius: 8, offset: Offset(0, 5)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: const Color(0xFF85FC6E), size: 26),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      description,
                      style: const TextStyle(
                        color: Color(0xFFAECCDD),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            height: 45,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF3B8550),
                shadowColor: Colors.transparent,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              onPressed: loading ? null : onPressed,
              child: loading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(
                      buttonText,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                        color: Colors.white,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CodeDisplayDialog extends StatefulWidget {
  final String code;
  final int expiresInSeconds;

  const _CodeDisplayDialog({
    required this.code,
    required this.expiresInSeconds,
  });

  @override
  State<_CodeDisplayDialog> createState() => _CodeDisplayDialogState();
}

class _CodeDisplayDialogState extends State<_CodeDisplayDialog> {
  late int _remaining;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _remaining = widget.expiresInSeconds;
    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) {
        t.cancel();
        return;
      }
      setState(() {
        _remaining--;
        if (_remaining <= 0) t.cancel();
      });
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  String _formatTime(int seconds) {
    if (seconds <= 0) return "انتهى";
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return "$m:${s.toString().padLeft(2, '0')}";
  }

  void _copyCode() {
    Clipboard.setData(ClipboardData(text: widget.code));
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text("تم نسخ الرمز")));
  }

  @override
  Widget build(BuildContext context) {
    final expired = _remaining <= 0;
    return Directionality(
      textDirection: TextDirection.rtl,
      child: AlertDialog(
        backgroundColor: const Color(0xFF344A52),
        title: const Text(
          "رمز التفويض",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          textAlign: TextAlign.center,
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "أعطِ هذا الرمز للشخص الذي تريد تفويضه:",
              style: TextStyle(color: Colors.white70, fontSize: 13),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              decoration: BoxDecoration(
                color: const Color(0xFF1F2E35),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: expired
                      ? const Color(0xFFE11D48)
                      : const Color(0xFF23AB49),
                  width: 2,
                ),
              ),
              child: Text(
                widget.code,
                style: TextStyle(
                  color: expired ? const Color(0xFFE11D48) : Colors.white,
                  fontSize: 38,
                  letterSpacing: 8,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.timer_outlined,
                  size: 18,
                  color: expired
                      ? const Color(0xFFE11D48)
                      : const Color(0xFF85FC6E),
                ),
                const SizedBox(width: 6),
                Text(
                  expired
                      ? "الرمز انتهى"
                      : "ينتهي خلال ${_formatTime(_remaining)}",
                  style: TextStyle(
                    color: expired
                        ? const Color(0xFFE11D48)
                        : const Color(0xFF85FC6E),
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          if (!expired)
            TextButton.icon(
              onPressed: _copyCode,
              icon: const Icon(Icons.copy, size: 16, color: Color(0xFF23AB49)),
              label: const Text(
                "نسخ",
                style: TextStyle(color: Color(0xFF23AB49)),
              ),
            ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF3B8550),
            ),
            onPressed: () => Navigator.pop(context),
            child: const Text("إغلاق", style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
