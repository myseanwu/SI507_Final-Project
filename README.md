# SI507_Final-Project

This project will aim at travels. The proposed program would provide users to select a city and see some hotels with scores and reviews. 
Then, users could search popular topics regarding the city they are interested in. 
Also, users could look up the forecasted weather with the trending graph for the next week in this program.
## Instructions for running the code (e.g., how to supply API keys)


#### Reddit API keys:
* Client_id, client_secret, user_agent, username, password
  ##### Create an app in Reddit to get these OAuth2 keys to access the API
* Use PRAW,the Python Reddit API Wrapper, to connect API
  ##### Reference: https://github.com/reddit-archive/reddit/wiki/oauth2
  ##### Reference: https://praw.readthedocs.io/en/latest/getting_started/quick_start.html

#### Mapbox api_key:
* Client_key
* Reference: https://docs.mapbox.com/api/accounts/#tokens

#### Darksky api key:
* API key
* Reference: https://darksky.net/dev/docs#data-block-object
* Note: Darksky API service will no longer accept new signups since 3/31 2020.

#### Weatherbit api key: (alternative to Darksky api)
* API key
* Reference: https://www.weatherbit.io/api/weather-forecast-16-day

## Required Python packages for this project to work (e.g., requests, flask)
* PRAW, datetime, requests, BeautifulSoup, sqlite3, re, flask, plotly, pytz

## Brief description of how to interact with the program
* Running main.py file, users will have the interaction in the terminal with command line prompt, asking users to type selections step by step. 
* Running app_flask.py file, the program will generate a Flask web application running on http://127.0.0.1:5000/.
Either feeding the form by typing country and city name or selecting them by drop-down options, 
the program will then generate the hotel information. 
Also, there are some options related to the selected city that users could choose, which are Reddit topic search and weather information.



