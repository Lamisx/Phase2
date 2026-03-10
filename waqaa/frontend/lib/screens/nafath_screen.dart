import 'dart:math';
import 'package:flutter/material.dart';
import 'registration_flow.dart';

class NafathScreen extends StatefulWidget {
  const NafathScreen({super.key});

  @override
  _NafathScreenState createState() => _NafathScreenState();
}

class _NafathScreenState extends State<NafathScreen> {
  int requestNumber = 0;

  @override
  void initState() {
    super.initState();
    generateRequestNumber();

    Future.delayed(const Duration(seconds: 4), () {
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => RegistrationFlow()),
        );
      }
    });
  }

  void generateRequestNumber() {
    final random = Random();
    setState(() {
      requestNumber = random.nextInt(90) + 10;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF314048),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 30),
            child: Column(
              children: [
                const SizedBox(height: 50),

                Image.asset('assets/images/WaqaaRBg.png', width: 110),

                const SizedBox(height: 40),

                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Column(
                    children: [
                      Image.asset(
                        'assets/images/nafath.png',
                        width: 100,
                        errorBuilder: (context, error, stackTrace) =>
                            const Icon(
                              Icons.fingerprint,
                              size: 50,
                              color: Colors.green,
                            ),
                      ),

                      const SizedBox(height: 20),

                      const Text(
                        ":الرجاء فتح تطبيق نفاذ وتأكيد الطلب باختيار الرقم التالي:",
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          height: 1.5,
                        ),
                      ),

                      const SizedBox(height: 25),

                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 40,
                          vertical: 15,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFF438A52).withOpacity(0.15),
                          borderRadius: BorderRadius.circular(15),
                          border: Border.all(
                            color: const Color(0xFF438A52),
                            width: 1.5,
                          ),
                        ),
                        child: Text(
                          "$requestNumber",
                          style: const TextStyle(
                            fontSize: 65,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 4,
                          ),
                        ),
                      ),

                      const SizedBox(height: 30),

                      Container(
                        padding: const EdgeInsets.symmetric(
                          vertical: 10,
                          horizontal: 15,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFAECCDD).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.security_rounded,
                              color: Color(0xFFAECCDD),
                              size: 18,
                            ),
                            SizedBox(width: 10),
                            Text(
                              "تنبيه: لا تشارك هذا الرقم مع أي شخص",
                              style: TextStyle(
                                color: Color(0xFFAECCDD),
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 60),

                SizedBox(
                  width: double.infinity,
                  height: 55,
                  child: ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF438A52),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 0,
                    ),
                    child: const Text(
                      "إلغاء الطلب",
                      style: TextStyle(
                        fontSize: 18,
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 25),

                const Text(
                  "في حال لم يصلك التنبيه، تأكد من اتصالك بالإنترنت",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white38, fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
