import os
import nltk
import requests
from urllib.parse import quote
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

nltk.data.path.append(os.path.join(os.path.dirname(__file__), 'nltk_data'))

app = Flask(__name__)
Bootstrap(app)

API_URL = os.getenv("API_URL")


def truncate_text(text, max_length=120):
    return text if len(text) <= max_length else text[:max_length] + '...'


JOKE = "Why don't scientists trust atoms? Because they make up everything!"
FACT = ("Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over "
        "3,000 years old and still perfectly edible.")
QUOTE = "The only way to do great work is to love what you do."
AUTHOR = "Steve Jobs"


@app.route("/api/cron")
def fetch_jfq():
    global JOKE, FACT, QUOTE, AUTHOR

    j_api_url = f'{os.getenv("JFQ_API_URL")}/jokes?limit=1'
    api_key = os.getenv("JFQ_API_KEY")
    joke_response = requests.get(j_api_url, headers={'X-Api-Key': api_key})
    joke = joke_response.json()[0]
    JOKE = joke["joke"]

    f_api_url = f'{os.getenv("JFQ_API_URL")}/facts'
    fact_response = requests.get(f_api_url, headers={'X-Api-Key': api_key})
    fact = fact_response.json()[0]
    FACT = fact["fact"]

    q_api_url = f'{os.getenv("JFQ_API_URL")}/quotes'
    quote_response = requests.get(q_api_url, headers={'X-Api-Key': api_key})
    quote = quote_response.json()[0]
    AUTHOR = quote["author"]
    QUOTE = quote["quote"]


@app.route("/")
def home():
    global JOKE, FACT, QUOTE, AUTHOR
    response = requests.get(f"{API_URL}/api/articles")
    data = response.json()
    all_titles = list(reversed([article["title"] for article in data][-7:]))
    all_articles = list(reversed([truncate_text(article["content"]) for article in data][-7:]))
    all_sources = list(reversed([article["source"] for article in data][-7:]))
    all_dates = list(reversed([article["date"] for article in data][-7:]))

    return render_template("index.html", titles=all_titles,
                           articles=all_articles, sources=all_sources, dates=all_dates,
                           joke=JOKE, fact=FACT, quote=QUOTE, author=AUTHOR,
                           year=datetime.now().year, total=len(data))


def short_paragraphs(text, max_length=200):
    sentences = sent_tokenize(text)
    paragraphs = []
    current_paragraph = ""

    for sentence in sentences:
        if len(current_paragraph) + len(sentence) + 1 <= max_length:
            current_paragraph += sentence + " "
        else:
            paragraphs.append(current_paragraph.strip())
            current_paragraph = sentence + " "

    if current_paragraph:
        paragraphs.append(current_paragraph.strip())

    return paragraphs


@app.route("/article/<title>")
def show_article(title):
    print(f"{API_URL}/api/article/{quote(title)}")
    response = requests.get(f"{API_URL}/api/article/{quote(title)}")
    data = response.json()
    print(data)
    content = short_paragraphs(data["content"])
    source = data["source"]
    date = data["date"]
    return render_template("article.html",
                           title=title, article=content, source=source, year=datetime.now().year, date=date)


@app.route("/articles/older")
def older_articles():
    response = requests.get(f"{API_URL}/api/articles")
    data = sort_acc_to_date(response.json())
    all_titles = [article["title"] for article in data][7:]
    all_articles = [truncate_text(article["content"]) for article in data][7:]
    all_sources = [article["source"] for article in data][7:]
    all_dates = [article["date"] for article in data][7:]
    return render_template("older.html", titles=all_titles,
                           articles=all_articles, sources=all_sources, dates=all_dates, year=datetime.now().year)


def sort_acc_to_date(data):
    date_format = "%B %d, %Y"
    for article in data:
        article["date"] = datetime.strptime(article["date"], date_format)

    data = sorted(data, key=lambda x: x["date"], reverse=True)
    for article in data:
        article["date"] = article["date"].strftime(date_format)

    return data


if __name__ == "__main__":
    app.run(debug=True)
