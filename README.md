# 📺 Multi-Language YouTube Subtitle Translator & Vocab Builder

A powerful Python tool that extracts subtitles from YouTube videos in various languages (English, Spanish, Arabic, Japanese, etc.), translates them into Korean, and helps language learners by generating bilingual scripts and vocabulary lists.

## ✨ Key Features
- **Auto Language Detection:** Automatically detects and lists all available subtitle tracks (manual & auto-generated).
- **Supports latest youtube-transcript-api (v1.2+):** Fully compatible with the current API structure (2026).
- **Bilingual Output:** Saves original subtitles + Korean translation line-by-line with timestamps for easy comparison.
- **Smart Vocab Builder:** Extracts and deduplicates words from subtitles to create a custom study list (coming soon / in progress).
- **Copyright Safe:** Processes everything locally — no copyrighted content is stored or distributed.

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hazel-jeon/my-subtitle-translator.git
   cd my-subtitle-translator
   ```

2. **Install dependencies (latest version required):**
   ```bash
   pip install -r requirements.txt
   pip install --upgrade youtube-transcript-api   # Force upgrade to 1.2.4+ (2026 standard)
   ```

   Important: This project requires youtube-transcript-api 1.2.0 or higher.
   If you're using an older version (e.g., 0.6.x), update it with:

   ```bash
   pip install youtube-transcript-api>=1.2.0 --upgrade
   ```

3. **(Optional) Install tomli for Python 3.10 or below:**
   Python 3.11+ includes `tomllib` built-in. If you're on an older version, install `tomli` manually:
   ```bash
   pip install tomli
   ```

## 🚀 How to Use
1. Run the main script:
   ```bash
   python main.py
   ```

2. Paste the YouTube video URL (e.g., Bluey episodes, TED Talks, language learning videos, news, etc.).

3. The script will automatically:
- Detect available subtitles
- Prioritize manually created subtitles → fall back to auto-generated ones
- Translate to Korean using Gemini API (falls back to Google Translate if key is unavailable)
- Save the result as a .txt file (e.g. study_script_VIDEOID.txt)

4. Open the generated .txt file to review the bilingual script with timestamps!

### Common issues & fixes (2026 version):
- `'YouTubeTranscriptApi' has no attribute 'list_transcripts'`
→ Fixed in latest code: Use `YouTubeTranscriptApi().list(video_id)` instead of class method.
- `'FetchedTranscriptSnippet' object is not subscriptable`
→ Fixed: Access with `snippet.text` and `snippet.start` instead of `entry['text']`.
- No subtitles found (TranscriptsDisabled / NoTranscriptFound)
→ Video has no subtitles, or YouTube blocked access. Try a different video or add proxies/cookies (advanced).
- `GEMINI_API_KEY를 찾을 수 없습니다` / Gemini not working
→ Check that the key is set via environment variable or `.streamlit/secrets.toml`. See API Key Setup below.
- Still having issues? Reinstall the library:
   ```bash
   pip uninstall youtube-transcript-api
   pip install youtube-transcript-api --upgrade
   ```

## API Key Setup (Required for Gemini Translation)

This tool uses the **Google Gemini API** for high-quality translation.  
If the API key is not set, it automatically falls back to Google Translate.

### 1. Get Your Gemini API Key
1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API key"** → copy the key (starts with `AIzaSy...`)

### 2. Option A — Environment Variable (Recommended)
Do **not** hardcode the key in the script. Use an environment variable instead.

**macOS / Linux**
```bash
export GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxx
python main.py
```

**Windows (Command Prompt or PowerShell)**
```cmd
set GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxx
python main.py
```

### 3. Option B — `.streamlit/secrets.toml`
If you're also running the Streamlit app (`app.py`), you can store the key in one place:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Both `main.py` and `app.py` will automatically read from this file.

### 4. Make the Environment Variable Permanent

- **Windows:**
Go to Control Panel → System → Advanced system settings → Environment Variables.
Under "User variables" → New.
Variable name: `GEMINI_API_KEY` / Variable value: your API key.

- **macOS / Linux:**
```bash
nano ~/.zshrc    # or ~/.bash_profile if using bash
```
Add this line at the end:
```bash
export GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
Save (Ctrl+O → Enter → Ctrl+X) and reload:
```bash
source ~/.zshrc
```

### 5. Notes
- Never commit your API key to GitHub (it will be exposed publicly).
- If you lose the key or want a new one, just generate another at the link above.
- The script will still work without the key (using Google Translate fallback).

Happy translating! If you run into any issues, feel free to open an Issue on GitHub.

## ⚠️ Disclaimer

- **Educational Purpose Only:** This tool is intended for personal language learning and research purposes.
- **Copyright Notice:** All original video content and subtitles are the intellectual property of their respective copyright owners (e.g., Ludo Studio, BBC Studios).
- **Data Usage:** This script does not host or distribute copyrighted data. It only provides a technical method to process subtitles for personal use. Users are responsible for complying with YouTube's Terms of Service.
- **Non-official API Warning:** This tool relies on the unofficial youtube-transcript-api library, which scrapes YouTube data. It may break if YouTube changes its internal structure. Always keep the library updated.

## 📝 License
This project is open-source and available under the MIT License.