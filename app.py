import os
import requests
import json
import urllib.parse
import geopy.distance
from flask import Flask, request, render_template, abort
from deeppavlov import build_model, configs
from bs4 import BeautifulSoup
from unicodedata import normalize

model = build_model(configs.squad.squad, download=True)
app = Flask(__name__)
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']
NPS_API_KEY = os.environ['NPS_API_KEY']
national_parks_official = None
meters_per_mile = 1609.344;


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
    limit = 50
    start = 0
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
                parks.append({'name': name, 'lat': latitude, 'lng': longitude})
        start += limit
    return parks
national_parks_official = get_national_parks_official()


@app.route('/', methods=['GET'])
def landing():
    return 'This is the NLP Project 3 API service.'


@app.route('/parksNearby', methods=['GET'])
def results_in_radius():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')
    radius = float(request.args.get('radius')) / meters_per_mile
    if radius > 300:
        abort(400)
    print(radius)

    inbound_parks = []
    for park in national_parks_official:
        name = park['name'] 
        loc_lat = park['lat']
        loc_lng = park['lng']
        distance = geopy.distance.distance((latitude, longitude), (loc_lat, loc_lng)).miles
        print('Name & distance: {} - {}'.format(name, distance))
        if distance <= radius:
            park = {'name': name, 'latitude': loc_lat, 'longitude': loc_lng}
            print(park)
            inbound_parks.append(park)
    return json.dumps(inbound_parks)


def ask_questions(national_parks):
    responses = []
    for park in national_parks:
        page = get_wikipedia_page(park['name'])
        responses.append((park['name'], model([page], [question])))
    print(responses)
    return str(responses)


def get_wikipedia_page(title):
    url = 'https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&titles={}&redirects=true'.format(urllib.parse.quote_plus(title))
    print(url)
    raw = requests.get(url).content
    data = json.loads(raw)
    pages = data['query']['pages']
    for item in pages.values():
        if title in item['title']:
            page = item['extract']
            break
    if page is None:
        return None
    text = BeautifulSoup(page, 'lxml').get_text()
    normalized_text = normalize('NFKD', text)
    return normalized_text


@app.route('/answer', methods=['GET'])
def answer_form():
    return render_template('answerform.html', GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)


@app.route('/answer', methods=['POST'])
def answer():
    print(request.form)
    context = request.form.get('context')
    question = request.form.get('question')
    response = model([context], [question])
    return render_template('answerform.html', ans=response[0])
