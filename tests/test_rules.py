"""
test_rules.py

Rule Engine 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.condition_matcher import ConditionMatcher
from core.rule_engine import RuleEngine


def test_condition_matcher():
    """조건식 매칭 테스트"""
    print("\n=== Condition Matcher 테스트 ===\n")
    
    # 테스트 심볼
    symbol = {
        'symbol_name': 'viewDidLoad',
        'symbol_kind': 'method',
        'attributes': ['@objc', 'override'],
        'inherits': ['UIViewController', 'UIResponder'],
        'modifiers': ['override']
    }
    
    # Test 1: contains_any
    condition1 = "S.attributes contains_any ['@objc', '@objcMembers']"
    result1 = ConditionMatcher.evaluate(condition1, symbol)
    print(f"Test 1 - contains_any: {result1}")
    assert result1 == True, "Expected True"
    
    # Test 2: in
    condition2 = "M.name in ['viewDidLoad', 'viewWillAppear']"
    result2 = ConditionMatcher.evaluate(condition2, symbol)
    print(f"Test 2 - in: {result2}")
    assert result2 == True, "Expected True"
    
    # Test 3: ==
    condition3 = "M.kind == 'method'"
    result3 = ConditionMatcher.evaluate(condition3, symbol)
    print(f"Test 3 - ==: {result3}")
    assert result3 == True, "Expected True"
    
    # Test 4: contains_any (inherits)
    condition4 = "M.typeInheritanceChain contains_any ['UIViewController']"
    result4 = ConditionMatcher.evaluate(condition4, symbol)
    print(f"Test 4 - typeInheritanceChain: {result4}")
    assert result4 == True, "Expected True"
    
    print("\n✅ Condition Matcher 테스트 통과!\n")


def test_rule_engine():
    """Rule Engine 테스트"""
    print("\n=== Rule Engine 테스트 ===\n")
    
    # 간단한 Rule YAML 생성
    import yaml
    import tempfile
    
    test_rules = {
        'rules': [
            {
                'id': 'TEST_OBJC_ATTRIBUTE',
                'description': 'Test @objc attribute',
                'pattern': [
                    {'find': {'target': 'S'}},
                    {'where': ["S.attributes contains_any ['@objc']"]}
                ]
            },
            {
                'id': 'TEST_LIFECYCLE_METHOD',
                'description': 'Test lifecycle method',
                'pattern': [
                    {'find': {'target': 'M'}},
                    {'where': [
                        "M.name in ['viewDidLoad', 'viewWillAppear']",
                        "M.typeInheritanceChain contains_any ['UIViewController']"
                    ]}
                ]
            }
        ]
    }
    
    # 임시 YAML 파일
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_rules, f)
        temp_yaml_path = Path(f.name)
    
    try:
        # Rule Engine 초기화
        engine = RuleEngine(temp_yaml_path)
        
        # 테스트 심볼 1: @objc 메서드
        symbol1 = {
            'symbol_name': 'viewDidLoad',
            'symbol_kind': 'method',
            'attributes': ['@objc', 'override'],
            'inherits': ['UIViewController'],
            'modifiers': ['override']
        }
        
        matches1 = engine.match_symbol(symbol1)
        print(f"Symbol 1 매칭: {len(matches1)}개 Rule")
        for match in matches1:
            print(f"  - {match.rule_id}: {match.matched}")
        
        assert len(matches1) == 2, "Expected 2 rule matches"
        
        # 테스트 심볼 2: 일반 메서드 (Rule 미매칭)
        symbol2 = {
            'symbol_name': 'customMethod',
            'symbol_kind': 'method',
            'attributes': [],
            'inherits': [],
            'modifiers': []
        }
        
        matches2 = engine.match_symbol(symbol2)
        print(f"\nSymbol 2 매칭: {len(matches2)}개 Rule")
        
        assert len(matches2) == 0, "Expected 0 rule matches"
        
        print("\n✅ Rule Engine 테스트 통과!\n")
        
    finally:
        # 임시 파일 삭제
        temp_yaml_path.unlink()


def test_verifier():
    """Verifier 테스트"""
    print("\n=== Verifier 테스트 ===\n")
    
    from verifiers import StrictVerifier
    import yaml
    import tempfile
    
    # 테스트 Rule
    test_rules = {
        'rules': [
            {
                'id': 'TEST_OBJC',
                'description': 'Test',
                'pattern': [
                    {'find': {'target': 'S'}},
                    {'where': ["S.attributes contains_any ['@objc']"]}
                ]
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_rules, f)
        temp_yaml_path = Path(f.name)
    
    try:
        # Verifier 초기화
        verifier = StrictVerifier(temp_yaml_path)
        
        # 테스트 AST
        ast_data = {
            'symbols': [
                {
                    'symbol_name': 'viewDidLoad',
                    'symbol_kind': 'method',
                    'attributes': ['@objc'],
                    'inherits': ['UIViewController']
                },
                {
                    'symbol_name': 'customMethod',
                    'symbol_kind': 'method',
                    'attributes': [],
                    'inherits': []
                }
            ]
        }
        
        # LLM 예측
        llm_identifiers = ['viewDidLoad', 'customMethod', 'nonExistent']
        
        # 검증
        results = verifier.verify(ast_data, llm_identifiers)
        
        print(f"검증 결과: {len(results)}개")
        for r in results:
            print(f"  - {r.identifier}: AST={r.found_in_ast}, Rule={len(r.rule_matches)>0}, Decision={r.final_decision}")
        
        # 최종 제외
        exclusions = verifier.get_final_exclusions(results)
        print(f"\n최종 제외: {exclusions}")
        
        assert len(exclusions) == 1, "Expected 1 exclusion"
        assert 'viewDidLoad' in exclusions, "Expected viewDidLoad"
        
        print("\n✅ Verifier 테스트 통과!\n")
        
    finally:
        temp_yaml_path.unlink()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("테스트 시작")
    print("=" * 60)
    
    test_condition_matcher()
    test_rule_engine()
    test_verifier()
    
    print("=" * 60)
    print("✅ 모든 테스트 통과!")
    print("=" * 60)
