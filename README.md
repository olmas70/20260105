# YouTube Subtitle Generation and Correction System

유튜브 동영상 파일(MP4)에서 자막을 자동 생성하고, AI가 문맥을 이해하여 오타를 수정하는 자동화 시스템입니다.

## 📋 시스템 개요

**3단계 파이프라인 구조**:
1. **Generator** - 음성을 텍스트로 변환 (Whisper API) ✅
2. **Analyzer** - 문맥 파악 및 전문용어 추출 (Claude API) ✅
3. **Fixer** - 오타 교정 및 SRT 생성 (Claude API) ✅

**현재 구현 상태**: ✅ **전체 파이프라인 완성!**

---

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.8+
- FFmpeg (오디오 추출용)
- OpenAI API Key (Whisper용)
- Anthropic API Key (Claude용 - Analyzer/Fixer)

#### FFmpeg 설치

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드
```

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd 20260105

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 추가
# OPENAI_API_KEY=your-openai-api-key-here
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 4. 사용 방법

#### ⭐ 권장: main.py로 전체 파이프라인 실행

**가장 간단한 방법!** 한 명령어로 MP4 → SRT 변환:

```bash
# 기본 사용 (한국어)
python main.py -i data/input/my_video.mp4

# 출력 경로 지정
python main.py -i video.mp4 -o output/subtitles.srt

# 영어 비디오
python main.py -i video.mp4 -l en

# 임시 파일 유지 (디버깅용)
python main.py -i video.mp4 --keep-temp

# 상세 로그 출력
python main.py -i video.mp4 -v
```

**실행 예시:**
```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎬 YouTube Subtitle Generation & Correction System 🎬     ║
║                                                              ║
║   Generator → Analyzer → Fixer → Perfect Subtitles!         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

📹 Input video: data/input/my_video.mp4
📏 File size: 45.23 MB
🌐 Language: ko
📄 Output SRT: data/output/my_video.srt

============================================================
  📌 Step 1/3: Generator - Audio to Text (Whisper API)
============================================================

🎙️  Extracting audio and transcribing...
✅ Success!
   - Segments: 120
   - Duration: 300.5s (5.0 minutes)

============================================================
  📌 Step 2/3: Analyzer - Context Analysis (Claude API)
============================================================

🔍 Analyzing context and vocabulary...
✅ Success!
   - Topic: 파이썬 프로그래밍 기초 강의
   - Domain: 기술/IT
   - Technical terms: 15
   - Proper nouns: 5

============================================================
  📌 Step 3/3: Fixer - Error Correction (Claude API)
============================================================

✏️  Correcting errors and generating SRT...
✅ Success!
   - Total segments: 120
   - Corrected: 45 (37.5%)

============================================================
  🎉 Pipeline Complete!
============================================================

📄 Next steps:
   1. Review the subtitle file: data/output/my_video.srt
   2. Apply subtitles to your video
   3. Enjoy your perfectly subtitled video! 🎬
```

#### 옵션 2: Python 코드에서 사용 (고급)

개별 에이전트를 세밀하게 제어하고 싶을 때:

```python
from agents.generator import generate_subtitles
from agents.analyzer import analyze_subtitles
from agents.fixer import fix_subtitles

# 1단계: 자막 생성
raw = generate_subtitles(
    video_path="data/input/video.mp4",
    output_json_path="data/temp/raw.json"
)

# 2단계: 문맥 분석
context = analyze_subtitles(
    raw_subtitle_path="data/temp/raw.json",
    output_json_path="data/temp/context.json"
)

# 3단계: 오타 교정
result = fix_subtitles(
    raw_subtitle_path="data/temp/raw.json",
    context_metadata_path="data/temp/context.json",
    output_srt_path="data/output/video.srt"
)

