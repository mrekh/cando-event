"""This app helps you automate the process of getting Google SERPs related searches,
and do a simple analysis on ths SERP results.
"""

# Importing needed libraries
from collections import Counter
from random import randint
from time import sleep

import advertools as adv
import lxml
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


def clean_query(query):
    """Cleaning query leading, and trailing space.
    Also, it replaces between word space with + sign.
    """
    return str(query).strip().replace(" ", "+")


def get_related_searches(query):
    """Getting Google related searches based on input query
    """
    request = requests.get(
        "http://suggestqueries.google.com/complete/search",
        params={"output": "toolbar", "hl": "fa", "q": clean_query(query)},
    )
    soup = BeautifulSoup(request.text, "lxml")
    res = soup.find_all("suggestion")
    res = [res["data"] for res in res]

    return res


def loop_over_related_searches(current_results):
    """Getting the related searches of each realted search.
    """
    new_results = Counter()

    for related_search in current_results:
        if current_results[related_search] == 1:
            new_results.update(get_related_searches(related_search))
            sleep(randint(1, 6))

    return new_results


def get_related_searches_based_on_depth(query, depth):
    """The main function that handeling the process of getting getting related searches.
    If the input depth be larger than 0, it calls an other function to loop over got related searches.
    """
    # Using "Counter" to get rid of duplicate API calls. It be usefull, when depth is larget than 0.
    results = Counter(get_related_searches(query))

    if depth > 0:
        for _ in range(depth):
            results.update(
                loop_over_related_searches(results))

    return list(results)
