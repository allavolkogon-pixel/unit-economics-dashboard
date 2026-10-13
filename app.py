"""Дашборд «Анализ юнит-экономики и воронки продаж» (Dash)."""
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html


DATA_DIR = 'data/'
UE_FILE = 'unit_economics.xlsx'
FUNNEL_FILE = 'funnel_tableau.xlsx'

ue = pd.read_excel(DATA_DIR + UE_FILE)
funnel = pd.read_excel(DATA_DIR + FUNNEL_FILE)


TOTAL = 'Итого'
PRODUCTS = ue.loc[ue['Product'] != TOTAL, 'Product'].tolist()

# id кнопки -> значение Product в данных
BUTTONS = {'btn-all': TOTAL}
BUTTONS.update({f'btn-{i}': product for i, product in enumerate(PRODUCTS)})

COLOR_ACTIVE = '#7F77DD'
COLOR_INACTIVE = '#D3D1C7'
COLOR_FUNNEL = '#5DCAA5'
COLOR_TEXT = '#2C2C2A'
COLOR_MUTED = '#73726C'
FONT = 'Arial, sans-serif'


def fmt_num(value, decimals=0):
    """Число в русском формате: 1 234 567,89."""
    text = f'{value:,.{decimals}f}'
    return text.replace(',', ' ').replace('.', ',')


def fmt_pct(value, decimals=2):
    """Доля в процентах: 0.0254 -> 2,54%."""
    return fmt_num(value * 100, decimals) + '%'


def make_revenue_fig(selected):
    """Горизонтальный бар Revenue по продуктам, выбранный подсвечен."""
    data = ue[ue['Product'] != TOTAL].sort_values('Revenue')
    colors = [
        COLOR_ACTIVE if selected in (TOTAL, product) else COLOR_INACTIVE
        for product in data['Product']
    ]
    labels = [fmt_num(value / 1000) + ' тыс' for value in data['Revenue']]

    fig = go.Figure(go.Bar(
        x=data['Revenue'],
        y=data['Product'],
        orientation='h',
        marker_color=colors,
        text=labels,
        textposition='outside',
        textfont=dict(color=COLOR_TEXT, size=13),
        cliponaxis=False,
        # 'none' убирает подсказку, но клик работает ('skip' отключает и клик)
        hoverinfo='none',
    ))
    fig.update_layout(
        margin=dict(l=10, r=70, t=10, b=10),
        height=260,
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(size=14, color=COLOR_TEXT)),
        plot_bgcolor='white',
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
    business_item('AC', fmt_num(total['AC'])),
    business_item('CPA', fmt_num(total['CPA'], 2)),
    business_item('CM', fmt_num(total['CM'])),
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
        html.Div('Revenue по продуктам · клик = фильтр',
                 style=STYLE_PANEL_TITLE),
        dcc.Graph(id='revenue-graph', config={'displayModeBar': False}),
    ], style=STYLE_PANEL),
    html.Div([
        html.Div(id='funnel-title', style=STYLE_PANEL_TITLE),
        dcc.Graph(id='funnel-graph', config={'displayModeBar': False}),
    ], style=STYLE_PANEL),
], style=STYLE_ROW)

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
    [header, buttons, business_row, kpi_row, charts_row, footnote],
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
        selected = click_data['points'][0]['y']
    else:
        selected = TOTAL

    row = ue[ue['Product'] == selected].iloc[0]
    product_name = 'все продукты' if selected == TOTAL else selected
    button_styles = [
        STYLE_BUTTON_ACTIVE if product == selected else STYLE_BUTTON
        for product in BUTTONS.values()
    ]

    return (
        fmt_num(row['Revenue']),
        'выручка продукта',
        fmt_pct(row['C1']),
        f'B = {fmt_num(row["B"])} покупателей',
        fmt_num(row['AOV']),
        'средний платёж',
        fmt_num(row['APC'], 2),
        f'CLTV = {fmt_num(row["CLTV"])}',
        make_revenue_fig(selected),
        make_funnel_fig(selected),
        f'Воронка сделок · {product_name}',
        *button_styles,
    )


# Для хостинга: gunicorn запускает Flask-сервер, который лежит внутри Dash
server = app.server

if __name__ == '__main__':
    app.run(debug=False)