print(f"✅ 완료: {result['output_srt']}")
```

---

## 📁 프로젝트 구조

```
.
├── agents/                 # 에이전트 모듈
│   ├── generator.py       # ✅ Generator 에이전트 (완료)
│   ├── analyzer.py        # ✅ Analyzer 에이전트 (완료)
│   └── fixer.py           # ✅ Fixer 에이전트 (완료)
│
├── utils/                 # 유틸리티 모듈
│   ├── audio_extractor.py # FFmpeg 오디오 추출
│   ├── api_client.py      # API 클라이언트 (Whisper, Claude)
│   └── srt_formatter.py   # SRT 파일 포맷터
│
├── data/
│   ├── input/             # 입력 비디오 파일
│   ├── output/            # 최종 SRT 파일
│   └── temp/              # 임시 파일 (오디오, JSON)
│
├── config/
│   └── config.yaml        # 설정 파일
│
├── tests/                 # 테스트 코드
│   ├── test_generator.py
│   ├── test_analyzer.py
│   └── test_fixer.py
│
├── main.py                # ⭐ 메인 CLI 스크립트 (전체 파이프라인)
├── ARCHITECTURE.md        # 시스템 아키텍처 설계 문서
├── requirements.txt       # Python 의존성
└── README.md             # 이 파일
```

---

## 🔧 Generator 에이전트 상세

### 기능

1. **오디오 추출**: MP4 비디오에서 WAV 오디오 추출 (FFmpeg)
2. **음성 인식**: Whisper API로 음성을 텍스트로 변환
3. **타임스탬프**: 각 자막에 시작/끝 시간 포함
4. **JSON 출력**: 구조화된 JSON 형식으로 저장

### 입력

- **파일 형식**: MP4, AVI, MOV 등 (FFmpeg 지원 형식)
- **최대 크기**: 오디오 25MB (Whisper API 제한)
- **언어**: 한국어 기본 (다른 언어도 지원)

### 출력 예시

```json
{
  "video_path": "data/input/video.mp4",
  "audio_path": "data/temp/video.wav",
  "language": "ko",
  "duration": 120.5,
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 3.5,
      "text": "안녕하세요 오늘은 파이썬에 대해 알아보겠습니다"
    },
    {
      "id": 2,
      "start": 3.5,
      "end": 7.2,
      "text": "먼저 변수선언 방법을 설명하겠습니다"
    }
  ]
}
```

### 고급 사용법

```python
from agents.generator import GeneratorAgent

# 커스텀 설정으로 에이전트 생성
agent = GeneratorAgent(
    whisper_model="whisper-1",
    language="ko",
    temp_dir="data/temp"
)

# 프롬프트를 사용하여 정확도 향상
# (특정 용어나 이름을 미리 알려줄 수 있음)
result = agent.generate(
    video_path="data/input/video.mp4",
    output_json_path="data/temp/raw_subtitle.json",
    prompt="이 동영상은 파이썬 프로그래밍에 관한 내용입니다."
)

# 임시 파일 정리
agent.cleanup_temp_files()
```

---

## 🔍 Analyzer 에이전트 상세

### 기능

1. **문맥 분석**: 전체 스크립트의 주제와 도메인 파악
2. **어휘 추출**: 전문용어, 고유명사, 핵심구문 식별
3. **오류 패턴 예측**: 음성 인식에서 발생 가능한 오류 패턴 분석
4. **메타데이터 생성**: Fixer가 사용할 문맥 정보 JSON 생성

### 입력

- **파일 형식**: Generator 출력 JSON
- **필수 필드**: segments (자막 세그먼트 리스트)

### 출력 예시

```json
{
  "source_file": "data/input/video.mp4",
  "total_segments": 50,
  "total_duration": 300.5,
  "full_transcript": "안녕하세요 오늘은 파이썬에 대해...",
  "metadata": {
    "topic": "파이썬 프로그래밍 기초 강의",
    "domain": "기술/IT",
    "language_style": "강의형",
    "formality": "보통"
  },
  "vocabulary": {
    "technical_terms": ["파이썬", "변수", "데이터타입", "함수", "클래스"],
    "proper_nouns": ["Python", "VSCode", "GitHub"],
    "key_phrases": ["알아보겠습니다", "설명하겠습니다"]
  },
  "error_patterns": [
    {
      "type": "spacing",
      "examples": ["변수선언 → 변수 선언", "데이터타입 → 데이터 타입"],
      "correction_guide": "합성어 띄어쓰기 규칙 적용"
    },
    {
      "type": "homophone",
      "examples": ["설명하겟습니다 → 설명하겠습니다"],
      "correction_guide": "'-겠-' 어미 교정"
    }
  ]
}
```

### 사용 방법

#### 방법 1: 스크립트로 실행

```bash
# Generator 출력을 Analyzer로 분석
python agents/analyzer.py data/temp/raw_subtitle.json data/temp/context_metadata.json
```

#### 방법 2: Python 코드에서 사용

```python
from agents.analyzer import analyze_subtitles

