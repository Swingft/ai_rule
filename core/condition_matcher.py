"""
condition_matcher.py

YAML Rule 조건식을 AST 데이터로 엄격하게 평가
"""

from typing import Any, List, Dict


class ConditionMatcher:
    """조건식 평가기 (엄격한 매칭)"""
    
    @staticmethod
    def evaluate(condition: str, symbol: Dict[str, Any]) -> bool:
        """
        조건식을 평가하여 True/False 반환
        
        지원하는 조건식:
        - S.attributes contains_any ['@objc', '@objcMembers']
        - M.name in ['viewDidLoad', 'viewWillAppear']
        - C.typeInheritanceChain contains_any ['UIViewController']
        - P.kind == 'property'
        - M.parent.name in ['AppDelegate']
        
        Args:
            condition: YAML에서 온 조건식 문자열
            symbol: AST 심볼 데이터
        
        Returns:
            조건 만족 여부
        """
        condition = condition.strip()
        
        # 1. contains_any 연산자
        if 'contains_any' in condition:
            return ConditionMatcher._eval_contains_any(condition, symbol)
        
        # 2. in 연산자
        elif ' in ' in condition:
            return ConditionMatcher._eval_in(condition, symbol)
        
        # 3. == 연산자
        elif ' == ' in condition:
            return ConditionMatcher._eval_equals(condition, symbol)
        
        # 4. != 연산자
        elif ' != ' in condition:
            return ConditionMatcher._eval_not_equals(condition, symbol)
        
        else:
            # 지원하지 않는 연산자
            return False
    
    @staticmethod
    def _eval_contains_any(condition: str, symbol: Dict[str, Any]) -> bool:
        """
        contains_any 평가
        
        예: S.attributes contains_any ['@objc', '@objcMembers']
        → symbol['attributes']에 '@objc' 또는 '@objcMembers' 있는지
        """
        try:
            # 좌변 파싱 (S.attributes 또는 M.typeInheritanceChain 등)
            left_part = condition.split('contains_any')[0].strip()
            field_name = ConditionMatcher._parse_field(left_part)
            
            # 우변 파싱 (['@objc', '@objcMembers'])
            right_part = condition.split('contains_any')[1].strip()
            values = ConditionMatcher._parse_list(right_part)
            
            # 실제 값 가져오기
            field_value = symbol.get(field_name, [])
            
            # contains_any 검사
            if isinstance(field_value, list):
                return any(v in field_value for v in values)
            else:
                return field_value in values
                
        except Exception:
            return False
    
    @staticmethod
    def _eval_in(condition: str, symbol: Dict[str, Any]) -> bool:
        """
        in 연산자 평가
        
        예: M.name in ['viewDidLoad', 'viewWillAppear']
        → symbol['symbol_name']이 리스트에 있는지
        """
        try:
            # 좌변 파싱
            left_part = condition.split(' in ')[0].strip()
            field_name = ConditionMatcher._parse_field(left_part)
            
            # 우변 파싱
            right_part = condition.split(' in ')[1].strip()
            values = ConditionMatcher._parse_list(right_part)
            
            # 실제 값
            field_value = symbol.get(field_name)
            
            return field_value in values
            
        except Exception:
            return False
    
    @staticmethod
    def _eval_equals(condition: str, symbol: Dict[str, Any]) -> bool:
        """
        == 연산자 평가
        
        예: P.kind == 'property'
        → symbol['symbol_kind'] == 'property'
        """
        try:
            parts = condition.split('==')
            field_name = ConditionMatcher._parse_field(parts[0].strip())
            expected_value = parts[1].strip().strip("'\"")
            
            actual_value = symbol.get(field_name)
            
            # boolean 처리
            if expected_value.lower() in ['true', 'false']:
                expected_value = expected_value.lower() == 'true'
            
            return actual_value == expected_value
            
        except Exception:
            return False
    
    @staticmethod
    def _eval_not_equals(condition: str, symbol: Dict[str, Any]) -> bool:
        """!= 연산자 평가"""
        try:
            parts = condition.split('!=')
            field_name = ConditionMatcher._parse_field(parts[0].strip())
            expected_value = parts[1].strip().strip("'\"")
            
            actual_value = symbol.get(field_name)
            
            return actual_value != expected_value
            
        except Exception:
            return False
    
    @staticmethod
    def _parse_field(field_expr: str) -> str:
        """
        필드 표현식을 실제 필드명으로 변환
        
        S.attributes → attributes
        M.name → symbol_name
        C.typeInheritanceChain → inherits
        P.kind → symbol_kind
        M.parent.name → parent_type (특수 케이스)
        """
        # 심볼 타입 제거 (S., M., P., C.)
        if '.' in field_expr:
            parts = field_expr.split('.')
            if len(parts) >= 2:
                field = parts[1]
                
                # 필드명 매핑
                field_mapping = {
                    'name': 'symbol_name',
                    'kind': 'symbol_kind',
                    'typeInheritanceChain': 'inherits',
                    'attributes': 'attributes',
                    'modifiers': 'modifiers',
                    'conforms': 'conforms',
                    'accessLevel': 'access_level',
                }
                
                # parent.name 같은 중첩 처리
                if len(parts) >= 3 and parts[1] == 'parent':
                    if parts[2] == 'name':
                        return 'parent_type'
                
                return field_mapping.get(field, field)
        
        return field_expr
    
    @staticmethod
    def _parse_list(list_str: str) -> List[str]:
        """
        문자열 리스트 파싱
        
        "['@objc', '@objcMembers']" → ['@objc', '@objcMembers']
        """
        list_str = list_str.strip()
        
        # 대괄호 제거
        if list_str.startswith('[') and list_str.endswith(']'):
            list_str = list_str[1:-1]
        
        # 쉼표로 분리
        items = []
        for item in list_str.split(','):
            item = item.strip().strip("'\"")
            if item:
                items.append(item)
        
        return items
