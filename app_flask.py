from flask import Flask, render_template,request
import sqlite3
import plotly.graph_objects as go
from main import list_city_url
from main import go_to_hotels_browse, hotel_info_from_browse_list, reddit_topics
import re

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def results():
    selected_region = request.form['region']
    selected_country = request.form['country_name']
    selected_city = request.form['city_name']

    info = list_city_url(selected_region,selected_country,selected_city) # city url from sql
    try: 
        city_url = info[3] # retreive browse url
        browse_url = go_to_hotels_browse(city_url)  # return browse url

        # check browser_url, if there is a 'https://', then go to the url
        pattern = r'(http.*.html)'
        search = re.match(pattern,browse_url)
        if search:
            results = hotel_info_from_browse_list(browse_url) 
            # return list of hotel_name, score, comment_title, review_num, url
            # sorted_re = sorted(results, key=lambda x:x[3].split()[0], reverse=True)
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
                                results=results, region=selected_region,plot_div=div,
                                topic=topic_list, title=search_title, sort=selected_sorting)
    else:

        return render_template('results.html', 
                                results=results, region=selected_region,
                                topic=topic_list, title=search_title,sort=selected_sorting)



if __name__ == '__main__':
    app.run(debug=True)

