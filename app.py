import os
import requests
import json
import urllib.parse
from flask import Flask, request, render_template
from deeppavlov import build_model, configs
from bs4 import BeautifulSoup
from unicodedata import normalize

model = build_model(configs.squad.squad, download=True)
app = Flask(__name__)
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']

@app.route('/', methods=['GET'])
def landing():
    return 'This is the NLP Project 3 API service.'

def google_results(latitude, longitude):
    print('API key: {}'.format(GOOGLE_MAPS_API_KEY))
    url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?location={},{}&query=national%20parks&type=park&key={}'.format(latitude, longitude, GOOGLE_MAPS_API_KEY)
    print('URL: {}'.format(url))
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
        if 'National Park' in location['name']:
            national_parks.append(location['name'])

    responses = []
    for park in national_parks[:6]:
        page = get_wikipedia_page(park)
        responses.append((park, model([page], [question])))
    return str(responses)


def get_wikipedia_page(title):
    url = 'https://en.wikipedia.org/w/api.php?format=xml&action=query&prop=extracts&titles={}&redirects=true'.format(title)
    raw = requests.get(url).content
    soup = BeautifulSoup(raw, 'xml')
    page = soup.api.query.pages.findAll('page')[0]
    extract = str(page.extract)
    text = BeautifulSoup(extract, 'lxml')
    page = normalize("NFKD", text.get_text())
    return page



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
