import requests
import json
import datetime
from datetime import datetime, date, time, timedelta, timezone
import secrets
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from flask import Flask, render_template
import pytz

## Reference:
# api doc: https://darksky.net/dev/docs#data-block-object
# mapbox aip: https://docs.mapbox.com/api/search/#data-types
# timezone: https://pypi.org/project/pytz/

client_key = secrets.client_key # mapquest api_key
api_key = secrets.api_key # darksky api_key
mapbox_access_token = secrets.mapbox_access_token # location (lon, lat)

app = Flask(__name__)

# def unix_time_convert(time_stamp):  ## 和 datetime.fromtimestamp 一樣，應該不需要使用
#     return datetime.fromtimestamp(int(time_stamp)).strftime('%Y-%m-%d %H:%M:%S')

class Weather:
    def __init__(self,json):
        data = json
        self.timezone = data['timezone']
        current_time = datetime.fromtimestamp(data['currently']['time']) #
        # new_time = time.astimezone(pytz.timezone(self.timezone))
        self.current_time = current_time.astimezone(pytz.timezone(self.timezone))
        self.wk_data = data['daily']['data']
        daily_sum,comment,sunrise,sunset,precipitation_prob = [],[],[],[],[]
        temp_high,temp_low,humid,uv_index = [],[],[],[]
        tt = []
        total = {}
        for item in self.wk_data:
            time = datetime.fromtimestamp(item['time'])
            time = time.astimezone(pytz.timezone(self.timezone)) # convert time
            tt.append(str(time))
            daily_sum.append(item['summary'])
            comment.append(item['icon'])
            sr = datetime.fromtimestamp(item['sunriseTime'])
            sr = sr.astimezone(pytz.timezone(self.timezone)) # convert time
            sunrise.append(sr) # 
            ss = datetime.fromtimestamp(item['sunsetTime'])
            ss = ss.astimezone(pytz.timezone(self.timezone))  # convert time
            sunset.append(ss) # 
            precipitation_prob.append(item['precipProbability'])
            temp_high.append(item['temperatureHigh'])
            temp_low.append(item['temperatureLow'])
            humid.append(item['humidity'])
            uv_index.append(item['uvIndex'])
        total['wk_time'] = tt
        total['daily_sum'] = daily_sum
        total['comment'] = comment
        total['sunrise'] = sunrise
        total['sunset'] = sunset
        total['precipitation_prob'] = precipitation_prob
        total['temp_high'] = temp_high
        total['temp_low'] = temp_low
        total['humid'] = humid
        total['uv_index'] = uv_index
        self.total = total
        self.wk_time = tt
        self.daily_sum = daily_sum
        self.comment = comment
        self.sunrise = sunrise
        self.sunset = sunset
        self.precipitation_prob = precipitation_prob
        self.temp_high = temp_high
        self.temp_low = temp_low
        self.humid = humid
        self.uv_index = uv_index

    def plot_temp(self):
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=self.wk_time,
            y=self.temp_high,
            name='temp_high',
            marker_color= 'indianred'  #'rgb(55, 83, 109)'
        ))
        fig.add_trace(go.Bar(
            x=self.wk_time,
            y=self.temp_low,
            name='temp_low',
            marker_color= 'steelblue'#'rgb(26, 118, 255)' #'lightsalmon'
        ))

        fig.update_layout(barmode='group', xaxis_tickangle=0,title="High vs Low temperature" )
        fig.show()

    def plot_precip_line(self):  ## plot precipitation_prob
        fig = go.Figure()
        xvals = self.wk_time
        yvals = self.precipitation_prob

        line_data = go.Scatter(
            x=xvals,y=yvals,mode='lines+markers+text', 
            marker ={'symbol':'square', 'size': 10, 'color':'green'},
            text=xvals, textposition='top center'
        )

        basic_layout = go.Layout(title="Weekly Precipitation Probability")
        fig = go.Figure(data=line_data, layout=basic_layout)
        # fig.write_html("scatter_square.html", auto_open=True)
        fig.show()



def location_check(search_text):
    end_point = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{search_text}.json?access_token={mapbox_access_token}'
    response = requests.get(end_point)
    # print(response.status_code)
    search = response.json()

    x = search['features'][0]['text']
    y = search['features'][0]['center'] # return [lon,lat]
    lng = y[0]
    lat = y[1]
    location = "{0:.4f},{1:.4f}".format(lat,lng)
    # print(x,y)
    # print(search['features'])
    return location 

def weather_data(place): # add language option?!
    location = location_check(place)
    base_url = 'https://api.darksky.net/forecast/'
    param = {'lang':'zh-tw', 'extend':True, 'exclude':['minutely','hourly'] }  # 'zh-tw', extend = True so as to have a week
    url = base_url + api_key + '/' + location
    #weather
    response = requests.get(url, params=param)
    # response = requests.request("GET", url,params=param)
    # print(response.status_code)
    data = response.json()
    # print(data)
    return Weather(data)

p = 'Ann Arobr'
aa = weather_data(p)
tp = weather_data('taipei') # 最好用地址
# print(tp.timezone)
print(aa.daily_sum)

tp.plot_temp()
# # print(tp.total)
# print(location_check(p))


@app.route('/weather/<nm>')
def find_headlines(nm): # weather table
    # loc = location_check(nm)
    obj = weather_data(nm)

    headline = obj.total

    return render_template('weather.html', 
            word=nm, 
            word_list=headline)




# if __name__ == '__main__':  
#     app.run(debug=True)