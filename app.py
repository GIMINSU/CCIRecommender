from flask import Flask, render_template, request, make_response
import io
from matplotlib import font_manager, rc

from scripts.config import LocalFilePathConfig as lfpc, DefaultValueConfig as dvc

from scripts.web_utils import generate_stock_data, plot_signal_with_cci

import traceback

import logging
import sys


# 한글 폰트 설정 (예: Malgun Gothic)
font_file_name = 'Pretendard-Medium.otf'
font_path = f'{lfpc.font_path}/{font_file_name}'  # 폰트 파일 경로

symbol_var = dvc.symbol_var
type_var = dvc.type_var
date_var = dvc.date_var
name_var = dvc.name_var

font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)

app = Flask(__name__)

# 로깅 설정: stdout으로 로깅 출력
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Flask 기본 로거 설정
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

# Jinja 템플릿에 zip 함수 전달
app.jinja_env.globals.update(zip=zip)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/recommend', methods=['POST', 'GET'])
def recommend():
    try:
        # 요청 처리
        investment_type = request.args.get('investment_type')
        investment_target = request.args.get('investment_target')
        symbol = request.args.get('symbol', '').strip()
        holding_days = request.args.get('condition_holding_days', 'all')
        target_return = request.args.get('condition_target_return', 'all')
        sort_column = request.args.get('sort_column', None)
        sort_order = request.args.get('sort_order', 'asc')  # 기본값: 오름차순

        if not investment_type or not investment_target:
            return "investment_type 또는 investment_target이 제공되지 않았습니다.", 400

        # 데이터 생성
        result_df = generate_stock_data(investment_type, investment_target)
        if result_df is None or result_df.empty:
            return "추천 데이터가 없습니다. 입력 조건을 다시 확인하세요.", 400

        # 필터링
        if symbol:
            result_df = result_df[result_df['symbol'].str.contains(symbol, case=False, na=False)]
        if holding_days != 'all':
            result_df = result_df[result_df['condition_holding_days'] == int(float(holding_days))]
        if target_return != 'all':
            result_df = result_df[result_df['condition_target_return'] == int(float(target_return))]

        if result_df.empty:
            return "조건에 맞는 데이터가 없습니다.", 404

        # 컬럼 매핑
        column_map = {
            'symbol': '종목코드',
            'name': '종목명',
            'condition_target_return': '목표수익률',
            'condition_holding_days': '목표 투자기간',
            'condition_buy_cci_threshold': '구매 기준 CCI',
            'condition_stop_loss_cci_threshold': '손절기준 CCI',
            'win_rate': '승률',
            'count_win': '익절 횟수',
            'revenue_rate': '수익률',

            'avg_revenue_per_days_held': '실제 투자일당 수익(원)',
        }
        result_df = result_df.rename(columns=column_map)

        stock_name = result_df['종목명'].iloc[0]

        # 정렬 처리
        if sort_column and sort_column in column_map.values():
            reverse = (sort_order == 'desc')
            result_df = result_df.sort_values(by=sort_column, ascending=not reverse)

        # 페이지네이션
        page = int(request.args.get('page', 1))
        per_page = 10
        total = len(result_df)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        paginated_df = result_df.iloc[start_idx:end_idx]
        has_next = end_idx < total

        return render_template(
            'recommend.html',
            data=paginated_df.values,
            columns=paginated_df.columns,
            page=page,
            has_next=has_next,
            condition_holding_days=holding_days,
            condition_target_return=target_return,
            investment_type=investment_type,
            investment_target=investment_target,
            symbol=symbol,
            sort_column=sort_column,
            sort_order=sort_order, 
            stock_name=stock_name
        )

    except Exception as e:
        traceback.print_exc
        return str(e), 500



@app.route('/trade_history/<symbol>')
def trade_history(symbol):
    try:
        # 종목 이름 가져오기
        stock_name = request.args.get('stock_name')

        # 쿼리 파라미터에서 값 가져오기
        condition_holding_days = int(float(request.args.get('condition_holding_days')))
        condition_target_return = int(float(request.args.get('condition_target_return')))
        condition_buy_cci_threshold = int(float(request.args.get('condition_buy_cci_threshold')))
        condition_stop_loss_cci_threshold = int(float(request.args.get('condition_stop_loss_cci_threshold')))

        count_win = int(float(request.args.get('count_win')))
        win_rate = float(request.args.get('win_rate'))
        revenue_rate = float(request.args.get('revenue_rate'))
        avg_revenue_per_days_held = int(float(request.args.get('avg_revenue_per_days_held')))


        investment_target = request.args.get('investment_target')  # investment_target 기본값 처리
        

        # 그래프 및 데이터 처리
        graphJSON, target_df, graph_df = plot_signal_with_cci(
            symbol=symbol,
            condition_holding_days=condition_holding_days,
            condition_target_return=condition_target_return,
            condition_buy_cci_threshold=condition_buy_cci_threshold,
            condition_stop_loss_cci_threshold=condition_stop_loss_cci_threshold
        )

        if target_df.empty:
            return f"{symbol} ({stock_name})에 대해 필터링 조건에 맞는 데이터가 없습니다.", 404

        # 페이지네이션
        columns = list(graph_df.columns)
        page = int(float(request.args.get('page', 1)))
        per_page = 10
        total = len(graph_df)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        paginated_df = graph_df.iloc[start_idx:end_idx]
        has_next = end_idx < total


        return render_template(
            'trade_history.html',
            symbol=symbol,
            stock_name=stock_name,
            investment_target=investment_target,
            graphJSON=graphJSON,
            columns=columns,
            data=paginated_df.values,
            page=page,
            has_next=has_next,
            condition_holding_days=condition_holding_days,
            condition_target_return=condition_target_return,
            condition_buy_cci_threshold=condition_buy_cci_threshold,
            condition_stop_loss_cci_threshold=condition_stop_loss_cci_threshold,
            win_rate = win_rate,
            count_win = count_win,
            revenue_rate = revenue_rate,
            avg_revenue_per_days_held=avg_revenue_per_days_held,
        )

    except Exception as e:
        traceback.print_exc
        return str(e), 500




@app.template_filter('format_thousands')
def format_thousands(value):
    if isinstance(value, (int, float)):
        return f"{value:,.0f}"  # 3자리마다 콤마, 소수점 제거
    return value

@app.route('/download_trade_history/<symbol>')
def download_trade_history(symbol):
    try:
        # 그래프 및 데이터 처리
        _, _, graph_df = plot_signal_with_cci(
            symbol=symbol,
            condition_holding_days=int(float(request.args.get('condition_holding_days', 10))),
            condition_target_return=int(float(request.args.get('condition_target_return', 5))),
            condition_buy_cci_threshold=int(float(request.args.get('condition_buy_cci_threshold', 0))),
            condition_stop_loss_cci_threshold=int(float(request.args.get('condition_stop_loss_cci_threshold', 0))),
        )

        if graph_df.empty:
            return "No trade history data available.", 404

        # 데이터프레임을 CSV로 변환
        output = io.StringIO()
        graph_df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        # CSV 파일로 응답 반환
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename={symbol}_trade_history.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    except Exception as e:
        traceback.print_exc
        return str(e), 500

if __name__ == '__main__':
    print('Start! Auto Trade Flask Server!')
    app.run(host='0.0.0.0', port=5000, use_reloader=False, threaded=True, debug=False)