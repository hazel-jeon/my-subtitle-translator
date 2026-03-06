# 📺 Multi-Language YouTube Subtitle Translator & Vocab Builder

A powerful Python tool that extracts subtitles from YouTube videos in various languages (English, Spanish, etc.), translates them into Korean, and automatically generates a vocabulary list for language learners.

## ✨ Key Features
- **Auto Language Detection:** Automatically detects and lists all available subtitle tracks (manual & auto-generated).
- **Supports latest youtube-transcript-api (v1.2+):** Fully compatible with the current API structure (2026).
- **Bilingual Output:** Saves original subtitles + Korean translation line-by-line with timestamps for easy comparison.
- **Smart Vocab Builder:** Extracts and deduplicates words from subtitles to create a custom study list (coming soon / in progress).
- **Copyright Safe:** Processes everything locally — no copyrighted content is stored or distributed.

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   ```

2. **Install dependencies (latest version required):**
    ```bash
    pip install -r requirements.txt
    pip install --upgrade youtube-transcript-api    # Force upgrade to 1.2.4+ (2026 standard)
    ```

    Important: This project requires youtube-transcript-api 1.2.0 or higher.
    If you're using an older version (e.g., 0.6.x), update it with:

    ```bash
    pip install youtube-transcript-api>=1.2.0 --upgrade
    ```
    It's recommended to add youtube-transcript-api>=1.2.0 to your requirements.txt file.

## 🚀 How to Use
1. Run the main script:
    ```bash
    python main.py
    ```

2. Paste the YouTube video URL (e.g., Bluey episodes, TED Talks, language learning videos, news, etc.).

3. The script will automatically:
- Detect available subtitles
- Prioritize manually created subtitles → fall back to auto-generated ones
- Translate to Korean using Google Translate
- Save the result as a .txt file (e.g. study_script_VIDEOID.txt)

### Common issues & fixes (2026 version):
- 'YouTubeTranscriptApi' has no attribute 'list_transcripts'
- → Fixed in latest code: Use YouTubeTranscriptApi().list(video_id) instead of class method.
- 'FetchedTranscriptSnippet' object is not subscriptable
- → Fixed: Access with snippet.text and snippet.start instead of entry['text'].
- No subtitles found (TranscriptsDisabled / NoTranscriptFound)
- → Video has no subtitles, or YouTube blocked access. Try a different video or add proxies/cookies (advanced).
- Still having issues? Reinstall the library:
    ```bash
    pip uninstall youtube-transcript-api
    pip install youtube-transcript-api --upgrade
    ```

4. Open the generated .txt file to review the bilingual script with timestamps!


## ⚠️ Disclaimer

- Educational Purpose Only: This tool is for personal language learning and study only.
- Copyright Notice: All video content and subtitles belong to their original owners (YouTube creators, studios, etc.).
- Data Usage: This script does not store, host, or distribute any copyrighted material. It only processes subtitles locally for personal use. You are responsible for following YouTube's Terms of Service.
- Unofficial API Warning: This tool depends on the unofficial youtube-transcript-api library, which may stop working if YouTube changes its internal structure. Always keep the library up to date.

## 📝 License
This project is open-source and available under the MIT License.
```text

Just replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub info.

Let me know if you want to add anything else (e.g., screenshots, more detailed vocab builder section, or contribution guidelines)!
```