# 문맥 분석
context = analyze_subtitles(
    raw_subtitle_path="data/temp/raw_subtitle.json",
    output_json_path="data/temp/context_metadata.json"
)

# 결과 확인
print(f"주제: {context['metadata']['topic']}")
print(f"도메인: {context['metadata']['domain']}")
print(f"전문용어: {len(context['vocabulary']['technical_terms'])}개")

# 요약 보기
from agents.analyzer import AnalyzerAgent
analyzer = AnalyzerAgent()
print(analyzer.get_summary(context))
```

#### 방법 3: 파이프라인 (Generator → Analyzer)

```python
from agents.generator import generate_subtitles
from agents.analyzer import analyze_subtitles

# 1단계: 자막 생성
raw_subtitle = generate_subtitles(
    video_path="data/input/video.mp4",
    output_json_path="data/temp/raw_subtitle.json"
)

# 2단계: 문맥 분석
context = analyze_subtitles(
    raw_subtitle_path="data/temp/raw_subtitle.json",
    output_json_path="data/temp/context_metadata.json"
)

print(f"✅ 파이프라인 완료!")
print(f"  - 자막: {len(raw_subtitle['segments'])}개")
print(f"  - 주제: {context['metadata']['topic']}")
```

---

## ✏️ Fixer 에이전트 상세

### 기능

1. **오타 교정**: 문맥 기반 맞춤법 및 띄어쓰기 수정
2. **동음이의어 구분**: 문맥에 맞는 올바른 단어 선택
3. **문장 부호 추가**: 적절한 위치에 마침표, 쉼표 등 추가
4. **SRT 파일 생성**: 표준 SRT 형식의 최종 자막 파일 생성

### 입력

- **파일 1**: Generator 출력 JSON (raw_subtitle.json)
- **파일 2**: Analyzer 출력 JSON (context_metadata.json)

### 출력 예시 (SRT 파일)

```srt
1
00:00:00,000 --> 00:00:03,500
안녕하세요. 오늘은 파이썬 프로그래밍에 대해 알아보겠습니다.

2
00:00:03,500 --> 00:00:07,200
먼저 변수 선언 방법을 설명하겠습니다.

3
00:00:07,200 --> 00:00:12,000
파이썬에서는 변수 타입을 명시하지 않아도 됩니다.
```

### 사용 방법

#### 방법 1: 스크립트로 실행

```bash
# Analyzer 출력을 Fixer로 교정
python agents/fixer.py data/temp/raw_subtitle.json data/temp/context_metadata.json data/output/video.srt
```

#### 방법 2: Python 코드에서 사용

```python
from agents.fixer import fix_subtitles

# 자막 교정 및 SRT 생성
result = fix_subtitles(
    raw_subtitle_path="data/temp/raw_subtitle.json",
    context_metadata_path="data/temp/context_metadata.json",
    output_srt_path="data/output/video.srt"
)

