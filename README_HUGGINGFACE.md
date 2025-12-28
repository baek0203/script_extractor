---
title: YouTube Script Extractor
emoji: 📹
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
---

# 📹 YouTube Script Extractor

유튜브 영상의 자막을 자동으로 추출하고 AI로 의미 단위 문단을 생성합니다.

## 🎯 주요 기능

- **자동 자막 추출**: YouTube URL만 입력하면 자막 자동 다운로드
- **의미 단위 분리**: AI가 문맥을 분석하여 자연스러운 문단으로 구분
- **주제 자동 생성**: 각 문단의 주제를 AI가 자동으로 생성
- **다양한 형식**: TXT, JSON, CSV 형식으로 제공
- **실시간 처리 과정**: 진행 상황을 실시간으로 확인
- **간편한 복사**: 복사 버튼으로 원클릭 복사

## 📖 사용 방법

1. YouTube URL 입력 (예: `https://www.youtube.com/watch?v=...`)
2. **Extract** 버튼 클릭
3. 처리 과정 확인 (1-3분 소요)
4. 원하는 탭을 선택하여 결과 확인
5. 복사 버튼으로 내용 복사 또는 직접 선택하여 복사

## 📄 출력 형식

### TXT (주제 포함)
- 의미 단위로 분리된 문단
- AI가 생성한 주제 포함
- 읽기 쉬운 형식

### JSON (구조화)
- 프로그래밍에 활용 가능한 구조화된 데이터
- 주제, 문장, 전체 텍스트 포함
- API 연동에 적합

### CSV (타임스탬프)
- 원본 자막의 타임스탬프 포함
- 시간대별 분석 가능
- 엑셀에서 바로 열기 가능

## ⚠️ 주의사항

- 자막이 없는 영상은 처리할 수 없습니다
- 비공개 또는 제한된 영상은 접근할 수 없습니다
- 처리 시간은 영상 길이에 따라 다릅니다 (보통 1-3분)

## 🛠️ 기술 스택

- **yt-dlp**: YouTube 자막 다운로드
- **Sentence Transformers**: 의미 분석 및 문단 분리
- **Gradio**: 웹 인터페이스
- **scikit-learn**: 클러스터링 알고리즘

## 📝 라이선스

MIT License
