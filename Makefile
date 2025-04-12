install:
	pip install -r requirements.txt

run:
	python application/src/main.py

deploy:
	rm -rf dist build
	pyinstaller --onefile --name concilia_pagamentos application/src/main.py --distpath dist --workpath build --clean