# 결과 확인
print(f"총 {result['total_segments']}개 중 {result['corrected_segments']}개 교정됨")
print(f"SRT 파일: {result['output_srt']}")

# 교정 요약 보기
from agents.fixer import FixerAgent
fixer = FixerAgent()
print(fixer.get_correction_summary(result))
```

#### 방법 3: 파이프라인 (Analyzer → Fixer)

```python
from agents.analyzer import analyze_subtitles
from agents.fixer import fix_subtitles

# 2단계: 문맥 분석
context = analyze_subtitles(
    raw_subtitle_path="data/temp/raw_subtitle.json",
    output_json_path="data/temp/context_metadata.json"
)

# 3단계: 오타 교정 및 SRT 생성
result = fix_subtitles(
    raw_subtitle_path="data/temp/raw_subtitle.json",
    context_metadata_path="data/temp/context_metadata.json",
    output_srt_path="data/output/video.srt"
)

print(f"✅ 최종 SRT 생성 완료: {result['output_srt']}")
```

---

## 🎬 전체 파이프라인 사용법

### 완전한 워크플로우 (Generator → Analyzer → Fixer)

```python
from agents.generator import generate_subtitles
from agents.analyzer import analyze_subtitles
from agents.fixer import fix_subtitles

# 1단계: 자막 생성 (Whisper API)
print("1단계: 음성 인식 중...")
raw_subtitle = generate_subtitles(
    video_path="data/input/my_video.mp4",
    output_json_path="data/temp/raw_subtitle.json",
    language="ko"
)
print(f"✅ {len(raw_subtitle['segments'])}개 자막 생성 완료")

# 2단계: 문맥 분석 (Claude API)
print("\n2단계: 문맥 분석 중...")
context = analyze_subtitles(
    raw_subtitle_path="data/temp/raw_subtitle.json",
    output_json_path="data/temp/context_metadata.json"
)
print(f"✅ 주제: {context['metadata']['topic']}")
print(f"✅ 도메인: {context['metadata']['domain']}")

# 3단계: 오타 교정 및 SRT 생성 (Claude API)
print("\n3단계: 자막 교정 및 SRT 생성 중...")
result = fix_subtitles(
    raw_subtitle_path="data/temp/raw_subtitle.json",
    context_metadata_path="data/temp/context_metadata.json",
    output_srt_path="data/output/my_video.srt"
)
print(f"✅ {result['corrected_segments']}/{result['total_segments']}개 자막 교정 완료")
print(f"✅ 최종 파일: {result['output_srt']}")

print("\n🎉 전체 파이프라인 완료!")
print(f"📄 비디오에 {result['output_srt']} 자막을 적용하세요!")
```

### 간단한 원라이너 스크립트

```bash
# 전체 파이프라인을 한 번에 실행
python -c "
from agents.generator import generate_subtitles
from agents.analyzer import analyze_subtitles
from agents.fixer import fix_subtitles

raw = generate_subtitles('data/input/video.mp4', 'data/temp/raw.json')
ctx = analyze_subtitles('data/temp/raw.json', 'data/temp/ctx.json')
result = fix_subtitles('data/temp/raw.json', 'data/temp/ctx.json', 'data/output/video.srt')
print(f'✅ 완료: {result[\"output_srt\"]}')
"
```

---

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest tests/ -v

# Generator 테스트
pytest tests/test_generator.py -v

# Analyzer 테스트
pytest tests/test_analyzer.py -v

# Fixer 테스트
pytest tests/test_fixer.py -v

# 실제 API를 사용한 통합 테스트 (API 키 필요)
OPENAI_API_KEY=your-key ANTHROPIC_API_KEY=your-key pytest tests/ -v
```

---

## ⚙️ 설정 (config/config.yaml)

```yaml
openai:
  api_key: ${OPENAI_API_KEY}
  whisper_model: "whisper-1"
  language: "ko"
  temperature: 0

ffmpeg:
  audio_format: "wav"
  sample_rate: 16000
  channels: 1

paths:
  input_dir: "data/input"
  output_dir: "data/output"
  temp_dir: "data/temp"
```

