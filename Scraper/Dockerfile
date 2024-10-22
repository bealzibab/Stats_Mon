FROM python:3.9

WORKDIR /scraper

COPY ../requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scraper.py"]
