import 'package:flutter/material.dart';
import 'profile_page.dart';
import 'support_options_page.dart';
import 'AddTrustDevice.dart';
import 'linked_accounts_page.dart';

// ══════════════════════════════════════════════
//                الواجهة الرابعه
// ══════════════════════════════════════════════

class TrustedDevicesPage extends StatelessWidget {
  const TrustedDevicesPage({super.key});
  //
  @override
  Widget build(BuildContext context) {
    const bg = Color(0xFF2E3F47);
    const divider = Color(0xFF3A4D55);
    const accent = Color(0xFF22C55E);

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: bg,

        drawer: Drawer(
          width: 320,
          backgroundColor: const Color(0xFF22323A),
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.horizontal(right: Radius.circular(28)),
          ),
          child: SafeArea(
            child: Column(
              children: [
                // Header
                Container(
                  height: 56,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: const BoxDecoration(
                    border: Border(
                      bottom: BorderSide(color: Color(0xFF6B7D2E), width: 1),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Padding(
                        padding: EdgeInsets.only(left: 10),
                        child: Text(
                          "القائمة",
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,

                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const Spacer(),
                      IconButton(
                        onPressed: () => Navigator.pop(context),
                        icon: const Icon(
                          Icons.close,
                          color: Color(0xFF00A86B),
                          size: 18,
                        ),
                        splashRadius: 18,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 14),

                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  child: Column(
                    children: [
                      _DrawerCardItem(
                        title: "الملف الشخصي",
                        icon: Icons.person_outline,
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const ProfilePage(),
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 12),
                      _DrawerCardItem(
                        title: "إضافة جهاز موثوق",
                        icon: Icons.verified_outlined,
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const GenerateCodeScreen(),
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 12),
                      _DrawerCardItem(
                        title: "الحسابات المرتبطة",
                        icon: Icons.people_outline,
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const LinkedAccountsPage(),
                            ),
                          );
                        },
                      ),

                      const SizedBox(height: 12),
                      _DrawerCardItem(
                        title: "المساعدة والدعم",
                        icon: Icons.support_agent_outlined,
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const SupportOptionsPage(),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),

                const Spacer(),

                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 16),
                  child: SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF8B1D1D),
                        foregroundColor: const Color.fromARGB(
                          255,
                          228,
                          194,
                          194,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      onPressed: () => Navigator.pop(context),
                      child: const Text(
                        "تسجيل الخروج",
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: SafeArea(
            bottom: false,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              decoration: const BoxDecoration(
                border: Border(
                  bottom: BorderSide(color: Color(0xFF6B7D2E), width: 1),
                ),
              ),
              child: Row(
                children: [
                  Builder(
                    builder: (context) => IconButton(
                      onPressed: () => Scaffold.of(context).openDrawer(),
                      icon: const Icon(Icons.menu),
                      color: accent,
                      splashRadius: 22,
                    ),
                  ),
                  const Expanded(
                    child: Center(
                      child: Text(
                        "الأجهزة الموثوقة",
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 48),
                ],
              ),
            ),
          ),
        ),
        body: SafeArea(
          child: Column(
            children: [
              Container(height: 2, color: divider),
              const SizedBox(height: 14),

              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: _DeviceCard(
                  deviceName: "iPhone 14 Pro",
                  deviceKey: "A93F••••92E",
                  lastSeen: "آخر ظهور 30 نوفمبر 7:30",
                  onDelete: () {},
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DrawerCardItem extends StatelessWidget {
  final String title;
  final IconData icon;
  final VoidCallback onTap;

  const _DrawerCardItem({
    required this.title,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: Container(
        height: 64,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: const Color(0xFF2A4047),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xff23AB49)),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                title,
                textAlign: TextAlign.right,
                style: const TextStyle(
                  color: Color.fromARGB(255, 255, 255, 255),
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DeviceCard extends StatelessWidget {
  final String deviceName;
  final String deviceKey;
  final String lastSeen;
  final VoidCallback onDelete;

  const _DeviceCard({
    required this.deviceName,
    required this.deviceKey,
    required this.lastSeen,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    const cardBg = Color(0xFF344A52);
    const accent = Color(0xFF22C55E);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(
                Icons.phone_iphone,
                color: Colors.white.withOpacity(0.85),
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  deviceName,
                  textAlign: TextAlign.right,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            "Device Key: $deviceKey",
            textAlign: TextAlign.right,
            style: TextStyle(
              color: Colors.white.withOpacity(0.70),
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerRight,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
              decoration: BoxDecoration(
                color: accent.withOpacity(0.18),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: accent.withOpacity(0.35)),
              ),
              child: Text(
                lastSeen,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerLeft,
            child: GestureDetector(
              onTap: onDelete,
              child: const Text(
                "حذف",
                style: TextStyle(
                  color: Color(0xFFE11D48),
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
