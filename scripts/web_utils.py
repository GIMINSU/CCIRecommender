import os
import re
import json


import pandas as pd
import numpy as np


from datetime import datetime
import plotly

import traceback

from config import LocalFilePathConfig as lfpc, DefaultValueConfig as dvc


daily_best_win_csvs_path = lfpc.daily_best_win_csvs_path
daily_best_return_csvs_path = lfpc.daily_best_return_csvs_path
daily_best_return_per_days_held_csvs_path = lfpc.daily_best_return_per_days_held_csvs_path

daily_cci_index_csvs_path = lfpc.daily_cci_index_csvs_path
daily_trades_csvs_path = lfpc.daily_trades_csvs_path

symbol_var = dvc.symbol_var
type_var = dvc.type_var

date_var = dvc.date_var
close_pr_var = dvc.close_pr_var
close_cci_index_var = dvc.close_cci_index_var

def get_latest_best_file(directory, date_format="%Y%m%d"):
    """
    특정 디렉토리 내 파일 목록에서 파일명에 포함된 날짜를 기준으로 가장 최신 파일을 반환합니다.
    
    :param directory: 파일이 저장된 디렉토리 경로
    :param date_format: 파일명에 포함된 날짜의 형식 (기본값: YYYYMMDD)
    :return: 가장 최신 파일의 경로 또는 None
    """
    latest_file = None
    latest_date = None

    # 디렉토리 내 파일 목록 가져오기
    try:
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except FileNotFoundError:
        print(f"디렉토리 {directory}를 찾을 수 없습니다.")
        return None

    # 파일명에서 날짜 추출 및 최신 파일 찾기
    for file in files:
        # 정규표현식으로 날짜 추출
        match = re.search(r'\d+', file)
        if match:
            try:
                file_date = datetime.strptime(match.group(), date_format)
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
                    latest_file = file
            except ValueError:
                # 날짜 형식에 맞지 않는 경우 무시
                continue

    if latest_file:
        return os.path.join(directory, latest_file)
    else:
        print("파일명에서 날짜를 찾을 수 없거나 유효한 파일이 없습니다.")
        return None

def generate_stock_data(investment_type, investment_target):
    try:
        win_file = get_latest_best_file(daily_best_win_csvs_path)
        return_file = get_latest_best_file(daily_best_return_csvs_path)
        revenue_file = get_latest_best_file(daily_best_return_per_days_held_csvs_path)

        if investment_target == 'win_rate':
            df = pd.read_csv(win_file, parse_dates=['last_price_date'], dtype={symbol_var:'string'})
            df = df.sort_values(['win_rate', 'count_win'], ascending=False).reset_index(drop=True)
        elif investment_target == 'revenue_rate':
            df = pd.read_csv(return_file, parse_dates=['last_price_date'], dtype={symbol_var:'string'})
            df = df.sort_values(['revenue_rate', 'count_win'], ascending=False).reset_index(drop=True)
        elif investment_target == 'revenue_per_investment_day':
            df = pd.read_csv(revenue_file, parse_dates=['last_price_date'], dtype={symbol_var:'string'})
            df = df.sort_values(['avg_revenue_per_days_held', 'count_win'], ascending=False).reset_index(drop=True)
        else:
            raise ValueError("Invalid investment_target parameter.")

        if investment_type == 'stock':
            df = df[df[type_var] == 'stock'].reset_index(drop=True)
        elif investment_type == 'etf':
            df = df[df[type_var] == 'etf'].reset_index(drop=True)

        return df[
            [symbol_var, 'name', 'condition_target_return', 'condition_holding_days',
             'condition_buy_cci_threshold', 'condition_stop_loss_cci_threshold',
             'win_rate', 'count_win', 'revenue_rate', 'avg_revenue_per_days_held']
        ]
    except Exception as e:
        print(f"Error in generate_stock_data: {e}")
        traceback.print_exc()
        return None


