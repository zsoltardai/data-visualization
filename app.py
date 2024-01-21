import json

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure
from dash import Dash, html, dcc, Input, Output

RELIGIONS: list[dict[str, str]] = [
    {'label': 'Katolikus', 'value': 'catholic'},
    {'label': 'Református', 'value': 'calvinist'},
    {'label': 'Evangélikus', 'value': 'lutheran'},
    {'label': 'Ortodox keresztény', 'value': 'orthodox_christian'},
    {'label': 'Más keresztény', 'value': 'other_christian'},
    {'label': 'Zsidó', 'value': 'jewish'},
    {'label': 'Egyéb', 'value': 'other'},
    {'label': 'Ateista', 'value': 'atheist'},
]

RELIGION_VALUES: list[str] = [x['value'] for x in RELIGIONS]


def load_geojson() -> dict:
    with open('assets/geo.json', mode='r', encoding='utf-8') as file:
        return json.load(file)


def merge_with_county_names(df: pd.DataFrame) -> pd.DataFrame:
    file = open('assets/counties.json', mode='r', encoding='utf-8')

    counties = json.load(file)

    file.close()

    df_l = pd.DataFrame({
        'id': [],
        'county': [],
    })

    for county in counties:
        name: str = county['name']
        for district_id in county['ids']:
            df_l.loc[len(df_l.index)] = {
                'id': district_id,
                'county': name,
            }

    df = df.merge(df_l, on='id')

    return df


def load_data_frame(year: int = 2011) -> pd.DataFrame:
    df = pd.read_json(
        f'assets/religious_denominations_{year}.json',
        orient='records',
        dtype={
            'id': 'string',
        }
    )

    df = merge_with_county_names(df)

    return df


def load_change_data_frame() -> pd.DataFrame:
    df = pd.read_json(
        f'assets/change_between_2011_and_2022_by_district.json',
        orient='records',
        dtype={
            'id': 'string',
        },
    )

    df = merge_with_county_names(df)

    return df


def transform_data_orientation(df: pd.DataFrame) -> pd.DataFrame:
    new_df = pd.DataFrame({
        'id': [],
        'county': [],
        'group': [],
        'value': [],
    })

    for record in df.to_records(index=False):
        for index, column in enumerate(df.columns):
            if column in RELIGION_VALUES:
                new_df.loc[len(new_df.index)] = {
                    'id': record[1],
                    'county': record[-1],
                    'group': column,
                    'value': record[index],
                }

    return new_df


def make_choropleth_map(df: pd.DataFrame, religion: str = 'catholic') -> Figure:
    geojson = load_geojson()

    labels: dict[str, str] = {
        'catholic': 'Katolikus',
        'calvinist': 'Református',
        'lutheran': 'Evangélikus',
        'orthodox_christian': 'Ortodox keresztény',
        'other_christian': 'Más keresztény',
        'jewish': 'Zsidó',
        'other': 'Egyéb',
        'atheist': 'Ateista',
    }

    figure = px.choropleth_mapbox(
        df,
        locations='id',
        color=religion,
        featureidkey='properties.id',  # we are using it to map the right data to the right district
        geojson=geojson,
        color_continuous_scale="Viridis",
        mapbox_style='white-bg',
        center={'lon': 19.040236, 'lat': 47.497913},  # Budapest
        zoom=5.2,
        custom_data=[religion],
        labels=labels,
    )

    figure.update_geos(fitbounds="locations", visible=False, projection_type='natural earth')

    figure.update_layout(mapbox_bounds={"west": 15, "east": 24, "south": 45, "north": 49})

    figure.update_traces(hovertemplate='Érték: %{customdata[0]} fő')

    return figure


