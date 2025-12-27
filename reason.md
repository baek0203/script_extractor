# Technical Decisions and Rationale

## 개요
이 문서는 프로젝트의 각 모듈에서 사용된 기술적 결정과 그 이유를 설명합니다.

---

## 1. download.py - YouTube 자막 다운로드

### 사용된 기법

#### 1.1 yt-dlp 라이브러리 선택
```python
import yt_dlp
```

**이유:**
- **성능**: youtube-dl보다 빠르고 활발히 유지보수됨
- **안정성**: YouTube의 빈번한 API 변경에 대응
- **기능**: 자동 생성 자막 및 수동 자막 모두 지원

#### 1.2 PO Token 처리
```python
'extractor_args': {
    'youtube': {
        'player_client': ['android', 'web'],
        'skip': ['dash', 'hls']
    }
}
```

**이유:**
- **회피 전략**: YouTube의 PO Token 요구사항 우회
- **다중 클라이언트**: Android와 Web 클라이언트를 순차적으로 시도
- **안정성**: 한 클라이언트 실패 시 자동 fallback

#### 1.3 자막 형식 선택 (VTT)
```python
'subtitleslangs': ['en']
```

**이유:**
- **표준화**: WebVTT는 웹 표준 자막 형식
- **파싱 용이성**: 타임스탬프와 텍스트가 명확히 구분됨
- **라이브러리 지원**: webvtt-py로 쉽게 파싱 가능

---

## 2. preprocessing.py - 텍스트 전처리

### 사용된 기법

#### 2.1 pandas DataFrame 사용
```python
df = pd.DataFrame({
    'start': starts,
    'end': ends,
    'text': texts
})
```

**이유:**
- **데이터 조작**: 시계열 데이터 처리에 최적화
- **성능**: 벡터화 연산으로 빠른 처리
- **직관성**: 데이터 확인 및 디버깅 용이

#### 2.2 시간 기반 병합 (25초 윈도우)
```python
def merge_by_time_window(df, window_seconds=25)
```

**이유:**
- **의미 단위**: 일반적인 말하기 속도에서 한 생각을 표현하는 시간
- **실험적 결정**: 너무 짧으면 단편적, 너무 길면 주제 혼재
- **균형**: 컨텍스트 유지와 세분화 사이의 최적점

#### 2.3 중복 제거 알고리즘
```python
def remove_sequential_overlap(texts)
```

**이유:**
- **YouTube 특성**: 자막이 중복되어 나타나는 경우 많음
- **품질**: 중복 제거로 읽기 품질 향상
- **순차적 처리**: 이전 텍스트와만 비교하여 효율성 확보

#### 2.4 HTML 태그 제거
```python
text = re.sub(r'<[^>]+>', '', text)
```

**이유:**
- **깔끔함**: 자막에 포함된 서식 태그 제거
- **호환성**: 모든 출력 형식에서 문제 없도록
- **정규식 사용**: 간단하고 효과적인 처리

---

## 3. semantic_segmentation.py - AI 단락 분할

### 사용된 기법

#### 3.1 Sentence Transformers 사용
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
```

**이유:**
- **의미 이해**: 단순 키워드가 아닌 의미적 유사도 측정
- **모델 선택**: all-MiniLM-L6-v2
  - 크기: 90MB (가벼움)
  - 성능: 문장 임베딩에 최적화
  - 속도: CPU에서도 빠른 추론
- **사전 학습**: 별도 학습 없이 바로 사용 가능

#### 3.2 코사인 유사도 계산
```python
from sklearn.metrics.pairwise import cosine_similarity
```

**이유:**
- **정규화**: 벡터 크기와 무관하게 방향성만 비교
- **효율성**: 빠른 계산 (내적 기반)
- **해석 용이성**: 0~1 사이 값으로 유사도 직관적 이해

#### 3.3 상대적 경계 감지 (Adaptive Threshold)
```python
if sim < running_avg * drop_ratio:
    boundaries.add(i + 1)
