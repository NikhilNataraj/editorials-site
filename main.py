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


def truncate_text(text, max_length=120):
    return text if len(text) <= max_length else text[:max_length] + '...'


@app.route("/")
def home():
    response = requests.get(f"{API_URL}/api/articles")
    data = response.json()
    all_titles = list(reversed([article["title"] for article in data][-7:]))
    all_articles = list(reversed([truncate_text(article["content"]) for article in data][-7:]))
    all_sources = list(reversed([article["source"] for article in data][-7:]))
    return render_template("index.html", titles=all_titles,
                           articles=all_articles, sources=all_sources, year=datetime.now().year, total=len(data))


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
    return render_template("article.html",
                           title=title, article=content, source=source, year=datetime.now().year)


@app.route("/articles/older")
def older_articles():
    response = requests.get(f"{API_URL}/api/articles")
    data = response.json()
    all_titles = list(reversed([article["title"] for article in data][:-7]))
    all_articles = list(reversed([truncate_text(article["content"]) for article in data][:-7]))
    all_sources = list(reversed([article["source"] for article in data][:-7]))
    return render_template("older.html", titles=all_titles,
                           articles=all_articles, sources=all_sources, year=datetime.now().year)


if __name__ == "__main__":
    app.run(debug=True)
