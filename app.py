from dash import Dash, html, dcc, Output, Input, callback
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------------
# Load Data
# ------------------------
df = pd.read_csv('data.csv')

# ------------------------
# App Initialization
# ------------------------
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap"
]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# ------------------------
# Filter Function
# ------------------------
def filter_data(gender, age_range, disease):
    filtered = df.copy()
    if gender != 'All':
        filtered = filtered[filtered['Gender'] == gender]
    if disease != 'All':
        filtered = filtered[filtered[disease] == 1]
    filtered = filtered[filtered['Age'].between(age_range[0], age_range[1])]
    return filtered

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

## Filters
filter_row = dbc.Row([
    dbc.Col([
        html.Label("Gender"),
        dcc.Dropdown(
            id='gender_filter',
            options=[{'label': g, 'value': g} for g in sorted(df['Gender'].unique())] + [{'label': 'All', 'value': 'All'}],
            value='All',
            clearable=False
        )
    ], width=3),

    dbc.Col([
        html.Label("Age Range"),
        dcc.RangeSlider(
            id='age_filter',
            min=df['Age'].min(),
            max=df['Age'].max(),
            step=1,
            value=[df['Age'].min(), df['Age'].max()],
            marks={int(a): str(int(a)) for a in np.linspace(df['Age'].min(), df['Age'].max(), num=6)},
            tooltip={"placement": "bottom", "always_visible": False}
        )
    ], width=6),

    dbc.Col([
        html.Label("Disease"),
        dcc.Dropdown(
            id='disease_filter',
            options=[
                {'label': 'All', 'value': 'All'},
                {'label': 'Hypertension', 'value': 'Hipertension'},
                {'label': 'Diabetes', 'value': 'Diabetes'},
                {'label': 'Alcoholism', 'value': 'Alcoholism'},
                {'label': 'Handicap', 'value': 'Handcap'}
            ],
            value='All',
            clearable=False
        )
    ], width=3)
], className="mb-4")

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

kpi_cards = dbc.Row(id="kpi_cards", className="mb-4 text-center")

## Visual Section with Delay Graph and Age Bar Plot
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

    dbc.Col([
        dcc.Loading(
            dcc.Graph(id="age_bar_chart", style={"height": "500px"}),
            type="default",
            color="#8B0000"
        )
    ], width=6, style={"paddingLeft": "15px"})
], className="mb-4")

# Neighbourhood Section (fixed alignment)
neighbourhood_section = html.Div([
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Loading(
                    dcc.Graph(id="neighbourhood_scatter", style={"height": "500px", "paddingTop": "50px"}),
                    type="default",
                    color="#8B0000"
                )
            ], style={"position": "relative"})
        ], width=6),

        dbc.Col([
            html.Div([
                # Centered Dropdown
                html.Div([
                    html.Label("Top Neighbourhoods Count", style={
                        "marginRight": "10px",
                        "fontWeight": "600"
                    }),
                    dcc.Dropdown(
                        id="top_n_input",
                        options=[{"label": str(i), "value": i} for i in [5, 10, 15, 20, 25, 30]],
                        value=5,
                        clearable=False,
                        style={"width": "100px"}
                    )
                ], style={
                    "position": "absolute",
                    "top": "10px",
                    "left": "50%",
                    "transform": "translateX(-50%)",
                    "zIndex": "10",
                    "backgroundColor": "white",
                    "padding": "6px 12px",
                    "borderRadius": "8px",
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.15)",
                    "display": "flex",
                    "alignItems": "center"
                }),

                dcc.Loading(
                    dcc.Graph(id="neighbourhood_bar", style={"height": "500px", "paddingTop": "50px"}),
                    type="default",
                    color="#8B0000"
                )
            ], style={"position": "relative"})
        ], width=6)
    ])
])


# ------------------------
# Callbacks
# ------------------------

## KPIs
@callback(
    Output("kpi_cards", "children"),
    Input("gender_filter", "value"),
    Input("age_filter", "value"),
    Input("disease_filter", "value")
)
def update_kpis(gender, age_range, disease):
    filtered_df = filter_data(gender, age_range, disease)
    if filtered_df.empty:
        return [create_kpi_card("No Data", "—")] * 3

    summary = filtered_df.groupby('No-show').size().reset_index(name='count')
    summary['pct'] = summary['count'] / summary['count'].sum() * 100
    no_show_pct = round(summary.loc[summary['No-show'] == 'No show', 'pct'].values[0], 2) if 'No show' in summary['No-show'].values else 0
    total_no_show = int(summary.loc[summary['No-show'] == 'No show', 'count'].values[0]) if 'No show' in summary['No-show'].values else 0
    repeat = filtered_df[filtered_df['No-show'] == 'No show'].groupby('PatientId').size()
    repeat_pct = round(repeat[repeat >= 2].sum() / total_no_show * 100, 2) if total_no_show > 0 else 0

    return [
        create_kpi_card("Overall No-Show Rate", f"{no_show_pct}%"),
        create_kpi_card("Total Missed Appointments", total_no_show),
        create_kpi_card("Impact of Repeat Offenders", f"{repeat_pct}%")
    ]

