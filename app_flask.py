from flask import Flask, render_template,request
import sqlite3
import plotly.graph_objects as go
from main import list_city_url
from main import go_to_hotels_browse, hotel_info_from_browse_list, reddit_topics, hotel_review
import re
from darksky_api import weather_data, weatherbit_data
from main import list_region_to_select, list_country_by_region,list_city_by_country

app = Flask(__name__)

class Location():
    region = ''
    country = ''

place = Location()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def results():
    selected_city = request.form['city_name']
    try:
    # if place.region == "" and place.country == "":
        selected_region = request.form['region']
        selected_country = request.form['country_name']
    except:
    # else:
        selected_region = place.region
        selected_country = place.country


    info = list_city_url(selected_region,selected_country,selected_city) # city url from sql
    # print(info)

    try:
        city_url = info[3] # retreive browse url
        browse_url = go_to_hotels_browse(city_url)  # return browse url

        # check browser_url, if there is a 'https://', then go to the url
        pattern = r'(http.*.html)'
        search = re.match(pattern,browse_url)
        if search:
            results = hotel_info_from_browse_list(browse_url)

    except:
        results = [('N/A','N/A','N/A','N/A','N/A')]

    # Reddit topics
    reddit = request.form.get('reddit', False)
    selected_sorting = request.form['reddit_sort']
    if (reddit):
        result_topic = reddit_topics(selected_city,5,selected_sorting) # return dict
        search_title = selected_city
        if len(result_topic) == 0:
            result_topic = reddit_topics(selected_country,5)
            search_title = selected_country
        topic_list = result_topic.values()
    else:
        topic_list = None
        search_title = ''

    ## weather
    # print(seleccted_city)
    weather_or_not = request.form.get('weather', False)
    no_weatherbit = False
    # darksky api
    try:
        try: # if mapbox no data, search country location
            obj = weather_data(selected_city)
        except:
            obj = weather_data(selected_country)
    # weatherbit api
    except: # weatherbit (obj of weatherbit api)
        try:
            try:
                obj = weatherbit_data(selected_city)
            except:
                obj = weatherbit_data(selected_country)
        except:
            weather_or_not = False
            no_weatherbit = True
            
    
    if weather_or_not:
        weather_table = obj.total
        # weather plot
        fig_1 = obj.plot_precip_line()
        weather_div_1 = fig_1.to_html(full_html=False)
        fig_2 = obj.plot_temp()
        weather_div_2 = fig_2.to_html(full_html=False)

        # plot
        plot_results = request.form.get('plot', False)
        if (plot_results):
            x_vals = [x[0] for x in results] #hotel name
            y_vals = [x[1] for x in results] # review_num
            bars_data = go.Bar(
                x=x_vals,
                y=y_vals
            )
            fig = go.Figure(data=bars_data)
            fig.update_layout(  title="Hotels vs Scores",
                                xaxis_title="Hotel",
                                yaxis_title="Score")
            div = fig.to_html(full_html=False)

            return render_template('results.html',
                                    results=results,
                                    region=selected_region,
                                    plot_div=div,
                                    topic=topic_list,
                                    title=search_title,
                                    city=selected_city,
                                    sort=selected_sorting,
                                    weather_plot = weather_or_not,
                                    weather=weather_table,
                                    weather_div_1 = weather_div_1,
                                    weather_div_2 = weather_div_2
                                    )
        else:
            return render_template('results.html',
                                    results=results,
                                    region=selected_region,
                                    topic=topic_list,
                                    title=search_title,
                                    city=selected_city,
                                    sort=selected_sorting,
                                    weather_plot = weather_or_not,
                                    weather=weather_table,
                                    weather_div_1 = weather_div_1,
                                    weather_div_2 = weather_div_2
                                    )
    else:
        return render_template('results.html',
                                    results=results,
                                    region=selected_region,
                                    topic=topic_list,
                                    title=search_title,
                                    city=selected_city,
                                    sort=selected_sorting,
                                    weather_plot = weather_or_not,
                                    weatherbit = no_weatherbit
                                    )


@app.route('/reviews', methods=['POST'])
def review():   # read review
    url = request.form['hotel_url']
    if url != 'N/A':
        reviews = hotel_review(url)
    else:
        reviews = ['N/A']
    return render_template('reviews.html',results=reviews)

#route for 'select'
@app.route('/select')
def select():
    all_regions = list_region_to_select()
    return render_template('select.html',region=all_regions)

@app.route('/country', methods=['POST'])
def country_results():
    selected_area = request.form['region']
    place.region = selected_area
    all_country = list_country_by_region(selected_area)

    return render_template('country.html',
                                region=selected_area,
                                countries = all_country
                                )

@app.route('/city', methods=['POST'])
def city():
    select_country = request.form['country_name']
    place.country = select_country
    cities = list_city_by_country(select_country)

    return render_template('city.html',
                                country=select_country,
                                city = cities
                                )


if __name__ == '__main__':
    app.run(debug=True)