def get_latest_date_from_trade_file(symbol):
    """
    특정 디렉토리에서 symbol에 해당하는 최신 end_date_str 파일을 반환.
    
    :param symbol: 종목코드 (예: '000660')
    :return: lastest_trade_date <class 'datetime.datetime'> 해당 심볼의 최신 파일 날짜(예: '20241122')
    """
    lastest_trade_date = None
    
    # 파일 리스트 가져오기
    try:
        files = os.listdir(daily_trades_csvs_path)
    except FileNotFoundError:
        print(f"디렉토리를 찾을 수 없습니다: {daily_trades_csvs_path}")
        return None
    
    # 파일 필터링: symbol에 해당하는 파일 찾기
    pattern = re.compile(rf'all_trades_{symbol}_end_date_(\d+)\.csv')
    
    for file in files:
        match = pattern.match(file)
        if match:
            # end_date_str 추출
            try:
                file_date = datetime.strptime(match.group(1), '%Y%m%d')
                if lastest_trade_date is None or file_date > lastest_trade_date:
                    lastest_trade_date = file_date
            except ValueError:
                # 날짜 형식이 올바르지 않은 경우 무시
                continue
    return lastest_trade_date


def plot_signal_with_cci(symbol, condition_holding_days, condition_target_return, condition_buy_cci_threshold, condition_stop_loss_cci_threshold):
    
    
    cci_df = pd.DataFrame()
    history_df = pd.DataFrame()
    target_df = pd.DataFrame()
    graphJSON = None

    try:

        lastest_trade_date = get_latest_date_from_trade_file(symbol)
        
        # 파일명 형식으로 변환
        formatted_date_with_time = lastest_trade_date.strftime("%Y%m%d")


        cci_df = pd.read_csv(f'{daily_cci_index_csvs_path}/kr_cci_symbol_{symbol}.csv')
        cci_df[date_var] = pd.to_datetime(cci_df[date_var], errors='coerce', format='ISO8601')

        history_df = pd.read_csv(f'{daily_trades_csvs_path}/all_trades_{symbol}_end_date_{formatted_date_with_time}.csv')
        history_df = history_df.drop_duplicates(keep='last')  # 모든 열 기준으로 중복 제거

        history_df['buy_date'] = pd.to_datetime(history_df['buy_date'], errors='coerce', format='ISO8601')
        history_df['reach_target_date'] = pd.to_datetime(history_df['reach_target_date'], errors='coerce', format='ISO8601')
        history_df['stop_loss_date'] = pd.to_datetime(history_df['stop_loss_date'], errors='coerce', format='ISO8601')
        history_df['maturity_date'] = pd.to_datetime(history_df['maturity_date'], errors='coerce', format='ISO8601')

        target_df = history_df[
            (history_df['condition_holding_days'] == condition_holding_days) &
            (history_df['condition_target_return'] == condition_target_return) &
            (history_df['condition_buy_cci_threshold'] == condition_buy_cci_threshold) &
            (history_df['condition_stop_loss_cci_threshold'] == condition_stop_loss_cci_threshold)
                ].reset_index(drop=True)


        graph_df = pd.merge(cci_df, target_df[['buy_date', 'buy_price']], how = 'left', left_on = date_var, right_on = 'buy_date')
        graph_df = pd.merge(graph_df, target_df[['reach_target_date', 'reach_target_price']], how = 'left', left_on = date_var, right_on = 'reach_target_date')
        graph_df = pd.merge(graph_df, target_df[['stop_loss_date', 'stop_loss_price']], how = 'left', left_on = date_var, right_on = 'stop_loss_date')
        graph_df = pd.merge(graph_df, target_df[['maturity_date', 'maturity_price']], how = 'left', left_on = date_var, right_on = 'maturity_date')

        graph_df['signal'] = None

        graph_df['signal'] = np.where(graph_df['buy_date'].isna()==False, 'buy', graph_df['signal'])
        graph_df['signal'] = np.where(graph_df['reach_target_date'].isna()==False, 'reach_target', graph_df['signal'])
        graph_df['signal'] = np.where(graph_df['stop_loss_date'].isna()==False, 'stop_loss', graph_df['signal'])
        graph_df['signal'] = np.where(graph_df['maturity_date'].isna()==False, 'maturity', graph_df['signal'])
        graph_df[graph_df['signal'].isna()==False]

        from plotly.subplots import make_subplots
        import plotly.graph_objects as go

        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, vertical_spacing=0.02,
            specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
        )

        # 1행 1열: Daily Close Line 추가
        fig.add_trace(
            go.Scatter(
                mode="lines",
                x=graph_df[date_var],
                y=graph_df[close_pr_var],
                name="Daily Close",
                line=dict(color="#A9A9A9"),
                legendgroup='1',
                hoverinfo='skip'
            ),
            row=1, col=1
        )

        # 색상 및 마커 모양 매핑 정의
        bs_color_map = {
            'buy': {'color': '#000000', 'symbol': 'circle', 'fill': False},  # 속 비어있는 원
            'reach_target': {'color': '#FF6347', 'symbol': 'triangle-up'},
            'stop_loss': {'color': '#4682B4', 'symbol': 'triangle-down'},
            'maturity': {'color': '#FFA500', 'symbol': 'square'}
        }

        # 신호별 마커 추가
        for signal, props in bs_color_map.items():
            if signal == 'buy':
                # 속 비어있는 원 처리
                fig.add_trace(
                    go.Scatter(
                        mode="markers",
                        x=graph_df[f'{signal}_date'],
                        y=graph_df[f'{signal}_price'],
                        name=signal,
                        marker=dict(
                            symbol=props['symbol'], 
                            size=6, 
                            color='rgba(0,0,0,0)',  # 속 투명
                            line=dict(color=props['color'], width=1)  # 윤곽선 설정
                        ),
                        legendgroup=signal,
                        showlegend=True
                    ),
                    row=1, col=1
                )
            else:
                # 일반 마커 처리
                fig.add_trace(
                    go.Scatter(
                        mode="markers",
                        x=graph_df[f'{signal}_date'],
                        y=graph_df[f'{signal}_price'],
                        name=signal,
                        marker=dict(color=props['color'], symbol=props['symbol'], size=8),
                        legendgroup=signal,
                        showlegend=True
                    ),
                    row=1, col=1
                )

        # 2행 1열: CCI Index Line 추가
        fig.add_trace(
            go.Scatter(
                x=graph_df[date_var],
                y=graph_df[close_cci_index_var],
                name="CCI Index",
                line=dict(color="#8b8378"),
                legendgroup='cci'
            ),
            row=2, col=1
        )

        # CCI Index Overheat, Stagnation 범위 추가
        fig.add_trace(
            go.Scatter(
                x=graph_df[date_var],
                y=graph_df[close_cci_index_var].where(graph_df[close_cci_index_var] >= 200),
                mode="lines",
                line=dict(color="red"),
                name="Overheat",
                legendgroup="cci"
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=graph_df[date_var],
                y=graph_df[close_cci_index_var].where(graph_df[close_cci_index_var] <= -200),
                mode="lines",
                line=dict(color="blue"),
                name="Stagnation",
                legendgroup="cci"
            ),
            row=2, col=1
        )

        # 레이아웃 설정
        fig.update_layout(
            height=600,
            margin=dict(l=10, r=10, b=10, t=10),
            legend=dict(
                orientation="h",
                yanchor="top",
                xanchor="center",
                x=0.5
            ),
            yaxis1=dict(
                title="Daily Close",
                side="left",
                autorange=True,
                scaleanchor="x"  # X축과 동기화
            ),
            yaxis3=dict(
                title="CCI Index",
                side="left"
            ),
            hovermode="closest",
            legend_traceorder="normal"
        )

        # X축 및 Y축 설정
        fig.update_xaxes(showspikes=True)
        fig.update_yaxes(showspikes=True)

        # Create graphJSON
        graphJSON = json.dumps(fig.to_dict(), cls=plotly.utils.PlotlyJSONEncoder)

    except Exception as e:
        print(f"Error in plot_signal_with_cci: {e}")
        traceback.print_exc()

    return graphJSON, target_df, graph_df