running_avg = 0.8 * running_avg + 0.2 * sim
```

**이유:**
- **적응형**: 고정 임계값 대신 지역적 컨텍스트 고려
- **지수 평활**: 최근 유사도에 더 많은 가중치
- **안정성**: 국소적 변동에 덜 민감

#### 3.4 최소 간격 강제 (min_gap=5)
```python
if (i + 1 - last_boundary) >= min_gap:
```

**이유:**
- **과분할 방지**: 연속된 작은 변화를 하나로 묶음
- **인간적 사고**: 사람은 최소 5-8 문장을 하나의 생각 단위로 인식
- **품질**: 너무 짧은 단락 방지

#### 3.5 최소 단락 길이 (min_paragraph_length=8)
```python
if len(current) >= min_paragraph_length:
```

**이유:**
- **의미 있는 분량**: 주제를 충분히 다루는 길이
- **읽기 경험**: 너무 짧으면 맥락 파악 어려움
- **실용성**: 10-15개 주제로 나뉘는 최적 값

#### 3.6 drop_ratio=0.65 선택
```python
drop_ratio: float = 0.65
```

**이유:**
- **엄격함**: 35% 이상 유사도 감소 시에만 경계 인식
- **실험 결과**: 0.8은 너무 관대 (100+ 단락), 0.5는 너무 엄격 (5개 이하)
- **균형**: 대부분의 인터뷰/강의에서 10-15개 주제로 수렴

---

## 4. speaker_detection.py - 화자 인식

### 사용된 기법

#### 4.1 패턴 매칭 기반 감지
```python
match = re.match(r'^([A-Z][^:]{0,30}):\s*(.+)', text)
```

**이유:**
- **단순함**: 복잡한 ML 모델 불필요
- **효과적**: YouTube 자막의 일반적인 화자 표기 패턴
- **빠름**: 정규식 매칭은 매우 빠름

#### 4.2 약어 정규화 (Initials Matching)
```python
if len(speaker) <= 3 and speaker.isupper():
    # Match "CA" to "Chris Anderson"
```

**이유:**
- **실제 사용 패턴**: 인터뷰에서 약어 사용 빈번
- **자동 매칭**: 이니셜과 전체 이름 자동 연결
- **편의성**: 수동 매핑 불필요

#### 4.3 전방 전파 (Forward Propagation)
```python
current_speaker = seg.get('speaker', current_speaker)
```

**이유:**
- **컨텍스트 유지**: 화자 변경 전까지 동일 화자로 가정
- **자막 특성**: 모든 문장에 화자 표기 안 됨
- **실용성**: 대부분의 경우 정확

---

## 5. output.py - 출력 형식

### 사용된 기법

#### 5.1 다중 형식 지원 (CSV, TXT, JSON)
```python
def save_all_outputs(...)
```

**이유:**
- **유연성**: 다양한 사용 사례 지원
  - CSV: 데이터 분석 (Excel, pandas)
  - TXT: 읽기 (사람)
  - JSON: API 통합 (프로그래밍)
- **분리**: 각 형식별 독립적인 함수

#### 5.2 UTF-8-BOM 인코딩 (CSV)
```python
df.to_csv(output_path, encoding="utf-8-sig")
```

**이유:**
- **Excel 호환**: BOM으로 Excel이 UTF-8 자동 인식
- **한글 지원**: 다국어 문자 정확히 표현
- **범용성**: 대부분의 도구에서 호환

#### 5.3 파일명 정제 (Sanitize)
```python
title = re.sub(r'[<>:"/\\|?*]', '', title)
title = title[:100]
```

**이유:**
- **OS 호환성**: Windows/Mac/Linux 모두 지원
- **안정성**: 특수문자로 인한 파일 생성 오류 방지
- **길이 제한**: 파일 시스템 제한 고려

#### 5.4 메타데이터 헤더
```python
f.write(f"Video: {video_info['title']}\n")
f.write(f"URL: {video_info['url']}\n")
```

**이유:**
- **추적성**: 원본 영상 정보 보존
- **재현성**: URL로 다시 접근 가능
- **편의성**: 파일만 봐도 출처 확인

---

## 6. pipeline.py - 파이프라인 오케스트레이션

### 사용된 기법

#### 6.1 순차적 단계 처리
```python
# Step 1 → Step 2 → Step 3 → ...
```

**이유:**
- **명확성**: 각 단계가 독립적이고 이해하기 쉬움
- **디버깅**: 어느 단계에서 실패했는지 명확
- **확장성**: 새 단계 추가 용이

#### 6.2 Optional Features (use_semantic, with_speakers)
```python
def process_video(..., use_semantic=True, with_speakers=False)
```

**이유:**
- **유연성**: 필요한 기능만 활성화
- **성능**: 불필요한 계산 회피
- **의존성**: 선택적 라이브러리 설치 허용

#### 6.3 임시 파일 자동 정리
```python
try:
    os.remove(vtt_path)
