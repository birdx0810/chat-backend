# README.md
This is a chatbot backend written using Python

## Preface
This service is built for two users, which we would define as "patient" and "admin" in the following documentation.
- "patient": the user using LINE to communicate with the bot/admin (has status)
- "admin": the user using the frontend to communicate with patient (no status, determines if message has been read)
- "bot": the automatic response generator that determines responses via a bunch of `if...else` operations

## Install dependencies

```
# Create/activate Python virtual environment
python3 -m venv venv
source venv/bin/activate
# Download requirements
cat requirements.txt | xargs -n 1 pip install
python -m spacy download zh_core_web_lg
```

## Getting Started

```
# Switch to virtual environment (if not done)
source venv/bin/activate
# Run the service
python bot.py
```

## Documentation

The directory tree of the project is as follows:
```
|- config/
    |- database/
        |- development.json
        |- production.json
    |- server.json
|- key/
    |- development
    |- google_maps
    |- production
    |- vapid
|- scripts/
|- util/
|- venv/
|- bot.py
|- database.py
|- environment.py
|- event.py
|- README.md
|- requirements.txt
|- responder.py
|- sentiment.py
|- similarity.py
|- status_code.py
|- templates.py
```

### `bot.py`
This file is the main file for the chatbot. It also serves as the LINE message handler and API handlers (IoT service and chatbot frontend).

### `database.py`
This file holds the all the code for querying databases.

### `environment.py`
This file holds the code for getting config/key values from `config/` or `key/`.

#### `config`
This directory holds the `json` configuration files for the database and the server.

The format for `server.json` is as follows:
```json
{
    "mode": "",         // (str) The mode of server, i.e. "production" or "development",
    "server_name": "",  // (str) The hostname/IP address of backend (Python) server,
    "client_name": "",  // (str) The hostname/IP address of frontend (React) client,
}
```

The format for `database/development.json` and `database/production.json` is as follows:
```json
{
    "user": "",     // (str) Username for the database,
    "password": "", // (str) Password for the database,
    "database": "", // (str) The name of database schema,
    "host": "",     // (str) The hostname/IP address of database
}
```

#### `key`
This directory holds the API keys for LINE Messaging API, Google Maps API and VAPID (Push Notifications).
The files are normal text files that are read using the `open(PATH, "r")` built-in function.

The format for `development` and `production` LINE API keys is as follows
```
CHANNEL_ACCESS_TOKEN
CHANNEL_SECRET
```
The tokens derived from the [LINE developers](https://developers.line.biz/console/) page

The format for the Google Maps API is as follows
```
GOOGLE_MAP_API
```
The documentation for getting a Google Map API could be found [here](https://developers.google.com/maps/documentation/javascript/get-api-key)

The VAPID (Push Notifications) Key is generated from the frontend and is formatted as follows:
```
PUBLIC_KEY
PRIVATE_KEY
```

### `event.py`
This file determines the event logic flow of the patient and controls the status of the patient.
- The status of the patient is determined by their respective replies.
- If the patient's message is not within predefined answers, it will return an error code, **but would not change** the patient's original status.

### `responder.py`
This file takes the status returned by the `event.py` module and determines what to reply to the patient. Functions of the module include:
- sends responses of the bot/admin to the patient via the LINE API
- sends all messages to the frontend via webhooks
- triggers the push notification to the admin
- only changes the status of user into `s` (or `w`) if it is the end of conversation

### `sentiment.py`
The sentiment analysis module using LIWC for calculating the sentiment score of the patient's message. (For frontend)

### `similarity.py`
The similarity module for determining the question asked by the patient. (Used in QA)

### `status_code.py`
This file holds the magic codes for all status codes.
For each status family, there is dictionary which keys indicate the status of the patient and value is the status code.
Statuses include:
- Registration: `r` prefix
- High Temperature: `s1` prefix
- QA: `qa` prefix
- System statuses:
    - `s`: null state
    - `w`: wait for admin state

### `templates.py`
This file holds all the messages (text) or templates (LINE templates) needed for the application to send to patient or admin.
This file also includes the Google Maps API for querying the nearest hospital located to the patient.

### `util/`
This directory holds the dictionary for jieba and LIWC used for the sentiment analysis.

### `scripts/`
This directory holds the bash scripts for running certain tasks.

#### `rich_menu/`
This directory holds the scripts for generating, activating, uploading, and deleting LINE's Rich Menu. Documentation of Rich Menus could be found [here](https://developers.line.biz/en/docs/messaging-api/using-rich-menus/)

#### `api_text.sh`
This is the script for triggering the High Temperature Event of the patient using cURL.

## Other files:
- [ ] 改流程圖
