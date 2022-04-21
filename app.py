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

# ---------------------------------- Google related searches functions ----------------------------------


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
            results.update(loop_over_related_searches(results))

    return list(results)


# ---------------------------------- Scraping SERP ----------------------------------
def get_serp(
    query, custom_search_engine_id, key, geolocation="ir", interface_lang="fa"
):
    """Getting the SERP top 10 results
    """
    returned_df = adv.serp_goog(
        query.strip(),
        gl=geolocation,
        hl=interface_lang,
        cx=custom_search_engine_id,
        key=key,
    )

    return returned_df


# ---------------------------------- N-gram ----------------------------------
def ngram(text, max_phrase_len=2):
    """Calculating N-gram for input text corpus
    """
    phrases_df = pd.DataFrame()
    for i in range(1, max_phrase_len + 1):
        phrases_df = phrases_df.append(adv.word_frequency(text, phrase_len=i))

    # Calculating weighted frequency
    phrases_df.loc[:, "wtd_freq"] = phrases_df.apply(
        lambda row: row["abs_freq"] * pow(len(row["word"].split(" ")), 2), axis=1
    )
    # Sorting values
    phrases_df = phrases_df.sort_values(
        by=["wtd_freq", "abs_freq"], ascending=[False, False]
    ).reset_index(drop=True)

    return phrases_df


# ---------------------------------- App section ----------------------------------
st.title("SEOs swiss army knife 🔪")
st.markdown("-----")
st.subheader("Getting Google related searches")
target_depth = st.selectbox("Choose the depth", ["0", "1", "2", "3", "4"])
target_query = st.text_input("Insert the target query", key="target_query")


# A function for creating "CSV" files from DataFrames
@st.cache
def convert_df(df):
    """Converting a DataFrame to a CSV file
    """
    return df.to_csv().encode("utf-8")


if target_query and target_depth:
    with st.spinner("Please wait..."):
        # Getting related searches
        output = pd.DataFrame(
            get_related_searches_based_on_depth(
                target_query, int(target_depth)),
            columns=["Related searches"],
        )
        # Appending an empty column
        output[""] = ""
        # Calculating N-gram for related searches, and concating two DataFrames together
        output = pd.concat([output, ngram(output["Related searches"])], axis=1)
        # Converting output DataFrame to a CSV
        csv = convert_df(output)
        # Download button
        st.download_button(
            "Press to download your file",
            csv,
            f"{target_query}.csv",
            "text/csv",
            key="download-csv",
        )

st.markdown("-----")
st.subheader("Get the SERP 10 top results for your target query")
cse_id = st.text_input("Insert the custom search engine id", key="cse_id")
cse_key = st.text_input("Insert the custom search engine key", key="cse_key")
serp_target_query = st.text_input(
    "Insert the target query", key="serp_target_query")

if cse_id and cse_key and serp_target_query:
    with st.spinner("Please wait..."):
        # Getting the SERP data
        serp_csv = get_serp(serp_target_query, cse_id, cse_key)
        # N-gram for title, and description
        title_ngram = ngram(serp_csv["title"])
        title_ngram[""] = ""
        description_ngram = ngram(serp_csv["snippet"])
        # Concating "title" N-gram, and "description" N-gram
        title_description_ngram = pd.concat(
            [title_ngram, description_ngram], axis=1,)
        title_description_ngram[""] = ""
        # Concating two DataFrames
        serp_csv = convert_df(
            pd.concat([title_description_ngram, serp_csv], axis=1))
        # Download button
        st.download_button(
            "Press to download your file",
            serp_csv,
            f"{serp_target_query}.csv",
            "text/csv",
            key="download-csv",
        )
