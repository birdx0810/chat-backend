# -*- coding: UTF-8 -*-

import os
import json


class __Environment():
    def __init__(self, env):
        self.env = env
        self.freeze = False

    def lock(self):
        self.freeze = True

    def set_env(self, env):
        if self.freeze:
            raise ValueError("Try to update environment")
        self.env = env

    def get_env(self):
        return self.env

    def is_development(self):
        return self.get_env() == "development"


def get_key(env):
    """
    Get API and webhook key for given environment
    """
    if env == "development":
        path = os.path.abspath(
            f"{os.path.abspath(__file__)}/../key/development"
        )
    elif env == "production":
        path = os.path.abspath(
            f"{os.path.abspath(__file__)}/../key/production"
        )
    else:
        raise ValueError(
            "Invalid `env`, must be `development` or `production`")

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


def get_database_config(env):
    """
    Get database config file
    """
    if env == "development":
        path = os.path.abspath(
            f"{os.path.abspath(__file__)}/../config/database/development.json"
        )
    elif env == "production":
        path = os.path.abspath(
            f"{os.path.abspath(__file__)}/../config/database/production.json"
        )
    else:
        raise ValueError(
            "Invalid `env`, must be `development` or `production`")

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


environment = __Environment("development")
