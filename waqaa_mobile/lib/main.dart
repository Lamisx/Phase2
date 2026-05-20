import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'services/security_service.dart';

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
              print("BUTTON CLICKED");

              try {
                final publicKey = await SecurityService.generateKeyPair();

                print("PUBLIC KEY:");
                print(publicKey);
              } catch (e) {
                print("ERROR:");
                print(e);
              }
            },

            child: const Text("Generate KeyPair"),
          ),
        ),
      ),
    );
  }
}
