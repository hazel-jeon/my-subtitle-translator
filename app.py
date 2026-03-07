import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from deep_translator import GoogleTranslator
import re
import json
import zipfile
import io
import hashlib
import struct
import time

def get_video_id(url):
    pattern = r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def build_anki_package(vocab_list, deck_name="YouTube Vocab"):
    """
    vocab_list: [{"word": str, "meaning": str, "example": str}, ...]
    Returns bytes of a valid .apkg (Anki package) file.
    """
    import sqlite3, time, random

    deck_id = random.randint(1_000_000_000, 9_999_999_999)
    model_id = random.randint(1_000_000_000, 9_999_999_999)
    now = int(time.time())

    col_db = io.BytesIO()
    # Write to a temp file path (sqlite3 needs a real path or :memory:)
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    conn = sqlite3.connect(tmp.name)
    cur = conn.cursor()

    # Anki collection schema (simplified)
    cur.executescript("""
        CREATE TABLE col (
            id INTEGER PRIMARY KEY,
            crt INTEGER NOT NULL,
            mod INTEGER NOT NULL,
            scm INTEGER NOT NULL,
            ver INTEGER NOT NULL,
            dty INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            ls INTEGER NOT NULL,
            conf TEXT NOT NULL,
            models TEXT NOT NULL,
            decks TEXT NOT NULL,
            dconf TEXT NOT NULL,
            tags TEXT NOT NULL
        );
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY,
            guid TEXT NOT NULL,
            mid INTEGER NOT NULL,
            mod INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            tags TEXT NOT NULL,
            flds TEXT NOT NULL,
            sfld TEXT NOT NULL,
            csum INTEGER NOT NULL,
            flags INTEGER NOT NULL,
            data TEXT NOT NULL
        );
        CREATE TABLE cards (
            id INTEGER PRIMARY KEY,
            nid INTEGER NOT NULL,
            did INTEGER NOT NULL,
            ord INTEGER NOT NULL,
            mod INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            type INTEGER NOT NULL,
            queue INTEGER NOT NULL,
            due INTEGER NOT NULL,
            ivl INTEGER NOT NULL,
            factor INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            lapses INTEGER NOT NULL,
            left INTEGER NOT NULL,
            odue INTEGER NOT NULL,
            odid INTEGER NOT NULL,
            flags INTEGER NOT NULL,
            data TEXT NOT NULL
        );
        CREATE TABLE revlog (
            id INTEGER PRIMARY KEY,
            cid INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            ease INTEGER NOT NULL,
            ivl INTEGER NOT NULL,
            lastIvl INTEGER NOT NULL,
            factor INTEGER NOT NULL,
            time INTEGER NOT NULL,
            type INTEGER NOT NULL
        );
        CREATE TABLE graves (
            usn INTEGER NOT NULL,
            oid INTEGER NOT NULL,
            type INTEGER NOT NULL
        );
    """)

    model = {
        str(model_id): {
            "id": model_id,
            "name": "YouTube Vocab",
            "type": 0,
            "mod": now,
            "usn": -1,
            "sortf": 0,
            "did": deck_id,
            "tmpls": [{
                "name": "Card 1",
                "ord": 0,
                "qfmt": "<h2>{{Word}}</h2>",
                "afmt": "{{FrontSide}}<hr>{{Meaning}}<br><br><i>{{Example}}</i>",
                "bqfmt": "",
                "bafmt": "",
                "did": None,
                "bfont": "",
                "bsize": 0
            }],
            "flds": [
                {"name": "Word", "ord": 0, "sticky": False, "rtl": False, "font": "Arial", "size": 20},
                {"name": "Meaning", "ord": 1, "sticky": False, "rtl": False, "font": "Arial", "size": 20},
                {"name": "Example", "ord": 2, "sticky": False, "rtl": False, "font": "Arial", "size": 20},
            ],
            "css": ".card { font-family: arial; font-size: 20px; text-align: center; }",
            "latexPre": "",
            "latexPost": "",
            "tags": [],
            "vers": []
        }
    }

    deck = {
        str(deck_id): {
            "id": deck_id,
            "name": deck_name,
            "desc": "",
            "mod": now,
            "usn": -1,
            "collapsed": False,
            "newToday": [0, 0],
            "revToday": [0, 0],
            "lrnToday": [0, 0],
            "timeToday": [0, 0],
            "conf": 1,
            "extendNew": 10,
            "extendRev": 50,
            "browserCollapsed": False,
            "dyn": 0
        }
    }

    cur.execute("""
        INSERT INTO col VALUES (1,?,?,?,11,0,-1,0,'{}',?,?,'{}','{}')
    """, (now, now, now * 1000, json.dumps(model), json.dumps(deck)))

    for i, item in enumerate(vocab_list):
        note_id = now * 1000 + i
        card_id = now * 1000 + i + 100000
        guid = hashlib.sha1(item["word"].encode()).hexdigest()[:10]
        flds = f"{item['word']}\x1f{item['meaning']}\x1f{item.get('example', '')}"
        csum = struct.unpack(">I", hashlib.sha1(item["word"].encode()).digest()[:4])[0]

        cur.execute("""
            INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,0,'')
        """, (note_id, guid, model_id, now, -1, "", flds, item["word"], csum))

        cur.execute("""
            INSERT INTO cards VALUES (?,?,?,0,?,?,0,0,?,0,2500,0,0,0,0,0,0,'')
        """, (card_id, note_id, deck_id, now, -1, i + 1))

    conn.commit()
    conn.close()

    # Build .apkg (zip of collection.anki2 + media)
    apkg_buf = io.BytesIO()
    with zipfile.ZipFile(apkg_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        with open(tmp.name, "rb") as f:
            zf.writestr("collection.anki2", f.read())
        zf.writestr("media", "{}")
    os.unlink(tmp.name)

    apkg_buf.seek(0)
    return apkg_buf.read()


# ── UI ──────────────────────────────────────────────────────────────────────
st.title("YouTube 자막 번역기 📺➡️🇰🇷")
st.markdown("YouTube 영상 URL을 넣으면 자막을 추출해서 한국어로 번역해줍니다. (자동 자막도 지원)")

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

            fetched = target_transcript.fetch()

            full_original = ' '.join(
                s.text.strip() for s in fetched
                if s.text.strip() and s.text.strip() != '[Music]'
            )
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_original.strip()) if s.strip()]
            google_translator = GoogleTranslator(source='auto', target='ko')

            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel('gemini-2.5-flash')
            except KeyError:
                st.error("GEMINI_API_KEY가 secrets.toml에 없습니다.")
                st.stop()

            # ── 번역 ────────────────────────────────────────────────────────
            translate_prompt = f"""
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
                    response = model.generate_content(translate_prompt)
                    translated_full = response.text.strip()
                except Exception as e:
                    st.warning(f"Gemini 번역 오류: {e}\nGoogle 번역으로 대체합니다.")
                    translated_full = ' '.join(google_translator.translate_batch(sentences))

            if not translated_full:
                st.error("번역 결과가 없습니다.")
                st.stop()

            # ── 단어장 추출 (Gemini) ─────────────────────────────────────────
            vocab_items = []
            with st.spinner("단어장 생성 중..."):
                try:
                    vocab_prompt = f"""
