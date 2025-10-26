#!/usr/bin/env python3
"""
test_parallel.py

병렬 처리 통합 테스트
"""

import json
import sys
import tempfile
import shutil
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def create_test_project():
    """테스트용 Swift 프로젝트 생성"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Swift 파일 1
    file1 = temp_dir / "ViewController.swift"
    file1.write_text("""
import UIKit

class MyViewController: UIViewController {
    @objc func viewDidLoad() {
        super.viewDidLoad()
    }
    
    func customMethod() {
        print("custom")
    }
}
""")
    
    # Swift 파일 2
    file2 = temp_dir / "Model.swift"
    file2.write_text("""
struct User: Codable {
    let id: String
    let name: String
    let email: String
}
""")
    
    # Swift 파일 3
    file3 = temp_dir / "Service.swift"
    file3.write_text("""
class NetworkService {
    func fetchData() {
        // implementation
    }
}
""")
    
    return temp_dir


def create_test_predictions(temp_dir: Path):
    """테스트용 LLM 예측 생성"""
    predictions = {
        "identifiers": [
            "viewDidLoad",
            "customMethod",
            "id",
            "name",
            "email",
            "fetchData",
            "nonExistent"  # 환각
        ]
    }
    
    pred_file = temp_dir / "predictions.json"
    pred_file.write_text(json.dumps(predictions, indent=2))
    
    return pred_file


def test_parallel_processing():
    """병렬 처리 통합 테스트"""
    print("\n" + "=" * 70)
    print("🧪 병렬 처리 통합 테스트")
    print("=" * 70)
    
    # 1. 테스트 프로젝트 생성
    print("\n📁 테스트 프로젝트 생성 중...")
    temp_project = create_test_project()
    print(f"✓ 생성: {temp_project}")
    
    # Swift 파일 확인
    swift_files = list(temp_project.rglob("*.swift"))
    print(f"✓ Swift 파일: {len(swift_files)}개")
    for f in swift_files:
        print(f"  - {f.name}")
    
    # 2. 테스트 예측 생성
    print("\n📝 LLM 예측 생성 중...")
    pred_file = create_test_predictions(temp_project)
    print(f"✓ 생성: {pred_file}")
    
    # 3. SwiftASTAnalyzer 확인
    print("\n🔧 SwiftASTAnalyzer 확인 중...")
    analyzer_path = Path("SwiftASTAnalyzer/.build/release/SwiftASTAnalyzer")
    
    if not analyzer_path.exists():
        print("❌ SwiftASTAnalyzer 없음")
        print("   빌드 필요: cd SwiftASTAnalyzer && swift build -c release")
        return False
    
    print(f"✓ 발견: {analyzer_path}")
    
    # 4. main.py 실행
    print("\n🚀 병렬 처리 실행 중...")
    import subprocess
    
    result_file = temp_project / "result.json"
    
    cmd = [
        "python", "main.py",
        "--project", str(temp_project),
        "--identifiers", str(pred_file),
        "--output", str(result_file),
        "--workers", "2"
    ]
    
    print(f"실행: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("\n" + "=" * 70)
        print("📊 실행 결과:")
        print("=" * 70)
        print(result.stdout)
        
        if result.returncode != 0:
            print("\n❌ 실행 실패:")
            print(result.stderr)
            return False
        
        # 5. 결과 검증
        print("\n🔍 결과 검증 중...")
        
        if not result_file.exists():
            print(f"❌ 결과 파일 없음: {result_file}")
            return False
        
        with open(result_file, 'r') as f:
            verification = json.load(f)
        
        print(f"✓ 결과 파일 로드 완료")
        print(f"\n📈 검증 통계:")
        print(f"  - 총 파일: {verification['total_files']}")
        print(f"  - 성공: {verification['success_files']}")
        print(f"  - 실패: {verification['failed_files']}")
        print(f"  - 처리 시간: {verification['processing_time_seconds']:.2f}초")
        print(f"  - 속도: {verification['files_per_second']:.2f} files/sec")
        
        # 기대값 확인
        expected_files = 3
        if verification['total_files'] != expected_files:
            print(f"\n❌ 파일 수 불일치: {verification['total_files']} != {expected_files}")
            return False
        
        print("\n✅ 모든 검증 통과!")
        return True
        
    except subprocess.TimeoutExpired:
        print("\n❌ 타임아웃")
        return False
    except Exception as e:
        print(f"\n❌ 에러: {e}")
        return False
    finally:
        # 7. 정리
        print(f"\n🧹 임시 파일 정리 중...")
        shutil.rmtree(temp_project)
        print(f"✓ 삭제: {temp_project}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 ai_rule 통합 테스트")
    print("=" * 70)
    
    success = test_parallel_processing()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ 통합 테스트 통과!")
    else:
        print("❌ 통합 테스트 실패")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
