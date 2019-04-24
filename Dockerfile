FROM python:3.6

WORKDIR /usr/src/app

RUN pip install --no-cache-dir deeppavlov
RUN python -m deeppavlov install /usr/local/lib/python3.6/site-packages/deeppavlov/configs/squad/squad.json
RUN python -m deeppavlov download /usr/local/lib/python3.6/site-packages/deeppavlov/configs/squad/squad.json
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN FLASK_APP=app.py
COPY app.py ./
COPY templates ./templates/
COPY static ./static/

CMD ["flask", "run", "--host=0.0.0.0"]

# CMD ["python", "-m", "deeppavlov", "interact", "/usr/local/lib/python3.6/site-packages/deeppavlov/configs/squad/squad.json"]

# RUN python -m deeppavlov interact squad.json
