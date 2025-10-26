"""
settings.py

설정
"""

from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 디렉토리
RULES_DIR = PROJECT_ROOT / "rules"
DATA_DIR = PROJECT_ROOT / "data"
IDENTIFIERS_DIR = DATA_DIR / "identifiers"
RESULTS_DIR = DATA_DIR / "results"

# Rule 파일
RULES_YAML = RULES_DIR / "swift_exclusion_rules.yaml"

# 검증 설정
MIN_CONFIDENCE = 1.0  # 엄격: Rule 매칭 필수
STRICT_MODE = True

# 디버그
DEBUG = False
