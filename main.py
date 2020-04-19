import praw
import pandas as pd
import datetime as dt
import requests
from bs4 import BeautifulSoup
import sqlite3
import json
import re
import secrets
import darksky_api
from flask import Flask, render_template,request
import plotly.graph_objects as go

# reference: https://praw.readthedocs.io/en/latest/getting_started/quick_start.html
# reference: https://www.storybench.org/how-to-scrape-reddit-with-python/
# reference: https://www.reddit.com/dev/api#GET_search 
# https://github.com/reddit-archive/reddit/wiki/oauth2

app = Flask(__name__)

personal_use_script = secrets.personal_use_script
secret = secrets.secret
username = secrets.username
YOUR_REDDIT_LOGIN_PASSWORD = secrets.YOUR_REDDIT_LOGIN_PASSWORD
user_agent = secrets.user_agent

reddit = praw.Reddit(client_id= personal_use_script , \
                     client_secret= secret , \
                     user_agent= user_agent, \
                     username= username, \
                     password= YOUR_REDDIT_LOGIN_PASSWORD)

CACHE_FILE_NAME = 'cache.json'  ## cache
CACHE_DICT = {}  ## cache

def reddit_topics(topic,num,sorting='top'):
    subreddit = reddit.subreddit('travel')
 
    # print(f'Topics for {topic}:')
    search = subreddit.search(topic, limit = num, sort=sorting )  #sort= 'top', 'hot','new','comment (default)'
    result = {}
    i=1
    for x in search:
        num = f'[{i}]'
        topic = x.title.strip('\n')   #, '\n', x.url)
        pic = x.url
        i = i + 1
        result[num] = (topic,pic)
    return result


#############################below is Booking.com ##########################
############################################################################

def all_city():  # print: region/country/url, return 'country url'
    destination = '''
    https://www.booking.com/destination.html
    '''
    response = requests.get(destination)
    soup = BeautifulSoup(response.text, 'html.parser')
    li = soup.find_all('li',class_="dst-sitemap__sublist-item")
    # print(li)
    total = []
    for item in li:
        h4 = item.find_all('h4',class_="dest-sitemap__sublist-title")#.text.strip('\n')
        h = item.find_all('a')
        for item in h4:
            x = item.text.strip('\n').strip()
            # print(x)
        for i in h:
            c = i.text.strip('\n').strip()
            u = 'https://www.booking.com' +  i.get('href')
            # print(c)
            # print(u)
            result=[x,c,u]
            # print(result)
            total.append(result)
    return total


