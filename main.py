#!/usr/bin/python3

#from inky import InkyPHAT
from inky.auto import auto
from PIL import ImageFont, ImageDraw, Image
import textwrap
import requests
import time
from datetime import datetime
import yaml
from noaa_sdk import noaa
import requests
from requests.exceptions import HTTPError
import json
import logging
import os
import sys
import stockquotes
import socket

# Election
from urllib.request import urlopen
from xml.etree.ElementTree import parse
from datetime import datetime



logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""Status Dashboard for InkyPhat eInk display. Displays Weather, Covid-19 info, PiHole stats, Air Pollution from my personal station and top Hacker News stories. 
Press Ctrl+C to exit!
""")



font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
redBigFont = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
bigFont = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 15)
medWFont = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)


''' Font Options
DejaVuSans-Bold.ttf      DejaVuSansMono.ttf  DejaVuSerif-Bold.ttf
DejaVuSansMono-Bold.ttf  DejaVuSans.ttf      DejaVuSerif.ttf
'''

'''
Lazy person code copying
sudo nano /usr/lib/systemd/system/eink.service
sudo systemctl start eink.service
sudo systemctl daemon-reload
journalctl -f
'''

# Display Setup
#inky_display = InkyPHAT('yellow')
inky_display = auto(ask_user=True, verbose=True)

inky_display.set_border(inky_display.YELLOW)

img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)


# Setup When I want particular feeds to display

covidHours = [16,17,18,19,20,21]
stockHours = [8,9,10,11,12,13,14,15]
forecastHours = [6,7,8,9,10,17,18,19,20,12,22]
hnHours = [9,11,13,15,17,19,21]
piHours = [12,15,17]

#res1day = ""

# Utility Functions
def getConfig():
    # absolute to run as cron. PiTA
    with open('/home/pi/inkydash/config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        zipcode = config[0]["zip"]
        country = config[0]["country"]
        state = config[0]["state"]
        stocks = config[0]["stocks"]
        return zipcode, country, state, stocks


def fetchFeed(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        if 'application/json' in response.headers['content-type']:
          jsonResponse = response.json()
          return jsonResponse
        elif 'text/plain' in response.headers['content-type']:
          textResponse = response.text
          return textResponse
        else: 
          logging.warning("Unknown format in jquery assume json")
          jsonResponse = response.json()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        logging.warning(f'HTTP error occurred: {http_err}')

    except Exception as err:
        print(f'Other error occurred: {err}')
        logging.warning(f'Other error occurred: {err}')


def drawClean(color):
  if color == 'WHITE':
    draw.rectangle((0, 0, inky_display.WIDTH,
                        inky_display.HEIGHT), 
                        (inky_display.WHITE))
  elif color == 'BLACK':
    draw.rectangle((0, 0, inky_display.WIDTH,
                        inky_display.HEIGHT), 
                        (inky_display.BLACK))
  elif color == 'YELLOW':
    draw.rectangle((0, 0, inky_display.WIDTH,
                        inky_display.HEIGHT), 
                        (inky_display.RED))
  else:
    draw.rectangle((0, 0, inky_display.WIDTH,
                        inky_display.HEIGHT), 
                        (inky_display.WHITE))


def drawScreen():
  inky_display.set_image(img.rotate(180))
  inky_display.show()
  time.sleep(30)



def getWeather():
    try:
        n = noaa.NOAA()
        res = n.get_forecasts(config[0], config[1], False)
        res1day = res[0]["detailedForecast"]
        # display on InkyPHAT
        # Take string of text and wrap it at 38 chars
        txt = textwrap.fill(res1day, 36)

        # Get size of text
        # w, h = draw.multiline_textsize(txt, font)
        left, top, right, bottom = draw.multiline_textbbox((0, 0), txt, font=bigFont)
        w = right - left
        h = bottom - top

        # Center Center the text
        x = (inky_display.WIDTH / 2) - (w / 2)
        y = (inky_display.HEIGHT / 2) - (h / 2)

        drawClean('WHITE')


        # Draw multiline text on scren
        if (w * h) <= 11000:
          txt = textwrap.fill(res1day, 24)
          draw.multiline_text((x, 0), txt, inky_display.BLACK, medWFont)
        elif (w * h) > 11000:
          draw.multiline_text((x, 0), txt, inky_display.BLACK, font)
        
        drawScreen()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        logging.warning(f'HTTP error occurred: {http_err}')

    except Exception as err:
        print(f'Other error occurred: {err}')
        logging.warning(f'Other error occurred: {err}')


def getCovid():
  drawClean('WHITE')
  jsonResponse = fetchFeed(f'https://api.covidtracking.com/v1/states/{config[2]}/daily.json')
  todayCovid = jsonResponse[0]["hospitalizedCurrently"]
  yesterdayCovid = jsonResponse[1]["hospitalizedCurrently"]
  currentlyHospitalized = "Hospitalized: " + "{:,}".format(todayCovid)
  hospitalizationChange = str(
      todayCovid - yesterdayCovid) + " new hospitalizations"
  newCases = "{:,}".format(jsonResponse[0]["positiveIncrease"]) + " new positivity"
  covidUpdate = datetime.now().strftime('%a %b %d %-I:%M %p')
  draw.text((0, 0), {config[2]} + " Covid Update", inky_display.YELLOW, bigFont)
  draw.text((0, 20), currentlyHospitalized, inky_display.BLACK, bigFont)
  draw.text((0, 40), hospitalizationChange, inky_display.RED, bigFont)
  draw.text((0, 60), newCases, inky_display.RED, bigFont)
  draw.text((0, 88), covidUpdate, inky_display.BLACK, font)

  drawScreen()


def getCurrentConditions():
  drawClean('WHITE')

  # AQI
  aqiResponse = fetchFeed(
      'https://io.adafruit.com/api/v2/drkpxl/feeds/pollution.aqi')
  printAqi = "Current AQI: " + aqiResponse["last_value"]
  draw.text((0, 0), printAqi, inky_display.BLACK, bigFont)

  # Current Temp
  tempResponse = fetchFeed(
      'https://io.adafruit.com/api/v2/drkpxl/feeds/temp')
  printTemp = "Current Temp: " + tempResponse["last_value"] + " °F"
  draw.text((0, 20), printTemp, inky_display.BLACK, bigFont)

  # Current Humidity
  humResponse = fetchFeed(
      'https://io.adafruit.com/api/v2/drkpxl/feeds/humidity')
  printHum = "Current Humidity: " + humResponse["last_value"] + " %"
  draw.text((0, 40), printHum, inky_display.BLACK, bigFont)

  # Feed Last Update
  lastUpdate = aqiResponse["updated_at"]
  draw.text((0, 88), lastUpdate, inky_display.BLACK, font)

  drawScreen()


def getHackerNews():
  topics = fetchFeed('https://hacker-news.firebaseio.com/v0/topstories.json')
  toptopics = [topics[0], topics[1], topics[2]]
  topic = ""

  for x in toptopics:
    r = fetchFeed(
        'https://hacker-news.firebaseio.com/v0/item/' + str(x) + '.json')
    topic = (r['title'])
    score = str(r['score']) + " pts"

    # Take string of text and wrap it at 38 chars
    txt = textwrap.fill(topic, 24)

    # Get size of text
    w, h = draw.multiline_textsize(txt, bigFont)

    # Center Center the text
    x = (inky_display.WIDTH / 2) - (w / 2)
    y = (inky_display.HEIGHT / 2) - (h / 2)

    drawClean('BLACK')

    # Draw multiline text on scren
    draw.multiline_text((x, y), txt, inky_display.WHITE, bigFont)
    draw.text((0, 0), score, inky_display.RED, redBigFont)
    
    drawScreen()

    time.sleep(60)


def getPihole(hostname = 'pi.hole', port = 80, http_scheme = 'http'):
  drawClean('BLACK')

  piholeResponse = fetchFeed(http_scheme + '://' + hostname + ':' + str(port) + '/admin/api.php')
  printPercentBlockedToday = "PiHoled: " + str(round(piholeResponse["ads_percentage_today"])) + " %"
  printClientsSeen = "Total Clients: " + str(piholeResponse["clients_ever_seen"])
  printQueriesToday = "Queries Today: {:,}".format(piholeResponse['dns_queries_today'])

  #('{:,}'.format(value)) 
  printStatus = "PiHole Status: " + piholeResponse['status']
  draw.text((0, 0), printStatus, inky_display.WHITE, bigFont)
  draw.text((0, 20), printQueriesToday, inky_display.WHITE, bigFont)
  draw.text((0, 40), printPercentBlockedToday, inky_display.RED, bigFont)
  draw.text((0, 60), printClientsSeen, inky_display.WHITE, bigFont)

  # Get Public IP, both work.
  #ipResponse = fetchFeed('https://api.ipify.org?format=json')
  if hostname != 'pi.hole':
     ipResponse = socket.gethostbyname(hostname)
     printHostname = "Hostnamme: " + hostname
     draw.text((0, 100), printHostname, inky_display.YELLOW, bigFont)
  else:
     ipResponse = fetchFeed('https://icanhazip.com')

  printIpResonse = "Public IP: " + ipResponse
  draw.text((0, 80), printIpResonse, inky_display.WHITE, bigFont)
  
  drawScreen()


def get_yahoo_session_and_crumb():
    """Simulates a browser session to grab Yahoo's required security cookies and crumb."""
    session = requests.Session()
    # Mimic a clean browser visit
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
    )

    try:
        # Step 1: Visit the homepage to receive a tracking/session cookie
        session.get("https://finance.yahoo.com", timeout=10)

        # Step 2: Request the dynamic security crumb token linked to that cookie
        crumb_response = session.get(
            "https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10
        )
        if crumb_response.status_code == 200 and crumb_response.text:
            return session, crumb_response.text.strip()
    except Exception as e:
        print(f"Failed to establish automated session: {e}")

    # Fallback to a basic session if the crumb endpoint fails
    return session, None

