import 'package:flutter/material.dart';

import '../services/api_service.dart';

// ══════════════════════════════════════════════
//            الحسابات المرتبطة
//
//  تعرض التفويضات اللي استلمها المستخدم الحالي
//  (الناس اللي فوّضوه — من جانب B)
//
//  زر "حذف" → يلغي التفويض من جانب B
// ══════════════════════════════════════════════

class LinkedAccountsPage extends StatefulWidget {
  const LinkedAccountsPage({super.key});

  @override
  State<LinkedAccountsPage> createState() => _LinkedAccountsPageState();
}

class _LinkedAccountsPageState extends State<LinkedAccountsPage> {
  late Future<List<Map<String, dynamic>>> _delegationsFuture;

  @override
  void initState() {
    super.initState();
    _delegationsFuture = ApiService.getReceivedDelegations();
  }

  void _refresh() {
    setState(() {
      _delegationsFuture = ApiService.getReceivedDelegations();
    });
  }

  Future<void> _revokeDelegation({
    required String delegationId,
    required String ownerName,
  }) async {
    try {
      await ApiService.revokeMyDelegation(delegationId: delegationId);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('تم إلغاء التفويض عن $ownerName')));
      _refresh();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('فشل الإلغاء: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    const bg = Color(0xFF2B3C44);

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
                  const SizedBox(width: 44),
                ],
              ),
            ),
          ),
        ),

        body: SafeArea(
          child: FutureBuilder<List<Map<String, dynamic>>>(
            future: _delegationsFuture,
            builder: (context, snapshot) {
              // حالة التحميل
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(
                  child: CircularProgressIndicator(color: Color(0xFF22C55E)),
                );
              }

              // حالة الخطأ
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
                        'تعذّر تحميل الحسابات',
                        style: TextStyle(color: Colors.white),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _refresh,
                        child: const Text('إعادة محاولة'),
                      ),
                    ],
                  ),
                );
              }

              final delegations = (snapshot.data ?? [])
                  .where((d) => d['status'] == 'active')
                  .toList();

              // قائمة فاضية
              if (delegations.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Icon(
                        Icons.people_outline,
                        color: Color(0xFF22C55E),
                        size: 48,
                      ),
                      SizedBox(height: 16),
                      Text(
                        'لا توجد حسابات مرتبطة',
                        style: TextStyle(color: Colors.white),
                      ),
                      SizedBox(height: 8),
                      Text(
                        'لم يفوّضك أحد بعد',
                        style: TextStyle(color: Colors.white70, fontSize: 12),
                      ),
                    ],
                  ),
                );
              }

              // قائمة التفويضات
              return RefreshIndicator(
                onRefresh: () async => _refresh(),
                color: const Color(0xFF22C55E),
                child: ListView.builder(
                  padding: const EdgeInsets.all(14),
                  itemCount: delegations.length,
                  itemBuilder: (context, index) {
                    final d = delegations[index];
                    final displayName =
                        d['delegated_display_name']?.toString() ??
                        d['owner_username']?.toString() ??
                        'مستخدم';
                    // ملاحظة: في API الباك، owner_username هو اسم
                    // المستخدم اللي فوّض (A). delegated هو أنا (B).
                    // فنعرض اسم المُفوِّض (A).
                    final ownerName = d['owner_username']?.toString() ?? '—';
                    final delegationId = d['id']?.toString() ?? '';

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _AccountCard(
                        // الاسم المعروض = اسم صاحب الحساب (المُفوِّض A)
                        name: ownerName,
                        username: 'username: $ownerName',
                        onDelete: () => _revokeDelegation(
                          delegationId: delegationId,
                          ownerName: ownerName,
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

// ============================================================
// Account Card  (نفس التصميم الأصلي + onDelete callback)
// ============================================================

class _AccountCard extends StatefulWidget {
  final String name;
  final String username;
  final VoidCallback onDelete;

  const _AccountCard({
    required this.name,
    required this.username,
    required this.onDelete,
  });

  @override
  State<_AccountCard> createState() => _AccountCardState();
}

class _AccountCardState extends State<_AccountCard> {
  void _confirmDelete() {
    showDialog(
      context: context,
      builder: (ctx) => Directionality(
        textDirection: TextDirection.rtl,
        child: AlertDialog(
          backgroundColor: const Color(0xFF32474F),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          title: const Text(
            'تأكيد الحذف',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          content: Text(
            'هل أنت متأكد من إلغاء تفويضك عن "${widget.name}"؟',
            style: const TextStyle(color: Colors.white70, fontSize: 14),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
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
                Navigator.pop(ctx);
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
                widget.name,
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
            widget.username,
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

              GestureDetector(
                onTap: _confirmDelete,
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
