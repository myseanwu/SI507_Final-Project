import praw
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

# Reddit keys
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

    search = subreddit.search(topic, limit = num, sort=sorting )  #sort= 'top', 'hot','new','comment (default)'
    result = {}
    i=1
    for x in search:
        num = f'[{i}]'
        topic = x.title.strip('\n')
        pic = x.url
        i = i + 1
        result[num] = (topic,pic)
    return result


### Booking.com  scrawling and scraping

def all_city():  # print: region/country/url, return 'country url'
    destination = '''
    https://www.booking.com/destination.html
    '''
    response = requests.get(destination)
    soup = BeautifulSoup(response.text, 'html.parser')
    li = soup.find_all('li',class_="dst-sitemap__sublist-item")

    total = []
    for item in li:
        h4 = item.find_all('h4',class_="dest-sitemap__sublist-title")#.text.strip('\n')
        h = item.find_all('a')
        for item in h4:
            x = item.text.strip('\n').strip()

        for i in h:
            c = i.text.strip('\n').strip()
            u = 'https://www.booking.com' +  i.get('href')
            result=[x,c,u]
            total.append(result)
    return total


def make_city_url_list(country_url): # country_url/city_url, return city url
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
    return return_list # {city: city_url, city: city_url,...}


def go_to_hotels_browse(city_url):  # use city_url to browse city hotel list
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

    return total


def hotel_review(hotel_url): # return 3x review contents
    url_text = make_url_request_using_cache(hotel_url, CACHE_DICT) # using cache
    soup = BeautifulSoup(url_text, 'html.parser')
    reviews = soup.find_all('span',class_="c-review__body")
    re_list = []
    for re in reviews:
        r = re.text
        re_list.append(r)
    if len(re_list) == 0:
        return ['No available reviews!']
    else:
        try:
            return re_list[0:3] # only retrieve 3 reviews
        except:
            return re_list[:] # if reviews less than 3, retrieve all


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


def country_city_table(country_url): # country_url = [[region,country, country_url],[]..]
    lt = {}
    for item in country_url:
        lt[item[1]] = make_city_url_list(item[2])
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
    obj = read_city_url()   # obj is a dict of { country : {city: city_url} }
    for k,v in obj.items():
        country = k
        for key, val in v.items():
            city = key
            url = val
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
    ''' 
    result = cur.execute(q).fetchall()
    for tup in result:
        region = tup[0].strip()
        country = tup[1].strip()
        city = tup[2].strip()
        url = tup[3].strip()

        return (region,country,city,url)
    conn.close()


def read_review(hotel_url_list,num):
    # hotel_url_list = [[name, score, comment_title, review_num, url],[]..]
    if num.isnumeric() and int(num) >0 and int(num)<=len(hotel_url_list):
        url = hotel_url_list[int(num)-1][4]
        r =hotel_review(url)
        for l in r:
            print(l,'\n')
        return r # list
    else:
        print('Invalid input!')


def print_query_result(raw_query_result): # 1 element tuple
    region = [x[0] for x in raw_query_result]
    for i in range(len(region)):
        row = f'[{i+1}]  {region[i]}'
        print(row)
    return region


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
        all_or_pop = input('List "all" cities or "enter" or "exit": ')
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

        elif all_or_pop == 'all':
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

        else:
            print('Invalid command!')

        info = list_city_url(area,selected_c,selected_city) # city url from sql
        city_url = info[3] # retreive browse url
        browse_url = go_to_hotels_browse(city_url)  # return browse url

        # check browser_url, if there is a 'https://', then go to the url
        pattern = r'(http.*.html)'
        search = re.match(pattern,browse_url)
        if search:
            pass
        else:
            print('No search result!')
            exit()# exit or back?

        data = hotel_info_from_browse_list(browse_url) #use browse url to scrape hotel list
        # return list of hotel_name, score, comment_title, review_num, url
        print_hotel_data(data) # print: hotel_name, score, comment_title, review_num

        # select hotel
        while True:
            n = input('Select a hotel number to read reviews or type "topic" to read Reddit topics: ')
            if n.isnumeric() and int(n) >0 and int(n)<=len(data):
                print('\n')
                read_review(data,n)
                continue
            elif n == 'exit':
                exit()
            elif n == 'topic':
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


if __name__=="__main__":
    CACHE_DICT = load_cache()
    check_tables_sql()

    # hotel interaction
    select_city = hotel_interactive()
    country = select_city[0]
    city = select_city[1]

    # Reddit topic
    print(f'Top3 topics of {city} in Reddit :')
    result = reddit_topics(city,3)
    if len(result) == 0:
        print(f'No topic for {city} in Reddit!\n')
        print(f'Top5 topics of {country} in Reddit :')
        result = reddit_topics(country,5) # top 5
        for k,v in result.items():
            print(k,v[0])
    else:
        for k,v in result.items():
            print(k,v[0])

    # choose to read weather
    while True:
        n = input('Select "exit" or type "weather" to see weather results: ')
        if n == 'exit':
            exit()
        elif n == 'weather':
            try: # weather (obj of darksky api)
                try:  # weather obj: if city no result, use country
                    obj = darksky_api.weather_data(city)
                except:
                    obj = darksky_api.weather_data(country)

                info = obj.total
                for i in range(len(info['wk_time'])):
                    day = info['wk_time'][i].split()[0]
                    sum = info['daily_sum'][i]
                    print(f'[{day}] {sum}')
                fig = obj.plot_temp()
                fig.show()
                fig2 = obj.plot_precip_line()
                fig2.show()

            except: # weatherbit (obj of weatherbit api)
                try:
                    try:
                        obj = darksky_api.weatherbit_data(city)
                    except:
                        obj = darksky_api.weatherbit_data(country)

                    info = obj.total
                    for i in range(len(info['wk_time'])):
                        day = info['wk_time'][i].split()[0]
                        sum = info['comment'][i]
                        print(f'[{day}] {sum}')
                    fig = obj.plot_temp()
                    fig.show()
                    fig2 = obj.plot_precip_line()
                    fig2.show()
                except:
                    print('No content in weatherbid!')

        else:
            print('Invalid Command!')


