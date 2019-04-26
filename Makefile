build:
	docker build -t brandonharrisoncode/nlp-qna .

run: build
	docker run -it --rm -p 5000:5000 -e GOOGLE_MAPS_API_KEY -e NPS_API_KEY brandonharrisoncode/nlp-qna
