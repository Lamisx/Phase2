import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:dio/dio.dart';
// ══════════════════════════════════════════════
//               واجهة البروفايل
// ══════════════════════════════════════════════

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  String displayName = "Loading...";
  String username = "";
  String email = "";
  String phone = "";

  @override
  void initState() {
    super.initState();
    loadProfile();
  }

  Future<void> loadProfile() async {
    try {
      Response response = await ApiService.getMe();

      setState(() {
        displayName = response.data["display_name"] ?? "";
        username = response.data["username"] ?? "";
        email = response.data["email"] ?? "";
        phone = response.data["phone"] ?? "";
      });
    } catch (e) {
      debugPrint("Profile Error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    const bg = Color(0xFF1E2E36);
    const accent = Color(0xFF22C55E);
    const cardBg = Color(0xFF2A3C44);
    const divider = Color(0xFF3A4E57);

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: bg,

        // AppBar
        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: SafeArea(
            bottom: false,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: const BoxDecoration(
                color: Color(0xFF1E2E36),
                border: Border(
                  bottom: BorderSide(color: Color(0xFF3A4E57), width: 1.5),
                ),
              ),
              child: Row(
                children: [
                  // ✅ السهم في اليمين (مع منع الانعكاس)
                  IconButton(
                    icon: const Directionality(
                      textDirection: TextDirection.ltr,
                      child: Icon(
                        Icons.arrow_forward,
                        color: Color(0xFF22C55E),
                      ),
                    ),
                    onPressed: () {
                      Navigator.pop(context);
                    },
                  ),

                  const Spacer(),

                  const Text(
                    'الملف الشخصي',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),

                  const Spacer(),
                ],
              ),
            ),
          ),
        ),

        body: SafeArea(
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // ===== Banner + Avatar =====
                Stack(
                  clipBehavior: Clip.none,
                  alignment: Alignment.center,
                  children: [
                    // Banner
                    Container(
                      height: 90,
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Color(0xFF2A4A38), Color(0xFF1E3A2E)],
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight,
                        ),
                      ),
                    ),
                    // Avatar
                    Positioned(
                      bottom: -36,
                      child: Container(
                        width: 72,
                        height: 72,
                        decoration: BoxDecoration(
                          color: const Color(0xFF3A7A52),
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: const Color(0xFF1E2E36),
                            width: 3,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 48),

                // ===== Name =====
                // ===== Name =====
                Column(
                  children: [
                    Text(
                      displayName,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 8),

                    Text(
                      username,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),

                    const SizedBox(height: 8),

                    Text(
                      email,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),

                    const SizedBox(height: 8),

                    Text(
                      phone,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 28),

                // ===== Section: الحساب =====
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Text(
                        'الحساب',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 8),
                      _SettingsCard(
                        children: [
                          _SettingsRow(
                            title: 'تغيير كلمة المرور',
                            accent: accent,
                            onTap: () {},
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 22),

                // ===== Section: عام =====
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Text(
                        'عام',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 8),
                      _SettingsCard(
                        children: [
                          _SettingsRow(
                            title: 'الخصوصية',
                            accent: accent,
                            onTap: () {},
                          ),
                          Divider(
                            height: 1,
                            color: Colors.white.withOpacity(0.07),
                            indent: 16,
                            endIndent: 16,
                          ),
                          _SettingsRow(
                            title: 'تاريخ الأجهزة',
                            accent: accent,
                            onTap: () {},
                          ),
                        ],
                      ),
                    ],
                  ),
                ),

                // زخرفة أسفل اليمين
                Align(
                  alignment: Alignment.bottomRight,
                  child: Container(
                    margin: const EdgeInsets.only(top: 40),
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      color: accent.withOpacity(0.15),
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(80),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ============================================================
// Settings Card wrapper
// ============================================================

class _SettingsCard extends StatelessWidget {
  final List<Widget> children;
  const _SettingsCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF2A3C44),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Column(children: children),
    );
  }
}

// ============================================================
// Settings Row
// ============================================================

class _SettingsRow extends StatelessWidget {
  final String title;
  final Color accent;
  final VoidCallback onTap;

  const _SettingsRow({
    required this.title,
    required this.accent,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Icon(Icons.arrow_back, color: accent, size: 18),
            Text(
              title,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 15,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
