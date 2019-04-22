from flask import Flask, request, render_template
from deeppavlov import build_model, configs
from bs4 import BeautifulSoup
from urllib.request import urlopen
from unicodedata import normalize

model = build_model(configs.squad.squad, download=True)
app = Flask(__name__)

@app.route('/', methods=['GET'])
def landing():
    return 'This is the NLP Project 3 API service.'


@app.route('/test', methods=['GET'])
def test():
    url = 'https://en.wikipedia.org/w/api.php?format=xml&action=query&prop=extracts&titles=Zion%20National%20Park&redirects=true'
    raw = urlopen(url)
    soup = BeautifulSoup(raw, 'xml')
    page = soup.api.query.pages.findAll('page')[0]
    extract = str(page.extract)
    text = BeautifulSoup(extract, 'lxml')
    context = normalize("NFKD", text.get_text())
    question = 'When were the earliest humans in the park?'
    response = model([context], [question])
    return context + '\n\n' + str(response)


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
