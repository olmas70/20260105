# YouTube Subtitle Generation and Correction System

유튜브 동영상 파일(MP4)에서 자막을 자동 생성하고, AI가 문맥을 이해하여 오타를 수정하는 자동화 시스템입니다.

## 📋 시스템 개요

**3단계 파이프라인 구조**:
1. **Generator** - 음성을 텍스트로 변환 (Whisper API)
2. **Analyzer** - 문맥 파악 및 전문용어 추출 (Claude API) ⚠️ *구현 예정*
3. **Fixer** - 오타 교정 및 SRT 생성 (Claude API) ⚠️ *구현 예정*

**현재 구현 상태**: ✅ Generator 에이전트 완료

---

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.8+
- FFmpeg (오디오 추출용)
- OpenAI API Key (Whisper용)

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
# ANTHROPIC_API_KEY=your-anthropic-api-key-here (향후 필요)
```

### 4. 사용 방법

#### 옵션 1: Python 스크립트로 실행

```bash
# 비디오 파일을 data/input/ 에 복사
cp your_video.mp4 data/input/

# Generator 에이전트 실행
python agents/generator.py data/input/your_video.mp4 data/temp/raw_subtitle.json
```

#### 옵션 2: Python 코드에서 사용

```python
from agents.generator import generate_subtitles

# 자막 생성
result = generate_subtitles(
    video_path="data/input/your_video.mp4",
    output_json_path="data/temp/raw_subtitle.json",
    language="ko"
)

# 결과 확인
print(f"총 {len(result['segments'])} 개의 자막 생성됨")
print(f"영상 길이: {result['duration']:.2f}초")

# 첫 3개 자막 출력
for seg in result['segments'][:3]:
    print(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")
```

---

## 📁 프로젝트 구조

```
.
├── agents/                 # 에이전트 모듈
│   ├── generator.py       # ✅ Generator 에이전트 (완료)
│   ├── analyzer.py        # ⚠️ Analyzer 에이전트 (예정)
│   └── fixer.py           # ⚠️ Fixer 에이전트 (예정)
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
│   └── test_generator.py
│
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

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest tests/ -v

# 특정 테스트만 실행
pytest tests/test_generator.py -v

# 실제 API를 사용한 통합 테스트 (API 키 필요)
OPENAI_API_KEY=your-key pytest tests/test_generator.py -v
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
- Whisper API: $0.006/분 × 10분 = **$0.06**
- 매우 저렴한 비용으로 고품질 자막 생성 가능

---

## 🗺️ 로드맵

- [x] **Phase 1**: Generator 에이전트 구현
  - [x] 오디오 추출 (FFmpeg)
  - [x] Whisper API 연동
  - [x] JSON 출력
  - [x] 테스트 코드

- [ ] **Phase 2**: Analyzer 에이전트 구현
  - [ ] 문맥 분석 (Claude API)
  - [ ] 전문용어 추출
  - [ ] 도메인 파악

- [ ] **Phase 3**: Fixer 에이전트 구현
  - [ ] 오타 교정
  - [ ] 띄어쓰기 수정
  - [ ] SRT 파일 생성

- [ ] **Phase 4**: 통합 및 최적화
  - [ ] 메인 파이프라인 구현
  - [ ] CLI 인터페이스
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

### Q: 비디오 파일이 25MB보다 크면 어떻게 하나요?
A: 현재는 25MB 제한이 있습니다. 향후 자동 청킹 기능을 추가할 예정입니다.

### Q: 한국어 외 다른 언어도 지원하나요?
A: 네, Whisper는 다국어를 지원합니다. `language` 파라미터를 변경하세요 (예: "en", "ja", "zh").

### Q: 로컬 Whisper를 사용할 수 있나요?
A: 현재는 API만 지원하지만, 향후 로컬 Whisper 옵션을 추가할 수 있습니다.

### Q: Analyzer와 Fixer는 언제 완성되나요?
A: 순차적으로 개발 중입니다. Generator가 완성되었으니 다음은 Analyzer입니다!

---

**Made with ❤️ for better subtitles**