You are a vocabulary extraction assistant.
From the following English subtitle text, extract the 20 most useful vocabulary words for a Korean learner.

Return ONLY a valid JSON array, no markdown, no explanation.
Format:
[
  {{"word": "word", "meaning": "한국어 뜻", "example": "example sentence from the text"}},
  ...
]

Text:
{full_original[:3000]}
"""
                    vocab_response = model.generate_content(vocab_prompt)
                    raw = vocab_response.text.strip().replace("```json", "").replace("```", "")
                    vocab_items = json.loads(raw)
                except Exception as e:
                    st.warning(f"단어장 생성 실패: {e}")

            # ── 탭 UI ────────────────────────────────────────────────────────
            tab1, tab2 = st.tabs(["📝 번역 결과", "📚 단어장 & Anki Export"])

            with tab1:
                st.subheader("전체 한국어 번역 (문맥 보존)")
                st.text_area("번역 결과 (복사 가능)", translated_full, height=300)

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

            with tab2:
                st.subheader("📚 추출된 단어장")

                if not vocab_items:
                    st.info("단어장 생성에 실패했습니다. 다시 시도해주세요.")
                else:
                    # 테이블로 표시
                    st.dataframe(
                        data={"단어": [v["word"] for v in vocab_items],
                              "뜻": [v["meaning"] for v in vocab_items],
                              "예문": [v.get("example", "") for v in vocab_items]},
                        use_container_width=True,
                        hide_index=True
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        # CSV 다운로드
                        csv_lines = ["단어,뜻,예문"] + [
                            f'"{v["word"]}","{v["meaning"]}","{v.get("example","")}"'
                            for v in vocab_items
                        ]
                        st.download_button(
                            label="단어장 CSV 다운로드",
                            data="\n".join(csv_lines),
                            file_name=f"vocab_{video_id}.csv",
                            mime="text/csv"
                        )

                    with col2:
                        # Anki .apkg 다운로드
                        try:
                            apkg_bytes = build_anki_package(vocab_items, deck_name=f"YouTube_{video_id}")
                            st.download_button(
                                label="Anki 덱 다운로드 (.apkg)",
                                data=apkg_bytes,
                                file_name=f"vocab_{video_id}.apkg",
                                mime="application/octet-stream"
                            )
                            st.caption("Anki에서 파일 → 가져오기로 바로 import 가능합니다.")
                        except Exception as e:
                            st.error(f"Anki 파일 생성 오류: {e}")

        except (NoTranscriptFound, TranscriptsDisabled):
            st.error("자막을 찾을 수 없거나 비활성화되어 있습니다.")
        except Exception as e:
            st.error(f"오류 발생: {type(e).__name__} - {str(e)}")

st.markdown("---")
st.caption("Powered by youtube-transcript-api + Gemini + Streamlit | 개인 학습용으로만 사용하세요.")