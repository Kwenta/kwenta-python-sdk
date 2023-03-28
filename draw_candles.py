import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
pio.renderers.default = 'browser'

def get_candlestick_plot_simple(df: pd.DataFrame, ticker: str):
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f'{ticker} Stock Price', 'Candle Chart'),
        row_width=[.5, 25]
    )
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Candlestick chart'
        ),
        row=1,
        col=1,
    )
    fig['layout']['xaxis2']['title'] = 'Timestamp'
    fig['layout']['yaxis']['title'] = 'Price'
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    # fig['layout']['yaxis2']['title'] = 'Volume'
    fig.update_xaxes(
        rangebreaks=[{'bounds': ['sat', 'mon']}],
        rangeslider_visible=False,
    )
    fig.update_layout(
        autosize=True,
        width=500,
        height=800,
        margin=dict(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        )
    )
    return fig
