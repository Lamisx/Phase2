import 'package:flutter/material.dart';

// ══════════════════════════════════════════════
//            الحسابات المرتبطه
// ══════════════════════════════════════════════

class LinkedAccountsPage extends StatelessWidget {
  const LinkedAccountsPage({super.key});

  Widget build(BuildContext context) {
    const bg = Color(0xFF2B3C44);
    const divider = Color(0xFF3A4E57);
    const accent = Color(0xFF22C55E);
    const cardBg = Color(0xFF32474F);

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: bg,

        appBar: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: SafeArea(
            bottom: false,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: const BoxDecoration(
                color: Color(0xFF2B3C44),
                border: Border(
                  bottom: BorderSide(color: Color(0xFF3A4E57), width: 1.5),
                ),
              ),
              child: Row(
                children: [
                  // ✅ سهم مطابق لباقي الشاشات (يمين + أخضر + اتجاه صحيح)
                  IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Directionality(
                      textDirection: TextDirection.ltr,
                      child: Icon(
                        Icons.arrow_forward,
                        color: Color(0xFF22C55E),
                      ),
                    ),
                    splashRadius: 20,
                  ),

                  const Spacer(),

                  const Text(
                    'الحسابات المرتبطة',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),

                  const Spacer(),

                  const SizedBox(width: 44), // توازن التصميم
                ],
              ),
            ),
          ),
        ),

        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(14),
            children: const [
              _AccountCard(
                name: 'الاسم الثلاثي',
                username: 'username: username',
              ),
              SizedBox(height: 12),
              _AccountCard(
                name: 'الاسم الثلاثي',
                username: 'username: username',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ============================================================
// Account Card
// ============================================================

class _AccountCard extends StatelessWidget {
  final String name;
  final String username;

  const _AccountCard({required this.name, required this.username});

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFF22C55E);
    const cardBg = Color(0xFF32474F);

    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // أيقونة + اسم
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text(
                name,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.person, color: accent, size: 18),
            ],
          ),

          const SizedBox(height: 5),

          // username
          Text(
            username,
            textAlign: TextAlign.right,
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontSize: 11,
            ),
          ),

          const SizedBox(height: 10),

          // نشط + حذف
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // نشط
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: accent.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: accent.withOpacity(0.28)),
                ),
                child: const Text(
                  'نشط',
                  style: TextStyle(
                    color: accent,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),

              // حذف
              GestureDetector(
                onTap: () {},
                child: const Text(
                  'حذف',
                  style: TextStyle(
                    color: Color(0xFFE11D48),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