---

## 📊 비용 예상

**10분 분량 비디오 기준**:
- **Generator (Whisper API)**: $0.006/분 × 10분 = **$0.06**
- **Analyzer (Claude API)**: ~3K tokens (input) + ~1K tokens (output) ≈ **$0.01**
- **Fixer (Claude API)**: ~50 segments × ~500 tokens/segment ≈ **$0.08**
- **총 예상 비용**: 약 **$0.15** (10분 비디오 1개)

매우 저렴한 비용으로 고품질 자막 생성 가능!

💡 **비용 절감 팁**:
- Fixer의 temperature를 낮추면 토큰 사용량 감소
- 짧은 세그먼트는 교정 건너뛰기
- 배치 처리로 API 호출 최적화 (향후 개선)

---

## 🗺️ 로드맵

- [x] **Phase 1**: Generator 에이전트 구현
  - [x] 오디오 추출 (FFmpeg)
  - [x] Whisper API 연동
  - [x] JSON 출력
  - [x] 테스트 코드

- [x] **Phase 2**: Analyzer 에이전트 구현
  - [x] 문맥 분석 (Claude API)
  - [x] 전문용어 추출
  - [x] 도메인 파악
  - [x] 오류 패턴 예측
  - [x] 테스트 코드

- [x] **Phase 3**: Fixer 에이전트 구현
  - [x] 오타 교정
  - [x] 띄어쓰기 수정
  - [x] 문장 부호 추가
  - [x] SRT 파일 생성
  - [x] 테스트 코드

- [x] **Phase 4**: 통합 및 최적화 (진행 중)
  - [x] 메인 파이프라인 스크립트 (main.py) ⭐
  - [x] CLI 인터페이스 ⭐
  - [ ] 배치 처리 (여러 비디오)
  - [ ] 대용량 파일 청킹
  - [ ] 웹 UI (선택사항)

---

## 🤝 기여

이슈와 풀 리퀘스트를 환영합니다!

---

## 📝 라이센스

MIT License

---

## 📚 참고 문서

- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [시스템 아키텍처 설계](ARCHITECTURE.md)

---

## ❓ FAQ

### Q: 전체 파이프라인이 완성되었나요?
A: 네! Generator, Analyzer, Fixer 모든 에이전트가 완성되어 MP4 파일에서 교정된 SRT 자막까지 자동 생성 가능합니다.

### Q: 비디오 파일이 25MB보다 크면 어떻게 하나요?
A: 오디오 파일이 25MB를 초과하면 현재는 에러가 발생합니다. Phase 4에서 자동 청킹 기능을 추가할 예정입니다.

### Q: 한국어 외 다른 언어도 지원하나요?
A: 네, Whisper는 다국어를 지원합니다. `language` 파라미터를 변경하세요 (예: "en", "ja", "zh"). Analyzer와 Fixer도 한국어 외 언어를 지원합니다.

### Q: 교정 품질은 어떤가요?
A: Claude API가 문맥을 이해하여 교정하므로 품질이 매우 높습니다. 전문용어와 고유명사도 올바르게 처리합니다.

### Q: 비용이 너무 많이 나오는데 줄일 수 있나요?
A: Fixer의 temperature를 낮추거나, 짧은 세그먼트는 건너뛰도록 설정할 수 있습니다. 배치 처리 최적화도 Phase 4에서 추가 예정입니다.

### Q: 로컬 Whisper를 사용할 수 있나요?
A: 현재는 OpenAI Whisper API만 지원하지만, 향후 로컬 Whisper 옵션을 추가할 수 있습니다.

### Q: 여러 비디오를 한 번에 처리할 수 있나요?
A: 현재는 개별 처리만 가능하지만, Phase 4에서 배치 처리 기능을 추가할 예정입니다.

---

**Made with ❤️ for better subtitles**
