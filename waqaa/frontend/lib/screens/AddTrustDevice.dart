import 'package:flutter/material.dart';

// ══════════════════════════════════════════════
//  الواجهة الخامسه — رقم الجوال والبريد
// ══════════════════════════════════════════════

class GenerateCodeScreen extends StatefulWidget {
  const GenerateCodeScreen({super.key});

  @override
  State<GenerateCodeScreen> createState() => _GenerateCodeScreenState();
}

class _GenerateCodeScreenState extends State<GenerateCodeScreen> {
  bool isPressed = false;

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
                        onPressed: () {},
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
