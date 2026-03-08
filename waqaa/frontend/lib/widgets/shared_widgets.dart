import 'package:flutter/material.dart';

// ══════════════════════════════════════════════
//  مكوّنات مشتركة بين جميع الواجهات
// ══════════════════════════════════════════════

Widget buildWaveHeader(BuildContext context) {
  return SizedBox(
    height: 180,
    width: double.infinity,
    child: Stack(
      children: [
        CustomPaint(
          size: Size(MediaQuery.of(context).size.width, 180),
          painter: WavePainter(
              color: const Color(0xFF2E8B57).withOpacity(0.4), offset: 15),
        ),
        CustomPaint(
          size: Size(MediaQuery.of(context).size.width, 180),
          painter: WavePainter(color: const Color(0xFF2E8B57), offset: 0),
        ),
      ],
    ),
  );
}

Widget buildBackButton(VoidCallback onPressed) {
  return Align(
    alignment: Alignment.topRight,
    child: GestureDetector(
      onTap: onPressed,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.15),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 18),
      ),
    ),
  );
}

Widget fieldLabel(String text) => Text(
      text,
      textDirection: TextDirection.rtl,
      style: const TextStyle(color: Colors.white, fontSize: 16),
    );

Widget buildButton(String text, VoidCallback onPressed) {
  return SizedBox(
    width: double.infinity,
    height: 56,
    child: ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF2E8B57),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        elevation: 0,
      ),
      onPressed: onPressed,
      child: Text(text,
          style: const TextStyle(
              fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
    ),
  );
}

Widget buildFooter() {
  return const Center(
    child: Text(
      'بتسجيل الدخول، أنت توافق على الشروط والأحكام',
      textDirection: TextDirection.rtl,
      style: TextStyle(color: Colors.white38, fontSize: 12),
    ),
  );
}

InputDecoration inputDecoration(String hint) {
  return InputDecoration(
    hintText: hint,
    hintTextDirection: TextDirection.rtl,
    hintStyle: const TextStyle(color: Colors.white24, fontSize: 14),
    filled: true,
    fillColor: const Color(0xFF2C353F).withOpacity(0.7),
    contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 20),
    border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
    enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
    focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Color(0xFF2E8B57), width: 1.5)),
    errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Colors.redAccent, width: 1)),
    focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: Colors.redAccent, width: 1.5)),
    errorStyle: const TextStyle(height: 0.9, fontSize: 11),
  );
}

// ══════════════════════════════════════════════
//  رسّام التموجات
// ══════════════════════════════════════════════
class WavePainter extends CustomPainter {
  final Color color;
  final double offset;
  WavePainter({required this.color, required this.offset});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    final path = Path();
    path.moveTo(0, 0);
    path.lineTo(size.width, 0);
    path.lineTo(size.width, size.height * 0.55 + offset);
    path.quadraticBezierTo(
      size.width * 0.75,
      size.height * 0.85 + offset,
      size.width * 0.5,
      size.height * 0.65 + offset,
    );
    path.quadraticBezierTo(
      size.width * 0.25,
      size.height * 0.45 + offset,
      0,
      size.height * 0.55 + offset,
    );
    path.close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
