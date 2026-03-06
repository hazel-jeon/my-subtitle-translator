from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import google.generativeai as genai
import re
import os

def get_video_id(url):
    pattern = r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

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

        # Gemini 설정
        try:
            gemini_api_key = os.getenv("GEMINI_API_KEY") or open(os.path.expanduser("~/.streamlit/secrets.toml")).read()
            # secrets.toml에서 직접 읽는 대신 환경변수 우선, 또는 파일에서 파싱 (간단 구현)
            # 실제로는 st.secrets를 쓰지만 콘솔 스크립트라 os.getenv 사용
            # 더 정확히 하려면 secrets.toml 파싱 로직 추가 가능
            genai.configure(api_key=gemini_api_key.strip().split('=')[1].strip('" '))
            model = genai.GenerativeModel('gemini-2.5-flash')  # 최신 모델
        except Exception as key_err:
            print(f"[!] Gemini API 키 로드 실패: {key_err}")
            print("[!] Google Translate로 대체합니다.")
            translated_full = ' '.join(GoogleTranslator(source='auto', target='ko').translate_batch(sentences))
        else:
            # Gemini 프롬프트 (섞인 언어도 한국어로 번역 지시)
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

            try:
                print("[+] Gemini 번역 시작...")
                response = model.generate_content(prompt)
                translated_full = response.text.strip()
                print("[+] Gemini 번역 완료")
            except Exception as gemini_err:
                print(f"[!] Gemini 번역 오류: {gemini_err}")
                print("[!] Google Translate로 대체합니다.")
                translated_full = ' '.join(GoogleTranslator(source='auto', target='ko').translate_batch(sentences))

        translated_full = translated_full.replace('[Music]', '[음악]')

        filename = f"study_script_{video_id}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            # 헤더
            f.write(f"[원본 언어: {source_lang_name} ({source_lang_code}) - {transcript_type}]\n")
            f.write(f"[비디오 ID: {video_id}]\n\n")
            
            f.write("[타임스탬프 + 원본 자막]\n")
            f.write("-" * 60 + "\n")

            # timestamp + 원본만 출력
            for snippet in fetched:
                original = snippet.text.strip()
                if not original or original == '[Music]':
                    continue

                minutes, seconds = divmod(int(snippet.start), 60)
                time_str = f"[{minutes:02d}:{seconds:02d}]"

                output = f"{time_str} [{source_lang_code.upper()}] {original}"
                print(output)
                f.write(output + "\n")

            # 구분선
            f.write("\n" + "=" * 60 + "\n\n")
            
            # 전체 번역 (문맥 보존)
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