"""
rule_engine.py

엄격한 Rule 평가 엔진
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .condition_matcher import ConditionMatcher


@dataclass
class RuleMatch:
    """Rule 매칭 결과"""
    rule_id: str
    rule_description: str
    matched: bool
    confidence: float  # 엄격한 매칭이므로 항상 1.0 or 0.0
    conditions_met: List[str]  # 만족한 조건들


class RuleEngine:
    """엄격한 Rule 평가 엔진"""
    
    def __init__(self, rules_yaml_path: Path):
        """
        Args:
            rules_yaml_path: YAML Rule 파일 경로
        """
        with open(rules_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.rules = data.get('rules', [])
    
    def match_symbol(self, symbol: Dict[str, Any]) -> List[RuleMatch]:
        """
        심볼에 대해 매칭되는 모든 Rule 찾기
        
        Args:
            symbol: AST 심볼 데이터
        
        Returns:
            매칭된 Rule 리스트
        """
        matches = []
        
        for rule in self.rules:
            match_result = self._evaluate_rule(rule, symbol)
            if match_result.matched:
                matches.append(match_result)
        
        return matches
    
    def _evaluate_rule(self, rule: Dict, symbol: Dict[str, Any]) -> RuleMatch:
        """
        단일 Rule 평가
        
        Rule 구조:
        ```yaml
        - id: OBJC_ATTRIBUTE
          description: ...
          pattern:
            - find:
                target: S
            - where:
              - S.attributes contains_any ['@objc']
        ```
        """
        rule_id = rule.get('id', 'UNKNOWN')
        rule_desc = rule.get('description', '')
        pattern = rule.get('pattern', [])
        
        # 1. find 단계 (심볼 타입 확인)
        target_type = self._get_target_type(pattern)
        if not self._matches_symbol_type(symbol, target_type):
            return RuleMatch(
                rule_id=rule_id,
                rule_description=rule_desc,
                matched=False,
                confidence=0.0,
                conditions_met=[]
            )
        
        # 2. where 단계 (조건 평가)
        conditions = self._get_conditions(pattern)
        conditions_met = []
        
        for condition in conditions:
            if ConditionMatcher.evaluate(condition, symbol):
                conditions_met.append(condition)
            else:
                # 하나라도 실패하면 전체 실패 (AND 로직)
                return RuleMatch(
                    rule_id=rule_id,
                    rule_description=rule_desc,
                    matched=False,
                    confidence=0.0,
                    conditions_met=conditions_met
                )
        
        # 모든 조건 통과
        return RuleMatch(
            rule_id=rule_id,
            rule_description=rule_desc,
            matched=True,
            confidence=1.0,  # 엄격한 매칭이므로 항상 1.0
            conditions_met=conditions_met
        )
    
    def _get_target_type(self, pattern: List[Dict]) -> Optional[str]:
        """
        find 단계에서 target 추출
        
        pattern:
          - find:
              target: S
        → 'S'
        """
        for step in pattern:
            if 'find' in step:
                return step['find'].get('target')
        return None
    
    def _matches_symbol_type(self, symbol: Dict[str, Any], target: Optional[str]) -> bool:
        """
        심볼 타입이 target과 매칭되는지 확인
        
        target 매핑:
        - S: 모든 심볼
        - M: method
        - P: property
        - C: class, struct
        - E: enum
        """
        if not target:
            return True  # target 없으면 모든 심볼 매칭
        
        symbol_kind = symbol.get('symbol_kind', '')
        
        if target == 'S':
            return True  # 모든 심볼
        elif target == 'M':
            return symbol_kind in ['method', 'initializer', 'deinitializer']
        elif target == 'P':
            return symbol_kind in ['property', 'variable']
        elif target == 'C':
            return symbol_kind in ['class', 'struct']
        elif target == 'E':
            return symbol_kind == 'enum'
        else:
            return False
    
    def _get_conditions(self, pattern: List[Dict]) -> List[str]:
        """
        where 단계에서 조건 리스트 추출
        
        pattern:
          - where:
            - S.attributes contains_any ['@objc']
            - M.name in ['viewDidLoad']
        → ['S.attributes contains_any [...]', 'M.name in [...]']
        """
        conditions = []
        
        for step in pattern:
            if 'where' in step:
                where_conditions = step['where']
                if isinstance(where_conditions, list):
                    conditions.extend(where_conditions)
        
        return conditions
    
    def get_all_rules(self) -> List[Dict]:
        """모든 Rule 반환"""
        return self.rules
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """ID로 Rule 찾기"""
        for rule in self.rules:
            if rule.get('id') == rule_id:
                return rule
        return None
