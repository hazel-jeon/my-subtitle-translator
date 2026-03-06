from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import re

def get_word_list(text):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return words

def run_translator():
    try:
        video_url = input("YouTube URL을 입력하세요: ")
        video_id = video_url.split("v=")[-1].split("&")[0]
        
        print("[*] 사용 가능한 자막 언어를 확인 중입니다...")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        available_langs = []
        print("\n--- 선택 가능한 자막 목록 ---")
        for i, t in enumerate(transcript_list):
            lang_info = f"{i+1}. {t.language} ({t.language_code})"
            if t.is_generated:
                lang_info += " [자동 생성]"
            print(lang_info)
            available_langs.append(t.language_code)
            
        choice = int(input("\n번역할 언어 번호를 선택하세요: ")) - 1
        selected_lang = available_langs[choice]

        print(f"[*] '{selected_lang}' 자막 추출 및 한국어 번역 시작...")
        transcript = transcript_list.find_transcript([selected_lang]).fetch()
        
        translator = GoogleTranslator(source=selected_lang, target='ko')
        filename = f"study_{selected_lang}_{video_id}.txt"
        
        all_words = set()
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"--- Study Log: {video_id} ({selected_lang}) ---\n\n")
            
            for entry in transcript:
                original = entry['text']
                translated = translator.translate(original)
                

                words = get_word_list(original)
                all_words.update(words)
                
                line = f"[{selected_lang}] {original}\n[ko] {translated}\n"
                print(line)
                f.write(line + "\n")
            

            f.write("\n" + "="*30 + "\n")
            f.write(f"   VOCABULARY LIST ({len(all_words)} words)   \n")
            f.write("="*30 + "\n")
            

            for word in sorted(list(all_words)):
                f.write(f"- {word}\n")
                
        print(f"\n[!] 완료! 번역과 단어장이 '{filename}'에 저장되었습니다.")

    except Exception as e:
        print(f"\n[-] 오류 발생: {e}")

if __name__ == "__main__":
    run_translator()