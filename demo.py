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


def demo_enhanced_email_extraction():
    """향상된 이메일 추출 데모"""
    print("\n" + "=" * 50)
    print("향상된 이메일 추출 데모")
    print("=" * 50)
    
    extractor = EmailExtractor()
    
    # 테스트할 웹사이트들 (실제 존재하는 사이트)
    test_websites = [
        "https://www.starbucks.co.kr",  # 스타벅스
        "https://www.ediya.com",       # 이디야
        "https://www.hollys.co.kr",    # 할리스
        "https://www.twosome.co.kr",   # 투썸플레이스
    ]
    
    print("향상된 이메일 추출 기능:")
    print("✅ 표준 이메일 패턴")
    print("✅ 난독화된 이메일 (email[at]domain[dot]com)")
    print("✅ JavaScript에 숨겨진 이메일")
    print("✅ 연락 양식의 action 속성")
    print("✅ 숨겨진 입력 필드")
    print("✅ HTML 주석 내부")
    print("✅ 30자 초과 이메일 자동 제외")
    print()
    
    print("실제 웹사이트에서 이메일 추출 테스트:")
    print("(인터넷 연결이 필요합니다)")
    print()
    
    total_emails_found = 0
    
    for website in test_websites:
        print(f"📧 {website}에서 이메일 추출 중...")
        try:
            start_time = time.time()
            emails = extractor.extract_emails_from_website(website)
            end_time = time.time()
            
            if emails:
                print(f"  ✅ 발견된 이메일 ({len(emails)}개): {', '.join(emails)}")
                total_emails_found += len(emails)
                
                # 이메일 길이 체크
                for email in emails:
                    if len(email) <= 30:
                        print(f"    ✓ {email} (길이: {len(email)}자)")
                    else:
                        print(f"    ✗ {email} (길이: {len(email)}자 - 너무 길어서 제외됨)")
                        
            else:
                print(f"  ❌ 이메일을 찾을 수 없습니다.")
            
            print(f"  🕒 소요시간: {end_time - start_time:.1f}초")
            
        except Exception as e:
            print(f"  ❌ 오류 발생: {e}")
        print()
    
    print(f"📊 총 {total_emails_found}개의 이메일을 발견했습니다.")
    print()
    
    print("💡 향상된 기능 설명:")
    print("- 다양한 형태의 난독화된 이메일까지 감지")
    print("- JavaScript 내부에 숨겨진 이메일 추출")
    print("- 연락 양식과 숨겨진 요소에서도 이메일 검색")
    print("- 30자가 넘는 암호화된 이메일 자동 제외")
    print("- 가짜/테스트 이메일 필터링")
    print("- 비즈니스 이메일 우선순위 정렬")


def demo_obfuscated_emails():
    """난독화된 이메일 처리 데모"""
    print("\n" + "=" * 50)
    print("난독화된 이메일 처리 데모")
    print("=" * 50)
    
    extractor = EmailExtractor()
    
    # 테스트용 난독화된 이메일들
    test_emails = [
        "contact@example.com",                    # 정상 이메일
        "info[at]company[dot]com",               # [at][dot] 형태
        "support(at)business(dot)co(dot)kr",     # (at)(dot) 형태
        "hello AT domain DOT com",               # 대문자 형태
        "admin @ website . org",                 # 공백이 있는 형태
        "verylongencryptedkey123456789@domain.com",  # 30자 초과 (제외되어야 함)
        "test@test.com",                         # 가짜 이메일 (제외되어야 함)
        "contact",                               # 불완전한 이메일
        "sales@",                                # 불완전한 이메일
    ]
    
    print("난독화된 이메일 처리 테스트:")
    print()
    
    for test_email in test_emails:
        cleaned = extractor._clean_obfuscated_email(test_email)
        is_valid = extractor._is_basic_email_valid(cleaned) if cleaned else False
        
        status = "✅" if is_valid else "❌"
        result = cleaned if cleaned else "처리 실패"
        
        print(f"{status} '{test_email}' → '{result}'")
        
        if cleaned and len(cleaned) > 30:
            print(f"    ⚠️  길이 {len(cleaned)}자로 30자 초과하여 제외됨")
    
    print()
    print("필터링 규칙:")
    print("- 30자 초과 이메일 제외")
    print("- test@test.com 같은 가짜 이메일 제외")
    print("- 불완전한 이메일 형식 제외")
    print("- 숫자가 70% 이상인 이메일 제외")


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
    print(f"  향상된 이메일 추출: 활성화")
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
            print(f"    → 웹사이트가 있는 경우 향상된 이메일 추출")
    
    print("\n📧 향상된 이메일 추출 과정:")
    print("1. Google Places API에서 장소 정보 검색")
    print("2. Places Details API로 웹사이트 URL 획득") 
    print("3. 다중 페이지 웹사이트 크롤링:")
    print("   - 메인 페이지")
    print("   - /contact, /contact-us, /contactus")
    print("   - /about, /about-us, /aboutus")
    print("   - /support, /help, /info")
    print("   - /inquiry, /customer-service, /feedback")
    print("4. 다양한 방법으로 이메일 추출:")
    print("   - 텍스트 내용에서 표준/난독화 이메일")
    print("   - mailto 링크")
    print("   - 연락 양식의 action 속성")
    print("   - JavaScript 코드 내부")
    print("   - 숨겨진 입력 필드")
    print("   - HTML 주석")
    print("5. 이메일 정리 및 필터링:")
    print("   - 30자 초과 이메일 제외")
    print("   - 가짜/테스트 이메일 제거")
    print("   - 비즈니스 이메일 우선순위 정렬")
    
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
        demo_enhanced_email_extraction()
        demo_obfuscated_emails()
        demo_mock_search()
        
    except Exception as e:
        print(f"데모 실행 중 오류 발생: {e}")
    
    print("\n" + "=" * 50)
    print("Streamlit 앱을 실행하려면:")
    print("streamlit run app.py")
    print("=" * 50) 