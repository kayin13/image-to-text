import streamlit as st
from PIL import Image
import io
import os
import pandas as pd
from datetime import datetime, date

from database import (
    init_database, save_extracted_text, get_all_records, 
    search_records, search_records_advanced, delete_record,
    update_extracted_text, get_record_by_id
)
from ocr_service import extract_text_from_image

st.set_page_config(
    page_title="이미지 텍스트 추출기",
    page_icon="📄",
    layout="wide"
)

init_database()

st.title("이미지 텍스트 추출기")
st.markdown("이미지를 업로드하면 AI가 텍스트를 추출하여 데이터베이스에 저장합니다.")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

tab1, tab2, tab3 = st.tabs(["텍스트 추출", "저장된 데이터", "데이터 내보내기"])

with tab1:
    st.header("이미지 업로드")
    
    if not OPENAI_API_KEY:
        st.warning("OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    
    upload_mode = st.radio(
        "업로드 방식 선택",
        ["단일 이미지", "여러 이미지 일괄 처리"],
        horizontal=True
    )
    
    if upload_mode == "단일 이미지":
        uploaded_file = st.file_uploader(
            "이미지 파일을 선택하세요",
            type=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            help="지원 형식: JPG, JPEG, PNG, GIF, BMP, WEBP",
            key="single_upload"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("업로드된 이미지")
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)
            
            with col2:
                st.subheader("추출된 텍스트")
                
                if "extracted_text" not in st.session_state:
                    st.session_state.extracted_text = None
                if "current_file" not in st.session_state:
                    st.session_state.current_file = None
                
                if st.session_state.current_file != uploaded_file.name:
                    st.session_state.extracted_text = None
                    st.session_state.current_file = uploaded_file.name
                
                if st.button("텍스트 추출하기", type="primary", disabled=not OPENAI_API_KEY):
                    with st.spinner("AI가 텍스트를 추출하고 있습니다..."):
                        try:
                            uploaded_file.seek(0)
                            image_bytes = uploaded_file.read()
                            mime_type = uploaded_file.type or "image/jpeg"
                            
                            extracted_text = extract_text_from_image(image_bytes, mime_type)
                            st.session_state.extracted_text = extracted_text
                            st.success("텍스트 추출이 완료되었습니다!")
                        except Exception as e:
                            st.error(f"텍스트 추출 중 오류가 발생했습니다: {str(e)}")
                
                if st.session_state.extracted_text:
                    st.text_area(
                        "추출된 텍스트",
                        value=st.session_state.extracted_text,
                        height=300,
                        key="text_display"
                    )
                    
                    if st.button("데이터베이스에 저장", type="secondary"):
                        try:
                            record_id = save_extracted_text(
                                uploaded_file.name,
                                st.session_state.extracted_text
                            )
                            st.success(f"저장 완료! (ID: {record_id})")
                            st.session_state.extracted_text = None
                            st.session_state.current_file = None
                        except Exception as e:
                            st.error(f"저장 중 오류가 발생했습니다: {str(e)}")
    
    else:
        uploaded_files = st.file_uploader(
            "여러 이미지 파일을 선택하세요",
            type=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            help="지원 형식: JPG, JPEG, PNG, GIF, BMP, WEBP",
            accept_multiple_files=True,
            key="batch_upload"
        )
        
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)}개의 이미지가 선택되었습니다.**")
            
            if "batch_results" not in st.session_state:
                st.session_state.batch_results = []
            
            cols = st.columns(min(4, len(uploaded_files)))
            for idx, file in enumerate(uploaded_files[:8]):
                with cols[idx % 4]:
                    image = Image.open(file)
                    st.image(image, caption=file.name, use_container_width=True)
            
            if len(uploaded_files) > 8:
                st.info(f"... 외 {len(uploaded_files) - 8}개 이미지")
            
            if st.button("모든 이미지에서 텍스트 추출", type="primary", disabled=not OPENAI_API_KEY):
                st.session_state.batch_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"처리 중: {file.name} ({idx + 1}/{len(uploaded_files)})")
                    try:
                        file.seek(0)
                        image_bytes = file.read()
                        mime_type = file.type or "image/jpeg"
                        
                        extracted_text = extract_text_from_image(image_bytes, mime_type)
                        st.session_state.batch_results.append({
                            "filename": file.name,
                            "text": extracted_text,
                            "status": "success"
                        })
                    except Exception as e:
                        st.session_state.batch_results.append({
                            "filename": file.name,
                            "text": str(e),
                            "status": "error"
                        })
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("모든 이미지 처리 완료!")
                st.success(f"{len([r for r in st.session_state.batch_results if r['status'] == 'success'])}개 성공, "
                          f"{len([r for r in st.session_state.batch_results if r['status'] == 'error'])}개 실패")
            
            if st.session_state.batch_results:
                st.subheader("추출 결과")
                
                for idx, result in enumerate(st.session_state.batch_results):
                    with st.expander(f"{'✅' if result['status'] == 'success' else '❌'} {result['filename']}"):
                        if result['status'] == 'success':
                            st.text_area(
                                "추출된 텍스트",
                                value=result['text'],
                                height=200,
                                key=f"batch_text_{idx}"
                            )
                        else:
                            st.error(f"오류: {result['text']}")
                
                success_results = [r for r in st.session_state.batch_results if r['status'] == 'success']
                if success_results:
                    if st.button("모든 결과를 데이터베이스에 저장", type="secondary"):
                        saved_count = 0
                        for result in success_results:
                            try:
                                save_extracted_text(result['filename'], result['text'])
                                saved_count += 1
                            except Exception as e:
                                st.error(f"{result['filename']} 저장 실패: {str(e)}")
                        
                        st.success(f"{saved_count}개의 결과가 저장되었습니다!")
                        st.session_state.batch_results = []

