import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import sqlite3
import pandas as pd
import time
import sqlitefts

app_colors = {
    'background': '#838383',
    'text': '#FFFFFF',
    'sentiment-plot': '#41EAD4',
    'volume-bar': '#FBFC74',
    'someothercolor': '#FF206E',
}

app = dash.Dash(__name__)

server = app.server

app.layout = html.Div(style={'backgroundColor' : '#FFFFFF'}, children=[
        html.H4(
            children='[TESTING]Live Twitter Sentiment',
            style={
                'textAlign' : 'center',
                'color': app_colors['background']}),
        html.H5(children='Search Term:', style={'textAlign':'center', 'color': app_colors['background']}),
        dcc.Input(id='sentiment_term', value='Twitter', type='text', style={'textAlign':'center', 'color':app_colors['background']}),
        dcc.Graph(id='live-graph', animate=False),
        dcc.Graph(id='sentiment-pie', animate=False),
        dcc.Interval(
            id='graph-update',
            interval=1 * 1000,
            n_intervals=1
        ),
        dcc.Interval(
            id='sentiment-pie-update',
            interval=60 * 1000,
            n_intervals=0
        )
    ]
)


@app.callback(
    dash.dependencies.Output('live-graph', 'figure'),
    [dash.dependencies.Input('sentiment_term', 'value'),
     dash.dependencies.Input('graph-update', 'n_intervals')],
)
def update_graph_scatter(sentiment_term, n):
    try:
        conn = sqlite3.connect('twitter.db')
        c = conn.cursor()
        if sentiment_term:
            df = pd.read_sql(
                "SELECT sentiment.* FROM sentiment_fts fts LEFT JOIN sentiment ON fts.rowid = sentiment.id WHERE fts.sentiment_fts MATCH ? ORDER BY fts.rowid DESC LIMIT 1000",
                conn,
                params=(sentiment_term,))
        else:
            df = pd.read_sql("SELECT * FROM sentiment ORDER BY id DESC, unix DESC LIMIT 1000", conn)

        df.sort_values('unix', inplace=True)
        df['date'] = pd.to_datetime(df['unix'], unit='ms')

        df.set_index('date', inplace=True)
        init_length = len(df)

        df['sentiment_smoothed'] = df['sentiment'].rolling(int(len(df) / 2)).mean()
        df = df.resample('15000ms').mean()
        df.dropna(inplace=True)

        X = df.index
        Y = df.sentiment_smoothed.values

        data = plotly.graph_objs.Scatter(
            x=X,
            y=Y,
            name='Scatter',
            mode='lines+markers'
        )

        return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),
                                                    yaxis=dict(range=[min(Y), max(Y)], overlaying='y', title='Sentiment'),
                                                    title='Sentiment Analysis of Term: {}'.format(sentiment_term),
                                                    font={'color': app_colors['text']},
                                                    plot_bgcolor=app_colors['background'],
                                                    paper_bgcolor=app_colors['background'],
                                                    showlegend=False)}
    except Exception as e:
        with open('../errors.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')


@app.callback(Output('sentiment-pie', 'figure'),
              [Input(component_id='sentiment_term', component_property='value'),
               Input('sentiment-pie-update', 'n_intervals')])
def total(sentiment_term, n):
    conn = sqlite3.connect('twitter.db')
    c = conn.cursor()

    pos_sentiment = pd.read_sql("SELECT sentiment.* FROM  sentiment_fts fts LEFT JOIN sentiment ON "
                                "fts.rowid = sentiment.id WHERE fts.sentiment_fts MATCH ? AND"
                                " sentiment > 0 ORDER BY fts.rowid DESC LIMIT 10000", conn,
                                params=(sentiment_term,))
    pos_count = len(pos_sentiment.index)

    neg_sentiment = pd.read_sql("SELECT sentiment.* FROM  sentiment_fts fts LEFT JOIN sentiment ON fts.rowid = "
                                "sentiment.id WHERE fts.sentiment_fts MATCH ? AND sentiment < 0 ORDER BY fts.rowid "
                                "DESC "
                                "LIMIT 10000", conn,
                                params=(sentiment_term,))
    neg_count = len(neg_sentiment.index)

    labels = ['Positive Sentiment', 'Negative Sentiment']
    values = [pos_count, neg_count]
    colors = ['#007F25', '#800000']

    trace = go.Pie(labels=labels, values=values,
                   hoverinfo='label+percent', textinfo='value',
                   textfont=dict(size=20, color=app_colors['text']),
                   marker=dict(colors=colors,
                               line=dict(color=app_colors['background'], width=2)))

    return {"data": [trace], 'layout': go.Layout(
        title='Positive vs Negative sentiment for "{}"'.format(sentiment_term),
        font={'color': app_colors['text']},
        plot_bgcolor=app_colors['background'],
        paper_bgcolor=app_colors['background'],
        showlegend=True)}



if __name__ == '__main__':
    app.run_server(debug=True)