## Delay Graph
@callback(
    Output('delay_graph', 'figure'),
    Input('delay_range_slider', 'value'),
    Input('gender_filter', 'value'),
    Input('age_filter', 'value'),
    Input('disease_filter', 'value')
)
def draw_delay_graph(delay_range, gender, age_range, disease):
    filtered_df = filter_data(gender, age_range, disease)
    delay_group = filtered_df.groupby(['Delay_Days', 'No-show']).size().reset_index(name='count')
    delay_group['percent'] = delay_group['count'] / delay_group.groupby('Delay_Days')['count'].transform('sum') * 100
    delay_group = delay_group[(delay_group['No-show'] == 'No show') & (delay_group['Delay_Days'].between(delay_range[0], delay_range[1]))]

    fig = px.line(
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
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
    return fig

## Age Bar Chart
@callback(
    Output('age_bar_chart', 'figure'),
    Input('gender_filter', 'value'),
    Input('age_filter', 'value'),
    Input('disease_filter', 'value')
)
def update_age_bar(gender, age_range, disease):
    filtered_df = filter_data(gender, age_range, disease)
    age_crosstab = pd.crosstab(filtered_df['AgeGroup'], filtered_df['No-show'])
    if 'No show' not in age_crosstab.columns:
        return px.bar(title="No-show Percentage by Age Group (No Data)")
    pct = (age_crosstab['No show'] / age_crosstab.sum(axis=1) * 100).sort_values(ascending=False)
    age_data = pct.reset_index(name='Percentage')
    fig = px.bar(
        age_data,
        x='AgeGroup',
        y='Percentage',
        color='Percentage',
        color_continuous_scale='Reds',
        labels={'AgeGroup': 'Age Group', 'Percentage': 'No-show Percentage'},
        title='No-show Percentage by Age Group'
    )
    return fig

## Neighbourhood Graphs
@callback(
    Output("neighbourhood_scatter", "figure"),
    Output("neighbourhood_bar", "figure"),
    Input("gender_filter", "value"),
    Input("age_filter", "value"),
    Input("disease_filter", "value"),
    Input("top_n_input", "value")
)
def update_neighbourhood(gender, age_range, disease, top_n):
    filtered_df = filter_data(gender, age_range, disease)
    if filtered_df.empty:
        return px.scatter(title="No Data"), px.bar(title="No Data")

    df_summary = filtered_df.pivot_table(index='Neighbourhood', columns='No-show', aggfunc='size', fill_value=0).reset_index()
    df_summary.columns.name = None
    df_summary['Total'] = df_summary.get('Showed up', 0) + df_summary.get('No show', 0)
    df_summary['NoShow%'] = df_summary['No show'] / df_summary['Total'] * 100
    df_summary = df_summary[df_summary['Total'] >= 50]

    bar_data = filtered_df.groupby(['Neighbourhood', 'No-show']).size().reset_index(name='count')
    total = bar_data.groupby('Neighbourhood')['count'].transform('sum')
    bar_data['percent'] = bar_data['count'] / total * 100

    top_n = top_n if top_n else 5
    top_neigh = bar_data.groupby('Neighbourhood')['count'].sum().nlargest(top_n).index
    top_data = bar_data[bar_data['Neighbourhood'].isin(top_neigh)].sort_values('count')

    scatter = px.scatter(
        df_summary,
        x='NoShow%',
        y='Total',
        hover_name='Neighbourhood',
        title='Neighbourhood No-show Analysis',
        color='NoShow%',
        size='Total',
        color_continuous_scale='Reds'
    )

    bar = px.bar(
        top_data,
        y='Neighbourhood',
        x='count',
        color='No-show',
        title=f'Show vs No-show Count by Top {top_n} Neighbourhoods',
        barmode='stack',
        orientation='h',
        height=500,
        color_discrete_map={
            'Showed up': "#E0BCBC",
            'No show': '#8B0000'
        }
    ).update_layout(xaxis_tickangle=45)

    return scatter, bar

# ------------------------
# Tabs
# ------------------------
delay_tab = dbc.Card(dbc.CardBody([visual_section]), className="mt-3")
neighbourhood_tab = dbc.Card(dbc.CardBody([neighbourhood_section]), className="mt-3")

tabs = dbc.Tabs([
    dbc.Tab(delay_tab, label="Delay Days"),
    dbc.Tab(neighbourhood_tab, label="Neighbourhood")
])

# ------------------------
# App Layout
# ------------------------
app.layout = dbc.Container([
    title_section,
    filter_row,
    kpi_cards,
    tabs
], fluid=True)

# ------------------------
# Run Server
# ------------------------
if __name__ == '__main__':
    app.run(debug=True)