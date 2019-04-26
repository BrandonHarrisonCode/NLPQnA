import os
import requests
import json
import urllib.parse
import geopy.distance
import itertools
from multiprocessing.dummy import Pool as ThreadPool
from flask import Flask, request, render_template, abort, url_for
from deeppavlov import build_model, configs
from bs4 import BeautifulSoup
from unicodedata import normalize

model = build_model(configs.squad.squad, download=True)
app = Flask(__name__)
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']
NPS_API_KEY = os.environ['NPS_API_KEY']
national_parks_official = None
meters_per_mile = 1609.344;
pool = ThreadPool(4)

def getLatLong(park):
    data = park['latLong']
    lat_start = data.index(':') + 1
    lat_end = data.index(',', lat_start)
    lng_start = data.index(':', lat_end) + 1
    latitude = data[lat_start:lat_end]
    longitude = data[lng_start:]
    return float(latitude), float(longitude)


def get_national_parks_official():
    parks = []

    nps_parks = []
    limit = 50
    start = 0
    try:
        while True:
            url = 'https://developer.nps.gov/api/v1/parks?q=National Park&limit={}&start={}&api_key={}'.format(limit, start, NPS_API_KEY)
            result = requests.get(url)
            data = json.loads(result.content)['data']
            if not data:
                break
            for park in data:
                if 'National Park' in park['designation']:
                    name = park['fullName']
                    latitude, longitude = getLatLong(park)
                    nps_parks.append({'name': name, 'lat': latitude, 'lng': longitude})
                    start += limit
    except e:
        pass

    with open('static/national_parks.json') as f:
        fallback_parks = json.loads(f.read())

    if len(nps_parks) < len(fallback_parks):
        print('ERROR getting parks data from NPS.  Using fallback data.')
        parks = fallback_parks
    else:
        parks = nps_parks

    return parks
national_parks_official = get_national_parks_official()


@app.route('/', methods=['GET'])
def landing():
    return render_template('answerform.html', GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)



@app.route('/parksNearby', methods=['GET'])
def results_in_radius():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    radius = float(request.args.get('radius')) / meters_per_mile
    if radius > 300:
        abort(400)

    inbound_parks = []
    for park in national_parks_official:
        name = park['name']
        loc_lat = park['lat']
        loc_lng = park['lng']
        distance = geopy.distance.distance((latitude, longitude), (loc_lat, loc_lng)).miles
        if distance <= radius:
            inbound_parks.append(park)
    return json.dumps(inbound_parks)


def get_wikipedia_page(title):
    url = 'https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&titles={}&redirects=true'.format(urllib.parse.quote_plus(title))
    print(url)
    raw = requests.get(url).content
    data = json.loads(raw)
    pages = data['query']['pages']
    page = None
    for item in pages.values():
        if title in item['title']:
            page = item['extract']
            break
    if page is None:
        print('ERROR getting wikipedia page for {}'.format(title))
        return None
    text = BeautifulSoup(page, 'lxml').get_text()
    normalized_text = normalize('NFKD', text)
    return normalized_text


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    parks = data.get('parks')
    question = data.get('question')
    if parks is None or question is None:
        abort(400)

    results = pool.starmap(ask_park, zip(parks, itertools.repeat(question)))
    return json.dumps(results)

def ask_park(park, question):
    context = get_wikipedia_page(park)
    response = model([context], [question]) if context is not None else None
    return {'name': park, 'answer': response}
