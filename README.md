# **COVID-19 Dashboard**
###_By Nevan Masterson, UoE_
***
Thank you for downloading this COVID-19 Dashboard. 

###Python Version

To get started, you are firstly going to need to **make sure you possess
Python 3.9.x** or higher.

To check your current Python version, open your command line and simply
type `python` and press enter. This will display your current version.
Once you've confirmed your python version, you can close the command prompt.

###Package Dependencies

Additionally, you will also need to install some package dependencies
seen below. To install these, open your command prompt and type 
`pip install [package name]`, exactly as the package name is seen; it is
_cAsE sEnSiTiVe_.

**Package Names:**
* flask
* uk-covid19
* newsapi-python

###News API Key

Once all dependencies are acquired, you will also need a ***unique API key***
for the News API, which you can get [here](https://newsapi.org/register).
Simply provide a first name and an email address, and you should receive
a key via email. Don't lose it!

###Configuring the config.json File

Once you've received your API key, you'll want to put in the file named
_'config.json'_, located in the same directory as this file you're reading
right now. Upon opening it, you should be able to find a field named 'api_key'
at the very bottom. Store your API key in that field inside the quotation marks. 
You should then have something like `"api_key": "[your api key]"`.

Tweak the other values of the config file to personalise it to you and your
area. Any values you modify, make sure you keep them inside the `" "` quotation
marks. Or don't. It'll break the code if you don't put them there,
but who am I to tell you what to do with your life.

Please note that the UK COVID-19 API only works for countries inside the
United Kingdom, therefore the only entries that will work for the 'nation'
field are:
* 'england'
* 'wales'
* 'scotland'
* 'northern ireland'

Any other entry will fail to yield data from the COVID-19 API.

###Running the Application

To get the application running, right-click and execute the `main.py` file in 
this directory. You will automatically be redirected to a webpage on which the
dashboard will be displayed.

