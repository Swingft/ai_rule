"""
main.py

엄격한 AI-Rule 검증 시스템 메인 실행 파일
"""

import json
import argparse
from pathlib import Path

from config.settings import *
from verifiers import StrictVerifier


def load_ast_data(ast_json_path: Path) -> dict:
    """AST JSON 파일 로드"""
    with open(ast_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_llm_identifiers(identifiers_json_path: Path) -> list:
    """LLM 예측 식별자 로드"""
    with open(identifiers_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("identifiers", [])


def print_results(results, exclusions):
    """결과 출력"""
    print("\n" + "=" * 70)
    print("📊 검증 결과")
    print("=" * 70)
    
    total = len(results)
    found = sum(1 for r in results if r.found_in_ast)
    rule_matched = sum(1 for r in results if r.rule_matches)
    
    print(f"\n✓ 총 LLM 예측: {total}개")
    print(f"✓ AST 매칭: {found}/{total}개 ({found/total*100:.1f}%)")
    print(f"✓ Rule 매칭: {rule_matched}/{found}개 ({rule_matched/found*100:.1f}% if found > 0 else 0%)")
    print(f"\n🎯 최종 제외 식별자: {len(exclusions)}개")
    
    if exclusions:
        print("\n" + "=" * 70)
        print("제외 식별자 목록:")
        print("=" * 70)
        
        for identifier in exclusions:
            result = next(r for r in results if r.identifier == identifier)
            matched_rules = [m.rule_id for m in result.rule_matches]
            
            print(f"\n• {identifier}")
            print(f"  Rules: {', '.join(matched_rules)}")
            print(f"  Reasoning: {result.reasoning}")
    
    # 통계
    print("\n" + "=" * 70)
    print("통계:")
    print("=" * 70)
    hallucinations = total - found
    print(f"• LLM 환각 (AST 미존재): {hallucinations}개 ({hallucinations/total*100:.1f}%)")
    print(f"• Rule 미매칭 (근거 부족): {found - rule_matched}개")
    print(f"• 검증 통과 (제외 확정): {len(exclusions)}개")


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(
        description="엄격한 AI-Rule 검증 시스템"
    )
    parser.add_argument(
        '--ast',
        type=str,
        required=True,
        help='AST JSON 파일 경로'
    )
    parser.add_argument(
        '--identifiers',
        type=str,
        required=True,
        help='LLM 예측 식별자 JSON 파일 경로'
    )
    parser.add_argument(
        '--rules',
        type=str,
        default=str(RULES_YAML),
        help='Rule YAML 파일 경로'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='결과 저장 경로'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=MIN_CONFIDENCE,
        help='최소 신뢰도 (기본: 1.0 - Rule 매칭 필수)'
    )
    
    args = parser.parse_args()
    
    # 파일 확인
    ast_path = Path(args.ast)
    identifiers_path = Path(args.identifiers)
    rules_path = Path(args.rules)
    
    if not ast_path.exists():
        print(f"❌ AST 파일 없음: {ast_path}")
        return 1
    
    if not identifiers_path.exists():
        print(f"❌ 식별자 파일 없음: {identifiers_path}")
        return 1
    
    if not rules_path.exists():
        print(f"❌ Rule 파일 없음: {rules_path}")
        return 1
    
    # 데이터 로드
    print("\n🔍 데이터 로드 중...")
    ast_data = load_ast_data(ast_path)
    llm_identifiers = load_llm_identifiers(identifiers_path)
    
    print(f"✓ AST 로드 완료")
    print(f"✓ LLM 예측 {len(llm_identifiers)}개 로드")
    
    # 검증 실행
    print("\n" + "=" * 70)
    print("🚀 엄격한 검증 시작")
    print("=" * 70)
    
    verifier = StrictVerifier(rules_path)
    results = verifier.verify(
        ast_data=ast_data,
        llm_identifiers=llm_identifiers,
        min_confidence=args.min_confidence
    )
    
    # 최종 제외 식별자
    exclusions = verifier.get_final_exclusions(results, args.min_confidence)
    
    # 결과 출력
    print_results(results, exclusions)
    
    # 리포트 생성 및 저장
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = RESULTS_DIR / f"{ast_path.stem}_verification.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = verifier.generate_report(results, output_path)
    
    print(f"\n💾 상세 리포트 저장: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
