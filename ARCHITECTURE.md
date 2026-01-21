# 유튜브 자막 생성 및 오타 교정 시스템 아키텍처

## 📋 시스템 개요

**목적**: 유튜브 동영상 파일(MP4)에서 자막을 자동 생성하고, AI가 문맥을 이해하여 오타를 수정하는 자동화 시스템

**최종 결과물**: 정확도 높은 한국어 자막 파일(SRT)

---

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     YouTube Subtitle System                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├── Input: MP4 Video File
                              ↓
        ┌─────────────────────────────────────────────┐
        │         1️⃣  Generator (자막 생성기)         │
        │  - 음성 추출 (MP4 → WAV)                     │
        │  - Speech-to-Text (Whisper API)             │
        │  - 기본 자막 생성 (타임스탬프 포함)           │
        └─────────────────────────────────────────────┘
                              │
                              ↓
                    Raw Subtitle (JSON)
                    {
                      segments: [{
                        start, end, text
                      }]
                    }
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │         2️⃣  Analyzer (문맥 분석기)          │
        │  - 전체 스크립트 문맥 이해                   │
        │  - 주제/도메인 파악 (기술, 교육, 일상 등)    │
        │  - 전문용어/고유명사 추출                    │
        │  - 문장 경계 분석                           │
        └─────────────────────────────────────────────┘
                              │
                              ↓
                    Context Metadata (JSON)
                    {
                      topic: "...",
                      domain: "...",
                      technical_terms: [],
                      proper_nouns: []
                    }
                              │
                              ↓
        ┌─────────────────────────────────────────────┐
        │           3️⃣  Fixer (오타 수정기)           │
        │  - 문맥 기반 오타 탐지                       │
        │  - 동음이의어 구분                          │
        │  - 띄어쓰기 교정                            │
        │  - 문장 부호 추가/수정                       │
        └─────────────────────────────────────────────┘
                              │
                              ↓
                    Corrected Subtitle (SRT)
                              │
                              ↓
                    ✅ Final Output: video.srt
```

---

## 🔧 에이전트별 상세 설계

### 1️⃣ Generator (자막 생성기)

#### 📌 주요 기능
- MP4 비디오에서 오디오 추출
- Whisper API를 사용한 음성 인식
- 타임스탬프가 포함된 초기 자막 생성

#### 🔄 처리 흐름
```
MP4 Video → FFmpeg (Audio Extraction) → WAV/MP3 File
                                            ↓
                                    Whisper API
                                            ↓
                              Raw Subtitle with Timestamps
```

#### 📦 입력
- **파일**: `video.mp4`
- **형식**: MP4 동영상 파일

#### 📤 출력
```json
{
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
      "text": "먼저 변수선언 방법을 설명하겟습니다"
    }
  ]
}
```

#### 🛠️ 기술 스택
- **FFmpeg**: 오디오 추출
- **OpenAI Whisper API**: 음성 인식
- **Python**: `ffmpeg-python`, `openai` 라이브러리

---

### 2️⃣ Analyzer (문맥 분석기)

#### 📌 주요 기능
- 전체 스크립트의 문맥 이해
- 주제 및 도메인 분류
- 전문용어 및 고유명사 추출
- 문장 경계 및 화자의 의도 파악

#### 🔄 처리 흐름
```
Raw Subtitle → LLM Analysis (Claude/GPT) → Context Metadata
```

#### 📦 입력
- Generator의 출력 JSON
- 전체 스크립트 텍스트

#### 📤 출력
```json
{
  "metadata": {
    "topic": "프로그래밍 교육",
    "domain": "기술/IT",
    "language_style": "설명형/교육적",
    "formality": "보통"
  },
  "vocabulary": {
    "technical_terms": ["파이썬", "변수선언", "데이터타입", "함수"],
    "proper_nouns": ["Python", "VSCode", "GitHub"],
    "common_errors": [
      {
        "wrong": "변수선언",
        "correct": "변수 선언",
        "type": "spacing"
      }
    ]
  },
  "sentence_boundaries": [
    {
      "segment_id": 2,
      "needs_punctuation": true,
      "suggested": "먼저 변수 선언 방법을 설명하겠습니다."
    }
  ]
}
```

#### 🛠️ 기술 스택
- **LLM API**: Claude API (Anthropic) 또는 GPT-4
- **프롬프트 엔지니어링**: 문맥 분석 전용 프롬프트

---

### 3️⃣ Fixer (오타 수정기)

#### 📌 주요 기능
- 문맥 기반 오타 탐지 및 수정
- 띄어쓰기 교정
- 동음이의어 구분
- 문장 부호 추가/수정
- SRT 파일 생성

#### 🔄 처리 흐름
```
Raw Subtitle + Context Metadata → LLM Correction → Corrected Subtitle
                                                            ↓
                                                    SRT Formatter
                                                            ↓
                                                      Final SRT
