import 'dart:convert';
import 'dart:math' show min;
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';

void main() => runApp(ChangeNotifierProvider(
  create: (_) => AppState(),
  child: const AnekdotApp(),
));

// ============================================================
// State
// ============================================================
class AppState extends ChangeNotifier {
  String baseUrl = 'http://192.168.0.150:8000';
  bool isListening = false;
  bool isProcessing = false;
  String status = 'Нажмите 🎤 чтобы начать';
  String transcription = '';
  String jokeText = '';
  String jokeCategory = '';
  double speechProb = 0;
  List<String> logs = [];

  void log(String msg) {
    logs.insert(0, '[${DateTime.now().toIso8601String().substring(11, 19)}] $msg');
    if (logs.length > 50) logs.removeLast();
    notifyListeners();
  }

  void setStatus(String s) { status = s; notifyListeners(); }
  void setProcessing(bool v) { isProcessing = v; notifyListeners(); }
  void setListening(bool v) { isListening = v; notifyListeners(); }
  void setTranscription(String t) { transcription = t; notifyListeners(); }
  void setJoke(String text, String cat) { jokeText = text; jokeCategory = cat; notifyListeners(); }
  void clearJoke() { jokeText = ''; jokeCategory = ''; notifyListeners(); }
}

// ============================================================
// App
// ============================================================
class AnekdotApp extends StatelessWidget {
  const AnekdotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Анекдот в Тему',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF121212),
        colorScheme: const ColorScheme.dark(primary: Color(0xFF4CAF50)),
      ),
      home: const MainPage(),
    );
  }
}

// ============================================================
// Main Page with Bottom Navigation
// ============================================================
class MainPage extends StatefulWidget {
  const MainPage({super.key});
  @override State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  int _currentIndex = 0;
  final List<Widget> _pages = const [
    VoicePage(),
    RandomPage(),
    CategoriesPage(),
    SettingsPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.mic), label: 'Голос'),
          NavigationDestination(icon: Icon(Icons.casino), label: 'Случайная'),
          NavigationDestination(icon: Icon(Icons.category), label: 'Категории'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Настройки'),
        ],
      ),
    );
  }
}

