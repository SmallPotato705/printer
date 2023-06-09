import dash
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objs as go
import numpy as np
from flask import Flask, Response
import serial
import queue
import threading
import csv
import time
import asyncio
import base64
# import cv2
import dash_bootstrap_components as dbc
import subprocess
import os
import dash_daq as daq
import requests
import cv2


import os


# =============================================================================
# 
# =============================================================================
usbFPS = 10
imx462FPS = 10

showWidthUSB = 640
showHeightUSB = 480

saveWidthUSB = 640
saveHeightUSB = 480

showWidthIMX462 = 640
showHeightIMX462 = 480

saveWidthIMX462 = 640
saveHeightIMX462 = 480



saveDataFlag = 0
runAs7265 = True
updateImageCSI = False
updateImageUSB = False

xAxis=["410", "435", "460", "485", "510", "535", 
       "560", "585", "610", "645", "680", "705", 
       "730", "760", "810", "860", "900", "940"]

colors = ['#F7DC6F', '#82E0AA', '#5499C7', '#AF7AC5', '#F1948A', '#73C6B6', '#F5B7B1', '#85C1E9', '#BB8FCE', 
          '#F8C471', '#76D7C4', '#D7BDE2', '#F0B27A', '#7FB3D5', '#D2B4DE', '#E59866', '#7DCEA0', '#AED6F1']

external_stylesheets = [
    {
        'href': 'https://fonts.googleapis.com/css2?family=Roboto&display=swap',
        'rel': 'stylesheet'
    },
    {
        'href': 'https://cdn.jsdelivr.net/npm/tailwindcss/dist/tailwind.min.css',
        'rel': 'stylesheet'
    }
]



titleTestSize = '28'

allSenserValuesY = []
allSenserValuesX = []


os.chdir("/home/pi/raspberrypi/i2c_cmd/bin/")
levelIndex = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "e"]
commandList = ["wdrmode", "denoise", "agc", "lowlight", "daynightmode"]
wdrModeList = ['Backlight Mode off', 'Low Backlight', 'High Backlight', 'DOL-WDR']
mirrorModeList = ['Normal', 'mirror image', 'Flip vertically', 'Mirror and flip vertically']

Imx462_Path = "v4l2src device=/dev/video0 ! video/x-raw,format=(string)UYVY, width=(int)1920, height=(int)1080,framerate=(fraction)30/1 ! videoscale ! video/x-raw, width=" + str(showWidthIMX462) + ", height=" + str(showHeightIMX462) + "! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
saveVideoPath = "/home/pi/Desktop/取像模組0508/5.synchronize/SaveVideo/"
usbPath = 0

saveDataImx462 = 0
saveDataAs7265 = 0
saveDataUSB = 0

csiDelay = 0
usbDelay = 0

ttyUSB0 = False
ttyUSB1 = False
connectUSB = False
connectCSI = False

try:
    ser = serial.Serial('/dev/ttyUSB0', 115200)
except:
    try:
        ser = serial.Serial('/dev/ttyUSB1', 115200)
    except:
        pass
    
savefileName = "output"

q = queue.Queue(maxsize = 0)

# =============================================================================
# 
# =============================================================================
server = Flask(__name__)
app = Dash(server=server, external_stylesheets=external_stylesheets)


# =============================================================================
# 
# =============================================================================
def get_cpu_load():

    output = os.popen("top -n1 -b | grep 'Cpu(s)'").read()
    load = output.strip().split()[1]
    
    return float(load)

    
class Imx462_VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(Imx462_Path, cv2.CAP_GSTREAMER)
    def __del__(self):
        self.video.release()

    def get_frame(self):
 
        _, image = self.video.read()

        _, jpeg = cv2.imencode('.jpg', image)
        
        return jpeg.tobytes(), image
 
class setUSB_VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(usbPath, cv2.CAP_GSTREAMER)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, float(showWidthUSB)) 
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, float(showHeightUSB))  
        
    def __del__(self):
        self.video.release()

    def get_frame(self):
        
        _, image = self.video.read()
 
        _, jpeg = cv2.imencode('.jpg', image)
        
        return jpeg.tobytes(), image
        
