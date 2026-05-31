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

      if (!mounted) return;

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
                      child: Icon(Icons.chevron_left, color: Color(0xFF22C55E)),
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
                const SizedBox(height: 16),

                // ===== Name =====
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFF243841),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: Colors.green.withOpacity(0.15)),
                    ),
                    child: Column(
                      children: [
                        Container(
                          width: 90,
                          height: 90,
                          decoration: BoxDecoration(
                            color: accent.withOpacity(.15),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.person,
                            color: Color(0xFF22C55E),
                            size: 45,
                          ),
                        ),

                        const SizedBox(height: 16),

                        Text(
                          displayName,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),

                        const SizedBox(height: 24),

                        _InfoTile(
                          icon: Icons.person_outline,
                          title: "اسم المستخدم",
                          value: username,
                        ),

                        const SizedBox(height: 12),

                        _InfoTile(
                          icon: Icons.email_outlined,
                          title: "البريد الإلكتروني",
                          value: email,
                        ),

                        const SizedBox(height: 12),

                        _InfoTile(
                          icon: Icons.phone_outlined,
                          title: "رقم الجوال",
                          value: phone,
                        ),
                      ],
                    ),
                  ),
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

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;

  const _InfoTile({
    required this.icon,
    required this.title,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF2E444D),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF22C55E)),

          const SizedBox(width: 12),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  title,
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
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
