import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:math';
// ══════════════════════════════════════════════
//  اضافة الأجهزه الموثوقه
// ══════════════════════════════════════════════

class GenerateCodeScreen extends StatefulWidget {
  const GenerateCodeScreen({super.key});

  @override
  State<GenerateCodeScreen> createState() => _GenerateCodeScreenState();
}

class _GenerateCodeScreenState extends State<GenerateCodeScreen> {
  bool isPressed = false;
  List<int> generatedCode = [];
  Timer? _timer;
  int _secondsLeft = 120;
  bool codeVisible = false;

  void _generateCode() {
    _timer?.cancel();
    final random = Random();
    setState(() {
      generatedCode = List.generate(6, (_) => random.nextInt(10));
      _secondsLeft = 120;
      codeVisible = true;
    });

    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsLeft <= 1) {
        _generateCode(); // يجدد تلقائياً بعد دقيقتين
      } else {
        setState(() => _secondsLeft--);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: const Color(0xFF314048),

        appBar: AppBar(
          backgroundColor: const Color(0xFF314048),
          elevation: 0,
          centerTitle: true,

          // إلغاء السهم الافتراضي
          automaticallyImplyLeading: false,

          // ✅ سهم يمين أخضر واتجاه صحيح
          leading: Directionality(
            textDirection: TextDirection.ltr, // يمنع الانعكاس
            child: IconButton(
              icon: const Icon(Icons.arrow_forward, color: Color(0xFF3B8550)),
              onPressed: () {
                Navigator.pop(context);
              },
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
              /// CARD 1
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: const Color(0xFF536976),
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: const [
                    BoxShadow(
                      color: Colors.black45,
                      blurRadius: 8,
                      offset: Offset(0, 5),
                    ),
                  ],
                ),

                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Icon(
                          Icons.smartphone,
                          color: Color(0xFF85FC6E),
                          size: 26,
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "إنشاء رمز تسجيل",
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              SizedBox(height: 6),
                              Text(
                                "إنشاء رمز آمن لتسجيل جهاز جديد.",
                                style: TextStyle(
                                  color: Color(0xFFAECCDD),
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 18),

                    /// زر Gradient
                    Container(
                      width: double.infinity,
                      height: 45,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF3B8550), Color(0xFF3B8550)],
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight,
                        ),
                        borderRadius: BorderRadius.circular(10),
                      ),

                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),

                        onPressed: _generateCode,

                        child: const Text(
                          "توليد الرمز",
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                    if (codeVisible) ...[
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: generatedCode
                            .map(
                              (digit) => Container(
                                width: 42,
                                height: 42,
                                decoration: BoxDecoration(
                                  color: const Color(0xFF3B8550),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  '$digit',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            )
                            .toList(),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'ينتهي خلال ${_secondsLeft ~/ 60}:${(_secondsLeft % 60).toString().padLeft(2, '0')}',
                        style: const TextStyle(color: Colors.red, fontSize: 13),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'أدخل هذا الرمز على جهازك الجديد لإكمال التسجيل.',
                        style: TextStyle(
                          color: Color(0xFFAECCDD),
                          fontSize: 12,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ],
                ),
              ),

              const SizedBox(height: 40),

              /// أو
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

              /// CARD 2
              GestureDetector(
                onTapDown: (_) => setState(() => isPressed = true),
                onTapUp: (_) => setState(() => isPressed = false),
                onTapCancel: () => setState(() => isPressed = false),

                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 150),
                  padding: const EdgeInsets.all(18),

                  decoration: BoxDecoration(
                    color: isPressed
                        ? const Color(0xFF536A74)
                        : const Color(0xFF536976),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: const [
                      BoxShadow(
                        color: Colors.black45,
                        blurRadius: 8,
                        offset: Offset(0, 5),
                      ),
                    ],
                  ),

                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Icon(
                        Icons.smartphone_outlined,
                        color: Color(0xFF85FC6E),
                        size: 26,
                      ),
                      SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "أدخل الرمز من جهاز آخر",
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            SizedBox(height: 6),
                            Text(
                              "هل لديك رمز تحقق تم إنشاؤه على هذا الجهاز.",
                              style: TextStyle(
                                color: Color(0xFFAECCDD),
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
