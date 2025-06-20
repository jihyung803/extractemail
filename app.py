import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from typing import List, Dict, Tuple
import folium
from streamlit_folium import st_folium
from backend.search_engine import GridSearchEngine
from backend.config import Config

# 페이지 설정
st.set_page_config(
    page_title="Grid Search App",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'search_params' not in st.session_state:
    st.session_state.search_params = None
if 'search_duration' not in st.session_state:
    st.session_state.search_duration = 0

# 타이틀
st.title("🔍 Grid-based Location Search")
st.markdown("---")

# 사이드바 설정
with st.sidebar:
    st.header("검색 설정")
    
    # 중심점 설정
    st.subheader("📍 중심점 설정")
    col1, col2 = st.columns(2)
    with col1:
        center_lat = st.number_input("위도", value=32.9986389, format="%.6f", step=0.000001)
    with col2:
        center_lng = st.number_input("경도", value=-96.9076667, format="%.6f", step=0.000001)
    
    # 검색 반지름 설정
    st.subheader("📏 검색 반지름")
    radius = st.slider("반지름 (km)", min_value=0.1, max_value=50.0, value=5.0, step=0.1)
    
    # 키워드 설정
    st.subheader("🔤 검색 키워드")
    keywords = st.text_area(
        "키워드 입력 (줄바꿈으로 구분)",
        placeholder="카페\n음식점\n편의점\n약국",
        height=100
    )
    
    # 격자 설정
    st.subheader("⚏ 격자 설정")
    grid_size = st.selectbox(
        "격자 크기 (NxN)",
        options=[2, 3, 4, 5, 6],
        index=2,
        help="더 큰 격자는 더 세밀한 검색을 하지만 시간이 오래 걸립니다."
    )
    
    # 이메일 추출 설정
    st.subheader("📧 이메일 추출")
    extract_emails = st.checkbox(
        "웹사이트에서 이메일 추출",
        value=False,
        help="웹사이트를 크롤링하여 이메일 주소를 찾습니다. 시간이 오래 걸릴 수 있습니다."
    )
    
    if extract_emails:
        st.warning("⚠️ 이메일 추출은 시간이 오래 걸릴 수 있습니다.")
    
    # API 설정
    st.subheader("🔑 API 설정")
    api_key = st.text_input("API Key", type="password", help="Google Places API 키를 입력하세요")
    
    # 검색 버튼
    search_button = st.button("🔍 검색 시작", type="primary", use_container_width=True)
    
    # 결과 초기화 버튼
    if st.session_state.search_results is not None:
        if st.button("🔄 새로운 검색", use_container_width=True):
            st.session_state.search_results = None
            st.session_state.search_params = None
            st.session_state.search_duration = 0
            st.rerun()

# 검색 실행
if search_button:
    if not api_key:
        st.error("API Key를 입력해주세요!")
    elif not keywords.strip():
        st.error("검색할 키워드를 입력해주세요!")
    else:
        # 키워드 리스트 생성
        keyword_list = [k.strip() for k in keywords.split('\n') if k.strip()]
        
        # 검색 엔진 초기화
        config = Config(api_key=api_key)
        search_engine = GridSearchEngine(config)
        
        # 검색 진행
        with st.spinner("검색 중..."):
            start_time = time.time()
            results = search_engine.search_grid(
                center_lat=center_lat,
                center_lng=center_lng,
                radius_km=radius,
                keywords=keyword_list,
                grid_size=grid_size,
                extract_emails=extract_emails
            )
            end_time = time.time()
            search_duration = end_time - start_time
        
        # 결과를 세션 상태에 저장
        st.session_state.search_results = results
        st.session_state.search_duration = search_duration
        st.session_state.search_params = {
            'center_lat': center_lat,
            'center_lng': center_lng,
            'radius': radius,
            'keywords': keyword_list,
            'grid_size': grid_size,
            'extract_emails': extract_emails
        }

# 결과 표시 (세션 상태에서 가져옴)
if st.session_state.search_results is not None:
    results = st.session_state.search_results
    search_duration = st.session_state.search_duration
    params = st.session_state.search_params
    
    if results:
        # 결과 표시
        email_count = sum(1 for r in results if r.get('emails'))
        st.success(f"총 {len(results)}개의 결과를 찾았습니다! "
                  f"(검색 시간: {search_duration:.1f}초)")
        
        if params['extract_emails']:
            st.info(f"📧 {email_count}개 장소에서 이메일을 발견했습니다.")
        
        # 결과를 데이터프레임으로 변환
        df = pd.DataFrame(results)
        
        # 이메일 정보를 문자열로 변환
        if 'emails' in df.columns:
            df['emails_str'] = df['emails'].apply(lambda x: ', '.join(x) if x else '')
        
        # 탭으로 결과 분리
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 지도", "📊 결과 테이블", "📧 이메일 정보", "📈 통계"])
        
        with tab1:
            # 지도 표시
            st.subheader("검색 결과 지도")
            
            # 지도 생성
            m = folium.Map(
                location=[params['center_lat'], params['center_lng']],
                zoom_start=12
            )
            
            # 중심점 표시
            folium.Marker(
                [params['center_lat'], params['center_lng']],
                popup="검색 중심점",
                icon=folium.Icon(color='red', icon='star')
            ).add_to(m)
            
            # 검색 범위 원 표시
            folium.Circle(
                location=[params['center_lat'], params['center_lng']],
                radius=params['radius'] * 1000,  # km to meters
                color='red',
                fill=False,
                popup=f"검색 범위 ({params['radius']}km)"
            ).add_to(m)
            
            # 결과 마커 추가
            for idx, row in df.iterrows():
                # 마커 색상: 이메일이 있으면 녹색, 없으면 파란색
                color = 'green' if (row.get('emails') and len(row['emails']) > 0) else 'blue'
                
                popup_text = f"{row['name']}<br>{row['address']}<br>키워드: {row['keyword']}"
                if row.get('website'):
                    popup_text += f"<br>웹사이트: {row['website']}"
                if row.get('emails') and len(row['emails']) > 0:
                    popup_text += f"<br>이메일: {', '.join(row['emails'])}"
                
                folium.Marker(
                    [row['lat'], row['lng']],
                    popup=popup_text,
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)
            
            # 지도 표시
            st_folium(m, width=700, height=500)
            
            # 범례
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("🔵 **파란색**: 일반 장소")
            with col2:
                st.markdown("🟢 **녹색**: 이메일 발견된 장소")
        
        with tab2:
            # 결과 테이블
            st.subheader("검색 결과 상세")
            
            # 필터링 옵션
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_keywords = st.multiselect(
                    "키워드 필터",
                    options=df['keyword'].unique(),
                    default=df['keyword'].unique()
                )
            with col2:
                sort_by = st.selectbox(
                    "정렬 기준",
                    options=['name', 'rating', 'distance'],
                    index=0
                )
            with col3:
                if params['extract_emails']:
                    email_filter = st.selectbox(
                        "이메일 필터",
                        options=['전체', '이메일 있음', '이메일 없음'],
                        index=0
                    )
                else:
                    email_filter = '전체'
            
            # 필터링 적용
            filtered_df = df[df['keyword'].isin(selected_keywords)]
            
            if email_filter == '이메일 있음':
                filtered_df = filtered_df[filtered_df['emails'].apply(lambda x: len(x) > 0)]
            elif email_filter == '이메일 없음':
                filtered_df = filtered_df[filtered_df['emails'].apply(lambda x: len(x) == 0)]
            
            if sort_by == 'rating':
                filtered_df = filtered_df.sort_values('rating', ascending=False)
            elif sort_by == 'distance':
                filtered_df = filtered_df.sort_values('distance', ascending=True)
            else:
                filtered_df = filtered_df.sort_values('name')
            
            # 표시할 컬럼 선택
            display_columns = ['name', 'address', 'keyword', 'rating', 'distance']
            if 'website' in filtered_df.columns:
                display_columns.append('website')
            if 'phone' in filtered_df.columns:
                display_columns.append('phone')
            if params['extract_emails'] and 'emails_str' in filtered_df.columns:
                display_columns.append('emails_str')
            
            # 테이블 표시
            st.dataframe(
                filtered_df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'emails_str': st.column_config.TextColumn('이메일', width='large'),
                    'website': st.column_config.LinkColumn('웹사이트'),
                    'rating': st.column_config.NumberColumn('평점', format="%.1f"),
                    'distance': st.column_config.NumberColumn('거리', format="%.1f km")
                }
            )
            
            # CSV 다운로드
            csv_columns = ['name', 'address', 'keyword', 'rating', 'distance', 'lat', 'lng']
            if 'website' in filtered_df.columns:
                csv_columns.append('website')
            if 'phone' in filtered_df.columns:
                csv_columns.append('phone')
            if params['extract_emails'] and 'emails_str' in filtered_df.columns:
                csv_columns.append('emails_str')
            
            csv = filtered_df[csv_columns].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"search_results_with_emails_{int(time.time())}.csv",
                mime="text/csv"
            )
        
        with tab3:
            # 이메일 정보 탭
            st.subheader("📧 이메일 추출 결과")
            
            if params['extract_emails']:
                places_with_emails = [r for r in results if r.get('emails')]
                
                if places_with_emails:
                    st.success(f"🎉 {len(places_with_emails)}개 장소에서 총 {sum(len(p['emails']) for p in places_with_emails)}개의 이메일을 발견했습니다!")
                    
                    # 이메일 정보 표시
                    for place in places_with_emails:
                        with st.expander(f"📍 {place['name']} ({len(place['emails'])}개 이메일)"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**장소 정보:**")
                                st.write(f"주소: {place['address']}")
                                st.write(f"평점: {place['rating']}")
                                if place.get('website'):
                                    st.write(f"웹사이트: {place['website']}")
                            
                            with col2:
                                st.write("**발견된 이메일:**")
                                for email in place['emails']:
                                    st.write(f"📧 {email}")
                    
                    # 이메일만 따로 추출해서 표시
                    all_emails = []
                    for place in places_with_emails:
                        for email in place['emails']:
                            all_emails.append({
                                'place_name': place['name'],
                                'email': email,
                                'website': place.get('website', ''),
                                'address': place['address']
                            })
                    
                    if all_emails:
                        st.subheader("📋 이메일 목록")
                        email_df = pd.DataFrame(all_emails)
                        st.dataframe(email_df, use_container_width=True, hide_index=True)
                        
                        # 이메일 목록 CSV 다운로드
                        email_csv = email_df.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="📧 이메일 목록 CSV 다운로드",
                            data=email_csv,
                            file_name=f"extracted_emails_{int(time.time())}.csv",
                            mime="text/csv"
                        )
                else:
                    st.warning("😔 이메일을 발견한 장소가 없습니다.")
                    st.info("💡 팁: 일부 웹사이트는 이메일을 이미지로 표시하거나 접촉 양식만 제공할 수 있습니다.")
            else:
                st.info("이메일 추출을 활성화하지 않았습니다. 사이드바에서 '웹사이트에서 이메일 추출' 옵션을 체크하세요.")
        
        with tab4:
            # 통계 정보
            st.subheader("검색 결과 통계")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("총 결과 수", len(df))
            
            with col2:
                avg_rating = df['rating'].mean() if 'rating' in df.columns else 0
                st.metric("평균 평점", f"{avg_rating:.1f}")
            
            with col3:
                avg_distance = df['distance'].mean() if 'distance' in df.columns else 0
                st.metric("평균 거리", f"{avg_distance:.1f}km")
            
            with col4:
                if params['extract_emails']:
                    places_with_emails = len([r for r in results if r.get('emails')])
                    st.metric("이메일 발견", f"{places_with_emails}개소")
            
            # 키워드별 분포
            st.subheader("키워드별 결과 분포")
            keyword_counts = df['keyword'].value_counts()
            st.bar_chart(keyword_counts)
            
            # 평점 분포
            if 'rating' in df.columns:
                st.subheader("평점 분포")
                rating_counts = df[df['rating'] > 0]['rating'].value_counts().sort_index()
                st.bar_chart(rating_counts)
            
            # 이메일 통계
            if params['extract_emails']:
                st.subheader("이메일 추출 통계")
                
                total_websites = len([r for r in results if r.get('website')])
                total_emails_found = sum(len(r.get('emails', [])) for r in results)
                places_with_emails = len([r for r in results if r.get('emails')])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("웹사이트 보유", f"{total_websites}개소")
                with col2:
                    st.metric("이메일 발견 장소", f"{places_with_emails}개소")
                with col3:
                    st.metric("총 이메일 수", f"{total_emails_found}개")
                
                if total_websites > 0:
                    success_rate = (places_with_emails / total_websites) * 100
                    st.metric("이메일 추출 성공률", f"{success_rate:.1f}%")
    
    else:
        st.warning("검색 결과가 없습니다. 다른 키워드나 범위로 시도해보세요.")

