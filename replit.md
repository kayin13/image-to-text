# 이미지 텍스트 추출기

## Overview
이미지에서 텍스트를 추출(OCR)하고 PostgreSQL 데이터베이스에 저장하는 Streamlit 웹 앱입니다.

## 주요 기능
- 이미지 파일 업로드 (JPG, PNG, GIF, BMP, WebP 지원)
- OpenAI Vision API (gpt-5)를 사용한 고정확도 OCR
- 영어 및 한글 텍스트 추출 지원
- 추출된 텍스트를 PostgreSQL 데이터베이스에 저장
- 저장된 데이터 조회 및 검색 기능
- 데이터 삭제 기능
- **여러 이미지 일괄 업로드 및 처리**
- **추출된 텍스트 편집 및 수정**
- **데이터 필터링 및 고급 검색 (날짜, 키워드)**
- **CSV/Excel 내보내기**
- **히스토리 관리 및 통계**

## 프로젝트 구조
```
├── app.py              # 메인 Streamlit 앱
├── database.py         # PostgreSQL 데이터베이스 연동
├── ocr_service.py      # OpenAI Vision API OCR 서비스
├── .streamlit/
│   └── config.toml     # Streamlit 설정
└── pyproject.toml      # Python 의존성
```

## 의존성
- streamlit: 웹 앱 프레임워크
- openai: OpenAI API 클라이언트
- pillow: 이미지 처리
- psycopg2-binary: PostgreSQL 연결
- pandas: 데이터 처리 및 내보내기
- openpyxl: Excel 파일 생성

## 환경 변수
- `DATABASE_URL`: PostgreSQL 데이터베이스 연결 URL (자동 설정됨)
- `OPENAI_API_KEY`: OpenAI API 키 (사용자가 설정해야 함)

## 실행 방법
```bash
streamlit run app.py --server.port 5000
```

## 데이터베이스 스키마
```sql
CREATE TABLE extracted_texts (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    extracted_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 앱 탭 구성
1. **텍스트 추출**: 이미지 업로드 및 OCR (단일/일괄 처리)
2. **저장된 데이터**: 데이터 조회, 검색, 편집, 삭제
3. **데이터 내보내기**: CSV/Excel 다운로드, 통계 및 히스토리

## 최근 변경 사항
- 2025-11-27: 고급 기능 추가
  - 여러 이미지 일괄 업로드 및 처리 기능
  - 추출된 텍스트 편집 및 수정 기능
  - 날짜/키워드 고급 검색 필터
  - CSV/Excel 내보내기 기능
  - 히스토리 통계 및 차트

- 2025-11-27: 프로젝트 초기 생성
  - 이미지 업로드 및 미리보기 기능
  - OpenAI Vision API OCR 통합
  - PostgreSQL 데이터베이스 연동
  - 데이터 조회/검색/삭제 기능
