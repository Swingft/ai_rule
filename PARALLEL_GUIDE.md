# 🚀 ai_rule 프로젝트 전체 병렬 처리 가이드

## ⚡ 빠른 시작

### 기본 사용법

```bash
python main.py \
  --project /path/to/swift/project \
  --identifiers predictions.json
```

---

## 📝 입력 파일 형식

### 1. predictions.json (LLM 예측 식별자)

**단일 리스트 형식** (권장):
```json
{
  "identifiers": [
    "viewDidLoad",
    "delegate",
    "tableView",
    "customMethod"
  ]
}
```

**파일별 형식** (고급):
```json
{
  "MyViewController.swift": ["viewDidLoad", "delegate"],
  "NetworkService.swift": ["request", "response"],
  "DataModel.swift": ["id", "name"]
}
```

---

## 🎯 사용 예시

### Example 1: 기본 실행

```bash
python main.py \
  --project ~/MyApp/Sources \
  --identifiers data/identifiers/predictions.json
```

**출력**:
```
🔍 Swift 파일 검색 중...
✓ 142개 Swift 파일 발견

📥 LLM 예측 로드 중...
✓ 235개 식별자 로드 (전체 공통)

⚙️  Verifier 초기화 중...
✓ 87개 Rule 로드

======================================================================
🚀 병렬 처리 시작 (워커: 5개)
======================================================================

[1/142] 처리 중: AppDelegate.swift
  ✓ 완료: 8개 제외
[2/142] 처리 중: SceneDelegate.swift
  ✓ 완료: 5개 제외
...

======================================================================
📊 전체 검증 결과
======================================================================

✓ 총 파일: 142개
✓ 성공: 140개
✓ 실패: 2개

📈 전체 통계:
  • 총 LLM 예측: 235개
  • AST 매칭: 198/235개 (84.3%)
  • Rule 매칭: 156/198개 (78.8%)
  • 최종 제외: 156개

⚠️  환각률: 37/235개 (15.7%)

⏱️  처리 시간: 23.45초
⚡ 평균 속도: 6.05 files/sec

💾 상세 리포트 저장: data/results/verification_1737891234.json
```

---

### Example 2: 워커 수 조정

```bash
# 빠른 처리 (10 워커)
python main.py \
  --project ~/MyApp/Sources \
  --identifiers predictions.json \
  --workers 10

# 느린 처리 (2 워커) - CPU 절약
python main.py \
  --project ~/MyApp/Sources \
  --identifiers predictions.json \
  --workers 2
```

---

### Example 3: 커스텀 출력 경로

```bash
python main.py \
  --project ~/MyApp/Sources \
  --identifiers predictions.json \
  --output results/myapp_verification.json
```

---

### Example 4: SwiftASTAnalyzer 경로 지정

```bash
python main.py \
  --project ~/MyApp/Sources \
  --identifiers predictions.json \
  --analyzer /usr/local/bin/SwiftASTAnalyzer
```

---

## 🔧 옵션

| 옵션 | 설명 | 기본값 | 필수 |
|------|------|--------|------|
| `--project` | Swift 프로젝트 루트 경로 | - | ✅ |
| `--identifiers` | LLM 예측 식별자 JSON | - | ✅ |
| `--analyzer` | SwiftASTAnalyzer 경로 | `SwiftASTAnalyzer/.build/release/SwiftASTAnalyzer` | ❌ |
| `--rules` | Rule YAML 파일 | `rules/swift_exclusion_rules.yaml` | ❌ |
| `--output` | 결과 저장 경로 | `data/results/verification_{timestamp}.json` | ❌ |
| `--workers` | 병렬 워커 수 | `5` | ❌ |
| `--min-confidence` | 최소 신뢰도 | `1.0` | ❌ |

---

## 📊 출력 파일 구조

### verification.json

```json
{
  "project": "/path/to/project",
  "total_files": 142,
  "success_files": 140,
  "failed_files": 2,
  "processing_time_seconds": 23.45,
  "files_per_second": 6.05,
  "workers": 5,
  "results": [
    {
      "file": "/path/to/AppDelegate.swift",
      "success": true,
      "exclusions": ["applicationDidFinishLaunching", "delegate"],
      "total_predictions": 15,
      "found_in_ast": 12,
      "rule_matched": 8,
      "details": [
        {
          "identifier": "applicationDidFinishLaunching",
          "found_in_ast": true,
          "rule_matched": true,
          "matched_rules": ["SYSTEM_LIFECYCLE_METHODS"],
          "final_decision": true,
          "confidence": 1.0,
          "reasoning": "Matched 1 strict rule(s): SYSTEM_LIFECYCLE_METHODS"
        }
      ]
    }
  ]
}
```