// ============================================================
// Voice Page — main use case "2 friends in cafe"
// ============================================================
class VoicePage extends StatelessWidget {
  const VoicePage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  const Text('🎤 Голосовой режим', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white)),
                  const SizedBox(height: 4),
                  const Text('Скажите что-нибудь — я найду шутку!', style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 16),
                  // Status
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: const Color(0xFF1E1E1E), borderRadius: BorderRadius.circular(12)),
                    child: Row(
                      children: [
                        Icon(state.isProcessing ? Icons.sync : state.isListening ? Icons.mic : Icons.mic_none,
                          color: state.isListening ? Colors.red : const Color(0xFF4CAF50)),
                        const SizedBox(width: 8),
                        Expanded(child: Text(state.status, style: const TextStyle(color: Color(0xFF4CAF50), fontSize: 15))),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Transcription
            if (state.transcription.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: const Color(0xFF1A1A2E), borderRadius: BorderRadius.circular(8)),
                  child: Text('"${state.transcription}"', style: const TextStyle(color: Colors.grey, fontStyle: FontStyle.italic)),
                ),
              ),

            // Joke Card
            if (state.jokeText.isNotEmpty)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E1E1E),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFF4CAF50), width: 2),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('😂 ${state.jokeCategory}', style: const TextStyle(color: Color(0xFF4CAF50), fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text(state.jokeText, style: const TextStyle(color: Colors.white, fontSize: 16, height: 1.5)),
                    ],
                  ),
                ),
              ),

            const Spacer(),

            // Logs panel (collapsible)
            if (state.logs.isNotEmpty)
              Expanded(
                child: Container(
                  margin: const EdgeInsets.all(16),
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(8)),
                  child: ListView.builder(
                    itemCount: state.logs.length,
                    itemBuilder: (_, i) => Text(state.logs[i], style: const TextStyle(color: Color(0xFF4CAF50), fontSize: 10, fontFamily: 'monospace')),
                  ),
                ),
              ),

            // Mic Button
            Padding(
              padding: const EdgeInsets.all(32),
              child: FloatingActionButton.large(
                onPressed: () => _toggleMic(context),
                backgroundColor: state.isListening ? Colors.red : const Color(0xFF4CAF50),
                child: Icon(state.isListening ? Icons.stop : Icons.mic, size: 40, color: Colors.white),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _toggleMic(BuildContext context) async {
    final state = context.read<AppState>();
    if (state.isListening || state.isProcessing) {
      state.setListening(false);
      state.setStatus('Остановлено');
      return;
    }

    // Request permission
    final perm = await Permission.microphone.request();
    if (!perm.isGranted) {
      state.setStatus('❌ Нужен микрофон!');
      return;
    }

    state.clearJoke();
    state.setTranscription('');
    state.log('🎤 Starting recording...');

    try {
      final recorder = AudioRecorder();
      await recorder.start(
        const RecordConfig(encoder: AudioEncoder.wav, sampleRate: 16000, numChannels: 1),
        path: '/tmp/anekdot_voice.wav',
      );

      state.setListening(true);
      state.setStatus('🎙️ Слушаю... (скажите что-нибудь)');

      // Record for 5 seconds
      await Future.delayed(const Duration(seconds: 5));
      final audioPath = await recorder.stop();
      state.setListening(false);

      if (audioPath == null) return;

      state.log('📡 Audio recorded: $audioPath');
      state.setProcessing(true);
      state.setStatus('🔄 Отправляю на распознавание...');

      // Read audio file
      final audioBytes = await http.MultipartFile.fromPath('file', audioPath);
      final request = http.MultipartRequest('POST', Uri.parse('${state.baseUrl}/api/voice/stt/file'));
      request.files.add(audioBytes);

      final sttResponse = await request.send().timeout(const Duration(seconds: 30));
      final sttBody = await sttResponse.stream.bytesToString();
      final sttData = jsonDecode(sttBody) as Map<String, dynamic>;

      final text = (sttData['text'] ?? '') as String;
      state.log('📝 Transcribed: "$text"');

      if (text.isEmpty || ['[BLANK_AUDIO]', '[музыка]', '[ Music ]'].contains(text)) {
        state.setStatus('🤷 Речь не распознана. Попробуйте ещё.');
        state.setProcessing(false);
        return;
      }

      state.setTranscription(text);
      state.setStatus('😄 Ищу шутку...');

      // Search for joke
      final jokeResp = await http.post(
        Uri.parse('${state.baseUrl}/api/jokes/context'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'text': text, 'count': 3}),
      ).timeout(const Duration(seconds: 15));

      final jokeData = jsonDecode(jokeResp.body) as Map<String, dynamic>;
      final jokes = jokeData['jokes'] as List? ?? [];

      if (jokes.isNotEmpty) {
        final joke = jokes.first as Map<String, dynamic>;
        state.setJoke(joke['text'] as String? ?? '', joke['category'] as String? ?? '');
        state.setStatus('😂 Вот шутка!');
        state.log('😂 Found: ${(joke['text'] as String?)?.substring(0, min(80, (joke['text'] as String).length))}...');
      } else {
        state.setStatus('🤷 Не нашёл шутку');
      }

      state.setProcessing(false);

      // Cleanup
      await recorder.dispose();

    } catch (e) {
      state.setStatus('❌ Ошибка: $e');
      state.log('❌ Error: $e');
      state.setProcessing(false);
      state.setListening(false);
    }
  }
}

// ============================================================
// Random Joke Page
// ============================================================
class RandomPage extends StatefulWidget {
  const RandomPage({super.key});
  @override State<RandomPage> createState() => _RandomPageState();
}

