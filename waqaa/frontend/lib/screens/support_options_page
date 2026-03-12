import 'package:flutter/material.dart';

// ══════════════════════════════════════════════
//                   الدعم
// ══════════════════════════════════════════════

class SupportOptionsPage extends StatefulWidget {
  const SupportOptionsPage({super.key});

  @override
  State<SupportOptionsPage> createState() => _SupportOptionsPageState();

  static const Color bg = Color(0xFF31444D);
  static const Color headerBg = Color(0xFF31444D);
  static const Color lineColor = Color(0xFF7A8E2B);
  static const Color cardBg = Color(0xFF3C505A);
  static const Color textMain = Colors.white;
  static const Color textSoft = Color(0xFFD7E1E7);
  static const Color iconGreen = Color(0xFF63C46B);
  static const Color iconSoft = Color(0xFFBFC9CF);
}

class _SupportOptionsPageState extends State<SupportOptionsPage> {
  bool _chatOpen = false;
  final TextEditingController _controller = TextEditingController();
  final List<_ChatMessage> _messages = [
    _ChatMessage(text: 'مرحبًا! كيف أقدر أساعدك؟', isUser: false),
  ];

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(_ChatMessage(text: text, isUser: true));
      _messages.add(_ChatMessage(text: 'تم استلام رسالتك', isUser: false));
      _controller.clear();
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: SupportOptionsPage.bg,
        body: SafeArea(
          child: Column(
            children: [
              Container(
                height: 58,
                color: SupportOptionsPage.headerBg,
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Row(
                  children: [
                    const SizedBox(width: 40),
                    const Expanded(
                      child: Center(
                        child: Text(
                          'المساعدة والدعم',
                          style: TextStyle(
                            color: Color.fromARGB(255, 159, 178, 186),
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(
                        Icons.arrow_forward_ios,
                        color: Color.fromARGB(255, 25, 92, 52),
                        size: 24,
                      ),
                      splashRadius: 20,
                    ),
                  ],
                ),
              ),
              Container(height: 1.2, color: SupportOptionsPage.lineColor),
              Expanded(
                child: Stack(
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 26, 18, 18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Center(
                            child: Text(
                              'كيف نقدر نخدمك ؟',
                              style: TextStyle(
                                color: SupportOptionsPage.textSoft,
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                          const SizedBox(height: 22),
                          _SupportTile(
                            title: 'الأسئلة الشائعة',
                            icon: Icons.keyboard_arrow_down,
                            iconColor: SupportOptionsPage.iconSoft,
                            onTap: () {},
                          ),
                          const SizedBox(height: 18),
                          _SupportTile(
                            title: 'الشروط والأحكام',
                            icon: Icons.keyboard_arrow_down,
                            iconColor: SupportOptionsPage.iconSoft,
                            onTap: () {},
                          ),
                          const SizedBox(height: 18),
                          _SupportTile(
                            title: 'اتصل بنا',
                            icon: null,
                            iconColor: SupportOptionsPage.iconSoft,
                            onTap: () {},
                          ),
                        ],
                      ),
                    ),

                    if (_chatOpen)
                      Positioned(
                        left: 18,
                        right: 18,
                        bottom: 95,
                        child: Container(
                          height: 320,
                          decoration: BoxDecoration(
                            color: const Color(0xFF22323A),
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: const [
                              BoxShadow(
                                color: Color(0x44000000),
                                blurRadius: 10,
                                offset: Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Column(
                            children: [
                              Container(
                                height: 52,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                ),
                                decoration: const BoxDecoration(
                                  color: Color(0xFF1E2C33),
                                  borderRadius: BorderRadius.vertical(
                                    top: Radius.circular(16),
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    IconButton(
                                      onPressed: () {
                                        setState(() {
                                          _chatOpen = false;
                                        });
                                      },
                                      icon: const Icon(
                                        Icons.close,
                                        color: Colors.white70,
                                        size: 20,
                                      ),
                                      splashRadius: 18,
                                    ),
                                    const Expanded(
                                      child: Center(
                                        child: Text(
                                          'المساعد الذكي',
                                          style: TextStyle(
                                            color: Colors.white,
                                            fontSize: 16,
                                            fontWeight: FontWeight.w700,
                                          ),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 40),
                                  ],
                                ),
                              ),
                              Expanded(
                                child: ListView.builder(
                                  padding: const EdgeInsets.all(12),
                                  itemCount: _messages.length,
                                  itemBuilder: (context, index) {
                                    final msg = _messages[index];
                                    return Align(
                                      alignment: msg.isUser
                                          ? Alignment.centerRight
                                          : Alignment.centerLeft,
                                      child: Container(
                                        margin: const EdgeInsets.only(
                                          bottom: 10,
                                        ),
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 12,
                                          vertical: 10,
                                        ),
                                        constraints: const BoxConstraints(
                                          maxWidth: 220,
                                        ),
                                        decoration: BoxDecoration(
                                          color: msg.isUser
                                              ? SupportOptionsPage.iconGreen
                                                    .withOpacity(0.15)
                                              : Colors.white.withOpacity(0.08),
                                          borderRadius: BorderRadius.circular(
                                            12,
                                          ),
                                        ),
                                        child: Text(
                                          msg.text,
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 14,
                                          ),
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.fromLTRB(
                                  10,
                                  8,
                                  10,
                                  10,
                                ),
                                child: Row(
                                  children: [
                                    IconButton(
                                      onPressed: _sendMessage,
                                      icon: const Icon(
                                        Icons.send,
                                        color: SupportOptionsPage.iconGreen,
                                      ),
                                    ),
                                    Expanded(
                                      child: Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 12,
                                        ),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF31444D),
                                          borderRadius: BorderRadius.circular(
                                            12,
                                          ),
                                        ),
                                        child: TextField(
                                          controller: _controller,
                                          style: const TextStyle(
                                            color: Colors.white,
                                          ),
                                          decoration: const InputDecoration(
                                            border: InputBorder.none,
                                            hintText: 'اكتب رسالتك...',
                                            hintStyle: TextStyle(
                                              color: Colors.white54,
                                            ),
                                          ),
                                          onSubmitted: (_) => _sendMessage(),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),

                    Positioned(
                      left: 18,
                      bottom: 26,
                      child: GestureDetector(
                        onTap: () {
                          setState(() {
                            _chatOpen = !_chatOpen;
                          });
                        },
                        child: Container(
                          width: 54,
                          height: 54,
                          decoration: BoxDecoration(
                            color: SupportOptionsPage.iconGreen.withOpacity(
                              0.12,
                            ),
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: const Icon(
                            Icons.chat_bubble_outline_rounded,
                            color: SupportOptionsPage.iconGreen,
                            size: 28,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SupportTile extends StatelessWidget {
  const _SupportTile({
    required this.title,
    required this.iconColor,
    required this.onTap,
    this.icon,
  });

  final String title;
  final IconData? icon;
  final Color iconColor;
  final VoidCallback onTap;

  static const Color cardBg = Color(0xFF3C505A);
  static const Color textSoft = Color(0xFFD7E1E7);

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(6),
        onTap: onTap,
        child: Container(
          height: 54,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          decoration: BoxDecoration(
            color: cardBg,
            borderRadius: BorderRadius.circular(4),
            boxShadow: const [
              BoxShadow(
                color: Color(0x33000000),
                offset: Offset(0, 3),
                blurRadius: 4,
              ),
            ],
          ),
          child: Row(
            children: [
              if (icon != null) ...[
                Icon(icon, color: iconColor, size: 20),
              ] else ...[
                const SizedBox(width: 20),
              ],
              const Spacer(),
              Text(
                title,
                style: const TextStyle(
                  color: textSoft,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ChatMessage {
  final String text;
  final bool isUser;

  _ChatMessage({required this.text, required this.isUser});
}