def getStocks():

  stockSymbols = config[3]
  for x in stockSymbols:
     drawClean('WHITE')
     HEADERS = {
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
     }
     try:
        # Utilizing the highly stable v8 chart endpoint
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{x}?interval=1d"
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        # Error handling if Yahoo returns bad structure
        if (
            not data.get("chart")
            or not data["chart"]["result"]
            or data["chart"]["error"] is not None
        ):
            print(f"Error fetching data for {x}: {data.get('chart', {}).get('error')}")
            return

        # Navigate the /v8/chart JSON hierarchy
        result = data["chart"]["result"][0]
        meta = result["meta"]
        indicators = result["indicators"]["quote"][0]

        # Extract data points
        current_price = meta.get("regularMarketPrice", 0.0)
        previous_close = meta.get(
            "chartPreviousClose", current_price
        )  # fallback to current if missing

        # Calculate daily change percent
        if previous_close != 0:
            increase_percent = (
                (current_price - previous_close) / previous_close
            ) * 100
        else:
            increase_percent = 0.0

        # High/Low for the current period (safely pulling from the last index)
        high = indicators["high"][-1] if indicators.get("high") else current_price
        low = indicators["low"][-1] if indicators.get("low") else current_price

        # Fallback strings for presentation
        printName = f"{x} Stock"  # Note: Chart meta often skips full company names, defaults to symbol layout
        printCurrentPrice = f"${current_price:,.2f}"[0:7]
        printIncreasePercent = f"{increase_percent:.2f}%"
        printHighLow = f"H: {f'${high:,.2f}'[0:7]} / L: {f'${low:,.2f}'[0:7]}"

        # Rendering layout logic
        draw.text((0, 20), printName, inky_display.BLACK, bigFont)
        draw.text((0, 40), printCurrentPrice, inky_display.BLACK, bigFont)

        if increase_percent <= 0:
            draw.text(
                (68, 40), f" ^v  {printIncreasePercent}", inky_display.RED, bigFont
            )
        else:
            draw.text(
                (68, 40),
                f" ^v  {printIncreasePercent}",
                inky_display.BLACK,
                bigFont,
            )

        draw.text((0, 60), printHighLow, inky_display.BLACK, bigFont)
        drawScreen()
        time.sleep(20)

     except Exception as e:
        print(f"An error occurred: {e}")



