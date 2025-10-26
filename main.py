"""
main.py

엄격한 AI-Rule 검증 시스템 - 프로젝트 전체 병렬 처리
"""

import json
import argparse
import subprocess
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

from config.settings import *
from verifiers import StrictVerifier


def find_swift_files(project_path: Path) -> List[Path]:
    """
    프로젝트에서 모든 Swift 파일 찾기
    
    Args:
        project_path: 프로젝트 루트 경로
    
    Returns:
        Swift 파일 경로 리스트
    """
    return sorted(project_path.rglob("*.swift"))


def extract_ast(swift_file: Path, analyzer_path: Path) -> Optional[Dict]:
    """
    SwiftASTAnalyzer로 AST 추출
    
    Args:
        swift_file: Swift 파일 경로
        analyzer_path: SwiftASTAnalyzer 실행 파일 경로
    
    Returns:
        AST 데이터 또는 None
    """
    try:
        result = subprocess.run(
            [str(analyzer_path), str(swift_file)],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            return None
        
        output = result.stdout.strip()
        
        # JSON 파싱
        start_idx = output.find('{')
        if start_idx == -1:
            return None
        
        json_str = output[start_idx:]
        ast_data = json.loads(json_str)
        
        # SwiftASTAnalyzer 출력 구조 처리
        if isinstance(ast_data, dict) and "decisions" in ast_data:
            # decisions를 symbols로 변환
            decisions = ast_data["decisions"]
            symbols = []
            
            for category in ["classes", "structs", "enums", "protocols",
                            "methods", "properties", "variables", "enumCases",
                            "initializers", "deinitializers", "subscripts", "extensions"]:
                if category in decisions and isinstance(decisions[category], list):
                    symbols.extend(decisions[category])
            
            return {"symbols": symbols}
        
        return ast_data
        
    except Exception as e:
        print(f"  ⚠️  AST 추출 실패: {swift_file.name} - {e}")
        return None


def load_llm_identifiers(identifiers_json_path: Path) -> Dict[str, List[str]]:
    """
    LLM 예측 식별자 로드 (파일별)
    
    Args:
        identifiers_json_path: 식별자 JSON 파일 경로
    
    Returns:
        {파일명: [식별자...]} 딕셔너리
    """
    with open(identifiers_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        # 단일 리스트 형식
        if "identifiers" in data and isinstance(data["identifiers"], list):
            return {"all": data["identifiers"]}
        
        # 파일별 형식
        # {"file1.swift": ["id1", "id2"], "file2.swift": [...]}
        return data


def process_single_file(
    swift_file: Path,
    analyzer_path: Path,
    verifier: StrictVerifier,
    llm_identifiers: List[str],
    file_index: int,
    total_files: int,
    min_confidence: float
) -> Dict:
    """
    단일 Swift 파일 처리
    
    Args:
        swift_file: Swift 파일 경로
        analyzer_path: SwiftASTAnalyzer 경로
        verifier: StrictVerifier 인스턴스
        llm_identifiers: LLM 예측 식별자
        file_index: 파일 인덱스
        total_files: 전체 파일 수
        min_confidence: 최소 신뢰도
    
    Returns:
        검증 결과 딕셔너리
    """
    print(f"[{file_index}/{total_files}] 처리 중: {swift_file.name}")
    
    # AST 추출
    ast_data = extract_ast(swift_file, analyzer_path)
    
    if not ast_data:
        print(f"  ⚠️  AST 추출 실패")
        return {
            "file": str(swift_file),
            "success": False,
            "error": "AST extraction failed"
        }
    
    # 검증
    results = verifier.verify(
        ast_data=ast_data,
        llm_identifiers=llm_identifiers,
        min_confidence=min_confidence
    )
    
    # 최종 제외 식별자
    exclusions = verifier.get_final_exclusions(results, min_confidence)
    
    print(f"  ✓ 완료: {len(exclusions)}개 제외")
    
    return {
        "file": str(swift_file),
        "success": True,
        "exclusions": exclusions,
        "total_predictions": len(results),
        "found_in_ast": sum(1 for r in results if r.found_in_ast),
        "rule_matched": sum(1 for r in results if r.rule_matches),
        "details": [
            {
                "identifier": r.identifier,
                "found_in_ast": r.found_in_ast,
                "rule_matched": len(r.rule_matches) > 0,
                "matched_rules": [m.rule_id for m in r.rule_matches],
                "final_decision": r.final_decision,
                "confidence": r.confidence,
                "reasoning": r.reasoning
            }
            for r in results
        ]
    }


def print_summary(all_results: List[Dict]):
    """전체 결과 요약 출력"""
    print("\n" + "=" * 70)
    print("📊 전체 검증 결과")
    print("=" * 70)
    
    total_files = len(all_results)
    success_files = sum(1 for r in all_results if r.get("success", False))
    failed_files = total_files - success_files
    
    print(f"\n✓ 총 파일: {total_files}개")
    print(f"✓ 성공: {success_files}개")
    print(f"✓ 실패: {failed_files}개")
    
    if success_files > 0:
        # 통계
        total_predictions = sum(r.get("total_predictions", 0) for r in all_results if r.get("success"))
        total_found = sum(r.get("found_in_ast", 0) for r in all_results if r.get("success"))
        total_rule_matched = sum(r.get("rule_matched", 0) for r in all_results if r.get("success"))
        total_exclusions = sum(len(r.get("exclusions", [])) for r in all_results if r.get("success"))
        
        print(f"\n📈 전체 통계:")
        print(f"  • 총 LLM 예측: {total_predictions}개")
        print(f"  • AST 매칭: {total_found}/{total_predictions}개 ({total_found/total_predictions*100:.1f}%)")
        print(f"  • Rule 매칭: {total_rule_matched}/{total_found}개 ({total_rule_matched/total_found*100:.1f}% if total_found > 0 else 0%)")
        print(f"  • 최종 제외: {total_exclusions}개")
        
        # 환각률
        hallucination = total_predictions - total_found
        print(f"\n⚠️  환각률: {hallucination}/{total_predictions}개 ({hallucination/total_predictions*100:.1f}%)")


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(
        description="엄격한 AI-Rule 검증 시스템 - 프로젝트 전체 병렬 처리"
    )
    parser.add_argument(
        '--project',
        type=str,
        required=True,
        help='Swift 프로젝트 루트 경로'
    )
    parser.add_argument(
        '--identifiers',
        type=str,
        required=True,
        help='LLM 예측 식별자 JSON 파일 경로'
    )
    parser.add_argument(
        '--analyzer',
        type=str,
        default='SwiftASTAnalyzer/.build/release/SwiftASTAnalyzer',
        help='SwiftASTAnalyzer 실행 파일 경로'
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
        '--workers',
        type=int,
        default=5,
        help='병렬 처리 워커 수 (기본: 5)'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=MIN_CONFIDENCE,
        help='최소 신뢰도 (기본: 1.0)'
    )
    
    args = parser.parse_args()
    
    # 경로 확인
    project_path = Path(args.project)
    identifiers_path = Path(args.identifiers)
    analyzer_path = Path(args.analyzer)
    rules_path = Path(args.rules)
    
    if not project_path.exists():
        print(f"❌ 프로젝트 경로 없음: {project_path}")
        return 1
    
    if not identifiers_path.exists():
        print(f"❌ 식별자 파일 없음: {identifiers_path}")
        return 1
    
    if not analyzer_path.exists():
        print(f"❌ SwiftASTAnalyzer 없음: {analyzer_path}")
        print(f"   빌드 필요: cd SwiftASTAnalyzer && swift build -c release")
        return 1
    
    if not rules_path.exists():
        print(f"❌ Rule 파일 없음: {rules_path}")
        return 1
    
    # Swift 파일 찾기
    print("\n🔍 Swift 파일 검색 중...")
    swift_files = find_swift_files(project_path)
    
    if not swift_files:
        print(f"❌ Swift 파일 없음: {project_path}")
        return 1
    
    print(f"✓ {len(swift_files)}개 Swift 파일 발견")
    
    # LLM 식별자 로드
    print("\n📥 LLM 예측 로드 중...")
    identifiers_data = load_llm_identifiers(identifiers_path)
    
    # 단일 리스트 또는 파일별 처리
    if "all" in identifiers_data:
        llm_identifiers = identifiers_data["all"]
        print(f"✓ {len(llm_identifiers)}개 식별자 로드 (전체 공통)")
    else:
        # 파일별 식별자 (추후 구현)
        llm_identifiers = []
        for ids in identifiers_data.values():
            llm_identifiers.extend(ids)
        llm_identifiers = list(set(llm_identifiers))
        print(f"✓ {len(llm_identifiers)}개 식별자 로드 (파일별 병합)")
    
    # Verifier 초기화
    print("\n⚙️  Verifier 초기화 중...")
    verifier = StrictVerifier(rules_path)
    print(f"✓ {len(verifier.rule_engine.get_all_rules())}개 Rule 로드")
    
    # 병렬 처리
    print("\n" + "=" * 70)
    print(f"🚀 병렬 처리 시작 (워커: {args.workers}개)")
    print("=" * 70 + "\n")
    
    start_time = time.time()
    all_results = []
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        
        for i, swift_file in enumerate(swift_files, 1):
            future = executor.submit(
                process_single_file,
                swift_file,
                analyzer_path,
                verifier,
                llm_identifiers,
                i,
                len(swift_files),
                args.min_confidence
            )
            futures[future] = swift_file
        
        # 결과 수집
        for future in as_completed(futures):
            result = future.result()
            all_results.append(result)
    
    elapsed_time = time.time() - start_time
    
    # 결과 요약
    print_summary(all_results)
    
    print(f"\n⏱️  처리 시간: {elapsed_time:.2f}초")
    print(f"⚡ 평균 속도: {len(swift_files)/elapsed_time:.2f} files/sec")
    
    # 결과 저장
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = RESULTS_DIR / f"verification_{int(time.time())}.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "project": str(project_path),
        "total_files": len(swift_files),
        "success_files": sum(1 for r in all_results if r.get("success")),
        "failed_files": sum(1 for r in all_results if not r.get("success")),
        "processing_time_seconds": elapsed_time,
        "files_per_second": len(swift_files) / elapsed_time,
        "workers": args.workers,
        "results": all_results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 상세 리포트 저장: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
