from flask import Flask, redirect, url_for, render_template, json, jsonify, Response, make_response
from flask import request
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import paho.mqtt.client as mqtt
import mqtt_sub

import certifi
ca = certifi.where()

app = Flask(__name__)

# client = MongoClient('localhost', 27017)

client = MongoClient('mongodb+srv://amy:123@userfood.3gs9xwc.mongodb.net/?retryWrites=true&w=majority',tlsCAFile=ca)
db = client.get_database('userFood')
todos = db.get_collection('Item')
stand =  db.get_collection('Standard')

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method=='POST':
        content = request.form['food']
        date = request.form['startingDate']
        storage = request.form['storage']
        date = datetime.datetime.utcnow().strptime(date,'%Y-%m-%d')
        new_day = datetime.datetime.today() - date
        new_day_parse = str(new_day).split()
        days = 0
        if 'days,' in new_day_parse or 'day,' in new_day_parse :
            days = int(new_day_parse[0])
        todos.insert_one({'food': content, 'date': date, 'location': storage, 'store_days': days , 'status': "Fresh"})
        return redirect(url_for('index'))

    all_todos = todos.find()
   
    pck = [all_todos]
    return render_template('index.html', pck=pck)
  

@app.post('/<id>/delete/')
def delete(id):
    todos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))


@app.route('/getTemp', methods=['GET'])
def get_Temp():

    current_temp = mqtt_sub.get_temp()
    current_himid = mqtt_sub.get_himid()

    tp_dict = {"temp": current_temp , "humid" : current_himid}
    # print(tp_dict["temp"])
    # print(tp_dict["humid"])
    return tp_dict


@app.route('/updateDate', methods=('GET', 'POST'))
def update_date():
    all_todos = todos.find()
    for item in all_todos:
        new_day = datetime.datetime.today() - item['date']
        new_day_parse = str(new_day).split()
        days = 0
        if 'days,' in new_day_parse or 'day,' in new_day_parse :
            days = int(new_day_parse[0])
        
        myquery = { "name": item['food']} 
        mydoc = stand.find(myquery)[0]
        store_location = item['location']
        temp_humid = mydoc[store_location]
        food_in_storage = item['store_days']
        
        store_time = temp_humid['time']

        current_temp = mqtt_sub.get_temp()
        current_himid = mqtt_sub.get_himid()
        temp_dict = {"temperature": float(current_temp) , "humidity" : float(current_himid)}

    

        day_last =  expiration_cal(temp_humid, temp_dict, store_location,store_time )

        print(day_last)

        day_expire =  day_last - food_in_storage

        

        food_status = "Fresh"
        if  7> day_expire > 4:
            food_status = "Good"
        elif 4 > day_expire > 2:
            food_status = "Need to finish soon!"
        elif 2 > day_expire >0:
            food_status = "About to expire !!!"
        elif day_expire <= 0:
            food_status = "Spoiled !"

        todos.update_one({"_id": item["_id"]}, {"$set":{"store_days": days, "status": food_status}})
    
    return str(days)

def expiration_cal(temp_humid, real_temp_humid, location, standard_store_time):
    ratios = []
    temp_weight = {'refrigerator': 0.8, 'counter': 0.6}
    humidity_weight = {'refrigerator': 0.2, 'counter': 0.4}
    for measurement in ['temperature', 'humidity']:
            low = temp_humid[measurement][0]
            high = temp_humid[measurement][1]
            # if env measurement is less than the lower bar of standard range, find ratio by (env measurement-low)/low
            if real_temp_humid[measurement] < low:
                # spefial case for temperature - the lower the temp, the longer food can be stored
                if measurement == 'temperature':
                    ratio = abs(real_temp_humid[measurement] - low) / low + 1
                else:
                    ratio = 1 - abs(real_temp_humid[measurement] - low) / low
            elif real_temp_humid[measurement] > high:
                ratio = 1 - (real_temp_humid[measurement] - high) / high
            else:
                ratio = 1
            ratios.append(ratio)

        # multiply by the weight of different measurements
    final_ratio = temp_weight[location] * ratios[0] + humidity_weight[location] * ratios[1]
        # calculate the days food can last in env
    days_food_last = int(final_ratio * standard_store_time)

   
    
    return days_food_last
    

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8081, debug=True)