def make_city_url_list(country_url): # country_url/city_url, return city url
    # country = 'https://www.booking.com/destination/country/au.html'
    response = requests.get(country_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    city_li = soup.find_all('li', class_="dest-sitemap__subsublist-item")
    return_list = {}
    for i in city_li:
        city = i.text.strip('\n').strip()
        x = i.find_all('a',class_="dest-sitemap__subsublist-link")
        for url in x:
            city_url = 'https://www.booking.com' + url.get('href')
        return_list[city] = city_url
        # return_list.append([city,city_url])
        # print(city,city_url)
    return return_list # {city: city_url, city: city_url,...}


def go_to_hotels_browse(city_url):  # use city_url to browse city hotel list
    # city_url = 'https://www.booking.com'+'/destination/city/au/sydney.html'
    # response = requests.get(city_url)

    url_text = make_url_request_using_cache(city_url, CACHE_DICT) # using cache

    soup = BeautifulSoup(url_text, 'html.parser') # url_text, using cache
    browser = soup.find_all('div',class_="dest-sitemap__landing")
    try:
        x =browser[0].text
        y = browser[0].find('a').get('href')
        browse_url = 'https://www.booking.com' + y
        # print(x,pop_hotel)
        return browse_url
    except:
        print('No Recommendation!')
        return 'No Recommendation!'

def hotel_info_from_browse_list(browse_url):#use browse url to scrape hotel list
    # return list of hotel_name, score, comment_title, review_num  
    # response = requests.get(browse_url)

    url_text = make_url_request_using_cache(browse_url, CACHE_DICT) # using cache

    soup = BeautifulSoup(url_text, 'html.parser')
    div = soup.find_all('div', class_="sr__card_content")
    total = []
    for d in div:
        name = d.find('span', class_="bui-card__title").text.strip('\n')
        try:
            score = d.find('div',class_="bui-review-score__badge").text.strip('\n') # hotel score
        except:
            score = 'No Score result!'
        try:
            title = d.find('div',class_="bui-review-score__title").string.strip('\n').strip('\t')  ## maybe in hotel page
            pattern = r'\w+\s?\w+'
            title = re.findall(pattern,title)[0]
        except:
            title = 'No comment title!'
        try:
            re_num = d.find('div',class_="bui-review-score__text").text.strip('\n') # review num
        except:
            re_num = 'No review!'
        url = 'https://www.booking.com' + d.find_all('a')[0].get('href')
        total.append([name,score,title, re_num,url])

    # print(total)
    return total


def hotel_review(hotel_url): # return 3x review contents
    # response = requests.get(hotel_url)

    url_text = make_url_request_using_cache(hotel_url, CACHE_DICT) # using cache

    soup = BeautifulSoup(url_text, 'html.parser')
    reviews = soup.find_all('span',class_="c-review__body")
    re_list = []
    for re in reviews:
        r = re.text.rstrip().strip('\n')
        re_list.append(r)
    # print(re_list[0:5])
    if len(re_list) == 0:
        return 'No available reviews!'
    else:
        try:
            return re_list[0:3]
        except:
            return re_list[:]


def make_region_db(all_city):
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()

    drop_region = '''
        DROP TABLE IF EXISTS "Regions";
    '''

    create_region = '''
        CREATE TABLE IF NOT EXISTs "Regions"(
            "Id"            INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "region"        TEXT NOT NULL,
            "country"       TEXT NOT NULL,
            "country_url"   TEXT NOT NULL
        );
    '''
    insert_region = '''
        INSERT INTO Regions
        VALUES (NULL, ?,?,?)
    '''
    cur.execute(drop_region)
    cur.execute(create_region)

    for item in all_city:
        cur.execute(insert_region, [item[0],item[1],item[2]])

    conn.commit()
    conn.close()

def country_city_table(country_url):
    lt = {}
    for item in country_url: # country_url = [[region,country, country_url],[]..]
        lt[item[1]] = make_city_url_list(item[2])
    # print(lt)
    return lt   #lt = { country : {city: city_url} }

def city_list_write_to_json(lt):  # creat json file for { country : {city: city_url} }
    with open('city.json', 'w') as json_file:
        contents = json.dumps(lt)
        json_file.write(contents)
        json_file.close

def read_city_url(): # inside make_city_db()
    with open('city.json', 'r') as json_f:
        data = json_f.read()
        obj = json.loads(data)
        return obj

def make_city_db(): #create table of country, city, city_url
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    drop_city = '''
        DROP TABLE IF EXISTS "city_url";
    '''
    create_city = '''
        CREATE TABLE IF NOT EXISTS "city_url"(
            "Id"            INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "country"       TEXT NOT NULL,
            "city"          TEXT NOT NULL,
            "city_url"      TEXT NOT NULL
        );
    '''
    insert_city = '''
        INSERT INTO city_url
        VALUES (NULL, ?,?,?)
    '''
    cur.execute(drop_city)
    cur.execute(create_city)
    obj = read_city_url()   # obj is dict of { country : {city: city_url} }
    for k,v in obj.items():
        country = k
        for key, val in v.items():
            city = key
            url = val
            # print(country,city,url)
            cur.execute(insert_city, [country,city,url])
    conn.commit()
    conn.close()

def create_city_url_db(): # put this in main   
    total = all_city()
    x = country_city_table(total) ## this takes much time to scrape # main sql link
    city_list_write_to_json(x)
    # read json and create Region table
    make_region_db(total)
    # read json and create sqlDB/city_url
    make_city_db()

# make_city_db()  # make DB for city_url
def list_country_by_region(area):
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    where_1 = f'r.region="{area}"'

    q = f'''
    SELECT DISTINCT(r.country )
    FROM Regions AS r
    JOIN city_url AS c
    ON r.country = c.country 
    WHERE {where_1} 
    ORDER BY r.country 
    LIMIT 50
    '''
    result = cur.execute(q).fetchall()
    return [x[0].strip() for x in result]

def list_city_by_country(country):
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    where = f'r.country="{country}"'

    q = f'''
    SELECT c.city
    FROM Regions AS r
    JOIN city_url AS c
    ON r.country = c.country 
    WHERE {where} 
    ORDER BY c.city 
    LIMIT 100
    ''' 
    result = cur.execute(q).fetchall()

    return [x[0].strip() for x in result] #return city

def lookup_country_url(country):
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    where = f"'{country}'"

    q = f'''
    SELECT country_url
    FROM Regions
    WHERE country = {where} 
    ''' 
    result = cur.execute(q).fetchall()
    for tup in result:
        url = tup[0]
    return url   #return country_url

def lookup_city_url(country,city): 
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    
    where_1 = f'r.country="{country}"'
    where_2 = f'c.city LIKE "{city}%"'
    city = []

    q = f'''
    SELECT r.country , c.city , c.city_url
    FROM Regions AS r
    JOIN city_url AS c
    ON r.country = c.country 
    WHERE {where_1} AND {where_2}
    ORDER BY c.city 
    LIMIT 50
    ''' 
    result = cur.execute(q).fetchall()
    for tup in result:
        city.append(tup)
        # print(country,city,url)  ## debug for now
    return city
        
    conn.close()

def list_city_url(area,country,city): 
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    where_1 = f'r.region="{area}"'
    where_2 = f'r.country="{country}"'
    where_3 = f'c.city="{city}"'

    q = f'''
    SELECT r.region, r.country , c.city , c.city_url
    FROM Regions AS r
    JOIN city_url AS c
    ON r.country = c.country 
    WHERE {where_1} AND {where_2} AND {where_3}
    ORDER BY c.city 
    LIMIT 50
    ''' 
    result = cur.execute(q).fetchall()
    for tup in result:
        region = tup[0].strip()
        country = tup[1].strip()
        city = tup[2].strip()
        url = tup[3].strip()
        # print(region,country,city,url)  ## debug for now
        return (region,country,city,url)
        
    conn.close()


def read_review(hotel_url_list,num):
    # hotel_url_list = [ [name, score, comment_title, review_num, url],[]..]
    if num.isnumeric() and int(num) >0 and int(num)<=len(hotel_url_list):
        url = hotel_url_list[int(num)-1][4]
        r =hotel_review(url)
        print(r)
        # for l in r:
        #     text = l
        #     print(text)
    else:
        print('Invalid input!')


def print_query_result(raw_query_result): # 1 element tuple 
    region = [x[0] for x in raw_query_result]
    for i in range(len(region)):
        row = f'[{i+1}]  {region[i]}'
        print(row)
    return region

# read_review(hotel_link)
def list_region_to_select():
    print('Select region: ')
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    q= '''SELECT DISTINCT(region) FROM Regions'''
    result = cur.execute(q).fetchall()

    return print_query_result(result)
    conn.close()


def print_3_col(c_list):
    n = len(c_list)
    list_print = []
    for i in range(n):
        num = f'[{i+1}]'
        text = (num , c_list[i])
        list_print.append(text)

    if n % 3 == 1:
        list_print.extend([(' ',' '),(' ',' ')])
    elif n % 3 == 2:
        list_print.append((' ',' '))
    else:
        list_print = list_print

    i = 0
    while i <= (len(list_print)-2):
        text_1 = f'{list_print[i][0]} {list_print[i][1]}'
        text_2 = f'{list_print[i+1][0]} {list_print[i+1][1]}'
        text_3 = f'{list_print[i+2][0]} {list_print[i+2][1]}'
        row_1 = f'+--------------------+--------------------+--------------------+'
        row_2 = f'|{text_1:<{20}.{18}}|{text_2:<{20}.{18}}|{text_3:<{20}.{18}}|'
        print(row_1)
        print(row_2)
        i = i + 3
    print(row_1)

def print_hotel_data(data_list): # data_list=[[hotel_name, score, comment_title, review_num],[]..]
    num = 1
    for i in data_list:
        row_1 = f'+---+---------------+----------+---------------+---------------+'
        row_2 = f'|{str(num):^{3}.{3}}|{i[0]:<{15}.{12}}|{i[1]:<{10}.{9}}|{i[2]:<{15}.{12}}|{i[3]:<{15}.{12}}|'
        print(row_1)
        print(row_2)
        num = num + 1
    print(row_1)

def hotel_interactive(): # put this in main
    ## interactive
    region = list_region_to_select()
    # select region: Europe/Asia/Amerian/Africa
    while True:
        num = input('Enter a region: ')
        if num.isnumeric() and int(num) >0 and int(num)<=len(region):
            area = region[int(num)-1]
            break
        elif num == 'exit':
            exit()
        else:
            print('Invalid Input!')
            continue
    print(f'List all countries in {area}:')
    countries = list_country_by_region(area)
    print_3_col(countries)

    # select country
    while True:
        n = input('Enter a country from the list: ')
        if n.isnumeric() and int(n) >0 and int(n)<=len(countries):
            selected_c = countries[int(n)-1]
            break
        elif n == 'exit':
            exit()
        else:
            print('Invalid Input!')
            continue
    print(selected_c)
    
    # type city name / partial
    while True:
        all_or_pop = input('List "all cities" or "enter" or "exit": ')
        if all_or_pop == "exit":
            exit()
        elif all_or_pop == "enter":
            print(f'Look up cities in {selected_c}: ')

            while True:
                city = input('Enter the letter: ')
                result = lookup_city_url(selected_c, city)
                y = [x[1] for x in result ]

                if len(y) == 0:
                    print('City is Not in the list!')
                    continue
                elif city == 'exit':
                    exit()
                elif city == 'back':
                    continue
                else:
                    # print all countries under the selected region
                    print_3_col(y) 
                    break
            
            while True:
                n = input('Enter a city from the list: ')
                if n.isnumeric() and int(n) >0 and int(n)<=len(result):
                    selected_city = result[int(n)-1][1]
                    break
                elif n == 'exit':
                    exit()
                else:
                    print('Invalid Input!')
                    continue
                # break
            # break  

        else:
            # list all cities under selected_c    
            print(f'List all cities in {selected_c}: ')
            result = list_city_by_country(selected_c)
            print_3_col(result)
        
            # select city from all
            while True:
                n = input('Enter a city from the list: ')
                if n.isnumeric() and int(n) >0 and int(n)<=len(result):
                    selected_city = result[int(n)-1]
                    break
                elif n == 'exit':
                    exit()
                else:
                    print('Invalid Input!')
                    continue
                # break
            # break  

        # print(f'List the url of {selected_city}: ') # debug
        # print(area,selected_c,selected_city) # debug

        info = list_city_url(area,selected_c,selected_city) # city url from sql
        city_url = info[3] # retreive browse url
        browse_url = go_to_hotels_browse(city_url)  # return browse url

        # check browser_url, if there is a 'https://', then go to the url
        pattern = r'(http.*.html)'
        search = re.match(pattern,browse_url)
        if search:
            pass
            # print(search[0])  # comment out later, debug for now
        else:
            print('No search result!')
            exit()# exit or back?

        data = hotel_info_from_browse_list(browse_url) #use browse url to scrape hotel list
        # return list of hotel_name, score, comment_title, review_num, url
        # print(data)
        print_hotel_data(data) # print: hotel_name, score, comment_title, review_num


        # select hotel
        while True:
            n = input('Select a hotel number to read reviews or type "next" to read more: ')
            if n.isnumeric() and int(n) >0 and int(n)<=len(data):
                read_review(data,n)
                continue
            elif n == 'exit':
                exit()
            elif n == 'next':
                print('\n')
                break
            else:
                print('Invalid Input!')
                continue
        break
    
    return [selected_c,selected_city]

# create Region,city_url TABLE in sql
def check_tables_sql():
    conn = sqlite3.connect('hotelbooking.sqlite')
    cur = conn.cursor()
    check_q = '''
        SELECT name FROM sqlite_master 
        WHERE type='table';
    '''
    result = cur.execute(check_q).fetchall()
    find = [x[0] for x in result]
    if 'city_url' in find and 'Regions' in find:
        print('TABLE EXISTS!')
    else:
        print('Creat Database....now...')
        create_city_url_db()
    conn.close()

## cache ##
def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")

        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

def make_url_request_using_cache_json(url,params, uni_key, cache): # reserve for now
    # if url cannot be the keys
    if (uni_key in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[uni_key]
    else:
        print("Fetching")

        response = requests.get(url,params)
        cache[uni_key] = response.json()
        save_cache(cache)
        return cache[uni_key]

def construct_unique_key(baseurl, params):  ## if url cannot be the keys, reserve for now
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = baseurl + connector +  connector.join(param_strings)
    return unique_key

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
    except:
        results = [('N/A','N/A','N/A','N/A','N/A')]

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
        results=results, region=selected_region,plot_div=div)
    else:

        return render_template('results.html', 
        results=results, region=selected_region)


if __name__=="__main__":
    CACHE_DICT = load_cache()

    check_tables_sql()

    select_city = hotel_interactive()
    country = select_city[0]
    city = select_city[1]

    # Reddit topic
    print(f'Top3 topics of {city} in Reddit :')
    result = reddit_topics(city,3)
    if len(result) == 0:
        print(f'No topic for {city} in Reddit!')
        print(f'Top5 topics of {country} in Reddit :')
        result = reddit_topics(country,5) # top 5
        for k,v in result.items():
            print(k,v)
    else:
        print(result)


    # weather obj
    # obj = darksky_api.weather_data(select_city)
    # obj.plot_temp()
    # obj.plot_precip_line()

    # topic = 'taipei hotel' 
    # num = 3
    # reddit_topics(topic,num)


