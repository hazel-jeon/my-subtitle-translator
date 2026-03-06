import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from deep_translator import GoogleTranslator
import re

def get_video_id(url):
    pattern = r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

st.title("YouTube 자막 번역기 📺➡️🇰🇷")
st.markdown("YouTube 영상 URL을 넣으면 자막을 추출해서 한국어로 번역해줍니다. (자동 자막도 지원)")

# 입력 UI
video_url = st.text_input("YouTube URL을 입력하세요", placeholder="https://youtu.be/......")
process_button = st.button("자막 추출 & 번역 시작")

if process_button and video_url:
    video_id = get_video_id(video_url)
    if not video_id:
        st.error("올바른 YouTube URL이 아닙니다.")
        st.stop()

    with st.spinner("자막 정보 조회 중..."):
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)

            target_transcript = None
            is_auto = False

            # 수동 자막 우선
            for t in transcript_list:
                if not t.is_generated:
                    target_transcript = t
                    break

            if not target_transcript:
                for t in transcript_list:
                    if t.is_generated:
                        target_transcript = t
                        is_auto = True
                        break

            if not target_transcript:
                st.error("사용 가능한 자막이 없습니다.")
                st.stop()

            lang_code = target_transcript.language_code
            lang_name = target_transcript.language
            typ = "자동 생성" if is_auto else "수동 생성"

            st.success(f"감지된 자막: {lang_name} ({lang_code}) - {typ}")

            # 자막 가져오기
            fetched = target_transcript.fetch()

            # 전체 원문 준비
            full_original = ' '.join(
                s.text.strip() for s in fetched
                if s.text.strip() and s.text.strip() != '[Music]'
            )

            # 문장 단위 분할 (fallback용)
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_original.strip()) if s.strip()]

            # 번역기 준비 (fallback용)
            google_translator = GoogleTranslator(source='auto', target='ko')

            # Gemini 클라이언트
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-2.5-flash')  # 무료 티어 최고 성능 모델
            except KeyError:
                st.error("GEMINI_API_KEY가 secrets.toml에 없습니다.")
                st.stop()

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

            translated_full = None

            with st.spinner("Gemini로 고품질 번역 중..."):
                try:
                    response = model.generate_content(prompt)
                    translated_full = response.text.strip()
                except Exception as e:
                    st.warning(f"Gemini 번역 오류: {e}\nGoogle 번역으로 대체합니다.")
                    translated_full = ' '.join(google_translator.translate_batch(sentences))

            if not translated_full:
                st.error("번역 결과가 없습니다.")
                st.stop()

            # 결과 표시
            st.subheader("전체 한국어 번역 (문맥 보존)")
            st.text_area("번역 결과 (복사 가능)", translated_full, height=300)

            # 다운로드 버튼들
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="전체 한국어 번역 다운로드 (.txt)",
                    data=translated_full,
                    file_name=f"translated_{video_id}.txt",
                    mime="text/plain"
                )

            with col2:
                output_lines = []
                for snippet in fetched:
                    text = snippet.text.strip()
                    if not text or text == '[Music]':
                        continue
                    min_sec = divmod(int(snippet.start), 60)
                    ts = f"[{min_sec[0]:02d}:{min_sec[1]:02d}]"
                    output_lines.append(f"{ts} [{lang_code.upper()}] {text}")

                original_text = "\n".join(output_lines)
                bilingual = f"[원본: {lang_name} ({lang_code}) - {typ}]\n\n" + original_text + "\n\n" + "="*60 + "\n\n" + translated_full
                st.download_button(
                    label="원본 + 한국어 번역 합본 다운로드",
                    data=bilingual,
                    file_name=f"bilingual_{video_id}.txt",
                    mime="text/plain"
                )

        except (NoTranscriptFound, TranscriptsDisabled):
            st.error("자막을 찾을 수 없거나 비활성화되어 있습니다.")
        except Exception as e:
            st.error(f"오류 발생: {type(e).__name__} - {str(e)}")

st.markdown("---")
st.caption("Powered by youtube-transcript-api + Groq + Streamlit | 개인 학습용으로만 사용하세요.")