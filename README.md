# Strict AI-Rule Verifier

LLM 예측 식별자를 **엄격한 AST 기반 Rule**로 검증하는 시스템

## 🎯 핵심 원칙

### 1. **엄격한 Rule 매칭**
- YAML Rule의 조건식을 **정확히** 평가
- 휴리스틱 X, AST 데이터와 **1:1 매칭**만
- 모든 조건 만족 시에만 True (AND 로직)

### 2. **명확한 근거**
- Rule 매칭 = 제외 근거 명확
- Rule 미매칭 = 제외 근거 부족 → 제외하지 않음

### 3. **LLM의 역할**
- **후보 생성기** (넓게 예측)
- Rule이 최종 판단 (좁게 필터링)

---

## 📂 프로젝트 구조

```
ai_rule/
├── core/
│   ├── __init__.py
│   ├── condition_matcher.py    # 조건식 평가 엔진
│   └── rule_engine.py           # Rule 평가 엔진
├── verifiers/
│   ├── __init__.py
│   └── strict_verifier.py       # LLM 예측 검증기
├── config/
│   ├── __init__.py
│   └── settings.py              # 설정
├── rules/
│   └── swift_exclusion_rules.yaml  # ← Rule 파일
├── data/
│   ├── identifiers/             # LLM 예측 식별자
│   └── results/                 # 검증 결과
├── tests/
│   └── test_rules.py            # 테스트
├── main.py                      # 메인 실행 파일
├── requirements.txt
└── README.md
```

---

## ⚡ 빠른 시작

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. 테스트
```bash
python tests/test_rules.py
```

**예상 출력:**
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
  - TEST_OBJC_ATTRIBUTE: True
  - TEST_LIFECYCLE_METHOD: True

Symbol 2 매칭: 0개 Rule

✅ Rule Engine 테스트 통과!


=== Verifier 테스트 ===

검증 결과: 3개
  - viewDidLoad: AST=True, Rule=True, Decision=True
  - customMethod: AST=True, Rule=False, Decision=False
  - nonExistent: AST=False, Rule=False, Decision=False

최종 제외: ['viewDidLoad']

✅ Verifier 테스트 통과!

============================================================
✅ 모든 테스트 통과!
============================================================
```

### 3. 실제 사용
```bash
python main.py \
  --ast /path/to/ast.json \
  --identifiers /path/to/predictions.json
```

---

## 📝 입력 파일 형식

### 1. AST JSON (Swift AST Analyzer 출력)

```json
{
  "symbols": [
    {
      "symbol_name": "viewDidLoad",
      "symbol_kind": "method",
      "access_level": "internal",
      "attributes": ["@objc"],
      "inherits": ["UIViewController"],
      "modifiers": ["override"]
    }
  ]
}
```

### 2. LLM 예측 식별자 JSON

```json
{
  "identifiers": [
    "viewDidLoad",
    "tableView",
    "delegate",
    "customMethod"
  ]
}
```

### 3. Rule YAML

```yaml
rules:
- id: OBJC_ATTRIBUTE
  description: Symbols exposed to Objective-C runtime
  pattern:
  - find:
      target: S
  - where:
    - S.attributes contains_any ['@objc', '@objcMembers']
```

---

## 🎯 사용법

### 기본 실행

```bash
python main.py \
  --ast data/ast/example.json \
  --identifiers data/identifiers/predictions.json
```

### 전체 옵션

```bash
python main.py \
  --ast data/ast/example.json \
  --identifiers data/identifiers/predictions.json \
  --rules rules/swift_exclusion_rules.yaml \
  --output results/verification.json \
  --min-confidence 1.0
```

### 출력 예시

```
====================================================================
🚀 엄격한 검증 시작
====================================================================

====================================================================
📊 검증 결과
====================================================================

✓ 총 LLM 예측: 15개
✓ AST 매칭: 12/15개 (80.0%)
✓ Rule 매칭: 8/12개 (66.7%)

🎯 최종 제외 식별자: 8개

====================================================================
제외 식별자 목록:
====================================================================

• viewDidLoad
  Rules: SYSTEM_LIFECYCLE_METHODS
  Reasoning: Matched 1 strict rule(s): SYSTEM_LIFECYCLE_METHODS

• tableView
  Rules: UI_FRAMEWORK_SUBCLASSES
  Reasoning: Matched 1 strict rule(s): UI_FRAMEWORK_SUBCLASSES

