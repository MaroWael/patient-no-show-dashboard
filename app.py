from dash import Dash, html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------------
# Load and Prepare Data
# ------------------------
df = pd.read_csv('data.csv')

# KPI Calculations
no_show_summary = df.groupby('No-show').size().reset_index(name='count')
no_show_summary['percentage'] = (no_show_summary['count'] / no_show_summary['count'].sum()) * 100

no_show_percentage = round(no_show_summary.loc[no_show_summary['No-show'] == 'No show', 'percentage'].values[0], 2)
total_no_shows = int(no_show_summary.loc[no_show_summary['No-show'] == 'No show', 'count'].values[0])

repeat_counts = df[df['No-show'] == 'No show'].groupby('PatientId').size()
repeat_no_show_percentage = round(repeat_counts[repeat_counts >= 2].sum() / total_no_shows * 100, 2)

# Age Group Chart Data
age_crosstab = pd.crosstab(df['AgeGroup'], df['No-show'])
age_noshow_pct = (age_crosstab['No show'] / age_crosstab.sum(axis=1) * 100).sort_values(ascending=False)
age_plot_data = age_noshow_pct.reset_index(name='Percentage')

# ------------------------
# Initialize App
# ------------------------
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap"
]

app = Dash(__name__, external_stylesheets=external_stylesheets)

# ------------------------
# UI Components
# ------------------------

## Title
title_section = dbc.Row(
    dbc.Col(
        html.H1("Patient No-Show Analysis & Intervention Dashboard",
                className="text-center mt-4 mb-4 text-secondary",
                style={"fontFamily": "'Poppins', sans-serif"})
    )
)

## KPI Cards
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

kpi_cards = dbc.Row([
    create_kpi_card("Overall No-Show Rate", f"{no_show_percentage}%"),
    create_kpi_card("Total Missed Appointments", total_no_shows),
    create_kpi_card("Impact of Repeat Offenders", f"{repeat_no_show_percentage}%")
], className="mb-4 text-center")

## Age Bar Chart
age_bar_plot = px.bar(
    age_plot_data,
    x='AgeGroup',
    y='Percentage',
    color='Percentage',
    color_continuous_scale='Reds',
    labels={'AgeGroup': 'Age Group', 'Percentage': 'No-show Percentage'},
    title='No-show Percentage by Age Group',
    height=500
)

## Delay Days Range Slider + Graph
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
        dcc.Loading(
            dcc.Graph(id='delay_graph', style={"height": "400px", "margin": 0}),
            type="default",
            color="#8B0000"
        )
    ], width=6, style={"paddingRight": "15px"}),

    dbc.Col(
        dcc.Graph(figure=age_bar_plot, style={"height": "500px"}),
        width=6,
        style={"paddingLeft": "15px"}
    )
], className="mb-4")

## Neighbourhood Analysis
df_summary = df.pivot_table(index='Neighbourhood', columns='No-show', aggfunc='size', fill_value=0).reset_index()
df_summary.columns.name = None
df_summary['Total'] = df_summary['Showed up'] + df_summary['No show']
df_summary['NoShow%'] = (df_summary['No show'] / df_summary['Total']) * 100
filtered_df = df_summary[df_summary['Total'] >= 50]

neighbourhood_noshow_counts = df.groupby(['Neighbourhood', 'No-show']).size().reset_index(name='count')
neighbourhood_totals = neighbourhood_noshow_counts.groupby('Neighbourhood')['count'].transform('sum')
neighbourhood_noshow_counts['percent'] = neighbourhood_noshow_counts['count'] / neighbourhood_totals * 100

top_neighbourhoods = neighbourhood_noshow_counts.groupby('Neighbourhood')['count'].sum().nlargest(10).index
top_neighbourhood_data = neighbourhood_noshow_counts[neighbourhood_noshow_counts['Neighbourhood'].isin(top_neighbourhoods)]
top_neighbourhood_data = top_neighbourhood_data.sort_values('count', ascending=True)

neighbourhood_section = dbc.Row([
    dbc.Col([
        dcc.Loading(
            dcc.Graph(
                figure=px.scatter(
                    filtered_df,
                    x='NoShow%',
                    y='Total',
                    hover_name='Neighbourhood',
                    title='Neighbourhood No-show Analysis',
                    labels={'NoShow%': 'No-show Percentage', 'Total': 'Total Appointments'},
                    color='NoShow%',
                    color_continuous_scale='Reds',
                    size='Total',
                    height=500
                )
            ),
            type="default",
            color="#8B0000"
        )
    ], width=6),

    dbc.Col([
        dcc.Loading(
            dcc.Graph(
                figure=px.bar(
                    top_neighbourhood_data,
                    y='Neighbourhood',
                    x='count',
                    color='No-show',
                    title='Show vs No-show Count by Top 5 Neighbourhoods',
                    labels={'percent': 'Percentage (%)', 'Neighbourhood': 'Neighbourhood'},
                    barmode='stack',
                    orientation='h',
                    height=500,
                    color_discrete_map={
                        'Showed up': "#E0BCBC",
                        'No show': '#8B0000'
                    }
                ).update_layout(xaxis_tickangle=45)
            ),
            type="default",
            color="#8B0000"
        )
    ], width=6)
])

# ------------------------
# Callbacks
# ------------------------
@callback(
    Output('delay_graph', 'figure'),
    Input('delay_range_slider', 'value')
)
def draw_delay_graph(value):
    delay_group = df.groupby(['Delay_Days', 'No-show']).size().reset_index(name='count')
    delay_group['percent'] = delay_group['count'] / delay_group.groupby('Delay_Days')['count'].transform('sum') * 100
    delay_group = delay_group[(delay_group['No-show'] == 'No show') & (delay_group['Delay_Days'].between(value[0], value[1]))]

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
    line_plot.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    return line_plot

# ------------------------
# Layout & Tabs
# ------------------------
delay_tab = dbc.Card(dbc.CardBody([visual_section]), className="mt-3")
neighbourhood_tab = dbc.Card(dbc.CardBody([neighbourhood_section]), className="mt-3")

tabs = dbc.Tabs([
    dbc.Tab(delay_tab, label="Delay Days"),
    dbc.Tab(neighbourhood_tab, label="Neighbourhood"),
    dbc.Tab("This tab's content is never seen", label="Tab 3", disabled=True)
])

app.layout = dbc.Container([
    title_section,
    kpi_cards,
    tabs
], fluid=True)

# ------------------------
# Run Server
# ------------------------
if __name__ == '__main__':
    app.run(debug=True)
