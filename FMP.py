import json
import pandas as pd
import requests
import os
from apikey import OPENAI_API_KEY, FMP_API_KEY
from urllib.request import urlopen




def get_jsonparsed_data(url):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict
    """
    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

