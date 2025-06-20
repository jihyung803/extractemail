"""
Backend demonstration script
Google Places API 없이 백엔드 로직을 테스트해볼 수 있는 데모 스크립트
"""

from backend.config import Config
from backend.grid_calculator import GridCalculator
from backend.search_engine import GridSearchEngine
from backend.email_extractor import EmailExtractor
import time


def demo_grid_calculation():
    """격자 계산 데모"""
    print("=" * 50)
    print("격자 계산 데모")
    print("=" * 50)
    
    calculator = GridCalculator()
    
    # 서울시청 중심으로 5km 반지름, 3x3 격자
    center_lat = 37.5665
    center_lng = 126.9780
    radius_km = 5.0
    grid_size = 3
    
    print(f"중심점: ({center_lat}, {center_lng})")
    print(f"반지름: {radius_km}km")
    print(f"격자 크기: {grid_size}x{grid_size}")
    print()
    
    grid_points = calculator.calculate_grid_points(
        center_lat, center_lng, radius_km, grid_size
    )
    
    print(f"생성된 격자 포인트 수: {len(grid_points)}")
    print()
    
    for i, (lat, lng, grid_radius) in enumerate(grid_points, 1):
        distance = calculator.calculate_distance(center_lat, center_lng, lat, lng)
        print(f"격자 {i}: ({lat:.4f}, {lng:.4f}), 반지름: {grid_radius:.2f}km, 중심거리: {distance:.2f}km")


def demo_email_extraction():
    """이메일 추출 데모"""
    print("\n" + "=" * 50)
    print("이메일 추출 데모")
    print("=" * 50)
    
    extractor = EmailExtractor()
    
    # 테스트할 웹사이트들 (실제 존재하는 사이트)
    test_websites = [
        "https://www.starbucks.co.kr",  # 스타벅스
        "https://www.ediya.com",       # 이디야
        "https://www.hollys.co.kr",    # 할리스
    ]
    
    print("실제 웹사이트에서 이메일 추출 테스트:")
    print("(인터넷 연결이 필요합니다)")
    print()
    
    for website in test_websites:
        print(f"📧 {website}에서 이메일 추출 중...")
        try:
            emails = extractor.extract_emails_from_website(website)
            if emails:
                print(f"  ✅ 발견된 이메일: {', '.join(emails)}")
            else:
                print(f"  ❌ 이메일을 찾을 수 없습니다.")
        except Exception as e:
            print(f"  ❌ 오류 발생: {e}")
        print()
    
    print("💡 참고사항:")
    print("- 실제 웹사이트들은 이메일을 다양한 방식으로 숨기거나 보호할 수 있습니다.")
    print("- 일부 사이트는 이메일 대신 연락 양식만 제공할 수 있습니다.")
    print("- 이메일 추출 성공률은 웹사이트 구조에 따라 달라집니다.")


def demo_mock_search():
    """모의 검색 데모 (API 키 없이)"""
    print("\n" + "=" * 50)
    print("모의 검색 데모")
    print("=" * 50)
    
    # Mock config (실제 API 키 없이)
    config = Config(api_key="mock_api_key")
    
    # 격자 계산만 수행
    calculator = GridCalculator()
    
    center_lat = 37.5665
    center_lng = 126.9780
    radius_km = 3.0
    grid_size = 2
    keywords = ["카페", "음식점"]
    
    print(f"검색 설정:")
    print(f"  중심점: ({center_lat}, {center_lng})")
    print(f"  반지름: {radius_km}km")
    print(f"  격자 크기: {grid_size}x{grid_size}")
    print(f"  키워드: {keywords}")
    print(f"  이메일 추출: 활성화")
    print()
    
    grid_points = calculator.calculate_grid_points(
        center_lat, center_lng, radius_km, grid_size
    )
    
    total_api_calls = len(grid_points) * len(keywords)
    places_api_calls = total_api_calls * 20  # 최대 20개 결과 × places details API
    
    print(f"예상 API 호출 수:")
    print(f"  검색 API: {len(grid_points)} 격자 × {len(keywords)} 키워드 = {total_api_calls}회")
    print(f"  상세 정보 API: 최대 {places_api_calls}회 (결과 수에 따라)")
    print(f"  총 API 호출: 최대 {total_api_calls + places_api_calls}회")
    print(f"예상 최대 결과 수: {total_api_calls} × 20개 = {total_api_calls * 20}개")
    print()
    
    print("격자별 검색 시뮬레이션:")
    for i, (lat, lng, grid_radius) in enumerate(grid_points, 1):
        print(f"격자 {i}: ({lat:.4f}, {lng:.4f})")
        for keyword in keywords:
            print(f"  → '{keyword}' 검색 (최대 20개 결과)")
            print(f"    → 각 결과의 상세 정보 API 호출")
            print(f"    → 웹사이트가 있는 경우 이메일 추출")
    
    print("\n📧 이메일 추출 과정:")
    print("1. Google Places API에서 장소 정보 검색")
    print("2. Places Details API로 웹사이트 URL 획득")
    print("3. 웹사이트 크롤링:")
    print("   - 메인 페이지")
    print("   - /contact, /contact-us")
    print("   - /about, /about-us")
    print("   - /support, /help, /info")
    print("4. 이메일 주소 정규식으로 추출")
    print("5. 중복 제거 및 필터링")
    
    print("\n실제 검색을 위해서는 Google Places API 키가 필요합니다.")
    print("API 키를 얻는 방법:")
    print("1. https://console.cloud.google.com/ 접속")
    print("2. 새 프로젝트 생성 또는 기존 프로젝트 선택")
    print("3. Places API 활성화")
    print("4. 사용자 인증 정보에서 API 키 생성")


def demo_distance_calculation():
    """거리 계산 데모"""
    print("\n" + "=" * 50)
    print("거리 계산 데모")
    print("=" * 50)
    
    calculator = GridCalculator()
    
    # 서울의 주요 지점들
    locations = [
        ("서울시청", 37.5665, 126.9780),
        ("강남역", 37.4979, 127.0276),
        ("홍대입구역", 37.5567, 126.9220),
        ("잠실역", 37.5134, 127.1000),
        ("인천공항", 37.4602, 126.4407)
    ]
    
    center_name, center_lat, center_lng = locations[0]  # 서울시청 기준
    
    print(f"기준점: {center_name} ({center_lat}, {center_lng})")
    print()
    
    for name, lat, lng in locations[1:]:
        distance = calculator.calculate_distance(center_lat, center_lng, lat, lng)
        print(f"{center_name} → {name}: {distance:.2f}km")


if __name__ == "__main__":
    try:
        demo_grid_calculation()
        demo_distance_calculation()
        demo_email_extraction()
        demo_mock_search()
        
    except Exception as e:
        print(f"데모 실행 중 오류 발생: {e}")
    
    print("\n" + "=" * 50)
    print("Streamlit 앱을 실행하려면:")
    print("streamlit run app.py")
    print("=" * 50) 