except:
    pass
```

**이유:**
- **디스크 관리**: 불필요한 파일 자동 삭제
- **안정성**: 삭제 실패해도 프로그램 계속 진행
- **사용자 경험**: 수동 정리 불필요

#### 6.4 진행 상황 출력
```python
print("🧠 Performing semantic segmentation...")
print(f"   ✅ Created {len(paragraphs)} semantic paragraphs")
```

**이유:**
- **피드백**: 사용자에게 진행 상황 알림
- **신뢰**: 프로그램이 멈춘 게 아님을 확인
- **디버깅**: 문제 발생 시 어느 단계인지 파악

---

## 7. main.py - CLI 진입점

### 사용된 기법

#### 7.1 최소한의 코드
```python
if __name__ == "__main__":
    # argument parsing
    process_video(video_url, output_dir, ...)
```

**이유:**
- **단일 책임**: CLI만 담당, 비즈니스 로직은 분리
- **테스트 용이성**: 파이프라인 독립적으로 테스트 가능
- **재사용성**: 다른 인터페이스 쉽게 추가 가능

#### 7.2 절대 경로 계산
```python
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(current_dir, "data")
```

**이유:**
- **이식성**: 어디서 실행해도 올바른 경로
- **예측 가능성**: 항상 같은 위치에 저장
- **사용자 경험**: 파일 찾기 쉬움

#### 7.3 도움말 우선 표시
```python
if len(sys.argv) < 2:
    print("Usage: ...")
    sys.exit(1)
```

**이유:**
- **학습 곡선**: 잘못 사용 시 즉시 올바른 방법 제시
- **자기 문서화**: 별도 매뉴얼 읽지 않아도 사용법 파악
- **표준 관행**: Unix 철학 준수

---

## 8. 전체 시스템 설계 원칙

### 8.1 모듈화 (Modularity)
**이유:**
- 각 모듈이 독립적으로 테스트 가능
- 기능 추가/수정 시 영향 범위 최소화
- 코드 재사용성 극대화

### 8.2 Graceful Degradation
**이유:**
- sentence-transformers 없어도 기본 기능 동작
- 화자 감지 실패해도 텍스트 추출은 성공
- 사용자가 선택적으로 기능 활성화

### 8.3 사용자 중심 설계
**이유:**
- 기술적 완벽성보다 실용성 우선
- 10-15개 단락 = 인간이 인식하는 주제 단위
- 진행 상황 표시 = 사용자 불안감 해소

### 8.4 성능과 품질의 균형
**이유:**
- 임베딩 모델: 정확도와 속도 모두 고려
- 전처리: 필수적인 것만 수행
- 메모리: 전체 텍스트 로드하지만 스트리밍 가능하게 구조화

---

## 9. 알려진 한계와 트레이드오프

### 9.1 영어만 지원
**이유:**
- 초기 버전의 범위 제한
- 다국어 지원은 복잡도 크게 증가
- 영어 자막이 가장 흔함

### 9.2 CPU 기반 추론
**이유:**
- GPU 의존성 없이 동작
- 대부분의 환경에서 실행 가능
- 30초 정도 추가 시간은 허용 가능

### 9.3 고정된 파라미터
**이유:**
- 일반 사용자는 조정 불필요
- 개발자는 코드 수정으로 변경 가능
- 대부분의 경우 기본값이 최적

---

## 결론

이 프로젝트의 모든 기술적 결정은:
1. **실용성** - 실제 사용 가능한 솔루션
2. **단순성** - 복잡하지 않은 구현
3. **확장성** - 미래 개선 가능
4. **사용자 경험** - 직관적이고 신뢰할 수 있는 도구

의 균형을 맞추기 위해 이루어졌습니다.
