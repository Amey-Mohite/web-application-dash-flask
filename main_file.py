import dash
from dash import Dash, dcc, html, Input, Output, State,dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import geopandas as gpd 
import matplotlib.pyplot as plt
import folium 
from shapely.ops import nearest_points
from shapely.geometry import LineString

from sqlalchemy import Table, create_engine
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
import sqlite3

import os
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
import configparser

import base64
import io
import time

import webbrowser
from threading import Timer

import warnings
warnings.filterwarnings("ignore")

# Data base initilization
conn = sqlite3.connect('data.sqlite')
engine = create_engine('sqlite:///data.sqlite')
db = SQLAlchemy()
config = configparser.ConfigParser()

# USer table model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable = False)
    email = db.Column(db.String(50))
    password = db.Column(db.String(80))

Users_tbl = Table('users', Users.metadata)

# creating table
def create_users_table():
    Users.metadata.create_all(engine)

try:
    create_users_table()
except:
    print("table already present")

#Dash server
app = dash.Dash(__name__)
server = app.server
app.config.suppress_callback_exceptions = True

# Database Config
server.config.update(
    SECRET_KEY=os.urandom(12),
    SQLALCHEMY_DATABASE_URI='sqlite:///data.sqlite',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
db.init_app(server)

# Inilialising login manager
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

class Users(UserMixin, Users):
    pass




# Perticular DIV for every page.
create = html.Div([ html.H1('Create User Account')
        , dcc.Location(id='create_user', refresh=True)
        , dcc.Input(id="username"
            , type="text"
            , placeholder="user name"
            , maxLength =15
            , style = {'color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px"})
        ,html.Br()
        , dcc.Input(id="password"
            , type="password"
            , placeholder="password"
            , style = {'color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px"})
        ,html.Br()            
        , dcc.Input(id="email"
            , type="email"
            , placeholder="email"
            , maxLength = 50
            , style = {'color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px"})
        ,html.Br()             
        , html.Button('Create User', id='submit-val', n_clicks=0
        , style = {'border':'2px white solid', 'borderRadius':13,"backgroundColor":'#0000FF','color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px",'width' : '316.8px'})
        , html.Div(id='container-button-basic')
    ],
        style = {'margin-left': '600px'}
    )#end div

login =  html.Div([dcc.Location(id='url_login', refresh=True)
            , html.H2('''Please log in to continue:''', id='h1')
            ,html.Br()  
            , dcc.Input(placeholder='Enter your username',
                    type='text',
                    id='uname-box',
                    style = {'color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px"})
            ,html.Br()  
            , dcc.Input(placeholder='Enter your password',
                    type='password',
                    id='pwd-box',
                    style = {'color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px"})
            ,html.Br()  
            , html.Button(children='Login',
                    n_clicks=0,
                    type='submit',
                    id='login-button',
                    style = {'border':'2px white solid', 'borderRadius':13,"backgroundColor":'#0000FF','color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px",'width' : '316.8px'})
            , html.Div(children='', id='output-state')
        ],
         style = {'margin-left': '600px'}) #end div

failed = html.Div([ dcc.Location(id='url_login_df', refresh=True)
            , html.Div([html.H2('Log in Failed. Please try again.')
                    , html.Br()
                    , html.Div([login])
                    , html.Br()
                    , html.Button(id='back-button', children='Go back', n_clicks=0,style = {'border':'2px white solid', 'borderRadius':13,"backgroundColor":'#0000FF','color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px",'width' : '316.8px'})
                ]) #end div
        ],style = {'margin-left': '600px'}) #end div
      
logout = html.Div([dcc.Location(id='logout', refresh=True)
        , html.Br()
        , html.Div(html.H2('You have been logged out - Please login'))
        , html.Br()
        , html.Div([login])
        , html.Button(id='back-button', children='Go back', n_clicks=0,style = {'border':'2px white solid', 'borderRadius':13,"backgroundColor":'#0000FF','color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px",'width' : '316.8px'})
    ],style = {'margin-left': '600px'})#end div


# page layout
app.layout= html.Div([
            html.Div(id='page-content', className='content')
            ,  dcc.Location(id='url', refresh=False)
        ])

# callback on login user
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# callback for page traversel
@app.callback(
    Output('page-content', 'children')
    , [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return create
    elif pathname == '/login':
        return login
    elif pathname == '/success':
        if current_user.is_authenticated:
            return success
        else:
            return failed
    elif pathname == '/logout':
        if current_user.is_authenticated:
            logout_user()
            return logout
        else:
            return logout
    else:
        return '404'


# Callback for register
@app.callback(
   [Output('container-button-basic', "children")]
    , [Input('submit-val', 'n_clicks')]
    , [State('username', 'value'), State('password', 'value'), State('email', 'value')])
def insert_users(n_clicks, un, pw, em):
    if un is not None and pw is not None and em is not None:
        ins = Users_tbl.insert().values(username=un,  password=pw, email=em)
        conn = engine.connect()
        conn.execute(ins)
        conn.close()
        return [html.Div([html.H2('User is successfully created '), dcc.Link('Click here to Log In', href='/login')])]
    else:
        return [html.Div([html.H2('Already have a user account?'), dcc.Link('Click here to Log In', href='/login')])]

# On successfull login will go to success page
@app.callback(
    Output('url_login', 'pathname')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])
def successful(n_clicks, input1, input2):
    user = Users.query.filter_by(username=input1).first()
    if user:
        if user.password == input2:
            login_user(user)
            return '/success'
        else:
            pass
    else:
        pass


# checking for user in db
@app.callback(
    Output('output-state', 'children')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')])
def update_output(n_clicks, input1, input2):
    if n_clicks > 0:
        user = Users.query.filter_by(username=input1).first()
        if user:
            if user.password== input2:
                return ''
            else:
                return 'Incorrect username or password'
        else:
            return 'Incorrect username or password'
    else:
        return ''


# logout
@app.callback(
    Output('url_login_success', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'

@app.callback(
    Output('url_login_df', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'

# Create callbacks
@app.callback(
    Output('url_logout', 'pathname')
    , [Input('back-button', 'n_clicks')])
def logout_dashboard(n_clicks):
    if n_clicks > 0:
        return '/'




def create_gdf(df, x="Latitude", y="Longitude"):
    return gpd.GeoDataFrame(df,geometry=gpd.points_from_xy(df[x], df[y]),crs={"init":"EPSG:4326"})

def calculate_nearest(row, destination, val, col="geometry"):
    dest_unary = destination["geometry"].unary_union
    nearest_geom = nearest_points(row[col], dest_unary)
    match_geom = destination.loc[destination.geometry == nearest_geom[1]]
    match_value = match_geom[val].to_numpy()[0]
    return match_value


# checking for csv file
# @app.callback(
#    Output('container-button-basic1','children'),#,Output('f1','srcDoc')
#     Input('submit-val', 'n_clicks'),
#     [State('first', 'value'),
#     State('second', 'value')]
# )
# def read_data(n_clicks, value1,value2):
#     if n_clicks>0:
#         if value1.split('.')[-1] != 'csv' or value2.split('.')[-1] != 'csv':
#             n_clicks = 0
#             return("Please provide .csv files")
#         else:
#             return("")

@app.callback(Output('output-data-upload1', 'children'),
              Input('first', 'contents'),
              State('first', 'filename'))
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [ parse_contents(list_of_contents, list_of_names)]
        return children


@app.callback(Output('output-data-upload2', 'children'),
              Input('second', 'contents'),
              State('second', 'filename'))
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [
            parse_contents(list_of_contents, list_of_names)]
        return children


def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])
    return df

#passing table and map to dashboard
@app.callback(
   [Output('div-1', "children"),Output('f1','srcDoc')],#,Output('f1','srcDoc')
    [Input('submit-val', 'n_clicks'),
    Input('first', 'contents'),
    Input('first', 'filename'),
    Input('second', 'contents'),
    Input('second', 'filename')
    ]
        )
def update_output(n_clicks, contents1,filename1,contents2,filename2):
    if n_clicks>0:
        if filename1.split('.')[-1] != 'csv' or filename2.split('.')[-1] != 'csv':
            n_clicks = 0
        else:

            hotels = parse_data(contents1, filename1)
            restaurants = parse_data(contents2, filename2)
            hotel_gdf = create_gdf(hotels)
            restaurant_gdf = create_gdf(restaurants)

            restaurant_gdf["nearest_geom"] = restaurant_gdf.apply(calculate_nearest, destination=hotel_gdf, val="geometry", axis=1)
            restaurant_gdf["nearest_hotel"] = restaurant_gdf.apply(calculate_nearest, destination=hotel_gdf, val="geometry", axis=1)
            restaurant_gdf['line'] = restaurant_gdf.apply(lambda row: LineString([row['geometry'], row['nearest_geom']]), axis=1)

            line_gdf = restaurant_gdf[["OBJECTID", "nearest_hotel", "line"]].set_geometry('line')
            line_gdf.crs = crs={"init":"epsg:4326"}

            restaurant_gdf.drop(["nearest_geom", "line"], axis=1, inplace=True)
            m = folium.Map([40.703235, -74.012421],
                        zoom_start= 12,
                        tiles="CartoDb dark_matter")
            locs_hotel = zip(hotel_gdf.Latitude, hotel_gdf.Longitude)
            locs_restaurant = zip(restaurant_gdf.Latitude, restaurant_gdf.Longitude)
            for location in locs_hotel:
                folium.CircleMarker(location=location, color="blue", radius=8).add_to(m)
            for location in locs_restaurant:
                folium.CircleMarker(location=location, color="red", radius=4).add_to(m)
            m.save("map2.html")
            restaurant_gdf['geometry'] = restaurant_gdf['geometry'].astype(str)
            restaurant_gdf['nearest_hotel'] = restaurant_gdf['nearest_hotel'].astype(str)
            return [
                        dash_table.DataTable(
                            data=restaurant_gdf.to_dict('rows'),
                            columns =  [{"name": i, "id": i,} for i in (restaurant_gdf.columns)],
                            style_data={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                        },
                                        page_size=15
                        ),open('map2.html', 'r').read()
                    ]


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        else:
            return html.Div([
            'Please provide .csv files'
        ])

    except Exception as e:
        print(e)
        return html.Div([
            'Please provide .csv files'
        ])

    return html.Div([
        html.H5(filename)
    ])




success = html.Div(
    children=[
        dcc.Location(id='url_login_success', refresh=True),
        html.H1(children="Nearest Restraurants",),
        html.Div(children=[
        
        dcc.Upload(
        id='first',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select .CSV File')
        ]),style={
            'width': '25%',
            'height': '30px',
            'lineHeight': '30px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center'
        }),
        html.Div(id='output-data-upload1'),

        dcc.Upload(
        id='second',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select .CSV File')
        ]),style={
            'width': '25%',
            'height': '30px',
            'lineHeight': '30px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center'
        }),
        html.Div(id='output-data-upload2'),

        # dcc.Input(id='first',placeholder = 'path of hotel.csv', type='text',style = {"marginBottom": "15px",'color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
        # 'position': 'relative','left': '0px'}),
        # dcc.Input(id='second',placeholder = 'path of restraurant.csv', type='text',style = {"margin-left": "15px","marginBottom": "15px",'color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center'}),
        
        html.Button('Submit', id='submit-val', n_clicks=0,style={'border':'2px white solid', 'borderRadius':13,"backgroundColor":'#0000FF','font-size': '25px', 'width': '140px', 'display': 'inline-block', 'marginBottom': '15px', "margin-left": "15px", 'height':'35px', 'verticalAlign': 'top'}),
        html.Button(id='back-button', children='Logout', n_clicks=0,style = {'border':'2px white solid', 'borderRadius':13,"backgroundColor":'#0000FF','color':'black','font-family': "Times New Roman",'font-size': '25px','text-align':'center',
                    "marginBottom": "15px",'width' : '140px','float':'right'}),
        html.P(id='container-button-basic1')]
        ),
        html.Div(children=[
            dcc.Loading(
            id="loading-1",
            type="default",
            children=[
                        html.Div(id="div-1",style = {'float': 'left','width':'45%'}),
                        html.Iframe( id  = 'f1', style = {'float': 'right','width':'50%','height':'500px'})
                        ]
                            
                        )]
        ),      
    ]
)

port = 5000

def open_browser():
    	webbrowser.open_new("http://localhost:{}".format(port))

if __name__ == '__main__':
    Timer(1, open_browser).start();
    app.run_server(debug=False, port=port)