def make_change_choropleth_map(df: pd.DataFrame, religion: str = 'catholic') -> Figure:
    df_copy = pd.DataFrame.copy(df)

    geojson = load_geojson()

    labels: dict[str, str] = {
        'change_catholic': 'Változás a katolikus népességben',
        'change_calvinist': 'Változás a református népességben',
        'change_lutheran': 'Változás az evangélikus népességben',
        'change_orthodox_christian': 'Változás az ortodox keresztény népességben',
        'change_other_christian': 'Változás az más keresztény népességekben',
        'change_jewish': 'Változás a zsidó népességben',
        'change_other': 'Változás az egyéb népességekben',
        'change_atheist': 'Változás az ateista népességben',
    }

    df_copy[f'change_{religion}'] = df_copy[f'change_{religion}'] * 100

    figure = px.choropleth_mapbox(
        df_copy,
        locations='id',
        color=f'change_{religion}',
        featureidkey='properties.id',  # we are using it to map the right data to the right district
        geojson=geojson,
        color_continuous_scale="Viridis",
        mapbox_style='white-bg',
        center={'lon': 19.040236, 'lat': 47.497913},  # Budapest
        zoom=4.5,
        custom_data=[round(df_copy[f'change_{religion}'], 2)],
        labels=labels,
    )

    figure.update_geos(fitbounds="locations", visible=False, projection_type='natural earth')

    figure.update_layout(mapbox_bounds={"west": 15, "east": 24, "south": 45, "north": 49}, coloraxis_colorbar_title_side="right")

    figure.update_traces(hovertemplate='Érték: %{customdata[0]}%')

    return figure


def make_bar_chart_by_county(df: pd.DataFrame) -> Figure:
    new_df = transform_data_orientation(df)

    figure = px.bar(new_df, x='county', y='value', color='group', labels={'group': 'Vallás'})

    figure.update_layout(xaxis={'categoryorder': 'total descending'}, plot_bgcolor='white')

    figure.update_xaxes(title_text='Közigazgatási egységek', showgrid=False)

    figure.update_yaxes(title_text='Vallást gyakorlók száma', showgrid=False)

    return figure


def make_bar_chart_by_county_and_group(df: pd.DataFrame, group: str = None) -> Figure:
    new_df = transform_data_orientation(df)

    new_df = new_df[new_df['group'] == group]

    figure = px.bar(new_df, x='county', y='value')

    figure.update_layout(xaxis={'categoryorder': 'total descending'}, plot_bgcolor='white')

    figure.update_xaxes(title_text='Közigazgatási egységek', showgrid=False)

    figure.update_yaxes(title_text='Vallást gyakorlók száma', showgrid=False)

    return figure


def transform_changes_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    new_df = pd.DataFrame({
        'id': [],
        'county': [],
        'group': [],
        'value': [],
    })

    column_names = list(map(lambda x: f'change_{x}', RELIGION_VALUES))

    for record in df.to_records(index=False):
        for index, column in enumerate(df.columns):
            if column in column_names:
                new_df.loc[len(new_df.index)] = {
                    'id': record[0],
                    'county': record[-1],
                    'group': column,
                    'value': record[index],
                }

    new_df['value'] = round(new_df['value'] * 100, 2)

    return new_df


def make_bar_chart_of_changes_by_group(df: pd.DataFrame, group: str = 'catholic') -> Figure:
    new_df = transform_changes_data_frame(df)

    new_df = new_df[new_df['group'] == f'change_{group}']

    final_df = pd.DataFrame({
        'county': [],
        'average_change': [],
    })

    for county in pd.unique(new_df['county']):
        final_df.loc[len(final_df.index)] = {
            'county': county,
            'average_change': new_df[new_df['county'] == county]['value'].mean(),
        }

    figure = px.bar(final_df, x='county', y='average_change')

    figure.update_layout(xaxis={'categoryorder': 'total descending'}, plot_bgcolor='white')

    figure.update_xaxes(title_text='Közigazgatási egységek', showgrid=False)

    figure.update_yaxes(title_text='Változás a gyakorlók számában', showgrid=False)

    return figure


