"""
strict_verifier.py

LLM 예측 식별자를 AST + 엄격한 Rule로 검증
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from core.rule_engine import RuleEngine, RuleMatch


@dataclass
class VerificationResult:
    """검증 결과"""
    identifier: str
    found_in_ast: bool
    ast_symbol: Optional[Dict]
    rule_matches: List[RuleMatch]
    final_decision: bool  # True: 제외, False: 제외하지 않음
    confidence: float
    reasoning: str


class StrictVerifier:
    """엄격한 LLM 예측 검증기"""
    
    def __init__(self, rules_yaml_path: Path):
        self.rule_engine = RuleEngine(rules_yaml_path)
    
    def verify(
        self,
        ast_data: Dict,
        llm_identifiers: List[str],
        min_confidence: float = 1.0  # 엄격: Rule 매칭 필수
    ) -> List[VerificationResult]:
        """
        LLM 예측 식별자를 엄격하게 검증
        
        Args:
            ast_data: AST JSON 데이터
            llm_identifiers: LLM이 예측한 식별자 리스트
            min_confidence: 최소 신뢰도 (기본: 1.0 - Rule 매칭 필수)
        
        Returns:
            검증 결과 리스트
        """
        results = []
        
        # AST에서 심볼 추출
        symbols = self._extract_symbols(ast_data)
        
        for identifier in llm_identifiers:
            # Step 1: AST에서 찾기
            symbol = symbols.get(identifier)
            
            if not symbol:
                # AST에 없음 (LLM 환각)
                results.append(VerificationResult(
                    identifier=identifier,
                    found_in_ast=False,
                    ast_symbol=None,
                    rule_matches=[],
                    final_decision=False,
                    confidence=0.0,
                    reasoning="Not found in AST (LLM hallucination)"
                ))
                continue
            
            # Step 2: Rule 매칭
            rule_matches = self.rule_engine.match_symbol(symbol)
            
            if rule_matches:
                # Rule 매칭 성공
                matched_rules = [m.rule_id for m in rule_matches]
                results.append(VerificationResult(
                    identifier=identifier,
                    found_in_ast=True,
                    ast_symbol=symbol,
                    rule_matches=rule_matches,
                    final_decision=True,  # 제외 확정
                    confidence=1.0,
                    reasoning=f"Matched {len(rule_matches)} strict rule(s): {', '.join(matched_rules)}"
                ))
            else:
                # Rule 매칭 실패
                results.append(VerificationResult(
                    identifier=identifier,
                    found_in_ast=True,
                    ast_symbol=symbol,
                    rule_matches=[],
                    final_decision=False,  # 제외하지 않음
                    confidence=0.0,
                    reasoning="Found in AST but no rule match (insufficient evidence)"
                ))
        
        return results
    
    def get_final_exclusions(
        self,
        results: List[VerificationResult],
        min_confidence: float = 1.0
    ) -> List[str]:
        """
        최종 제외 식별자 리스트
        
        Args:
            results: 검증 결과
            min_confidence: 최소 신뢰도
        
        Returns:
            제외할 식별자 리스트
        """
        exclusions = []
        
        for result in results:
            if result.final_decision and result.confidence >= min_confidence:
                exclusions.append(result.identifier)
        
        return exclusions
    
    def _extract_symbols(self, ast_data: Dict) -> Dict[str, Dict]:
        """
        AST에서 모든 심볼 추출
        
        Args:
            ast_data: AST JSON 데이터
        
        Returns:
            {symbol_name: symbol_data} 딕셔너리
        """
        symbols = {}
        
        # AST 구조에 따라 심볼 추출
        # symbols 키에 리스트가 있는 경우
        if 'symbols' in ast_data:
            for symbol in ast_data['symbols']:
                name = symbol.get('symbol_name')
                if name:
                    symbols[name] = symbol
        
        # 또는 타입별로 분리되어 있는 경우
        for key in ['classes', 'structs', 'methods', 'properties', 'variables']:
            if key in ast_data:
                for symbol in ast_data[key]:
                    name = symbol.get('symbol_name')
                    if name:
                        symbols[name] = symbol
        
        return symbols
    
    def generate_report(
        self,
        results: List[VerificationResult],
        output_path: Optional[Path] = None
    ) -> Dict:
        """
        검증 결과 리포트 생성
        
        Args:
            results: 검증 결과
            output_path: 저장 경로 (선택)
        
        Returns:
            리포트 딕셔너리
        """
        # 통계
        total = len(results)
        found_in_ast = sum(1 for r in results if r.found_in_ast)
        rule_matched = sum(1 for r in results if r.rule_matches)
        final_exclusions = sum(1 for r in results if r.final_decision)
        
        # 리포트
        report = {
            "summary": {
                "total_llm_predictions": total,
                "found_in_ast": found_in_ast,
                "rule_matched": rule_matched,
                "final_exclusions": final_exclusions,
                "hallucination_rate": f"{((total - found_in_ast) / total * 100):.1f}%" if total > 0 else "0%",
                "rule_match_rate": f"{(rule_matched / found_in_ast * 100):.1f}%" if found_in_ast > 0 else "0%"
            },
            "exclusions": [r.identifier for r in results if r.final_decision],
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
        
        # 파일 저장
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
