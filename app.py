from dash import Dash, html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px

# Load data
df = pd.read_csv('data.csv')

# Dash app configuration
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap"
]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Title section
title_section = dbc.Row(
    dbc.Col(html.H1(
        "Patient No-Show Analysis & Intervention Dashboard",
        className="text-center mt-4 mb-4 text-secondary",
        style={"fontFamily": "'Poppins', sans-serif"}
    ))
)

# KPI card generator
def create_kpi_card(title, value):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody([
                html.H5(title, className="card-title"),
                html.P(f"{value}", className="card-text fs-2 fw-semibold text-danger")
            ]),
            className="shadow-sm"
        ),
        width=4
    )

# KPI calculations
no_show_summary = df.groupby('No-show').size().reset_index(name='count')
no_show_summary['percentage'] = (no_show_summary['count'] / no_show_summary['count'].sum()) * 100
no_show_percentage = float(no_show_summary.loc[no_show_summary['No-show'] == 'No show', 'percentage'].values[0].round(2))
total_no_shows = int(no_show_summary.loc[no_show_summary['No-show'] == 'No show', 'count'].values[0])

repeat_counts = df[df['No-show'] == 'No show'].groupby('PatientId').size()
repeat_no_show_percentage = float(np.round(repeat_counts[repeat_counts >= 2].sum() / total_no_shows * 100, 2))

# KPI card layout
kpi_cards = dbc.Row([
    create_kpi_card("Overall No-Show Rate", f"{no_show_percentage}%"),
    create_kpi_card("Total Missed Appointments", total_no_shows),
    create_kpi_card("Impact of Repeat Offenders", f"{repeat_no_show_percentage}%")
], className="mb-4 text-center")


# Age group bar chart
age_crosstab = pd.crosstab(df['AgeGroup'], df['No-show'])
age_noshow_pct = (age_crosstab['No show'] / age_crosstab.sum(axis=1) * 100).sort_values(ascending=False)
age_plot_data = age_noshow_pct.reset_index(name='Percentage')

bar_plot = px.bar(
    age_plot_data,
    x='AgeGroup',
    y='Percentage',
    color='Percentage',
    color_continuous_scale='Reds',
    labels={'AgeGroup': 'Age Group', 'Percentage': 'No-show Percentage'},
    title='No-show Percentage by Age Group',
    height=500
)

# Visual section
visual_section = dbc.Row([
    dbc.Col([
        html.Div(
            dcc.RangeSlider(
                id='delay_range_slider',
                min=df['Delay_Days'].min(),
                max=df['Delay_Days'].max(),
                step=1,
                marks={int(i): str(int(i)) for i in np.linspace(df['Delay_Days'].min(), df['Delay_Days'].max(), num=10)},
                value=[df['Delay_Days'].min(), df['Delay_Days'].max()],
                tooltip={"placement": "bottom", "always_visible": False}
            ),
            style={"marginTop": "20px", "marginBottom": "10px"}
        ),
        dcc.Graph(style={"height": "400px", "margin": 0}, id='delay_graph'),
    ], width=6, style={"paddingRight": "15px"}),

    dbc.Col(
        dcc.Graph(figure=bar_plot, style={"height": "500px"}),
        width=6,
        style={"paddingLeft": "15px"}
    )
], className="mb-4")

@callback(
    Output('delay_graph', 'figure'),
    Input('delay_range_slider', 'value')
)
def draw_delay_graph(value):
    # Delay days line plot
    delay_group = df.groupby(['Delay_Days', 'No-show']).size().reset_index(name='count')
    delay_group['percent'] = delay_group['count'] / delay_group.groupby('Delay_Days')['count'].transform('sum') * 100
    delay_group = delay_group[delay_group['No-show'] == 'No show']
    delay_group = delay_group[delay_group['Delay_Days'].between(value[0], value[1])]
    line_plot = px.line(
        delay_group,
        x='Delay_Days',
        y='percent',
        color_discrete_sequence=["#C42828"],
        title='Percentage of No-shows by Delay Days',
        labels={'Delay_Days': 'Delay in Days', 'percent': 'Percentage'},
        markers=True,
        height=400,
        hover_data='count'
    )
    line_plot.update_layout(
    margin=dict(l=40, r=40, t=50, b=40),
    height=400)
    return line_plot


# Final layout
app.layout = dbc.Container([
    title_section,
    kpi_cards,
    visual_section
], fluid=True)

# Run the server
if __name__ == '__main__':
    app.run(debug=True)