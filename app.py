"""Дашборд «Анализ юнит-экономики и воронки продаж» (Dash)."""
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html


DATA_DIR = 'data/'
UE_FILE = 'unit_economics.xlsx'
FUNNEL_FILE = 'funnel_tableau.xlsx'
AB_FILE = 'ab_monthly.xlsx'

ue = pd.read_excel(DATA_DIR + UE_FILE)
funnel = pd.read_excel(DATA_DIR + FUNNEL_FILE)
ab_monthly = pd.read_excel(DATA_DIR + AB_FILE)


TOTAL = 'Итого'
PRODUCTS = ue.loc[ue['Product'] != TOTAL, 'Product'].tolist()

# id кнопки -> значение Product в данных
BUTTONS = {'btn-all': TOTAL}
BUTTONS.update({f'btn-{i}': product for i, product in enumerate(PRODUCTS)})

ALL_SOURCES = 'Все источники'
CHANNELS = [ALL_SOURCES] + sorted(
    ab_monthly.loc[ab_monthly['Source'] != ALL_SOURCES, 'Source'].unique()
)
# id кнопки канала -> значение Source в данных
CHANNEL_BUTTONS = {f'ch-{i}': channel for i, channel in enumerate(CHANNELS)}
DROP_MONTH = pd.Timestamp('2024-02-01')

COLOR_ACTIVE = '#7F77DD'
COLOR_INACTIVE = '#D3D1C7'
COLOR_FUNNEL = '#5DCAA5'
COLOR_TEXT = '#2C2C2A'
COLOR_MUTED = '#73726C'
FONT = 'Arial, sans-serif'

# оттенки одного цвета для продуктов: выбранный продукт ярче остальных
PRODUCT_COLORS = ['#534AB7', '#7F77DD', '#AFA9EC']
CHANNEL_COLORS = {
    ALL_SOURCES: '#2C2C2A',
    'Facebook Ads': '#378ADD',
    'Google Ads': '#1D9E75',
    'Tiktok Ads': '#EF9F27',
    'Youtube Ads': '#E24B4A',
}
MONTHS_RU = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
             'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']


def fmt_num(value, decimals=0):
    """Число в русском формате: 1 234 567,89."""
    text = f'{value:,.{decimals}f}'
    return text.replace(',', ' ').replace('.', ',')


def fmt_pct(value, decimals=2):
    """Доля в процентах: 0.0254 -> 2,54%."""
    return fmt_num(value * 100, decimals) + '%'


def fmt_eur(value, decimals=0):
    """Сумма в евро: 1 234 567 €."""
    return fmt_num(value, decimals) + ' €'


def make_revenue_fig(selected):
    """Кольцевая диаграмма долей продуктов в выручке."""
    data = ue[ue['Product'] != TOTAL]
    colors = [
        color if selected in (TOTAL, product) else COLOR_INACTIVE
        for product, color in zip(data['Product'], PRODUCT_COLORS)
    ]
    pull = [0.08 if product == selected else 0 for product in data['Product']]
    total_mln = fmt_num(data['Revenue'].sum() / 1e6, 2)

    fig = go.Figure(go.Pie(
        labels=data['Product'],
        values=data['Revenue'],
        hole=0.5,
        sort=False,
        pull=pull,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        texttemplate='%{percent:.0%}',
        textfont=dict(size=14),
        customdata=[fmt_eur(value) for value in data['Revenue']],
        hovertemplate='%{label}<br>%{customdata}<extra></extra>',
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        legend=dict(font=dict(size=13, color=COLOR_TEXT)),
        annotations=[dict(text=f'{total_mln}<br>млн €', showarrow=False,
                          font=dict(size=15, color=COLOR_TEXT))],
        paper_bgcolor='white',
        font=dict(family=FONT),
    )
    return fig


def make_funnel_fig(selected):
    """Воронка сделок выбранного продукта с % перехода от этапа к этапу."""
    data = funnel[funnel['Product'] == selected].sort_values('stage_order')
    labels = [
        fmt_num(count) if pd.isna(conv)
        else f'{fmt_num(count)}  (↓ {fmt_pct(conv, 0)})'
        for count, conv in zip(data['count'], data['conv_prev'])
    ]

    fig = go.Figure(go.Funnel(
        y=data['stage'],
        x=data['count'],
        text=labels,
        textinfo='text',
        textposition='inside',
        marker_color=COLOR_FUNNEL,
        connector=dict(fillcolor='#E1F5EE'),
        hoverinfo='skip',
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        yaxis=dict(tickfont=dict(size=14, color=COLOR_TEXT)),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family=FONT),
    )
    return fig


def make_ab_fig(selected_channel):
    """Доля лидов A–B по месяцам: выбранный канал цветной, остальные серые."""
    months = sorted(ab_monthly['month'].unique())
    order = [ch for ch in CHANNELS if ch != selected_channel]
    order.append(selected_channel)

    fig = go.Figure()
    for channel in order:
        data = ab_monthly[ab_monthly['Source'] == channel].sort_values('month')
        active = channel == selected_channel
        color = CHANNEL_COLORS[channel] if active else COLOR_INACTIVE
        fig.add_trace(go.Scatter(
            x=data['month'],
            y=data['ab_share'],
            name=channel,
            mode='lines+markers',
            line=dict(color=color, width=3.5 if active else 1.5),
            marker=dict(color=color, size=8 if active else 5),
            customdata=data[['ab', 'deals']],
            hovertemplate=('%{y:.1%} (%{customdata[0]} из %{customdata[1]})'
                           f'<extra>{channel}</extra>'),
        ))

    fig.add_vline(x=DROP_MONTH, line=dict(color=COLOR_MUTED, width=1,
                                          dash='dash'))
    fig.add_annotation(x=DROP_MONTH, y=1, yref='paper', yanchor='bottom',
                       xanchor='left', showarrow=False,
                       text=' фев 2024: падение во всех каналах',
                       font=dict(size=12, color=COLOR_MUTED))
    fig.update_layout(
        margin=dict(l=10, r=10, t=30, b=10),
        height=340,
        showlegend=False,
        hovermode='x unified',
        xaxis=dict(
            tickvals=months,
            ticktext=[f'{MONTHS_RU[m.month - 1]} {m.year}'
                      for m in pd.to_datetime(months)],
            range=[months[0] - pd.Timedelta(days=15),
                   months[-1] + pd.Timedelta(days=15)],
            showgrid=False,
        ),
        yaxis=dict(tickformat='.0%', gridcolor='#EEEDE8', rangemode='tozero'),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family=FONT, color=COLOR_TEXT),
    )
    return fig


