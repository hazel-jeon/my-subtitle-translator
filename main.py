from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import re

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

        # 1. 영상의 전체 자막 목록 가져오기
        api = YouTubeTranscriptApi()                     # 인스턴스 생성
        transcript_list = api.list(video_id)             # .list() 로 호출
        
        target_transcript = None
        is_auto_generated = False

        # 2. 우선순위 1: 수동으로 작성된 자막 (아무 언어나)
        for transcript in transcript_list:
            if not transcript.is_generated:
                target_transcript = transcript
                break
                
        # 3. 우선순위 2: 수동 자막이 없다면 자동 생성 자막 사용
        if not target_transcript:
            for transcript in transcript_list:
                if transcript.is_generated:
                    target_transcript = transcript
                    is_auto_generated = True
                    break

        if not target_transcript:
            print("[-] 이 영상에서 추출할 수 있는 자막이 없습니다.")
            return

        # 선택된 자막의 정보 추출
        source_lang_code = target_transcript.language_code
        source_lang_name = target_transcript.language
        transcript_type = "자동 생성" if is_auto_generated else "수동 생성"
        
        print(f"[*] 감지된 자막: {source_lang_name}({source_lang_code}) - {transcript_type}")
        print(f"[*] 자막 추출 및 한국어 번역을 시작합니다. (시간이 소요될 수 있습니다...)")

        # 실제 자막 데이터 가져오기
        fetched = target_transcript.fetch()

        # 번역기 설정 (출발 언어를 'auto'로 설정하여 알아서 감지/대응하게 함)
        translator = GoogleTranslator(source='auto', target='ko')
        filename = f"study_script_{video_id}.txt"
        
        # 텍스트 배치 번역 (속도 향상)
        original_texts = [snippet.text for snippet in fetched]
        translated_texts = translator.translate_batch(original_texts)

        with open(filename, "w", encoding="utf-8") as f:
            for i, snippet in enumerate(fetched):
                original = snippet.text
                translated = translated_texts[i]
                
                # 타임스탬프 계산
                minutes, seconds = divmod(int(snippet.start), 60)
                time_str = f"[{minutes:02d}:{seconds:02d}]"

                # 하드코딩된 [EN] 대신 동적 언어 코드 사용 (예: [JA], [ES] 등)
                output = f"{time_str}\n[{source_lang_code.upper()}] {original}\n[KO] {translated}\n" + "-"*30
                print(output)
                f.write(output + "\n")

        print(f"\n[!] 성공! '{filename}' 파일이 생성되었습니다.")

    except TranscriptsDisabled:
        print("[-] 이 영상은 자막이 비활성화되어 있습니다.")
    except NoTranscriptFound:
        print("[-] 자막을 찾을 수 없습니다.")
    except Exception as e:
        print(f"\n[-] 에러 발생: {e}")

if __name__ == "__main__":
    run_translator()