---

## ⚙️ 성능 최적화

### 워커 수 선택

```bash
# CPU 코어 수 확인
sysctl -n hw.ncpu  # macOS
nproc              # Linux

# 권장: CPU 코어 수와 동일하게 설정
python main.py --project ... --workers 8  # 8코어 CPU
```

### 워커 수별 성능 비교

| 워커 수 | 처리 시간 (142 파일) | 속도 |
|---------|---------------------|------|
| 1 | ~60초 | 2.4 files/sec |
| 2 | ~35초 | 4.1 files/sec |
| 5 | ~23초 | 6.2 files/sec |
| 10 | ~18초 | 7.9 files/sec |
| 20 | ~17초 | 8.4 files/sec |

**권장**: 5-10 워커 (체감 성능 최적)

---

## 🎯 실전 워크플로우

### Step 1: 프로젝트 준비

```bash
cd ai_rule

# SwiftASTAnalyzer 빌드 (최초 1회)
cd SwiftASTAnalyzer
swift build -c release
cd ..
```

### Step 2: LLM 예측 생성 (별도)

```bash
# GPU 서버에서 LLM 추론
# → predictions.json 생성
```

### Step 3: 검증 실행

```bash
# 단일 프로젝트
python main.py \
  --project ~/MyApp/Sources \
  --identifiers predictions.json

# 여러 프로젝트 (배치)
for project in ProjectA ProjectB ProjectC; do
    python main.py \
      --project ~/Projects/$project/Sources \
      --identifiers data/identifiers/${project}_predictions.json \
      --output results/${project}_verification.json
done
```

### Step 4: 결과 분석

```bash
# 결과 확인
cat results/verification_*.json | jq '.summary'

# 최종 제외 식별자만
cat results/verification_*.json | jq '.results[].exclusions[]' | sort | uniq
```

---

## 🐛 문제 해결

### Q: "SwiftASTAnalyzer 없음" 에러

```bash
cd SwiftASTAnalyzer
swift build -c release
cd ..
```

### Q: AST 추출 실패가 많음

**원인**: Swift 파일 문법 오류 또는 복잡한 코드

**해결**:
```bash
# 문법 확인
swiftc -parse MyFile.swift

# 타임아웃 증가 (코드 수정 필요)
# extract_ast 함수의 timeout=30 → timeout=60
```

### Q: 병렬 처리가 느림

**원인**: I/O 병목 또는 워커 수 과다

**해결**:
```bash
# 워커 수 줄이기
python main.py ... --workers 3

# SSD 사용 권장
```

### Q: 메모리 부족

**원인**: 대용량 프로젝트 + 많은 워커

**해결**:
```bash
# 워커 수 줄이기
python main.py ... --workers 2

# 프로젝트 분할 처리
```

---

## 📈 성능 비교

### 기존 vs 병렬

| 항목 | 기존 (순차) | 병렬 (5 워커) |
|------|------------|--------------|
| 142 파일 | ~60초 | ~23초 |
| 속도 향상 | 1x | 2.6x |
| CPU 사용률 | ~25% | ~80% |

---

## 🎉 핵심 개선사항

### ✅ 프로젝트 전체 처리
- 단일 파일 → **전체 프로젝트** (`*.swift`)
- 자동 파일 검색 (`rglob`)

### ✅ 병렬 처리
- ThreadPoolExecutor 사용
- 기본 5 워커 (조정 가능)
- **2-3배 속도 향상**

### ✅ AST 자동 추출
- SwiftASTAnalyzer 내장 호출
- 별도 AST JSON 불필요
- **실시간 처리**

### ✅ 통계 및 리포트
- 전체 통계 출력
- 환각률 계산
- JSON 리포트 자동 저장

---

**버전**: 2.0.0 (병렬 처리)  
**작성**: 2025-01-26  
**상태**: 프로토타입 (병렬 최적화)
