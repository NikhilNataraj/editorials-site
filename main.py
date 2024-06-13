import os
import nltk
import requests
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


def truncate_text(text, max_length=100):
    return text if len(text) <= max_length else text[:max_length] + '...'


def fetch_jfq():
    joke_response = requests.get(os.getenv("JOKE_API_URL"))
    joke = joke_response.json()
    JOKE = joke["setup"] + "\n" + joke["punchline"]

    fact_response = requests.get(os.getenv("FACT_API_URL"))
    fact = fact_response.json()
    FACT = fact["text"]

    quote_response = requests.get(os.getenv("QUOTE_API_URL"))
    quote = quote_response.json()["data"][0]
    AUTHOR = quote["quoteAuthor"]
    QUOTE = quote["quoteText"]

    return {"JOKE": JOKE, "FACT": FACT, "AUTHOR": AUTHOR, "QUOTE": QUOTE}


@app.route("/")
def home():
    response = requests.get(f"{API_URL}/api/articles")
    data = sort_acc_to_date(response.json())
    all_ids = [article["id"] for article in data][:7]
    all_titles = [article["title"] for article in data][:7]
    all_articles = [truncate_text(article["content"]) for article in data][:7]
    all_sources = [article["source"] for article in data][:7]
    all_dates = [article["date"] for article in data][:7]

    jfq = fetch_jfq()

    return render_template("index.html", ids=all_ids, titles=all_titles,
                           articles=all_articles, sources=all_sources, dates=all_dates,
                           joke=jfq["JOKE"], fact=jfq["FACT"], quote=jfq["QUOTE"], author=jfq["AUTHOR"],
                           year=datetime.now().year)


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


@app.route("/article/<index>")
def show_article(index):
    index = int(index)
    response = requests.get(f"{API_URL}/api/article/{index}")
    data = response.json()
    title = data["title"]
    content = short_paragraphs(data["content"])
    source = data["source"]
    date = data["date"]
    return render_template("article.html",
                           title=title, article=content, source=source, year=datetime.now().year, date=date)


@app.route("/articles/older")
def older_articles():
    response = requests.get(f"{API_URL}/api/articles")
    data = sort_acc_to_date(response.json())
    all_ids = [article["id"] for article in data][7:]
    all_titles = [article["title"] for article in data][7:]
    all_articles = [truncate_text(article["content"]) for article in data][7:]
    all_sources = [article["source"] for article in data][7:]
    all_dates = [article["date"] for article in data][7:]
    return render_template("older.html", ids=all_ids,
                           titles=all_titles, articles=all_articles,
                           sources=all_sources, dates=all_dates,
                           year=datetime.now().year)


def sort_acc_to_date(data):
    date_format = "%B %d, %Y"
    for article in data:
        article["date"] = datetime.strptime(article["date"], date_format)

    data = sorted(data, key=lambda x: x["date"], reverse=True)
    for article in data:
        article["date"] = article["date"].strftime(date_format)

    return data


if __name__ == "__main__":
    app.run()