else:
    # 초기 화면 (검색 결과가 없을 때만 표시)
    if st.session_state.search_results is None:
        st.info("👈 사이드바에서 검색 조건을 설정하고 검색을 시작하세요!")
        
        # 사용법 안내
        st.markdown("""
        ## 📋 사용법
        
        1. **중심점 설정**: 검색할 중심 위치의 위도, 경도를 입력합니다.
        2. **검색 반지름**: 중심점에서 검색할 반지름을 km 단위로 설정합니다.
        3. **키워드 입력**: 검색할 키워드들을 줄바꿈으로 구분하여 입력합니다.
        4. **격자 설정**: 검색 범위를 격자로 나눌 크기를 선택합니다.
        5. **이메일 추출**: 웹사이트에서 이메일을 추출할지 선택합니다.
        6. **API Key**: Google Places API 키를 입력합니다.
        7. **검색 시작**: 모든 설정을 완료한 후 검색 버튼을 클릭합니다.
        
        ## 🔧 격자 검색 방식
        
        - 입력된 반지름 범위를 NxN 격자로 나누어 각 격자별로 검색합니다.
        - 각 API 호출에서 최대 20개의 결과만 반환되므로, 격자를 나누어 더 많은 결과를 얻을 수 있습니다.
        - 격자 크기가 클수록 더 세밀한 검색이 가능하지만 API 호출 횟수가 증가합니다.
        
        ## 📧 이메일 추출 기능
        
        - Google Places API에서 웹사이트 정보를 가져온 후, 해당 웹사이트를 크롤링합니다.
        - 메인 페이지, 연락처 페이지, 소개 페이지 등에서 이메일 주소를 찾습니다.
        - 추출된 이메일은 CSV 파일로 다운로드할 수 있습니다.
        - **주의**: 이메일 추출은 시간이 오래 걸릴 수 있습니다.
        
        ## 📊 결과 화면
        
        - **지도**: 검색 결과를 지도에 마커로 표시합니다. (녹색: 이메일 발견, 파란색: 일반)
        - **테이블**: 검색 결과를 표 형태로 확인하고 필터링할 수 있습니다.
        - **이메일**: 추출된 이메일 정보를 상세히 확인할 수 있습니다.
        - **통계**: 검색 결과에 대한 통계 정보를 확인할 수 있습니다.
        """) 