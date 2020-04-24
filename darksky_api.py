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
# darsky api doc: https://darksky.net/dev/docs#data-block-object
# weatherbit api: https://www.weatherbit.io/api/weather-forecast-16-day
# mapbox aip: https://docs.mapbox.com/api/search/#data-types
# timezone: https://pypi.org/project/pytz/


api_key = secrets.api_key # darksky api_key
mapbox_access_token = secrets.mapbox_access_token # location (lon, lat)
weatherbit_api_key = secrets.weatherbit_api_key  #weatherbit_api key (alternative for darksky)


app = Flask(__name__)


class Weather:
    def __init__(self,json):
        data = json
        self.timezone = data['timezone']
        current_time = datetime.fromtimestamp(data['currently']['time'])
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
            marker_color= 'indianred'
        ))
        fig.add_trace(go.Bar(
            x=self.wk_time,
            y=self.temp_low,
            name='temp_low',
            marker_color= 'steelblue'
        ))

        fig.update_layout(barmode='group', xaxis_tickangle=0,title="High vs Low temperature" )

        return fig

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

        return fig


class Weatherbit(Weather):
    def __init__(self,jsondata):
        self.all = jsondata # debug
        self.city = jsondata['city_name']
        self.timezone = jsondata['timezone']

        daily_sum,comment,sunrise,sunset,precipitation_prob = [],[],[],[],[]
        temp_high,temp_low,humid,uv_index = [],[],[],[]
        tt = []
        total = {}

        data_wk = jsondata['data']

        for data in data_wk:
            # datetime
            try:
                t = data['datetime'] # format '2020-04-24', no need to convert
            except:
                t = 'N/A'
            tt.append(t)

            # daily_sum
            daily_sum.append('No summary in Weatherbit')

            # comment
            try:
                c = data['weather']['description']
            except:
                c = 'N/A'
            comment.append(c)

            # sunrise timestamp need converted
            try:
                sr = datetime.fromtimestamp(data['sunrise_ts'])
                sr = sr.astimezone(pytz.timezone(self.timezone)) # convert ts to local time
            except:
                sr = 'N/A'
            sunrise.append(sr)

            # senset timestamp need converted
            try:
                ss = datetime.fromtimestamp(data['sunset_ts'])
                ss = ss.astimezone(pytz.timezone(self.timezone))  # convert ts to local time
            except:
                ss = 'N/A'
            sunset.append(ss)

            # precipitation
            try:
                p = data['pop']
            except:
                p = 'N/A'
            precipitation_prob.append(p)

            # temp high
            try:
                t_h = data['high_temp']
            except:
                t_h = 'N/A'
            temp_high.append(t_h)
            # temp low
            try:
                t_l = data['low_temp']
            except:
                t_l = 'N/A'
            temp_low.append(t_l)
            # humid
            try:
                hu = data['rh']
            except:
                hu = 'N/A'
            humid.append(hu)
            #uv
            try:
                uv = data['uv']
            except:
                uv = 'N/A'
            uv_index.append(uv)

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


def location_check(search_text):
    end_point = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{search_text}.json?access_token={mapbox_access_token}'
    response = requests.get(end_point)
    search = response.json()

    x = search['features'][0]['text']
    y = search['features'][0]['center'] # return [lon,lat]
    lng = y[0]
    lat = y[1]
    location = "{0:.4f},{1:.4f}".format(lat,lng)

    return location

def weather_data(place): # Darksky_api
    location = location_check(place)
    base_url = 'https://api.darksky.net/forecast/'
    param = {'lang':'en', 'extend':True, 'exclude':['minutely','hourly'] }  # 'zh-tw', extend = True so as to have a week
    url = base_url + api_key + '/' + location
    response = requests.get(url, params=param)
    data = response.json()

    return Weather(data)

def weatherbit_data(place): # Weatherbit_api
    end_point = 'https://api.weatherbit.io/v2.0/forecast/daily'
    param = {'key':weatherbit_api_key,'city' : place, 'lang':'en'} 
    response = requests.get(end_point,params=param)
    search = response.json()

    return Weatherbit(search)


@app.route('/weather/<nm>')
def find_headlines(nm): # weather table
    try:
        try:
            obj = weather_data(nm)
        except:
            obj = weatherbit_data(nm)

        headline = obj.total
        return render_template('weather.html', 
                                word=nm, 
                                word_list=headline,
                                chart=True)
    except:
        data = False
        return render_template('weather.html', 
                                word=nm, 
                                chart=data)

if __name__ == '__main__':
    app.run(debug=True)