def main() -> None:
    df_2011 = load_data_frame(2011)

    df_2022 = load_data_frame(2022)

    change_df = load_change_data_frame()

    app = Dash()

    row_style: dict[str, str] = {
        'display': 'flex',
        'flex-direction': 'row',
        'gap': '24px',
        'align-items': 'center',
        'justify-content': 'center',
    }

    app.layout = html.Div([
        html.Div(
            [
                dcc.Markdown('Vallást gyakorlók száma járásonként a tárgyévben', style={'text-align': 'center'}),
                html.Div(
                    [
                        choropleth_map := dcc.Graph(),
                        single_religion_bar_chart := dcc.Graph(),
                    ],
                    style=row_style,
                ),
                html.Div([
                    html.Div([
                        html.Div(
                            [
                                dcc.Markdown('Válassz vallást'),
                                html.Div(
                                    group := dcc.Dropdown(
                                        id='denomination',
                                        options=RELIGIONS,
                                        value='catholic',
                                        style={'width': '200px'},
                                    ),
                                    style={'flex': '1'},
                                )
                            ],
                            style=row_style,
                        ),
                        html.Div(
                            [
                                dcc.Markdown('Népszámlálás éve'),
                                html.Div(
                                    census := dcc.Dropdown(
                                        id='census',
                                        options=[2011, 2022],
                                        value=2011,
                                        style={'width': '200px'},
                                    ),
                                    style={'flex': '1'},
                                )
                            ],
                            style=row_style,
                        ),
                    ], style=row_style)
                ]),
                every_religion_bar_chart := dcc.Graph(),
                dcc.Markdown('Változások 2011 és 2022 között vallásonként', style={'text-align': 'center'}),
                html.Div([
                    change_map := dcc.Graph(),
                    change_bar := dcc.Graph(figure=make_bar_chart_of_changes_by_group(change_df)),
                ], style=row_style),
            ]
        ),
    ])

    def get_data_frame_by_year(year: int = 2011) -> pd.DataFrame:
        if year == 2011:
            return df_2011
        elif year == 2022:
            return df_2022

    @app.callback(
        Output(component_id=choropleth_map, component_property='figure'),
        Input(component_id=census, component_property='value'),
        Input(component_id=group, component_property='value'),
    )
    def update_map(selected_census, selected_group) -> Figure:
        df = get_data_frame_by_year(selected_census)
        return make_choropleth_map(df, selected_group)

    @app.callback(
        Output(component_id=single_religion_bar_chart, component_property='figure'),
        Input(component_id=census, component_property='value'),
        Input(component_id=group, component_property='value'),
    )
    def update_single_religion_bar_chart(selected_census: int, selected_group: str) -> Figure:
        df = get_data_frame_by_year(selected_census)
        return make_bar_chart_by_county_and_group(df, selected_group)

    @app.callback(
        Output(component_id=every_religion_bar_chart, component_property='figure'),
        Input(component_id=census, component_property='value'),
    )
    def update_every_religion_bar_chart(selected_census: int) -> Figure:
        df = get_data_frame_by_year(selected_census)
        return make_bar_chart_by_county(df)

    @app.callback(
        Output(component_id=change_map, component_property='figure'),
        Input(component_id=group, component_property='value'),
    )
    def update_change_map(selected_group: str) -> Figure:
        return make_change_choropleth_map(change_df, selected_group)

    @app.callback(
        Output(component_id=change_bar, component_property='figure'),
        Input(component_id=group, component_property='value'),
    )
    def update_change_map(selected_group: str) -> Figure:
        return make_bar_chart_of_changes_by_group(change_df, selected_group)

    app.run_server(debug=True, use_reloader=False)


if __name__ == '__main__':
    main()

# TODO !important
# 1. Merge 2011 & 2022 DataFrame(s) ?
# 2. Add change in number to the DataFrame DONE
# 3. Display change in percentage on a different choropleth_mapbox DONE
# 4. Add the possibility to toggle between 2011 & 2022 data | DONE
# TODO not important
# 5. Add a pie chart to show catholic denominations
# 6. Add educational attainment level choropleth map
# 7. Add map to display change between 2011 & 2022 DONE
# 8. Add bar chart to display chane between 2011 & 2022 DONE
