import 'package:flutter/material.dart';
import 'profile_page.dart';
import 'support_options_page.dart';
import 'AddTrustDevice.dart';
import 'linked_accounts_page.dart';
import 'login_screen.dart';
import '../services/device_service.dart';

class TrustedDevicesPage extends StatefulWidget {
  const TrustedDevicesPage({super.key});

  @override
  State<TrustedDevicesPage> createState() => _TrustedDevicesPageState();
}

class _TrustedDevicesPageState extends State<TrustedDevicesPage> {
  late Future<List<Map<String, dynamic>>> _devicesFuture;

  @override
  void initState() {
    super.initState();
    _devicesFuture = DeviceService.listDevices();
  }

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
                      onPressed: () {
                        Navigator.pushAndRemoveUntil(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const LoginScreen(),
                          ),
                          (route) => false,
                        );
                      },
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
                      color: const Color(0xFF22C55E),
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

        // =====================================================================
        // BODY - NOW FETCHES AND DISPLAYS REAL DEVICES
        // =====================================================================
        body: SafeArea(
          child: FutureBuilder<List<Map<String, dynamic>>>(
            future: _devicesFuture,
            builder: (context, snapshot) {
              // LOADING STATE
              if (snapshot.connectionState == ConnectionState.waiting) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      CircularProgressIndicator(color: Color(0xFF22C55E)),
                      SizedBox(height: 16),
                      Text(
                        "جاري تحميل الأجهزة...",
                        style: TextStyle(color: Colors.white),
                      ),
                    ],
                  ),
                );
              }

              // ERROR STATE
              if (snapshot.hasError) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.error_outline,
                        color: Color(0xFFE11D48),
                        size: 48,
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        "حدث خطأ في تحميل الأجهزة",
                        style: TextStyle(color: Colors.white),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {
                          setState(() {
                            _devicesFuture = DeviceService.listDevices();
                          });
                        },
                        child: const Text("إعادة محاولة"),
                      ),
                    ],
                  ),
                );
              }

              // NO DATA STATE
              final devices = snapshot.data ?? [];
              if (devices.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(
                        Icons.devices_other,
                        color: Color(0xFF22C55E),
                        size: 48,
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        "لا توجد أجهزة موثوقة",
                        style: TextStyle(color: Colors.white),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        "قم بإضافة جهاز موثوق من القائمة",
                        style: TextStyle(color: Colors.white70, fontSize: 12),
                      ),
                    ],
                  ),
                );
              }

              // DEVICES LIST
              return Column(
                children: [
                  Container(height: 2, color: const Color(0xFF3A4D55)),
                  const SizedBox(height: 14),
                  Expanded(
                    child: ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      itemCount: devices.length,
                      itemBuilder: (context, index) {
                        final device = devices[index];
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _DeviceCard(
                            deviceId: device["id"] ?? "unknown",
                            deviceName: device["label"] ?? "Unknown Device",
                            platform: device["platform"] ?? "android",
                            isPrimary: device["is_primary_device"] ?? false,
                            createdAt: device["created_at"] ?? "unknown",
                            onDelete: () {
                              // TODO: Implement delete device
                            },
                          ),
                        );
                      },
                    ),
                  ),
                ],
              );
            },
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

class _DeviceCard extends StatefulWidget {
  final String deviceId;
  final String deviceName;
  final String platform;
  final bool isPrimary;
  final String createdAt;
  final VoidCallback onDelete;

  const _DeviceCard({
    required this.deviceId,
    required this.deviceName,
    required this.platform,
    required this.isPrimary,
    required this.createdAt,
    required this.onDelete,
  });

  @override
  State<_DeviceCard> createState() => _DeviceCardState();
}

class _DeviceCardState extends State<_DeviceCard> {
  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (context) => Directionality(
        textDirection: TextDirection.rtl,
        child: AlertDialog(
          backgroundColor: const Color(0xFF344A52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          title: const Text(
            'تأكيد الحذف',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          content: Text(
            'هل أنت متأكد من حذف الجهاز "${widget.deviceName}"؟',
            style: const TextStyle(color: Colors.white70, fontSize: 14),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text(
                'تراجع',
                style: TextStyle(color: Colors.white70, fontSize: 14),
              ),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE11D48),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onPressed: () {
                Navigator.pop(context);
                widget.onDelete();
              },
              child: const Text(
                'حذف',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const cardBg = Color(0xFF344A52);
    const accent = Color(0xFF22C55E);

    // Get device icon based on platform
    IconData platformIcon = Icons.devices;
    if (widget.platform.toLowerCase() == "ios") {
      platformIcon = Icons.apple;
    } else if (widget.platform.toLowerCase() == "android") {
      platformIcon = Icons.android;
    } else if (widget.platform.toLowerCase() == "web") {
      platformIcon = Icons.language;
    }

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
                platformIcon,
                color: Colors.white.withOpacity(0.85),
                size: 20,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  widget.deviceName,
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
            "Device ID: ${widget.deviceId.substring(0, 8)}...",
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
                color: widget.isPrimary
                    ? accent.withOpacity(0.18)
                    : Colors.grey.withOpacity(0.18),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: widget.isPrimary
                      ? accent.withOpacity(0.35)
                      : Colors.grey.withOpacity(0.35),
                ),
              ),
              child: Text(
                widget.isPrimary ? "الجهاز الأساسي" : "متصل",
                style: TextStyle(
                  color: widget.isPrimary ? accent : Colors.white,
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
              onTap: _confirmDelete,
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
