import json
import logging
from requests import get
from sched import scheduler
import time
from flask import Markup
from datetime import datetime
from newsapi import NewsApiClient

global gbl_articles, removed_articles
gbl_articles, removed_articles = {}, []
news_scheduler = scheduler(time.time, time.sleep)
# noinspection PyArgumentList
logging.basicConfig(filename="log_file.log", encoding="utf-8")


def news_API_request(covid_terms=json.loads(open("config.json").read())["news_search_terms"]) -> list:
    """Function pulls articles from the news API and returns them as a list. Your own unique API key is needed; store
    it in the config file field named "api_key" in the same directory as this python module.

    :param covid_terms: String of terms (separated by spaces) to search for in titles of articles.
    :return: List of dictionaries containing news articles and their relevant metadata.
    """
    covid_terms = covid_terms.replace(" ", " OR ")
    newsapi = NewsApiClient(api_key=json.loads(open("config.json").read())["api_key"])  # API initialisation
    try:
        response = get("https://newsapi.org")
        if response.status_code == 200:
            headlines = newsapi.get_everything(qintitle=covid_terms,
                                               sources="bbc-news",
                                               language="en",
                                               # sort_by="relevancy",
                                               domains="bbc.co.uk",
                                               )
            return headlines
        elif response.status_code == 404:
            logging.error("ERROR: Could not connect to the news API at %s due to 404. Try again later.", datetime.now())
            return []
    except ConnectionError:
        logging.error("ERROR: Could not connect to news API at %s. Check your internet connection and try again.", datetime.now())
        return []

def remove_article(article) -> None:
    """Appends an article to the list removed_articles (defined in the global namespace).

    :param article: Dictionary of article and article metadata to append to removed_articles.
    :return: None-type.
    """
    removed_articles.append(article)

    return None


def limit_articles(articles, limit=int(json.loads(open("config.json").read())["num_articles"])) -> list:
    """Limits the number of articles that are to be rendered on the HTML template, thereby limiting the
    number of widgets that will appear.

    :param articles = A list of all articles pulled from the news API.
    :param limit: the number of articles that the user wishes to display on the template.
    :return: List of n articles that are to be displayed in widgets on the HTML template.
    """
    articles_to_display = []
    try:
        for article in articles["articles"]:
            if len(articles_to_display) >= limit:
                break
            elif article in removed_articles:
                continue
            else:
                articles_to_display.append(article)
                remove_article(article)
        return articles_to_display
    except KeyError:
        logging.error("ERROR: Could not find 'articles' value in dictionary.")
        return {}


def embed_hyperlinks(articles):
    """Embeds a hyperlink in the title of the article using Markup().

    :param articles: A list of dictionaries containing articles and their metadata.
    :return: A list of dictionaries containing articles and their metadata, with a markup hyperlink embedded in the title.
    """
    for article in articles:
        article["title"] = Markup("<a href=" + article["url"] + ">" + article["title"] + "</a>")
    return articles