def setImx462_Image(camera):
    
    global saveDataImx462, savefileName, Imx462_Path, connectCSI, csiDelay, imx462FPS, saveWidthIMX462, saveHeightIMX462, updateImageCSI
    
    index = 1
    count = 1
    while True:

        time.sleep(csiDelay)
        
        success, _ = camera.video.read()
        
        if success:
            connectCSI = True
            try:
                frame, image = camera.get_frame()
                if saveDataImx462 == 1:
                    if index == 1:
                        fourcc = cv2.VideoWriter_fourcc(*'XVID')
                        
                        out = cv2.VideoWriter((saveVideoPath + savefileName + "_IMX462.avi"), fourcc, imx462FPS, (saveWidthIMX462, saveHeightIMX462))
                        index = 0
                        
                    image2 = cv2.resize(image, (saveWidthIMX462, saveHeightIMX462))
                    
                    out.write(image2)
                    
                elif saveDataImx462 == 0 and index == 0:
                    out.release()
                    index = 1
                
                yield(b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                      
                      
                if updateImageCSI == True:
                    updateImageCSI = False
                    camera.__del__()
                    time.sleep(1)
                    
                      
            except:
                camera.__del__()

                time.sleep(1)
                
        else:
            connectCSI = False
            if count == 1:
                Imx462_Path = "v4l2src device=/dev/video0 ! video/x-raw,format=(string)UYVY, width=(int)1920, height=(int)1080,framerate=(fraction)30/1 ! videoscale ! video/x-raw, width=" + str(showWidthIMX462) + ", height=" + str(showHeightIMX462) + "! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
            elif count == 2:
                Imx462_Path = "v4l2src device=/dev/video1 ! video/x-raw,format=(string)UYVY, width=(int)1920, height=(int)1080,framerate=(fraction)30/1 ! videoscale ! video/x-raw, width=" + str(showWidthIMX462) + ", height=" + str(showHeightIMX462) + "! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
            elif count == 3:
                Imx462_Path = "v4l2src device=/dev/video2 ! video/x-raw,format=(string)UYVY, width=(int)1920, height=(int)1080,framerate=(fraction)30/1 ! videoscale ! video/x-raw, width=" + str(showWidthIMX462) + ", height=" + str(showHeightIMX462) + "! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
            
                count = 1
            count += 1
            camera.__init__()
            time.sleep(1)
        

def setUSB_Image(camera):
    global usbPath, saveDataUSB, savefileName, connectUSB, usbDelay, usbFPS, saveWidthUSB, saveHeightUSB, updateImageUSB
    index = 1
    
    while True:

        time.sleep(usbDelay)
        
        success, _ = camera.video.read()
        
        if success:  
            connectUSB = True
            try:
                frame, image = camera.get_frame()
                if saveDataUSB == 1:
                    if index == 1:
                        fourcc = cv2.VideoWriter_fourcc(*'XVID')
                        out = cv2.VideoWriter((saveVideoPath + savefileName + "_USB.avi"), fourcc, usbFPS, (saveWidthUSB, saveHeightUSB))
                        index = 0
                        
                    image2 = cv2.resize(image, (saveWidthUSB, saveHeightUSB))
                    
                    out.write(image2)
                    
                elif saveDataUSB == 0 and index == 0:
                    out.release()
                    index = 1
                    
                
                if updateImageUSB == True:
                    updateImageUSB = False
                    camera.__del__()
                    time.sleep(1)

                yield(b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
       
            except:
                camera.__del__()
                time.sleep(1)
                
        else:  
            connectUSB = False
            usbPath = 0 if int(usbPath) == 3 else int(usbPath) + 1
            camera.__init__()
            time.sleep(1)
  
        
def getSensorData():
    global savefileName, saveDataAs7265, ser
    
    while runAs7265:
        try:
            sensorData = ser.readline().decode().strip()  
            new_sensor_values = [int(val) for val in sensorData.split(',')]  
            if saveDataAs7265 == 1:
                with open(saveVideoPath + savefileName + "As7265.csv", 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(new_sensor_values)
            
            if q.qsize() == 1:
                q.get()  

            q.put(new_sensor_values)
        except:
            try:
                if ser.isOpen():
                    ser.close()
            except:
                pass
                
            break


# =============================================================================
# 
# =============================================================================
def webLayout():
    nowLevel = pd.DataFrame(np.zeros((1, len(commandList))), columns = commandList)
    switchValies = False
    for command in commandList:
        receivedData = subprocess.check_output("./veye_mipi_i2c.sh -r -f " + command, shell = True)
        
        for index, nums in enumerate(levelIndex):
            if nums == receivedData.decode("utf-8").split("\n")[0][-1]:
                nowLevel[command] = index
                
    if((nowLevel["daynightmode"] == 15).bool()):
        switchValies = False
    elif((nowLevel["daynightmode"] == 16).bool()):
        switchValies = True
            
            
    app.layout = html.Div([
        # =============================================================================
        # 左半部份    
        # =============================================================================
        dcc.Interval(
            id='chcekCamera',
            interval = 3000,
            n_intervals = 0,
            disabled=False
        ),
        
        
        dcc.Interval(
            id = 'connectedInterval',
            interval = 5000,
            n_intervals = 0,
            disabled = False
        ),
                
        dbc.Row([
            html.Div("", id = "SerialMesaage"),
            html.Div("", id = "USBMesaage"),
            html.Div("", id = "CSIMesaage"),
            html.Div("", id = "cpuLoad"),
            # =============================================================================
            #         
            # =============================================================================
            
            
            dbc.Col(children=[
                    html.Div(["As7265 參數設定"], style = {'text-align': 'center', "font-weight": "bold", 'font-size': titleTestSize + 'px'}),
                    html.Div(id = 'output01'),
                    dbc.Row(children=[
                        html.Div('增益控制', style={'font-size': '16px', 'font-weight': 'bold', 'color': 'balck', 'text-align': 'center'}),
                        dcc.RadioItems(
                            id='Gain',
                            options=[
                                {'label': '增益: 1', 'value': 'Gain1'},
                                {'label': '增益: 8', 'value': 'Gain8'},
                                {'label': '增益: 16', 'value': 'Gain16'},
                                {'label': '增益: 64', 'value': 'Gain64'},
                            ],
                            value = 'Gain64'
                            ),
                    ], style={'width': '100%', 'float': 'left'}),
                    
                    dbc.Row(children=[
                            html.Div(id = 'output02'),
                            html.Div('燈源選擇', style={'font-size': '16px', 'font-weight': 'bold', 'color': 'balck', 'text-align': 'center'}),
                            dcc.Checklist(
                                id='LightSource',
                                options=[
                                    {'label': 'Near-IR', 'value': "1"},
                                    {'label': 'Daylight', 'value': "2"},
                                    {'label': 'Ultraviolet', 'value': "3"},
                                ],
                                value=['1', '2', '3']
                            ),  
                            
                    dcc.Interval(
                        id='getSerialDataIntervals',
                        interval=600,
                        n_intervals=0,
                        disabled=False
                    ),
                    
                    ], style={'width': '100%', 'float': 'left'}),

                    html.Br(),
                    html.Div(id = "buttonAs7265Error"),
                    
            ], id = "As7265_Frame", style={'width': '100%', 'float': 'left', 'padding': '10px', 'border': '1px solid black'}),
            
            dbc.Col(children=[
                    html.Div(["IMX462 參數設定"], style = {'text-align': 'center', "font-weight": "bold", 'font-size': titleTestSize + 'px'}),
                    
                    dbc.Col(children=[
                            html.Div('圖片寬度', style={'font-size': '16px', 'font-weight': 'bold', 'color': 'balck', 'text-align': 'center'}),
                            dcc.Slider(
                                id='widthSliderImx462',
                                min=30,
                                max=100,
                                step=10,
                                value=50
                            )
                        ]),
                        
                    html.Div([
                        html.Div(id = 'fpsIMX462_mesaage'),
                        html.Div('Save Video FPS:', style={'font-size': '16px', 'font-weight': 'bold', 'color': 'balck', 'text-align': 'center'}),
                        dcc.Slider(id='fpsIMX462', min=5, max=30, step=5, value=10)
                    ]),
                    
                    dbc.Col(children=[    
                        html.Div(id = 'output03'),
                        html.Div('deNoise (Low to High)', style = {'text-align': 'center', "font-weight": "bold"}),
                        dcc.Slider(min = 0, max = 15, step = 1, value = nowLevel["denoise"], id = "deNoise"),
                        ]),
                    
                    dbc.Col(children=[ 
                        html.Div(id = 'output04'),                             
                        html.Div('Agc (Low to High)', style = {'text-align': 'center', "font-weight": "bold"}),
                        dcc.Slider(min = 0, max = 15, step = 1,
                                  value = nowLevel["agc"],
                                  id = "agc"),
                            
                        ]),
                    
                    dbc.Col(children=[   
                        html.Div(id = 'output05'),
                        html.Div('Low Light (Low to High)', style = {'text-align': 'center', "font-weight": "bold"}),
                        dcc.Slider(min = 0, max = 15, step = 1,
                                   value = nowLevel["lowlight"],
                                   id = "lowLight"),
                        ]),
                    
                    dbc.Col(children=[   
                        html.Div(id = 'output06'),
                        html.Div('wdrMode', style = {'text-align': 'center', "font-weight": "bold"}),
                    dbc.Col(children=[ 
                        dcc.RadioItems(wdrModeList, wdrModeList[int(nowLevel["wdrmode"])], id = "wdrMode", inline = True, labelStyle={'display': 'inline-block', 'margin-right': '20px'}),

                        ], style={'display': 'flex', 'flex-wrap': 'wrap'}),
                    ]),
                
                    
                    dbc.Col(children=[ 
                        html.Div(id = 'output07'),
                        html.Div('mirrorMode', style = {'text-align': 'center', "font-weight": "bold"}),
                    dbc.Col(children=[ 
                        dcc.RadioItems(mirrorModeList,"mirror image", id = "mirrorMode", inline = True, labelStyle={'display': 'inline-block', 'margin-right': '20px'}),
                        html.Br(),
                    
                        ], style={'display': 'flex', 'flex-wrap': 'wrap'}),
                    ]),

                    dbc.Col(children=[
                        html.Div(id = 'output08'),
                        html.Div('Day Night Mode', style = {'text-align': 'center', "font-weight": "bold"}),
                        html.Br(),

                        daq.ToggleSwitch(id = "dayNightMode",
                                         value = switchValies,
                                         color = "red"),
                        ]),
                    html.Br(),
                    
                    html.Div([
                        html.Div(id = 'save_Width_IMX462_Mesaage'),
                        html.Div('Save Width:', style={'display': 'inline-block', 'margin-right': '10px'}),
                        dcc.Input(id='save_Width_IMX462', type='text', value='640', style={'color': 'black', 'display': 'inline-block'}),
                    ]),
                    
                    html.Br(),
                    
                    html.Div([
                        html.Div(id = 'save_Height_IMX462_Mesaage'),
                        html.Div('Save Height:', style={'display': 'inline-block', 'margin-right': '10px'}),
                        dcc.Input(id='save_Height_IMX462', type='text', value='480', style={'color': 'black', 'display': 'inline-block'}),
                    ]),
                    
                    html.Br(),
                    
                    html.Div('影像顯示欄位', style = {'text-align': 'center', "font-weight": "bold"}),
                    html.Div([
                        html.Div(id = 'show_Width_IMX462_Mesaage'),
                        html.Div('Show Width:', style={'display': 'inline-block', 'margin-right': '10px'}),
                        dcc.Input(id='show_Width_IMX462', type='text', value='640', style={'color': 'black', 'display': 'inline-block'}),
                    ]),
                    
                    html.Br(),
                    
                    html.Div([
                        html.Div(id = 'show_Height_IMX462_Mesaage'),
                        html.Div('Show Height:', style={'display': 'inline-block', 'margin-right': '10px'}),
                        dcc.Input(id='show_Height_IMX462', type='text', value='480', style={'color': 'black', 'display': 'inline-block'}),
                    ]),
                    
                    html.Div(id = 'updateImx462Image_Mesaage'),
                    
                    html.Button("更新", id='updateImx462Image', style={'border': '1px solid black', 'background-color': '#4CAF50', 'font-size': '25px', 'width': '100%', 'text-align': 'center'}), 

            ], id = "IMX462_Frame", style={'width': '100%', 'float': 'center', 'padding': '10px', 'border': '1px solid black', 'marginBottom': 10}),
        
        dbc.Col(children=[
                html.Div(["USB 參數設定"], style = {'text-align': 'center', "font-weight": "bold", 'font-size': titleTestSize + 'px'}),
                
                dbc.Col(children=[
                        html.Div('圖片寬度', style={'font-size': '16px', 'font-weight': 'bold', 'color': 'balck', 'text-align': 'center'}),
                        dcc.Slider(
                            id='widthSliderUSB',
                            min=30,
                            max=100,
                            step=10,
                            value=50
                        )
                    ]),
                    
                html.Div([
                        html.Div(id = 'fpsUSB_mesaage'),
                        html.Div('Save Video FPS:', style={'font-size': '16px', 'font-weight': 'bold', 'color': 'balck', 'text-align': 'center'}),
                        dcc.Slider(id='fpsUSB', min=5, max=30, step=5, value=10)
                    ]),
                    
                    
                html.Div([
                    html.Div(id = 'save_Width_USB_Mesaage'),
                    html.Div('Save Width:', style={'display': 'inline-block', 'margin-right': '10px'}),
                    dcc.Input(id='save_Width_USB', type='text', value='640', style={'color': 'black', 'display': 'inline-block'}),
                ]),
                
                html.Br(),
                
                html.Div([
                    html.Div(id = 'save_Height_USB_Mesaage'),
                    html.Div('Save Height:', style={'display': 'inline-block', 'margin-right': '10px'}),
                    dcc.Input(id='save_Height_USB', type='text', value='480', style={'color': 'black', 'display': 'inline-block'}),
                ]),
                
                html.Br(),
                
                html.Div('影像顯示欄位', style = {'text-align': 'center', "font-weight": "bold"}),
                html.Div([
                    html.Div(id = 'show_Width_USB_Mesaage'),
                    html.Div('Show Width:', style={'display': 'inline-block', 'margin-right': '10px'}),
                    dcc.Input(id='show_Width_USB', type='text', value='640', style={'color': 'black', 'display': 'inline-block'}),
                ]),
                
                html.Br(),
                
                html.Div([
                    html.Div(id = 'show_Height_USB_Mesaage'),
                    html.Div('Show Height:', style={'display': 'inline-block', 'margin-right': '10px'}),
                    dcc.Input(id='show_Height_USB', type='text', value='480', style={'color': 'black', 'display': 'inline-block'}),
                ]),
                
                html.Div(id = 'updateUSBImage_Mesaage'),
                
                html.Button("更新", id='updateUSBImage', style={'border': '1px solid black', 'background-color': '#4CAF50', 'font-size': '25px', 'width': '100%', 'text-align': 'center'}), 
     
            ], style={'width': '100%', 'float': 'center', 'padding': '10px', 'border': '1px solid black', 'marginBottom': 10}),

        # =============================================================================
        #         
        # =============================================================================
        html.Div(["其他功能"], style = {'text-align': 'center', "font-weight": "bold", 'font-size': titleTestSize + 'px'}),
         
        html.Div([
            html.Div('儲存檔名:', style={'display': 'inline-block', 'margin-right': '10px'}),
            dcc.Input(id='saveFileName', type='text', value='output', style={'color': 'black', 'display': 'inline-block'}),
        ]),
        
        dbc.Row(children=[
                        html.Div(id = 'output09'),
                        html.Div('選擇要儲存的感測器', style={'font-size': '16px', 'font-weight': 'bold', 'color': 'balck', 'text-align': 'center'}),
                        dcc.Checklist(
                            id='saveSensor',
                            options=[
                                {'label': 'IMX462', 'value': "IMX462"},
                                {'label': 'As7265', 'value': "As7265"},
                                {'label': 'USB', 'value': "USB"},
                            ],
                            value=[''],
                        ),  
                ], style={'width': '100%', 'float': 'left'}),
        
        html.Br(),
        html.Br(),
        html.Button("儲存資料", id='SaveData', style={'border': '1px solid black', 'background-color': '#4CAF50', 'font-size': '25px', 'width': '100%', 'text-align': 'center'}),    
        html.Br(),

        ], style={'background-color': '#BDC4CC', 'color': 'black', 'width': '20%', 'float': 'left', 'padding': '10px', 'height': '300vh'}),
        
        # =============================================================================
        # 右半部份
        # =============================================================================
        dbc.Row([
            
            html.Div(children=[
                html.Div([
                    html.Div(id='graph01'),
                ],style={'width': '50%', 'padding': '1px', 'float': 'left'}),
                
                html.Div([
                    html.Div(id='graph02'),
                ],style={'width': '50%', 'padding': '1px', 'float': 'right'}),
                
            ], id = "as7265ShowFigure"),
            
            html.Div(children=[
                html.Img(src = "/feed_1", style = {'width': '100%', 'padding': '1px', 'float': 'right'}, id = "csiShowFigure"),
            ], id = "imx462ShowFigure"),


            
            html.Div(children=[
                html.Img(src = "/feed_2", style = {'width': '100%', 'padding': '1px', 'float': 'right'}, id = "usbShowFigure"),
            ]),

            
            

        ],style={'width': '80%', 'float': 'right', 'background-color': 'darkcyan', 'height': '300vh'})
        
    ])

# =============================================================================
# 
# =============================================================================
@app.callback(Output('save_Width_USB_Mesaage', 'children'),
              Input('save_Width_USB', 'value'),
              State('show_Width_USB', 'value'))
              
def update_Save_Width_USB(save, show):
    global saveWidthUSB
    
    if int(save) > int(show):
        return "儲存寬度不能大於顯示寬度"
        
    saveWidthUSB = int(save)
    return None

@app.callback(Output('save_Height_USB_Mesaage', 'children'),
              Input('save_Height_USB', 'value'),
              State('show_Height_USB', 'value'))
              
def update_Save_Height_USB(save, show):
    global saveHeightUSB
    
    if int(save) > int(show):
        return "儲存高度不能大於顯示高度"
    
    aveHeightUSB = int(save)
    return None
# =============================================================================
# 
# =============================================================================   
@app.callback(Output('save_Width_IMX462_Mesaage', 'children'),
              Input('save_Width_IMX462', 'value'),
              State('show_Width_IMX462', 'value'))
              
def update_Save_Width_IMX462(save, show):
    global saveWidthIMX462
    
    if int(save) > int(show):
        return "儲存寬度不能大於顯示寬度"
        
    saveWidthIMX462 = int(save)
    return None

@app.callback(Output('save_Height_IMX462_Mesaage', 'children'),
              Input('save_Height_IMX462', 'value'),
              State('show_Height_IMX462', 'value'))
              
def update_Save_Height_IMX462(save, show):
    global saveHeightIMX462
    
    if int(save) > int(show):
        return "儲存高度不能大於顯示高度"
        
    saveHeightIMX462 = int(save)
    return None




@app.callback(Output('updateImx462Image_Mesaage','children'),
              Input('updateImx462Image', 'n_clicks'),
              State('show_Width_IMX462', 'value'),
              State('show_Height_IMX462', 'value'))
              
def updateCSI_Image(n_clicks, w, h):
    
    global updateImageCSI, showWidthIMX462, showHeightIMX462
    
    if n_clicks != None:
        
        showWidthIMX462 = w
        showHeightIMX462 = h
        
        updateImageCSI = True
    
    return None
              
@app.callback(Output('updateUSBImage_Mesaage','children'),
              Input('updateUSBImage', 'n_clicks'),
              State('show_Width_USB', 'value'),
              State('show_Height_USB', 'value'))
              
def updateUSB_Image(n_clicks, w, h):
    
    global updateImageUSB, showWidthUSB, showHeightUSB
    
    if n_clicks != None:
        
        showWidthUSB = w
        showHeightUSB = h

        updateImageUSB = True
    
    return None
    
    
              
# =============================================================================
#  Serial Port
# =============================================================================
last_data = None        
@app.callback(Output('graph01', 'children'),
              Output('graph02', 'children'),
              Input('getSerialDataIntervals', 'n_intervals'),
              State('SerialMesaage', 'children'))

def update_As7265Graph(n, Mesaage):
    global last_data

    try:
        if Mesaage == "Serial port successfully connected":
            if not q.empty():
                new_sensor_values = q.get()
                last_data = new_sensor_values
                
            elif last_data is not None:
                new_sensor_values = last_data
                
            else:
                new_sensor_values = np.ones(18)

            graphs = []
            
            fig01 = go.Figure(data=[go.Bar(x = xAxis, y = new_sensor_values, marker=dict(color=colors))])

            fig02 = go.Figure(data=[go.Scatter(x = xAxis, y=new_sensor_values, mode='lines', marker=dict(color=colors), name='Line')])

            return [html.Div(dcc.Graph(figure=fig01)), html.Div(dcc.Graph(figure=fig02))] 
        else:
            return [None, None]
            
    except:
        return [None, None]

        
@app.callback(Output('SerialMesaage', 'children'),
              Input('connectedInterval', 'n_intervals'),
              State('Gain', 'value'),
              State('LightSource', 'value'))
              
              
def continueSerial(n, gainValue, lightSourceValue):
    global ser
    
    try:
        if ser.isOpen():
            return "Serial port successfully connected"
        else:
            
            try:
                ser = serial.Serial('/dev/ttyUSB0', 115200)
                getSensorDataThread = threading.Thread(target = getSensorData)
                getSensorDataThread.start()
                
                updateGain(gainValue)
                updateLightSource(lightSourceValue)
                    
                return "Serial port successfully connected"
            
            except:
                pass
            
            try:
                
                ser = serial.Serial('/dev/ttyUSB1', 115200)
                getSensorDataThread = threading.Thread(target = getSensorData)
                getSensorDataThread.start()
                
                updateGain(gainValue)
                updateLightSource(lightSourceValue)
                
                return "Serial port successfully connected"
                
            except:
                pass
    except:
        try:
            ser = serial.Serial('/dev/ttyUSB0', 115200)
            getSensorDataThread = threading.Thread(target = getSensorData)
            getSensorDataThread.start()
            
            updateGain(gainValue)
            updateLightSource(lightSourceValue)
            
            return "Serial port successfully connected"
            
        except:
            pass
            
        try:
            ser = serial.Serial('/dev/ttyUSB1', 115200)
            getSensorDataThread = threading.Thread(target = getSensorData)
            getSensorDataThread.start()
            
            updateGain(gainValue)
            updateLightSource(lightSourceValue)
            
            return "Serial port successfully connected"
            
        except:
            pass
                

    return "Serial port unable to connect"

    
@app.callback(
    Output(component_id = "output01", component_property =  "children"),
    Input(component_id = "Gain", component_property = "value"))

def updateGain(setValue):

    ser.write(setValue.encode())
    
    return None
    
    
@app.callback(
    Output(component_id = "output02", component_property =  "children"),
    Input(component_id = "LightSource", component_property = "value"))

def updateLightSource(setValue):

        
    if(len(setValue) > 1):
        writeData  = "".join([str(val) for val in setValue])[:len(setValue)]
    else: 
        writeData = "off"
        
    ser.write(writeData.encode())
        
    return None

# =============================================================================
# 
# =============================================================================
@server.route("/feed_2")
def feed_2():
    camera = setUSB_VideoCamera()
    return Response(setUSB_Image(camera), mimetype = "multipart/x-mixed-replace; boundary=frame")
    
@app.callback(Output('USBMesaage', 'children'),
              Output('CSIMesaage', 'children'),
              Output('usbShowFigure', 'style'),
              Output('csiShowFigure', 'style'),
              Output('cpuLoad', 'children'),
              Input('chcekCamera', 'n_intervals'),
              State('widthSliderUSB', 'value'),
              State('widthSliderImx462', 'value'),)


def update_usbMesaage(n, usbWidth, csiWidth):
    global connectUSB, connectCSI
    usbMesaage = "USB port successfully connected"
    usbDisplay = "block"
    
    csiMesaage = "CSI port successfully connected"
    csiDisplay = "block"
    
    if connectUSB == False:
        usbMesaage = "USB port unable to connect"
        usbDisplay = "none"
        
    if connectCSI == False:
        csiMesaage = "CSI port unable to connect"
        csiDisplay = "none"
    
    load = get_cpu_load()
    
    return [usbMesaage, csiMesaage, {'width': f'{usbWidth}%', 'padding': '1px', 'float': 'right', "display": usbDisplay}, {'width': f'{csiWidth}%', 'padding': '1px', 'float': 'right', "display": csiDisplay}, "CPU (%): " + str(load)]


# =============================================================================
# 
# =============================================================================
@server.route("/feed_1")
def feed_1():
    camera = Imx462_VideoCamera()
    return Response(setImx462_Image(camera), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.callback(
    Output(component_id = "output03", component_property =  "children"),
    Input(component_id = "deNoise", component_property = "value"),
)
def updateDeNoise(setdeNoise):
    for index, nums in enumerate(levelIndex):
        if index == setdeNoise:
            subprocess.check_output("./veye_mipi_i2c.sh -w -f denoise -p1 0x0" + str(nums), shell = True)
            return None
            
    return None
    
@app.callback(Output('fpsIMX462_mesaage', 'children'),
              Input('fpsIMX462', 'value'))
              
def setImx462FPS(value):
    global imx462FPS
    imx462FPS = value
    return None
    
@app.callback(Output('fpsUSB_mesaage', 'children'),
              Input('fpsUSB', 'value'))
              
def setUsbFPS(value):
    global usbFPS
    usbFPS = value
    
    return None


@app.callback(
    Output(component_id = "output04", component_property =  "children"),
    Input(component_id = "agc", component_property = "value"),
)
def updateAgc(setAgc):
    for index, nums in enumerate(levelIndex):
        if index == setAgc:
            subprocess.check_output("./veye_mipi_i2c.sh -w -f agc -p1 0x0" + str(nums), shell = True)
            return None
    
    return None

@app.callback(
    Output(component_id = "output05", component_property =  "children"),
    Input(component_id = "lowLight", component_property = "value"),
)
def updateLowLight(setLowLight):
    for index, nums in enumerate(levelIndex):
        if index == setLowLight:
            subprocess.check_output("./veye_mipi_i2c.sh -w -f lowlight -p1 0x0" + str(nums), shell = True)
            return None
            
    return None


@app.callback(
    Output(component_id = "output06", component_property =  "children"),
    Input(component_id = "wdrMode", component_property = "value"),
)
def updateWdrMode(setWdrMode):
    for index, nums in enumerate(wdrModeList):
        if nums == setWdrMode:
            subprocess.check_output("./veye_mipi_i2c.sh -w -f wdrmode -p1 0x0" + str(index), shell = True)
            return None
            
    return None
            
@app.callback(
    Output(component_id = "output07", component_property =  "children"),
    Input(component_id = "mirrorMode", component_property = "value"),
)
def updateWdrMode(setMirrorMode):
    for index, nums in enumerate(mirrorModeList):
        if nums == setMirrorMode:
            subprocess.check_output("./veye_mipi_i2c.sh -w -f mirrormode -p1 0x0" + str(index), shell = True)
            return None
            
    return None

@app.callback(
    Output(component_id = "output08", component_property =  "children"),
    Input(component_id = "dayNightMode", component_property = "value"),
)

def update_DayNightMode(setDayNightMode):
    
    if setDayNightMode == False:
        subprocess.check_output("./veye_mipi_i2c.sh -w -f daynightmode -p1 0xFF", shell = True)
        return None
    elif setDayNightMode == True:
        subprocess.check_output("./veye_mipi_i2c.sh -w -f daynightmode -p1 0xFE", shell = True)
        return None

@app.callback(
    Output("SaveData", "children"),
    Input("SaveData", "n_clicks"),
    [State('saveFileName', 'value'),
     State('saveSensor', 'value')])
   
def switchSaveVideo(n_clicks, Name, selected_values):
 
    global saveDataImx462, saveDataUSB, saveDataAs7265
    global savefileName

    savefileName = Name
    
    if n_clicks != None:
        
        buttonSate = int(n_clicks % 2)

        if 'IMX462' in selected_values:
            saveDataImx462 = 1
            
        if 'As7265' in selected_values:
            saveDataAs7265 = 1
            
        if 'USB' in selected_values:
            saveDataUSB = 1
            
        if buttonSate == 1:
            if (saveDataImx462 == 1) or (saveDataAs7265 == 1) or (saveDataUSB == 1):
                
                return ["停止"]
            
    saveDataImx462 = 0
    saveDataAs7265 = 0
    saveDataUSB = 0
           
    return ["啟動"]



getSensorDataThread = threading.Thread(target = getSensorData)
getSensorDataThread.start()

if __name__ == '__main__':
    webLayout()
    app.run_server(debug=False)