class _RandomPageState extends State<RandomPage> {
  Map<String, dynamic>? _joke;
  bool _loading = false;

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final state = context.read<AppState>();
      final resp = await http.get(Uri.parse('${state.baseUrl}/api/joke/random')).timeout(const Duration(seconds: 10));
      final data = jsonDecode(resp.body) as Map<String, dynamic>;
      setState(() => _joke = data);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ошибка: $e')));
    }
    setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('🎲 Случайная шутка'), backgroundColor: Colors.transparent),
      body: Center(
        child: _loading
          ? const CircularProgressIndicator(color: Color(0xFF4CAF50))
          : _joke != null
            ? Padding(
                padding: const EdgeInsets.all(24),
                child: Card(
                  color: const Color(0xFF1E1E1E),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(_joke!['category'] ?? '', style: const TextStyle(color: Color(0xFF4CAF50), fontWeight: FontWeight.bold)),
                        const SizedBox(height: 16),
                        Text(_joke!['text'] ?? '', style: const TextStyle(fontSize: 18, height: 1.5)),
                        const SizedBox(height: 16),
                        Text('⭐ ${(_joke!['rating'] ?? 0).toStringAsFixed(1)}', style: const TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ),
                ),
              )
            : const Text('Нажмите кнопку ↓', style: TextStyle(color: Colors.grey, fontSize: 18)),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _loading ? null : _load,
        backgroundColor: const Color(0xFF4CAF50),
        child: const Icon(Icons.casino, color: Colors.white, size: 32),
      ),
    );
  }
}

// ============================================================
// Categories Page
// ============================================================
class CategoriesPage extends StatefulWidget {
  const CategoriesPage({super.key});
  @override State<CategoriesPage> createState() => _CategoriesPageState();
}

class _CategoriesPageState extends State<CategoriesPage> {
  Map<String, int>? _cats;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final state = context.read<AppState>();
      final resp = await http.get(Uri.parse('${state.baseUrl}/api/categories')).timeout(const Duration(seconds: 10));
      setState(() => _cats = Map<String, int>.from(jsonDecode(resp.body)));
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('📂 Категории'), backgroundColor: Colors.transparent),
      body: _cats == null
        ? const Center(child: CircularProgressIndicator())
        : ListView(
            children: _cats!.entries.map((e) => ListTile(
              title: Text(e.key, style: const TextStyle(color: Colors.white)),
              trailing: Text('${e.value}', style: const TextStyle(color: Color(0xFF4CAF50))),
            )).toList(),
          ),
    );
  }
}

// ============================================================
// Settings Page
// ============================================================
class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    return Scaffold(
      appBar: AppBar(title: const Text('⚙️ Настройки'), backgroundColor: Colors.transparent),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('API сервер', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 8),
            TextField(
              controller: TextEditingController(text: state.baseUrl),
              onChanged: (v) => state.baseUrl = v.trim(),
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: 'http://192.168.0.150:8000',
                filled: true,
                fillColor: const Color(0xFF1E1E1E),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () async {
                try {
                  final resp = await http.get(Uri.parse('${state.baseUrl}/api/voice/status')).timeout(const Duration(seconds: 5));
                  final d = jsonDecode(resp.body);
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text('✅ STT: ${d['stt_available']}, Model: ${d['whisper_model_size']}'),
                    backgroundColor: const Color(0xFF4CAF50),
                  ));
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: Text('❌ $e'),
                    backgroundColor: Colors.red,
                  ));
                }
              },
              icon: const Icon(Icons.wifi_find),
              label: const Text('Проверить соединение'),
            ),
            const SizedBox(height: 24),
            const Text('Логи:', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 8),
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(8)),
                child: ListView.builder(
                  itemCount: state.logs.length,
                  itemBuilder: (_, i) => Text(state.logs[i], style: const TextStyle(color: Color(0xFF4CAF50), fontSize: 10, fontFamily: 'monospace')),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
