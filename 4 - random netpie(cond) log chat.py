import time
import random
from rpi_lcd import LCD
lcd = LCD()
aqi=-1
pm=-1
#################################################################
import time
import paho.mqtt.client as mqtt 
import json
import random
myData = { "ID" : 123, "aqi" : 0, "pm" : 0}
NETPIE_HOST = "broker.netpie.io"
CLIENT_ID = ""
DEVICE_TOKEN = ""
def on_connect(client, userdata, flags, rc):
    print("Result from connect : {}".format(mqtt.connack_string(rc)))
    client.subscribe("@shadow/data/updated")
def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribe successful")
def on_message(client, userdata, msg):
    data = str(msg.payload).split(",")
    data_split = data[1].split("{")[1].split(":")
    data_split2 = data[2].split(":")
    key = data_split[0].split('"')[1]
    key2 = data_split2[0].split('"')[1]
    value = data_split[1].split('}')[0]
    value2 = data_split2[1].split('}')[0]
    if value[0] == '"':
        value = value.split('"')[1]
    myData[key] = value
client = mqtt.Client(protocol=mqtt.MQTTv311,client_id=CLIENT_ID, clean_session=True)
client.username_pw_set(DEVICE_TOKEN)
client.on_connect = on_connect
client.on_message = on_message
client.connect(NETPIE_HOST, 1883)
client.loop_start()
################################################################
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
SheetName = "API test"
GSheet_OAUTH_JSON = ""
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(GSheet_OAUTH_JSON, scope)
clientG = gspread.authorize(credentials)
worksheet = clientG.open(SheetName).sheet1
row = ["Time","AQI","PM2.5"]
index = 1
worksheet.insert_row(row,index)
################################################################
from flask import Flask, request, make_response, jsonify
import os
import json
import locale
app = Flask(__name__)
log = app.logger
@app.route("/", methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print(req)
    print(req.get('queryResult').get('parameters').get('place'))

    try:
        action = req.get('queryResult').get('intent').get('displayName')
        print(action)
    except AttributeError:
        return 'json error'
    # action switcher 

    if action == 'AirNow':
        res = ("AQI="+str(aqi)+" PM2.5="+str(pm))
    elif action == 'SearchLog':
        try:
           resq = req.get('queryResult').get('outputContexts')[0].get('parameters').get('Time.original')
           print("User req time = " + resq)
        except:
            print("CUSTOM: can't obtain time")
        tg = worksheet.find(resq)
        print(tg)
        print(tg.row)
        haqi = worksheet.cell(tg.row,2)
        hpm = worksheet.cell(tg.row,3)
        res = ("Air at "+str(tg)+" is "+"AQI="+str(haqi)+" PM2.5="+str(hpm))
    else:
        log.error('Unexpected action.')


    print('Action: ' + str(action))
    print('Response: ' + res)

    # return response
    return make_response(jsonify({'fulfillmentText': res}))

try:
    app.run(host='0.0.0.0', debug=True, port=int(os.environ.get('PORT','5000')))
    while True:
        aqi = random.randint(0,100)
        pm = random.randint(0,250)
        #Line_Notify
        myData['aqi'] = aqi
        myData['pm'] = pm
        client.publish("@shadow/data/update",json.dumps({"data": myData}), 1)
        #Log
        currentTime = datetime.datetime.now().strftime("%H:%M:%S")
        worksheet.append_row([currentTime,aqi,pm])
        #LCD
        lcd.text("AQI = " + str(aqi), 1)
        lcd.text("PM2.5 = " + str(pm), 2)
        time.sleep(3)
    
finally:
    lcd.clear()
    lcd.backlight(0)


