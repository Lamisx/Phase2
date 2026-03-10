import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(WaqaaApp());
}

class WaqaaApp extends StatelessWidget {
  const WaqaaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Waqaa',
      home: LoginScreen(),
    );
  }
}
