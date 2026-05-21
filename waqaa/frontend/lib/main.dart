import 'package:flutter/material.dart';
import 'services/auth_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text("Waqaa")),

        body: Center(
          child: ElevatedButton(
            onPressed: () async {
              await AuthService.login(
                username: "rawan2",

                password: "12345678Aa",
              );
            },

            child: const Text("Generate KeyPair"),
          ),
        ),
      ),
    );
  }
}
