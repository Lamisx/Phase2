import 'package:flutter/material.dart';
import 'nafath_screen.dart';
import 'id_screen.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController idController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  bool hidePassword = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF314048),
      body: Stack(
        children: [
          Positioned(
            top: 0,
            left: 0,
            child: CustomPaint(
              size: Size(MediaQuery.of(context).size.width, 280),
              painter: TopWavePainter(),
            ),
          ),
          SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 30.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const SizedBox(height: 140),

                  Center(
                    child: Image.asset(
                      'assets/images/WaqaaRBg.png',
                      width: 160,
                      errorBuilder: (context, error, stackTrace) => const Icon(
                        Icons.security,
                        size: 80,
                        color: Colors.white,
                      ),
                    ),
                  ),

                  const SizedBox(height: 60),

                  _buildLabel("رقم الهوية"),
                  const SizedBox(height: 10),
                  _buildTextField(
                    controller: idController,
                    hintText: "ادخل رقم الهوية",
                    keyboardType: TextInputType.number,
                  ),

                  const SizedBox(height: 20),

                  _buildLabel("كلمة المرور"),
                  const SizedBox(height: 10),
                  _buildTextField(
                    controller: passwordController,
                    hintText: "أدخل كلمة المرور",
                    isPassword: true,
                    obscureText: hidePassword,
                    togglePassword: () {
                      setState(() {
                        hidePassword = !hidePassword;
                      });
                    },
                  ),

                  TextButton(
                    onPressed: () {},
                    child: const Text(
                      'نسيت كلمة المرور؟',
                      style: TextStyle(
                        color: Color.fromARGB(255, 174, 204, 221),
                        fontSize: 14,
                      ),
                    ),
                  ),

                  const SizedBox(height: 40),

                  SizedBox(
                    width: double.infinity,
                    height: 55,
                    child: ElevatedButton(
                      onPressed: () {
                        if (idController.text.isEmpty ||
                            passwordController.text.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text(
                                "الرجاء إدخال رقم الهوية وكلمة المرور",
                              ),
                            ),
                          );
                          return;
                        }
                        print("Pressed");

                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (context) => NafathScreen(),
                          ),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF3B8550),
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(15),
                        ),
                      ),
                      child: const Text(
                        'تسجيل الدخول',
                        style: TextStyle(
                          fontSize: 18,
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 25),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      GestureDetector(
                        onTap: () {
                          final formKey = GlobalKey<FormState>();
                          final idCtrl = TextEditingController();
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => IdScreen(
                                formKey: GlobalKey<FormState>(),
                                idController: TextEditingController(),
                                onNext: () {},
                              ),
                            ),
                          );
                        },
                        child: const Text(
                          'إنشاء حساب جديد',
                          style: TextStyle(
                            color: Color(0xFF8DB3B3),
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ),
                      const Text(
                        ' ليس لديك حساب؟ ',
                        style: TextStyle(color: Colors.white),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        color: Colors.white,
        fontSize: 16,
        fontWeight: FontWeight.w500,
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String hintText,
    bool isPassword = false,
    bool obscureText = false,
    VoidCallback? togglePassword,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.06),
        borderRadius: BorderRadius.circular(12),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        textAlign: TextAlign.right,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: const TextStyle(color: Colors.white30, fontSize: 13),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 15,
            vertical: 12,
          ),
          border: InputBorder.none,
          suffixIcon: isPassword
              ? IconButton(
                  icon: Icon(
                    obscureText
                        ? Icons.visibility_off_outlined
                        : Icons.visibility_outlined,
                    color: Colors.white30,
                  ),
                  onPressed: togglePassword,
                )
              : null,
        ),
      ),
    );
  }
}

class TopWavePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    Paint paint = Paint()..style = PaintingStyle.fill;

    paint.color = const Color(0xFF27AE60).withOpacity(0.2);
    Path path1 = Path();
    path1.moveTo(0, 0);
    path1.lineTo(0, size.height * 0.9);
    path1.cubicTo(
      size.width * 0.3,
      size.height * 1.1,
      size.width * 0.7,
      size.height * 0.5,
      size.width * 0.9,
      3,
    );
    path1.close();
    canvas.drawPath(path1, paint);

    paint.color = const Color(0xFF27AE60);
    Path path2 = Path();
    path2.moveTo(0, 0);
    path2.lineTo(0, size.height * 0.7);
    path2.cubicTo(
      size.width * 0.2,
      size.height * 0.85,
      size.width * 0.4,
      size.height * 0.4,
      size.width * 0.7,
      0,
    );
    path2.close();
    canvas.drawPath(path2, paint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