```

#### 📦 입력
- Generator의 Raw Subtitle JSON
- Analyzer의 Context Metadata JSON

#### 📤 출력 (SRT 형식)
```srt
1
00:00:00,000 --> 00:00:03,500
안녕하세요. 오늘은 파이썬에 대해 알아보겠습니다.

2
00:00:03,500 --> 00:00:07,200
먼저 변수 선언 방법을 설명하겠습니다.
```

#### 🛠️ 기술 스택
- **LLM API**: Claude API (문맥 기반 교정)
- **한글 처리**: `python-hanspell` (보조적으로 사용)
- **SRT 생성**: `pysrt` 라이브러리

---

## 🗂️ 프로젝트 디렉토리 구조

```
youtube-subtitle-system/
│
├── agents/                    # 에이전트 모듈
│   ├── __init__.py
│   ├── generator.py          # Generator 에이전트
│   ├── analyzer.py           # Analyzer 에이전트
│   └── fixer.py              # Fixer 에이전트
│
├── utils/                     # 유틸리티 함수
│   ├── __init__.py
│   ├── audio_extractor.py    # FFmpeg 오디오 추출
│   ├── srt_formatter.py      # SRT 파일 포맷터
│   └── api_client.py         # API 클라이언트 (Whisper, Claude)
│
├── data/                      # 데이터 디렉토리
│   ├── input/                # 입력 비디오 파일
│   ├── output/               # 최종 SRT 파일
│   └── temp/                 # 임시 파일 (오디오, JSON)
│
├── config/                    # 설정 파일
│   └── config.yaml           # API 키, 모델 설정 등
│
├── tests/                     # 테스트 코드
│   ├── test_generator.py
│   ├── test_analyzer.py
│   └── test_fixer.py
│
├── main.py                    # 메인 파이프라인
├── requirements.txt           # Python 의존성
└── README.md                  # 사용 설명서
```

---

## 🔌 데이터 흐름 (Data Flow)

```
[INPUT] video.mp4
    ↓
┌─────────────────┐
│   Generator     │ → temp/audio.wav
└─────────────────┘ → temp/raw_subtitle.json
    ↓
┌─────────────────┐
│   Analyzer      │ → temp/context_metadata.json
└─────────────────┘
    ↓
┌─────────────────┐
│   Fixer         │ → output/video.srt
└─────────────────┘
    ↓
[OUTPUT] video.srt
```

---

## 🔐 API 및 환경 변수

```yaml
# config/config.yaml
openai:
  api_key: ${OPENAI_API_KEY}
  whisper_model: "whisper-1"

anthropic:
  api_key: ${ANTHROPIC_API_KEY}
  model: "claude-3-5-sonnet-20241022"

ffmpeg:
  audio_format: "wav"
  sample_rate: 16000
  channels: 1
```

---

## 📊 에이전트 간 인터페이스

### Generator → Analyzer
```python
{
  "segments": List[Dict],
  "language": str,
  "duration": float
}
```

### Analyzer → Fixer
```python
{
  "metadata": Dict,
  "vocabulary": Dict,
  "sentence_boundaries": List[Dict]
}
```

### Fixer → Output
```python
# SRT 파일 (텍스트)
```

---

## 🚀 실행 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 설정
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# 3. 비디오 파일 처리
python main.py --input data/input/video.mp4 --output data/output/video.srt

# 4. 고급 옵션
python main.py --input video.mp4 --output video.srt \
  --language ko \
  --whisper-model whisper-1 \
  --claude-model claude-3-5-sonnet-20241022
```

---

## ⚙️ 향후 개선 방향

1. **배치 처리**: 여러 비디오 동시 처리
2. **UI 개발**: 웹 인터페이스 추가
3. **다국어 지원**: 한국어 외 언어 지원
4. **품질 검증**: 자동 품질 평가 시스템
5. **캐싱**: API 호출 결과 캐싱으로 비용 절감
6. **실시간 처리**: 스트리밍 비디오 지원

---

## 📝 예상 처리 시간

- **10분 분량 비디오 기준**:
  - Generator: ~2-3분 (Whisper API)
  - Analyzer: ~30초 (Claude API)
  - Fixer: ~1-2분 (Claude API)
  - **총 소요 시간**: 약 4-6분

---

## 💰 예상 비용

- **Whisper API**: $0.006 per minute → 10분 = $0.06
- **Claude API**: ~$0.003 per 1K tokens → 10분 스크립트 = ~$0.10
- **10분 비디오 1개 처리 비용**: **약 $0.16**