with tab2:
    st.header("저장된 데이터")
    
    with st.expander("고급 검색 옵션", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            keyword_search = st.text_input(
                "키워드 검색",
                placeholder="파일명 또는 텍스트 내용...",
                key="keyword_search"
            )
        
        with col2:
            use_start_date = st.checkbox("시작 날짜 필터", key="use_start_date")
            if use_start_date:
                start_date = st.date_input(
                    "시작 날짜",
                    value=date.today(),
                    key="start_date"
                )
            else:
                start_date = None
        
        with col3:
            use_end_date = st.checkbox("종료 날짜 필터", key="use_end_date")
            if use_end_date:
                end_date = st.date_input(
                    "종료 날짜",
                    value=date.today(),
                    key="end_date"
                )
            else:
                end_date = None
    
    if keyword_search or start_date or end_date:
        records = search_records_advanced(
            keyword=keyword_search if keyword_search else None,
            start_date=start_date,
            end_date=end_date
        )
    else:
        records = get_all_records()
    
    if records:
        st.markdown(f"**총 {len(records)}개의 기록**")
        
        for record in records:
            with st.expander(f"📄 {record['filename']} - {record['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                edit_key = f"edit_mode_{record['id']}"
                
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                
                if st.session_state[edit_key]:
                    edited_text = st.text_area(
                        "텍스트 편집",
                        value=record['extracted_text'],
                        height=200,
                        key=f"edit_text_{record['id']}"
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("저장", key=f"save_{record['id']}", type="primary"):
                            try:
                                update_extracted_text(record['id'], edited_text)
                                st.session_state[edit_key] = False
                                st.success("수정되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"수정 중 오류: {str(e)}")
                    with col2:
                        if st.button("취소", key=f"cancel_{record['id']}"):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    st.text_area(
                        "추출된 텍스트",
                        value=record['extracted_text'],
                        height=200,
                        key=f"text_{record['id']}",
                        disabled=True
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("편집", key=f"edit_{record['id']}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    with col2:
                        if st.button("삭제", key=f"delete_{record['id']}", type="secondary"):
                            try:
                                delete_record(record['id'])
                                st.success("삭제되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"삭제 중 오류: {str(e)}")
    else:
        if keyword_search or start_date or end_date:
            st.info("검색 결과가 없습니다.")
        else:
            st.info("저장된 데이터가 없습니다. 이미지를 업로드하여 텍스트를 추출해보세요.")

with tab3:
    st.header("데이터 내보내기")
    
    records = get_all_records()
    
    if records:
        st.markdown(f"**총 {len(records)}개의 데이터를 내보낼 수 있습니다.**")
        
        df = pd.DataFrame(records)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df.columns = ['ID', '파일명', '추출된 텍스트', '생성일시']
        
        st.dataframe(df, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV로 다운로드",
                data=csv_data,
                file_name=f"extracted_texts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='추출된 텍스트')
            excel_data = output.getvalue()
            
            st.download_button(
                label="Excel로 다운로드",
                data=excel_data,
                file_name=f"extracted_texts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.subheader("히스토리 요약")
        
        if len(records) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("총 기록 수", len(records))
            
            with col2:
                unique_files = len(set([r['filename'] for r in records]))
                st.metric("고유 파일 수", unique_files)
            
            with col3:
                total_chars = sum([len(r['extracted_text']) for r in records])
                st.metric("총 추출 문자 수", f"{total_chars:,}")
            
            st.subheader("날짜별 추출 기록")
            
            date_counts = {}
            for record in records:
                record_date = record['created_at'].strftime('%Y-%m-%d')
                date_counts[record_date] = date_counts.get(record_date, 0) + 1
            
            date_df = pd.DataFrame(
                list(date_counts.items()),
                columns=['날짜', '추출 횟수']
            )
            date_df = date_df.sort_values('날짜', ascending=False)
            
            st.bar_chart(date_df.set_index('날짜'))
    else:
        st.info("내보낼 데이터가 없습니다. 먼저 이미지에서 텍스트를 추출해주세요.")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Powered by OpenAI Vision API | 영어 및 한글 지원"
    "</div>",
    unsafe_allow_html=True
)
