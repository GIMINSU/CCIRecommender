# CCI 기반 주식 추천 웹 애플리케이션

이 프로젝트는 **CCI 지수(Commodity Channel Index)**를 활용하여 주식 및 ETF의 추천 데이터를 제공하며, 사용자의 투자 목표와 조건에 맞는 맞춤형 결과를 제공합니다. Flask 기반의 백엔드와 HTML/CSS를 사용한 프론트엔드로 구성되어 있으며, 데이터 시각화를 통해 직관적인 분석과 통계를 제공합니다.

## 주요 기능

1. **주식 및 ETF 추천**
   - 투자 목표(승률, 수익률, 투자일당 수익률)에 따른 최적 매매 조건 추천.
   - CCI 지수를 활용한 신호 기반 분석.

2. **조건부 필터링**
   - 종목코드, 목표 수익률, 목표 투자 기간 등의 조건에 따른 데이터 필터링.

3. **매매 이력 분석**
   - 종목별 상세 매매 이력 및 관련 그래프 제공.
   - 매매 이력을 CSV 파일로 다운로드 가능.

4. **데이터 시각화**
   - Plotly 라이브러리를 사용해 CCI 지수 및 매매 신호를 시각화.

## 기술 스택 및 구조

### 1. **백엔드**
- **Flask Framework**:
  - URL 라우팅 및 템플릿 렌더링.
  - 주요 엔드포인트:
    - `/`: 메인 페이지.
    - `/recommend`: 추천 결과 제공.
    - `/trade_history/<symbol>`: 매매 이력 분석.
    - `/download_trade_history/<symbol>`: 매매 이력 다운로드.

- **데이터 처리**:
  - `web_utils.py`:
    - CCI 데이터와 매매 기록을 기반으로 데이터 필터링 및 정제.
    - 최신 데이터 파일 검색 및 처리.

### 2. **프론트엔드**
- **HTML/CSS**:
  - 사용자 친화적인 UI 제공(`index.html`, `recommend.html`, `trade_history.html`).
  - `style.css`로 페이지별 맞춤형 디자인.

- **Jinja2 템플릿**:
  - Flask와 통합하여 동적 콘텐츠 렌더링.

### 3. **데이터 시각화**
- **Plotly**:
  - CCI 지수 및 매매 신호를 시각화하여 직관적인 그래프 제공.

### 4. **로컬 환경 설정**
- **Config 파일**:
  - 경로 및 기본값 설정 (`config.py`).

## 설치 및 실행 방법

1. **환경 설정**
   - Python 3.8 이상 필요.
   - `virtualenv`를 사용해 가상 환경 생성 및 활성화:
     ```bash
     python -m venv venv
     source venv/bin/activate  # Windows: venv\Scripts\activate
     ```

2. **필수 라이브러리 설치**
   - `requirements.txt` 파일 설치:
     ```bash
     pip install -r requirements.txt
     ```

3. **애플리케이션 실행**
   ```bash
   python app.py

## 파일 설명
* app.py: Flask 서버 엔트리 포인트. 모든 라우팅과 로직 처리.
* web_utils.py: 데이터 생성 및 분석 로직을 포함한 헬퍼 함수.
* style.css: 프론트엔드 스타일링.
* index.html, recommend.html, trade_history.html: 주요 웹 페이지 템플릿.

## 기여 및 피드백
이 프로젝트에 대한 피드백은 언제든 환영합니다. 개선 사항이나 문의사항은 GitHub Issues를 통해 남겨주세요.
