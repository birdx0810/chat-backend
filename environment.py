# -*- coding: UTF-8 -*-

import os
import json


def get_key():
    """
    Get API and webhook key for given environment
    """
    path = os.path.abspath(
        f"{os.path.abspath(__file__)}/../key/{get_server_config()['mode']}"
    )

    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} does not exist")

    with open(path, "r") as line_api_keys:
        keys = [line.strip() for line in line_api_keys.readlines()]

    return keys


def get_maps_key():
    """
    Get Google Maps API key
    """
    path = os.path.abspath(
        f"{os.path.abspath(__file__)}/../key/google_maps"
    )

    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} does not exist")

    with open(path, "r") as google_map_key:
        keys = google_map_key.read().strip()

    return keys


def get_database_config():
    """
    Get database config file
    """
    path = os.path.abspath(
        f"{os.path.abspath(__file__)}/../config/database/{get_server_config()['mode']}.json"
    )

    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} does not exist")

    with open(path, "r") as config_file:
        keys = json.load(config_file)

    return keys


def get_server_config():
    """
    Get server config file
    """

    path = os.path.abspath(
        f"{os.path.abspath(__file__)}/../config/server.json"
    )

    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} does not exist")

    with open(path, "r") as config_file:
        config = json.load(config_file)

    return config
