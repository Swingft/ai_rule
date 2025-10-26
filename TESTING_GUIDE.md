# 🧪 ai_rule 테스트 가이드

## 📋 테스트 종류

### 1. 단위 테스트 (Unit Tests)
**대상**: 개별 컴포넌트 (ConditionMatcher, RuleEngine, Verifier)
**변경**: 없음 ✅

### 2. 통합 테스트 (Integration Tests)
**대상**: 전체 시스템 (병렬 처리, AST 추출, 검증)
**변경**: 새로 추가 ✅

---

## ⚡ 빠른 테스트

### 모든 테스트 실행

```bash
cd ai_rule

# 1. 단위 테스트
python tests/test_rules.py

# 2. 통합 테스트
python tests/test_parallel.py
```

---

## 🧪 1. 단위 테스트 (기존)

### 실행
```bash
python tests/test_rules.py
```

### 테스트 내용
- ✅ ConditionMatcher: 조건식 평가
- ✅ RuleEngine: Rule 매칭
- ✅ StrictVerifier: 식별자 검증

### 예상 출력
```
============================================================
테스트 시작
============================================================

=== Condition Matcher 테스트 ===
Test 1 - contains_any: True
Test 2 - in: True
Test 3 - ==: True
Test 4 - typeInheritanceChain: True
✅ Condition Matcher 테스트 통과!

=== Rule Engine 테스트 ===
Symbol 1 매칭: 2개 Rule
Symbol 2 매칭: 0개 Rule
✅ Rule Engine 테스트 통과!

=== Verifier 테스트 ===
검증 결과: 3개
최종 제외: ['viewDidLoad']
✅ Verifier 테스트 통과!

============================================================
✅ 모든 테스트 통과!
============================================================
```

---

## 🚀 2. 통합 테스트 (새로 추가)

### 실행
```bash
python tests/test_parallel.py
```

### 테스트 내용
- ✅ Swift 프로젝트 자동 생성
- ✅ LLM 예측 JSON 생성
- ✅ 병렬 처리 실행
- ✅ 결과 검증

### 예상 출력
```
======================================================================
🧪 ai_rule 통합 테스트
======================================================================

🧪 병렬 처리 통합 테스트
======================================================================

📁 테스트 프로젝트 생성 중...
✓ 생성: /tmp/tmpxxx
✓ Swift 파일: 3개
  - ViewController.swift
  - Model.swift
  - Service.swift

📝 LLM 예측 생성 중...
✓ 생성: /tmp/tmpxxx/predictions.json

🔧 SwiftASTAnalyzer 확인 중...
✓ 발견: SwiftASTAnalyzer/.build/release/SwiftASTAnalyzer

🚀 병렬 처리 실행 중...
실행: python main.py --project /tmp/tmpxxx --identifiers ...

======================================================================
📊 실행 결과:
======================================================================
[1/3] 처리 중: ViewController.swift
  ✓ 완료: 1개 제외
[2/3] 처리 중: Model.swift
  ✓ 완료: 3개 제외
[3/3] 처리 중: Service.swift
  ✓ 완료: 0개 제외

======================================================================
📊 전체 검증 결과
======================================================================
✓ 총 파일: 3개
✓ 성공: 3개
✓ 실패: 0개
...

🔍 결과 검증 중...
✓ 결과 파일 로드 완료

📈 검증 통계:
  - 총 파일: 3
  - 성공: 3
  - 실패: 0
  - 처리 시간: 2.34초
  - 속도: 1.28 files/sec

✅ 모든 검증 통과!

🧹 임시 파일 정리 중...
✓ 삭제: /tmp/tmpxxx

======================================================================
✅ 통합 테스트 통과!
======================================================================
```

---

## 🔧 수동 테스트

### Step 1: 테스트 프로젝트 준비

```bash
# 테스트 디렉토리 생성
mkdir -p test_project

# Swift 파일 생성
cat > test_project/Test.swift << 'EOF'
import UIKit

class TestViewController: UIViewController {
    @objc func viewDidLoad() {
        super.viewDidLoad()
    }
}
EOF
```

### Step 2: LLM 예측 생성

```bash
cat > test_predictions.json << 'EOF'
{
  "identifiers": ["viewDidLoad", "customMethod"]
}
EOF
```

### Step 3: 실행

```bash
python main.py \
  --project test_project \
  --identifiers test_predictions.json \
  --output test_result.json
```

### Step 4: 결과 확인

```bash
# 요약 보기
cat test_result.json | jq '.total_files, .success_files'

# 제외 식별자 보기
cat test_result.json | jq '.results[].exclusions[]'
```

---

## 🐛 문제 해결

### Q: "SwiftASTAnalyzer 없음" 에러

**통합 테스트 전 필수**:
```bash
cd SwiftASTAnalyzer
swift build -c release
cd ..
```

### Q: 단위 테스트는 통과, 통합 테스트 실패

**원인**: SwiftASTAnalyzer 미빌드

**해결**:
```bash
cd SwiftASTAnalyzer
swift build -c release
cd ..
python tests/test_parallel.py
```

### Q: 통합 테스트 타임아웃

**원인**: 시스템이 느림

**해결**:
```python
# tests/test_parallel.py 수정
result = subprocess.run(..., timeout=120)  # 60 → 120
```

---

## 📊 테스트 체크리스트

### 개발 시
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] SwiftASTAnalyzer 빌드 완료

### 배포 전
- [ ] 모든 테스트 통과
- [ ] 실제 프로젝트로 수동 테스트
- [ ] 성능 확인 (files/sec)

### CI/CD
```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: python tests/test_rules.py

- name: Build SwiftASTAnalyzer
  run: cd SwiftASTAnalyzer && swift build -c release

- name: Run integration tests
  run: python tests/test_parallel.py
```

---

## ✅ 요약

| 테스트 | 명령어 | 빌드 필요 | 시간 |
|--------|--------|----------|------|
| 단위 | `python tests/test_rules.py` | ❌ | ~1초 |
| 통합 | `python tests/test_parallel.py` | ✅ | ~5초 |

**순서**:
1. 단위 테스트 먼저 (빠름)
2. SwiftASTAnalyzer 빌드
3. 통합 테스트 (느림)

---

**버전**: 2.0.0  
**작성**: 2025-01-26  
**상태**: 테스트 완료 ✅