def getElection():
  var_url = urlopen('https://raw.githubusercontent.com/alex/nyt-2020-election-scraper/master/battleground-state-changes.xml')
  xmldoc = parse(var_url)
  for item in xmldoc.iterfind('channel/item'):
      description = item.findtext('description')
      date = item.findtext('pubDate')
      print(description)
      # Take string of text and wrap it at 38 chars
      txt = textwrap.fill(description, 24)

      # Get size of text
      left, top, right, bottom = draw.multiline_textbbox((0, 0), txt, font=bigFont)
      w = right - left
      h = bottom - top

      # Center Center the text
      x = (inky_display.WIDTH / 2) - (w / 2)
      y = (inky_display.HEIGHT / 2) - (h / 2)

      drawClean('WHITE')
      
      currentLead = (int(''.join(list(filter(str.isdigit, description)))))
      currentLead = "{:,}".format(currentLead)
      if "Trump" in txt:
        draw.multiline_text((x, y), txt, inky_display.RED, bigFont)
        
        #logging.info(f'Trump Current Lead: {currentLead}')
      else:
        draw.multiline_text((x, y), txt, inky_display.BLACK, bigFont)
        #logging.info(f'Biden Current Lead: {currentLead}')

      
      drawScreen()

      time.sleep(20)
    



# Get initial YAML
config = getConfig()

# Main Loop
while True:
  try:
    currentTime = ((datetime.now()).hour)
#    getPihole('vpn.ctptech.dev', 8443, 'https')
#    getPihole('aws.ctptech.dev', 8443, 'https')
#    getPihole('home.ctptech.dev', 8443, 'https')
#    getCovid()
    getWeather()
    getStocks()
    getCurrentConditions()
#    getHackerNews()
#    getElection()
  except (KeyboardInterrupt, SystemExit, Exception) as e:
    print('\nkeyboardinterrupt found!')
    print(e)
    sys.exit(0)
    print('\n...Program Stopped Manually!')
    raise