STYLE_PAGE = {
    'fontFamily': FONT, 'maxWidth': '1100px', 'margin': '0 auto',
    'padding': '20px', 'backgroundColor': 'white', 'color': COLOR_TEXT,
}
STYLE_BUTTON = {
    'padding': '8px 18px', 'marginRight': '10px', 'fontSize': '15px',
    'borderRadius': '8px', 'border': '1px solid #B4B2A9',
    'backgroundColor': 'white', 'color': COLOR_TEXT, 'cursor': 'pointer',
}
STYLE_BUTTON_ACTIVE = {
    **STYLE_BUTTON, 'backgroundColor': COLOR_ACTIVE,
    'border': f'1px solid {COLOR_ACTIVE}', 'color': 'white',
}
STYLE_CHANNEL = {
    **STYLE_BUTTON, 'padding': '5px 12px', 'fontSize': '13px',
    'borderRadius': '999px', 'marginBottom': '6px',
}
STYLE_ROW = {'display': 'flex', 'gap': '20px'}
STYLE_PANEL = {
    'flex': '1', 'border': '1px solid #E5E4DF', 'borderRadius': '12px',
    'padding': '14px',
}
STYLE_PANEL_TITLE = {'fontSize': '15px', 'color': COLOR_MUTED,
                     'marginBottom': '6px'}


def business_item(label, value):
    """Один показатель статичной строки: подпись + значение."""
    return html.Span([
        html.Span(label + ' ', style={'color': COLOR_MUTED}),
        html.B(value),
    ], style={'marginRight': '40px'})


def kpi_card(title, card_id):
    """Карточка KPI: заголовок + значение и подпись (заполняет callback)."""
    return html.Div([
        html.Div(title, style={'color': COLOR_MUTED, 'fontSize': '15px'}),
        html.Div(id=f'{card_id}-value',
                 style={'fontSize': '34px', 'fontWeight': 'bold'}),
        html.Div(id=f'{card_id}-note',
                 style={'color': COLOR_MUTED, 'fontSize': '13px'}),
    ], style={'flex': '1'})


total = ue[ue['Product'] == TOTAL].iloc[0]

business_row = html.Div([
    html.Span('Бизнес в целом:',
              style={'color': COLOR_MUTED, 'marginRight': '30px'}),
    business_item('UA', fmt_num(total['UA'])),
    business_item('AC', fmt_eur(total['AC'])),
    business_item('CPA', fmt_eur(total['CPA'], 2)),
    business_item('CM', fmt_eur(total['CM'])),
], style={'borderTop': '1px solid #E5E4DF',
          'borderBottom': '1px solid #E5E4DF',
          'padding': '8px 0', 'margin': '16px 0', 'fontSize': '15px'})

buttons = html.Div([
    html.Button('Все продукты' if product == TOTAL else product,
                id=btn_id, n_clicks=0, style=STYLE_BUTTON)
    for btn_id, product in BUTTONS.items()
])

kpi_row = html.Div([
    kpi_card('Revenue', 'revenue'),
    kpi_card('C1', 'c1'),
    kpi_card('AOV', 'aov'),
    kpi_card('APC', 'apc'),
], style={**STYLE_ROW, 'marginBottom': '20px'})

