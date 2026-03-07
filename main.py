from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import google.generativeai as genai
import re
import os

def get_video_id(url):
    pattern = r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def load_gemini_api_key():
    """Gemini API 키를 환경변수 → secrets.toml 순서로 로드"""
    # 1순위: 환경변수
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key.strip()

    # 2순위: .streamlit/secrets.toml (toml 파싱)
    secrets_paths = [
        os.path.join(os.getcwd(), ".streamlit", "secrets.toml"),
        os.path.expanduser("~/.streamlit/secrets.toml"),
    ]
    for path in secrets_paths:
        if os.path.exists(path):
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                try:
                    import tomli as tomllib  # pip install tomli
                except ImportError:
                    tomllib = None

            if tomllib:
                with open(path, "rb") as f:
                    data = tomllib.load(f)
                key = data.get("GEMINI_API_KEY", "")
            else:
                # tomllib 없을 때 직접 파싱 (간단한 key = "value" 형식만)
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY"):
                            key = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break

            if key:
                return key

    return None

def run_translator():
    try:
        video_url = input("YouTube URL을 입력하세요: ")
        video_id = get_video_id(video_url)

        if not video_id:
            print("[-] 올바른 유튜브 URL이 아닙니다.")
            return

        print(f"[*] 비디오 ID({video_id}) 자막 정보 조회 중...")

        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        target_transcript = None
        is_auto_generated = False

        # 수동 자막 우선
        for transcript in transcript_list:
            if not transcript.is_generated:
                target_transcript = transcript
                break

        # 수동 없으면 자동 자막
        if not target_transcript:
            for transcript in transcript_list:
                if transcript.is_generated:
                    target_transcript = transcript
                    is_auto_generated = True
                    break

        if not target_transcript:
            print("[-] 이 영상에서 추출할 수 있는 자막이 없습니다.")
            return

        source_lang_code = target_transcript.language_code
        source_lang_name = target_transcript.language
        transcript_type = "자동 생성" if is_auto_generated else "수동 생성"

        print(f"[*] 감지된 자막: {source_lang_name}({source_lang_code}) - {transcript_type}")
        print(f"[*] 자막 추출 및 한국어 번역을 시작합니다... (시간 소요될 수 있음)")

        fetched = target_transcript.fetch()

        # 전체 원문 합치기 (번역용)
        full_original = ' '.join(
            snippet.text.strip()
            for snippet in fetched
            if snippet.text.strip() and snippet.text.strip() != '[Music]'
        )

        # 문장 단위 분할 (fallback용)
        sentences = re.split(r'(?<=[.!?])\s+', full_original.strip())
        sentences = [s.strip() for s in sentences if s.strip()]

        translated_full = None

        # Gemini 시도
        gemini_api_key = load_gemini_api_key()

        if gemini_api_key:
            try:
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')

                prompt = f"""
You are a professional Korean subtitle translator.
Follow these instructions **strictly and absolutely**:

- All output must be **100% natural, fluent, and idiomatic Korean only**.
- **Do NOT use Chinese, English, Japanese, Thai, Vietnamese, or any other language at all.**
- **All output must be written entirely in Korean characters (Hangul).**
- **Never mix languages, never insert foreign words unless they are proper nouns.**
- If the original text contains mixed languages, **translate everything into natural Korean**.
- Replace [Music] with [음악].
- Maintain a conversational tone and subtitle style.
- Connect short subtitle fragments contextually.

Now translate the following text **entirely into Korean**:

Text to translate:
{full_original}
"""
                print("[+] Gemini 번역 시작...")
                response = model.generate_content(prompt)
                translated_full = response.text.strip()
                print("[+] Gemini 번역 완료")

            except Exception as gemini_err:
                print(f"[!] Gemini 번역 오류: {gemini_err}")
                print("[!] Google Translate로 대체합니다.")
        else:
            print("[!] GEMINI_API_KEY를 찾을 수 없습니다. Google Translate로 대체합니다.")

        # fallback: Google Translate
        if not translated_full:
            try:
                translated_full = ' '.join(
                    GoogleTranslator(source='auto', target='ko').translate_batch(sentences)
                )
            except Exception as trans_err:
                print(f"[!] Google Translate도 실패: {trans_err}")
                translated_full = full_original  # 최후 fallback: 원문 그대로

        translated_full = translated_full.replace('[Music]', '[음악]')

        filename = f"study_script_{video_id}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"[원본 언어: {source_lang_name} ({source_lang_code}) - {transcript_type}]\n")
            f.write(f"[비디오 ID: {video_id}]\n\n")
            f.write("[타임스탬프 + 원본 자막]\n")
            f.write("-" * 60 + "\n")

            for snippet in fetched:
                original = snippet.text.strip()
                if not original or original == '[Music]':
                    continue
                minutes, seconds = divmod(int(snippet.start), 60)
                time_str = f"[{minutes:02d}:{seconds:02d}]"
                output = f"{time_str} [{source_lang_code.upper()}] {original}"
                print(output)
                f.write(output + "\n")

            f.write("\n" + "=" * 60 + "\n\n")
            f.write("[전체 한국어 번역 - 문맥 완전 보존]\n")
            f.write(translated_full + "\n")

        print(f"\n[!] 완료! 파일이 생성되었습니다: {filename}")

    except TranscriptsDisabled:
        print("[-] 이 영상은 자막이 비활성화되어 있습니다.")
    except NoTranscriptFound:
        print("[-] 자막을 찾을 수 없습니다.")
    except Exception as e:
        print(f"\n[-] 에러 발생: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    run_translator()