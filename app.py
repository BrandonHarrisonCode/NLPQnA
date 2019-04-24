import os
import requests
import json
import urllib.parse
import geopy.distance
from flask import Flask, request, render_template
from deeppavlov import build_model, configs
from bs4 import BeautifulSoup
from unicodedata import normalize

model = build_model(configs.squad.squad, download=True)
app = Flask(__name__)
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']
NPS_API_KEY = os.environ['NPS_API_KEY']
national_park_names = None

def get_national_park_names():
    names = set()
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
                names.add(park['fullName'])
        start += limit
    return names
national_park_names = get_national_park_names()

@app.route('/', methods=['GET'])
def landing():
    return 'This is the NLP Project 3 API service.'

def google_results(latitude, longitude):
    url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?location={},{}&query=national%20park&type=park&key={}'.format(latitude, longitude, GOOGLE_MAPS_API_KEY)
    result = requests.get(url)
    if result.ok:
        print('Response ok')
        return json.loads(result.content)
    return None


@app.route('/test', methods=['GET'])
def test():
    question = 'How big is the park?'
    latitude = '47.6918452'
    longitude = '-122.2226413'
    maps_results = google_results(latitude, longitude)
    locations = maps_results['results']
    national_parks = []
    for location in locations:
        name = location['name']
        loc_lat = location['geometry']['location']['lat']
        loc_lng = location['geometry']['location']['lng']
        distance = geopy.distance.distance((latitude, longitude), (loc_lat, loc_lng)).miles
        print('Name & distance: {} - {}'.format(location['name'], distance))
        if distance <= 300 and name in national_park_names:
            park = {'name': name, 'latitude': loc_lat, 'longitude': loc_lng, 'distance': distance}
            print(park)
            national_parks.append(park)

    responses = []
    for park in national_parks:
        page = get_wikipedia_page(park['name'])
        responses.append((park['name'], park['distance'], model([page], [question])))
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
    return render_template('answerform.html')


@app.route('/answer', methods=['POST'])
def answer():
    print(request.form)
    context = request.form.get('context')
    question = request.form.get('question')
    response = model([context], [question])
    return render_template('answerform.html', ans=response[0])