charts_row = html.Div([
    html.Div([
        html.Div('Доля продуктов в выручке · клик = фильтр',
                 style=STYLE_PANEL_TITLE),
        dcc.Graph(id='revenue-graph', config={'displayModeBar': False}),
    ], style=STYLE_PANEL),
    html.Div([
        html.Div(id='funnel-title', style=STYLE_PANEL_TITLE),
        dcc.Graph(id='funnel-graph', config={'displayModeBar': False}),
    ], style=STYLE_PANEL),
], style=STYLE_ROW)

channel_buttons = html.Div([
    html.Button([
        html.Span(style={
            'display': 'inline-block', 'width': '9px', 'height': '9px',
            'borderRadius': '50%', 'marginRight': '6px',
            'backgroundColor': CHANNEL_COLORS[channel],
        }),
        channel,
    ], id=btn_id, n_clicks=0, style=STYLE_CHANNEL)
    for btn_id, channel in CHANNEL_BUTTONS.items()
])

ab_panel = html.Div([
    html.Div('Доля лидов A–B по месяцам создания сделки', style={
        **STYLE_PANEL_TITLE, 'display': 'inline-block', 'marginRight': '12px',
    }),
    html.Span('Поток лидов: до выбора продукта, кнопки продуктов '
              'не действуют',
              style={'fontSize': '12px', 'color': COLOR_MUTED,
                     'border': '1px solid #E5E4DF', 'borderRadius': '999px',
                     'padding': '2px 10px'}),
    channel_buttons,
    dcc.Graph(id='ab-graph', config={'displayModeBar': False}),
], style={**STYLE_PANEL, 'marginTop': '20px'})

DASHBOARD_TITLE = 'Анализ юнит-экономики и воронки продаж'

header = html.H2(DASHBOARD_TITLE,
                 style={'margin': '0 0 16px 0', 'fontSize': '26px'})

footnote = html.Div(
    'Допущение: расходы на рекламу не связаны с продуктами, '
    'UA и AC общие для всех продуктов. CM = Revenue − AC.',
    style={'color': COLOR_MUTED, 'fontSize': '13px', 'marginTop': '14px'},
)

app = Dash(__name__)
app.title = DASHBOARD_TITLE
app.layout = html.Div(
    [header, buttons, business_row, kpi_row, charts_row, ab_panel, footnote],
    style=STYLE_PAGE,
)


@app.callback(
    Output('revenue-value', 'children'),
    Output('revenue-note', 'children'),
    Output('c1-value', 'children'),
    Output('c1-note', 'children'),
    Output('aov-value', 'children'),
    Output('aov-note', 'children'),
    Output('apc-value', 'children'),
    Output('apc-note', 'children'),
    Output('revenue-graph', 'figure'),
    Output('funnel-graph', 'figure'),
    Output('funnel-title', 'children'),
    *[Output(btn_id, 'style') for btn_id in BUTTONS],
    Input('revenue-graph', 'clickData'),
    *[Input(btn_id, 'n_clicks') for btn_id in BUTTONS],
)
def update_dashboard(click_data, *button_clicks):
    trigger = ctx.triggered_id
    if trigger in BUTTONS:
        selected = BUTTONS[trigger]
    elif trigger == 'revenue-graph' and click_data:
        selected = click_data['points'][0]['label']
    else:
        selected = TOTAL

    row = ue[ue['Product'] == selected].iloc[0]
    product_name = 'все продукты' if selected == TOTAL else selected
    button_styles = [
        STYLE_BUTTON_ACTIVE if product == selected else STYLE_BUTTON
        for product in BUTTONS.values()
    ]

    return (
        fmt_eur(row['Revenue']),
        'выручка продукта',
        fmt_pct(row['C1']),
        f'B = {fmt_num(row["B"])} покупателей',
        fmt_eur(row['AOV']),
        'средний платёж',
        fmt_num(row['APC'], 2),
        f'CLTV = {fmt_eur(row["CLTV"])}',
        make_revenue_fig(selected),
        make_funnel_fig(selected),
        f'Воронка сделок · {product_name}',
        *button_styles,
    )


@app.callback(
    Output('ab-graph', 'figure'),
    *[Output(btn_id, 'style') for btn_id in CHANNEL_BUTTONS],
    *[Input(btn_id, 'n_clicks') for btn_id in CHANNEL_BUTTONS],
)
def update_ab(*channel_clicks):
    selected = CHANNEL_BUTTONS.get(ctx.triggered_id, ALL_SOURCES)
    channel_styles = [
        {**STYLE_CHANNEL, 'border': f'1px solid {COLOR_TEXT}',
         'fontWeight': 'bold'}
        if channel == selected else STYLE_CHANNEL
        for channel in CHANNEL_BUTTONS.values()
    ]
    return make_ab_fig(selected), *channel_styles


# Для хостинга: gunicorn запускает Flask-сервер, который лежит внутри Dash
server = app.server

if __name__ == '__main__':
    app.run(debug=False)