====================================================================
통계:
====================================================================
• LLM 환각 (AST 미존재): 3개 (20.0%)
• Rule 미매칭 (근거 부족): 4개
• 검증 통과 (제외 확정): 8개

💾 상세 리포트 저장: data/results/example_verification.json
```

---

## 📄 출력 파일 (verification.json)

```json
{
  "summary": {
    "total_llm_predictions": 15,
    "found_in_ast": 12,
    "rule_matched": 8,
    "final_exclusions": 8,
    "hallucination_rate": "20.0%",
    "rule_match_rate": "66.7%"
  },
  "exclusions": [
    "viewDidLoad",
    "tableView",
    "delegate"
  ],
  "details": [
    {
      "identifier": "viewDidLoad",
      "found_in_ast": true,
      "rule_matched": true,
      "matched_rules": ["SYSTEM_LIFECYCLE_METHODS"],
      "final_decision": true,
      "confidence": 1.0,
      "reasoning": "Matched 1 strict rule(s): SYSTEM_LIFECYCLE_METHODS"
    }
  ]
}
```

---

## 🔍 지원하는 조건식

### 1. contains_any
```yaml
S.attributes contains_any ['@objc', '@objcMembers']
```
→ `symbol['attributes']`에 '@objc' 또는 '@objcMembers' 있는지

### 2. in
```yaml
M.name in ['viewDidLoad', 'viewWillAppear']
```
→ `symbol['symbol_name']`이 리스트에 있는지

### 3. == (등호)
```yaml
P.kind == 'property'
```
→ `symbol['symbol_kind'] == 'property'`

### 4. != (부등호)
```yaml
M.kind != 'method'
```
→ `symbol['symbol_kind'] != 'method'`

---

## 🎨 핵심 특징

### 1. **엄격한 평가**
```python
# ❌ 휴리스틱 (이전)
if 'objc' in rule_description:
    return True

# ✅ 엄격 (현재)
if '@objc' in symbol['attributes']:
    return True  # 정확한 매칭만
```

### 2. **AND 로직**
```yaml
- where:
  - M.name == 'viewDidLoad'
  - M.typeInheritanceChain contains_any ['UIViewController']
```
→ **두 조건 모두** 만족해야 True

### 3. **신뢰도 = 1.0 or 0.0**
- Rule 매칭 성공 = 1.0 (확실함)
- Rule 매칭 실패 = 0.0 (근거 없음)
- **중간값 없음** (엄격)

---

## ⚙️ 설정

### config/settings.py

```python
MIN_CONFIDENCE = 1.0  # 엄격: Rule 매칭 필수
STRICT_MODE = True
DEBUG = False
```

---

## 🎯 사용 시나리오

### Scenario 1: 대량 프로젝트 검증

```bash
# GPU 서버: LLM 추론 (오래 걸림)
gpu> python inference.py --projects 1000

# 로컬: 엄격한 검증 (빠름)
for project in projects:
    python main.py \
      --ast $project/ast.json \
      --identifiers $project/predictions.json
```

### Scenario 2: CI/CD 통합

```yaml
# .github/workflows/verify.yml
- name: Verify exclusions
  run: |
    python main.py \
      --ast build/ast.json \
      --identifiers model/predictions.json \
      --min-confidence 1.0
```

---

## 💡 LLM vs Rule 비교

| 항목 | LLM | Rule (엄격) |
|------|-----|-------------|
| 역할 | 후보 생성 | 최종 판단 |
| 목표 | Recall (넓게) | Precision (좁게) |
| 신뢰도 | 0.0 ~ 1.0 | 1.0 or 0.0 |
| 속도 | 느림 (GPU) | 빠름 (로컬) |
| 근거 | 암묵적 | 명시적 |

---

## 📦 의존성

```bash
pip install pyyaml
```

---

## 🎉 핵심 장점

1. **엄격성**: 휴리스틱 없음, 정확한 매칭만
2. **투명성**: Rule 매칭 과정 추적 가능
3. **속도**: 로컬에서 실시간 처리
4. **확장성**: YAML Rule 추가만으로 확장
5. **신뢰성**: 명확한 근거 기반 결정

---

## 📚 관련 문서

- **QUICKSTART.md**: 빠른 시작 가이드
- **tests/test_rules.py**: 테스트 코드 예시
- **core/condition_matcher.py**: 조건식 평가 로직
- **core/rule_engine.py**: Rule 엔진 코어

---

**프로젝트**: ai_rule  
**버전**: 1.0.0  
**날짜**: 2025-01-26  
**상태**: 프로토타입 (테스트 통과) ✅
