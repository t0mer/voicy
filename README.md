# Voicy

[![Docker Pulls](https://img.shields.io/docker/pulls/techblog/voicy)](https://hub.docker.com/r/techblog/voicy)
[![License](https://img.shields.io/github/license/t0mer/voicy)](LICENSE.md)

## Voice-controlled Telegram bot for smart homes

Voicy is a Telegram bot written in Python. You send it a voice message, it transcribes the
message with Google Cloud Speech-to-Text, and it runs the matching command as an MQTT publish or
an HTTP POST request. Voicy can be easily integrated with Home Assistant, Node-RED, or any other
smart home platform that speaks MQTT or exposes an HTTP API.

## Table of contents

- [Features](#features)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Step 1) Create a Google application, service account and enable the Speech-to-Text API](#step-1-create-a-google-application-service-account-and-enable-the-speech-to-text-api)
  - [Step 2) Create a Telegram bot](#step-2-create-a-telegram-bot)
  - [Step 3) Set up the configuration folder](#step-3-set-up-the-configuration-folder)
  - [Step 4) Run Voicy](#step-4-run-voicy)
- [Configuration](#configuration)
- [Usage](#usage)
- [Integrations](#integrations)
- [Troubleshooting](#troubleshooting)
- [Security and privacy](#security-and-privacy)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- Transcribes Telegram voice messages with
  [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text); the recognition language
  is configurable (any [supported language](https://cloud.google.com/speech-to-text/docs/languages)
  code, for example `en-US` or `iw-IL`).
- Maps spoken phrases to actions in a simple YAML file (`commands.yaml`).
- Publishes MQTT messages (topic + payload).
- Sends HTTP POST requests (with optional headers and payload).
- Forwards every unrecognized phrase to the MQTT topic `voicy/raw` (when `default.protocol=mqtt`), so you can parse free-form
  commands in Node-RED or Home Assistant.
- Replies in Telegram with the transcript and a configurable success/error message.
- Multi-arch Docker image (`linux/amd64`, `linux/arm64`).

### Built with

* [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/) (`telebot`)
* [google-cloud-speech](https://pypi.org/project/google-cloud-speech/)
* [pydub](https://pypi.org/project/pydub/) + ffmpeg (audio conversion)
* [SoundFile](https://pypi.org/project/SoundFile/)
* [wavinfo](https://pypi.org/project/wavinfo/)
* [Wave](https://pypi.org/project/Wave/)
* [NumPy](https://pypi.org/project/numpy/)
* [paho-mqtt](https://pypi.org/project/paho-mqtt/)
* [Requests](https://pypi.org/project/requests/)
* [PyYAML](https://pypi.org/project/PyYAML/)
* [configparser](https://pypi.org/project/configparser/)
* [Loguru](https://pypi.org/project/loguru/)

## How it works

```mermaid
flowchart LR
    U[Telegram user] -- voice message --> B[Voicy bot]
    B -- OGG to 16-bit PCM WAV<br/>pydub + ffmpeg --> B
    B -- WAV audio --> G[Google Cloud<br/>Speech-to-Text]
    G -- transcript --> B
    B --> M{Exact match in<br/>commands.yaml?}
    M -- "type: mqtt" --> Q[(MQTT broker)]
    M -- "type: post" --> H[HTTP endpoint<br/>e.g. Home Assistant]
    M -- no match --> R["MQTT topic voicy/raw<br/>(payload = transcript)"]
    R --> Q
    Q --> HA[Home Assistant / Node-RED]
    B -- "transcript + result" --> U
```

1. The bot long-polls Telegram and handles **voice messages**. `/start` and `/help` reply with the
   configured welcome message.
2. The voice note is saved as an `.ogg` file under `recordings/`, converted to a 16-bit PCM WAV
   file (pydub, which uses ffmpeg), and sent to Google Cloud Speech-to-Text with the language
   from `config.ini`. Both audio files are deleted after a successful transcription.
3. The transcript is compared with the `text` field of every entry in `commands.yaml`. The match
   is an exact, case-sensitive string comparison.
4. A matching entry is executed by its `type` (`mqtt` or `post`). If nothing matches, the
   transcript is published as-is to the MQTT topic `voicy/raw` (when `default.protocol=mqtt`).
5. The bot replies with the transcript followed by `result.ok` or `result.error`. For `mqtt`
   actions (including the `voicy/raw` fallback), `result.ok` only means the publish was attempted:
   MQTT errors are logged but never reported as failures.

## Requirements

- A Google Cloud project with the **Cloud Speech-to-Text API** enabled, billing enabled, and a
  service account JSON key (see [Step 1](#step-1-create-a-google-application-service-account-and-enable-the-speech-to-text-api)).
  Pricing is listed [here](https://cloud.google.com/speech-to-text/pricing).
- A Telegram bot token from [@BotFather](https://t.me/BotFather) (see [Step 2](#step-2-create-a-telegram-bot)).
- An MQTT broker with username/password authentication, listening on port 1883, if you use MQTT
  commands or the `voicy/raw` fallback.
- Docker, **or** Python 3 with ffmpeg installed (see [From source](#from-source)).

## Installation

### Step 1) Create a Google application, service account and enable the Speech-to-Text API

To use Google Speech-to-Text, you need a Google Cloud application with the API enabled, plus a
service account key that Voicy uses to authenticate.

The first thing you need is a Google account and a Google application. You can create one in the
Google Cloud console: [Go to Google Cloud console](https://console.cloud.google.com/).

Once the console is open, click the project drop-down at the top. It shows your existing Google
applications. After you click it, a pop-up appears; click **New Project**.

[![Google Application](https://github.com/t0mer/tts-stt/blob/main/screenshots/google%20applications%20dashboard.png?raw=true "Google Application")](https://github.com/t0mer/tts-stt/blob/main/screenshots/google%20applications%20dashboard.png?raw=true "Google Application")

[![New Application](https://github.com/t0mer/tts-stt/blob/main/screenshots/new%20project.png?raw=true "New Application")](https://github.com/t0mer/tts-stt/blob/main/screenshots/new%20project.png?raw=true "New Application")

Enter your application name and click **Create**.

Once the application exists, grant it access to the **Cloud Speech-to-Text** API. Go to the
application dashboard and open the APIs overview:

[![APIs overview](https://github.com/t0mer/tts-stt/blob/main/screenshots/apis%20overview.png?raw=true "APIs overview")](https://github.com/t0mer/tts-stt/blob/main/screenshots/apis%20overview.png?raw=true "APIs overview")

Click **Enable APIs and Services** and search for "speech". All the speech-related Google APIs are
listed.

[![Enable APIs and Services](https://github.com/t0mer/tts-stt/blob/main/screenshots/enable%20api%20and%20services.png?raw=true "Enable APIs and Services")](https://github.com/t0mer/tts-stt/blob/main/screenshots/enable%20api%20and%20services.png?raw=true "Enable APIs and Services")

[![Enable STT](https://github.com/t0mer/tts-stt/blob/main/screenshots/enable%20stt%20service.png?raw=true "Enable STT")](https://github.com/t0mer/tts-stt/blob/main/screenshots/enable%20stt%20service.png?raw=true "Enable STT")

Click **Enable**. Your application can now call the Cloud Speech-to-Text API.

The next step is downloading your Google credentials. Google uses them to authenticate your
application, measure how much you use the API, and bill you if usage passes the free tier.

From the home dashboard, go to **APIs overview** as before, and click **Credentials** in the
left-hand menu.

[![Credentials](https://github.com/t0mer/tts-stt/blob/main/screenshots/credentials.png?raw=true "Credentials")](https://github.com/t0mer/tts-stt/blob/main/screenshots/credentials.png?raw=true "Credentials")

Click **Create Credentials** and choose **Service account**.

[![Service Account](https://github.com/t0mer/tts-stt/blob/main/screenshots/Service%20Account.png?raw=true "Service Account")](https://github.com/t0mer/tts-stt/blob/main/screenshots/Service%20Account.png?raw=true "Service Account")

Enter any service account name you like and click **Create**.
Granting the service account access to the project is optional; if you do, prefer a narrow role
over broad ones such as **Owner**. Click **Done**.

[![Grant Access](https://github.com/t0mer/tts-stt/blob/main/screenshots/Grant%20Access.png?raw=true "Grant Access")](https://github.com/t0mer/tts-stt/blob/main/screenshots/Grant%20Access.png?raw=true "Grant Access")

Click the service account you just created to open its details.

[![Service account details](https://github.com/t0mer/tts-stt/blob/main/screenshots/Service%20Accounts.png?raw=true "Service account details")](https://github.com/t0mer/tts-stt/blob/main/screenshots/Service%20Accounts.png?raw=true "Service account details")

Go to the **Keys** tab, click **Add Key** and then **Create new key**. The new key is associated
with your application through the service account.

[![Add Key](https://github.com/t0mer/tts-stt/blob/main/screenshots/add%20key.png?raw=true "Add Key")](https://github.com/t0mer/tts-stt/blob/main/screenshots/add%20key.png?raw=true "Add Key")

In the pop-up, select **JSON** and click **Create**. A JSON file containing the key is downloaded
to your machine. Note where you saved it; you will need it in Step 3.

[![JSON File](https://github.com/t0mer/tts-stt/blob/main/screenshots/Key%20type.png?raw=true "JSON File")](https://github.com/t0mer/tts-stt/blob/main/screenshots/Key%20type.png?raw=true "JSON File")

### Step 2) Create a Telegram bot

Open [Telegram](https://web.telegram.org/) and sign in to your account, or create a new one.

Enter `@BotFather` in the search tab and choose this bot. (Official Telegram bots have a blue
checkmark beside their name.)

[![@BotFather](https://github.com/t0mer/voicy/blob/main/screenshots/scr1-min.png?raw=true "@BotFather")](https://github.com/t0mer/voicy/blob/main/screenshots/scr1-min.png?raw=true "@BotFather")

Click **Start** to activate the BotFather bot.

[![Start](https://github.com/t0mer/voicy/blob/main/screenshots/scr2-min.png?raw=true "Start")](https://github.com/t0mer/voicy/blob/main/screenshots/scr2-min.png?raw=true "Start")

In response, you receive a list of commands to manage bots.
Choose or type the `/newbot` command and send it.

[![/newbot](https://github.com/t0mer/voicy/blob/main/screenshots/scr3-min.png?raw=true "/newbot")](https://github.com/t0mer/voicy/blob/main/screenshots/scr3-min.png?raw=true "/newbot")

Choose a name for your bot; users see it in the conversation. Then choose a username for your bot;
the bot can be found by its username in searches. The username must be unique and end with the
word "bot".

[![Username](https://github.com/t0mer/voicy/blob/main/screenshots/scr4-min.png?raw=true "Username")](https://github.com/t0mer/voicy/blob/main/screenshots/scr4-min.png?raw=true "Username")

After you choose a suitable name, the bot is created. You receive a message with a link to your
bot (`t.me/<bot_username>`), your **bot token**, recommendations for setting a profile picture and
description, and a list of commands to manage the new bot. Copy the token into `bot.token` in
`config.ini` and keep it secret.

[![Bot token](https://github.com/t0mer/voicy/blob/main/screenshots/scr5-min.png?raw=true "Bot token")](https://github.com/t0mer/voicy/blob/main/screenshots/scr5-min.png?raw=true "Bot token")

### Step 3) Set up the configuration folder

Voicy reads everything from a single `config` folder (mounted at `/app/config` in the container).
Create a folder on the host (for example `./voicy/config`) with these three files:

| File | Purpose |
|------|---------|
| `config.ini` | Bot token, MQTT broker, speech language, default protocol and reply texts. See [config.ini](#configini) and the [sample file](app/config/config.ini). |
| `commands.yaml` | Mapping between spoken phrases and actions. See [commands.yaml](#commandsyaml) and the [sample file](app/config/commands.yaml). |
| `key-file.json` | The Google service account key from Step 1. The file name must be exactly `key-file.json`. |

`config.ini`:

```ini
[Telegram]
bot.token=<your-telegram-bot-token>
bot.allowedid=
bot.welcome.message=Hi, my name is Voicy

[MQTT]
mqtt.host=<broker-host>
mqtt.port=1883
mqtt.username=<mqtt-username>
mqtt.password=<mqtt-password>

[GOOGLE]
speech.language=iw-IL

[Defaults]
default.protocol=mqtt

[RESULTS]
result.ok=Done
result.error=Something went wrong
```

`commands.yaml`:

```yaml
commands:

  - name: Boiler on
    text: turn boiler on
    type: mqtt
    topic: voicy/boiler
    payload: "on"

  - name: Send POST request with data and headers
    text: test post with data and headers
    type: post
    url: https://example.com/webhook
    data:
      id: 1001
      name: geek
      passion: coding
    headers:
      Content-Type: application/json; charset=utf-8
      User-Agent: My User Agent 1.0
      Authorization: Bearer <your-token>
```

`key-file.json` (downloaded in Step 1; shown here with values removed):

```json
{
  "type": "service_account",
  "project_id": "",
  "private_key_id": "",
  "private_key": "-----BEGIN PRIVATE KEY-----\n \n-----END PRIVATE KEY-----\n",
  "client_email": "my-service-account@***.iam.gserviceaccount.com",
  "client_id": "",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/my-service-account-***.iam.gserviceaccount.com"
}
```

### Step 4) Run Voicy

#### Docker Compose

```yaml
services:

  voicy:
    image: techblog/voicy:latest
    container_name: voicy
    restart: always
    volumes:
      - ./voicy/config:/app/config
```

Start the bot:

```bash
docker compose up -d
```

#### Docker

```bash
docker run -d \
  --name voicy \
  --restart always \
  -v "$(pwd)/voicy/config:/app/config" \
  techblog/voicy:latest
```

The bot only makes outbound connections (Telegram, Google, your MQTT broker and HTTP endpoints),
so no port mapping is needed. The image declares `EXPOSE 8080`, but nothing listens on it.

#### Published images

| Registry | Image | Tags | Platforms |
|----------|-------|------|-----------|
| Docker Hub | `techblog/voicy` | `latest`, `1.1.0`, `1.0.0` (October 2022) | `linux/amd64`, `linux/arm64` |

The repository `VERSION` file says `1.2.0`, but no `1.2.0` image has been published yet. There are
no GitHub releases or git tags.

#### From source

Voicy loads its files from paths relative to the working directory (`config/…`, `recordings/`),
so it must be started from the `app` folder.

Use **Python 3.8–3.11**: the pinned dependencies in `requirements.txt` need Python 3.8 or newer,
and the code uses `configparser.readfp()`, which was removed in Python 3.12. `paho-mqtt` must be
pinned below 2, because paho-mqtt 2.x rejects the client constructor used by Voicy. A virtual
environment avoids the "externally managed environment" error (PEP 668) of a system-wide `pip`.

```bash
# System packages (Debian/Ubuntu); install a Python 3.8-3.11 interpreter as well
sudo apt install ffmpeg

git clone https://github.com/t0mer/voicy.git
cd voicy
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt "paho-mqtt<2"

# Put config.ini, commands.yaml and key-file.json in app/config/
cd app
python voicy.py
```

## Configuration

Voicy has no CLI flags or environment variables; all settings come from `config/config.ini`,
`config/commands.yaml` and `config/key-file.json`. The code sets
`GOOGLE_APPLICATION_CREDENTIALS=config/key-file.json` itself, so the key file path cannot be changed.

### config.ini

| Section | Key | Example / default in sample | Description |
|---------|-----|-----------------------------|-------------|
| `[Telegram]` | `bot.token` | *(empty)* | Telegram bot token from @BotFather. Required. |
| `[Telegram]` | `bot.allowedid` | *(empty)* | Intended as the allowed chat ID. **The current code reads this value but does not enforce it**; see [Security](#security-and-privacy). |
| `[Telegram]` | `bot.welcome.message` | `Hi, my name is Voicy` | Reply to `/start` and `/help`. |
| `[MQTT]` | `mqtt.host` | *(empty)* | MQTT broker host name or IP. |
| `[MQTT]` | `mqtt.port` | *(empty)* | Must be non-empty, but **the code does not use it**: Voicy always connects to port 1883. |
| `[MQTT]` | `mqtt.username` | *(empty)* | MQTT username. |
| `[MQTT]` | `mqtt.password` | *(empty)* | MQTT password. |
| `[GOOGLE]` | `speech.language` | `iw-IL` | Speech-to-Text language code (BCP-47, e.g. `en-US`, `iw-IL`). |
| `[Defaults]` | `default.protocol` | `mqtt` | Action type used for phrases that are not in `commands.yaml`. Only `mqtt` works for the fallback (it publishes the transcript to `voicy/raw`). |
| `[RESULTS]` | `result.ok` | *(empty)* | Text appended to the bot reply when the action succeeds. For `mqtt` actions it is always used, because publish errors are only logged (see [Troubleshooting](#troubleshooting)). |
| `[RESULTS]` | `result.error` | *(empty)* | Text appended to the bot reply when the action fails. |

MQTT is only enabled when **all four** MQTT keys have a value; anonymous brokers are not supported.
The connection uses plain TCP (no TLS), client ID `voicy`, and a keep-alive of 3600 seconds.
Messages are published with QoS 0 and without the retain flag.

### commands.yaml

The file has a single top-level `commands` list. Each entry supports these fields:

| Field | Used by | Required | Description |
|-------|---------|----------|-------------|
| `name` | all | no | Descriptive name (not used for matching). |
| `text` | all | yes | The phrase to match. It must equal the transcript exactly (case-sensitive, same words and punctuation Google returns). |
| `type` | all | yes | `mqtt` or `post`. (`get` is accepted by the parser but not implemented; see [Troubleshooting](#troubleshooting).) |
| `topic` | `mqtt` | yes | MQTT topic to publish to. |
| `payload` | `mqtt` | yes | MQTT payload (sent as a string; quote values like `"on"` so YAML does not turn them into booleans). |
| `url` | `post` | yes | Target URL. |
| `data` | `post` | one of `data`/`headers` | Key/value map sent as the request body. |
| `headers` | `post` | one of `data`/`headers` | HTTP headers. |

The code decides whether a `post` entry has `data` and/or `headers` by searching the whole entry
(as text) for the words `data` and `headers`. Avoid those words in `name`, `text` or `url` unless
the entry really has that field; otherwise the request may fail or be sent without the field.

A `post` entry is successful only when the endpoint returns HTTP **200**. The `data` map is
serialized to its Python string form and sent as a JSON **string** (for example
`"{'id': 1001, 'name': 'geek'}"`), not as a JSON object, so endpoints that expect a JSON object may
reject it.

Example with placeholders:

```yaml
commands:

  - name: Boiler on
    text: turn boiler on
    type: mqtt
    topic: voicy/boiler
    payload: "on"

  - name: Send POST request with data
    text: test post with data
    type: post
    url: https://example.com/webhook
    data:
      id: 1001
      name: geek

  - name: Send POST request with headers
    text: test post with headers
    type: post
    url: https://example.com/webhook
    headers:
      Content-Type: application/json; charset=utf-8
      Authorization: Bearer <your-token>
```

## Usage

1. Open a chat with your bot and send `/start` to get the welcome message.
2. Hold the microphone button and record a command, for example "turn boiler on".
3. Voicy replies with the transcript and `result.ok` / `result.error`, for example:

   ```text
   turn boiler on
   Done
   ```

4. If the transcript does not match any `text` entry, it is published to `voicy/raw`. Copy the
   transcript from the reply into `commands.yaml` to turn it into an exact command.

Changes to `config.ini` and `commands.yaml` are read at startup, so restart the container after
editing them:

```bash
docker restart voicy
```

## Integrations

### Home Assistant (MQTT)

Use Voicy's MQTT commands as automation triggers. Add these as list items to your
`automations.yaml`. With the `Boiler on` command above, this automation turns on a boiler switch
(replace the entity ID with your own):

```yaml
- alias: "Voicy - boiler on"
  triggers:
    - trigger: mqtt
      topic: voicy/boiler
      payload: "on"
  actions:
    - action: switch.turn_on
      target:
        entity_id: switch.boiler
```

Free-form phrases arrive on `voicy/raw` with the transcript as the payload, so you can also react
to them directly:

```yaml
- alias: "Voicy - raw transcript"
  triggers:
    - trigger: mqtt
      topic: voicy/raw
  actions:
    - action: persistent_notification.create
      data:
        message: "Voicy heard: {{ trigger.payload }}"
```

Home Assistant must be connected to the same MQTT broker (MQTT integration).

### Node-RED

Once the bot is running, you can intercept the `voicy/raw` transcript messages in Node-RED. Use
the following flow as a starting point:

<details>
<summary>Node-RED flow (JSON)</summary>

```json
[{"id":"ad99fc9b200eb653","type":"mqtt in","z":"9b2c3983f8ebadfa","name":"","topic":"voicy/raw","qos":"2","datatype":"auto-detect","broker":"407a01e4.6b637","nl":false,"rap":true,"rh":0,"inputs":0,"x":120,"y":140,"wires":[["dd67bd29f2e421a7"]]},{"id":"a10f99f03027e442","type":"inject","z":"9b2c3983f8ebadfa","name":"","props":[{"p":"payload"},{"p":"topic","vt":"str"}],"repeat":"","crontab":"","once":true,"onceDelay":0.1,"topic":"","payload":"","payloadType":"date","x":130,"y":60,"wires":[["dfe92e6a8f57dac1"]]},{"id":"dfe92e6a8f57dac1","type":"function","z":"9b2c3983f8ebadfa","name":"set flow utils","func":"flow.set(\"operatorsMap\", (op) => {\n    switch(op) {\n        case 'on':\n        case 'להדליק':\n            return 'turn_on';\n        case 'off':\n        case 'לכבות':\n            return 'turn_off';\n        case 'toggle':\n        case 'להחליף':\n            return 'toggle';\n        case 'לסגור':\n            return 'close';\n        case 'לפתוח':\n            return 'open';\n        default:\n            return op;\n    }\n});\n\nflow.set(\"locationsMap\", (where) => {\n    switch(where) {\n        case 'סלון':\n        case 'בסלון':\n            return 'salon';\n        case 'מרתף':\n        case 'למטה':\n            return 'basement';\n        case 'כל':\n        case 'כולם':\n            return 'all';\n        case 'מטבח':\n        case 'במטבח':\n            return 'kitchen';\n        default:\n            return 'none';\n    }\n});\n\nflow.set(\"rawDeviceMap\", (device) => {\n    switch (device) {\n        case 'בוילר':\n        case 'דוד':\n            return 'boiler';\n        case 'תריס':\n        case 'תריסים':\n            return 'cover';\n        case 'אור':\n        case 'אורות':\n            return 'light';\n        default:\n            return device;\n    }\n});\n\n","outputs":1,"noerr":0,"initialize":"","finalize":"","libs":[],"x":330,"y":60,"wires":[[]]},{"id":"dd67bd29f2e421a7","type":"function","z":"9b2c3983f8ebadfa","name":"analyse","func":"const rawDeviceMap = flow.get(\"rawDeviceMap\");\nconst operatorsMap = flow.get(\"operatorsMap\");\nconst locationsMap = flow.get(\"locationsMap\");\n\nconst [op, what, ...args] = msg.payload.split(' ');\n\nconst commandObj = {\n    command: operatorsMap(op),\n    device: rawDeviceMap(what),\n}\n\n//handle args\nif (args.length) {\n    // check if 1st arg is location\n    const where = locationsMap(args[0])\n    if (where !== 'none') {\n        // a location\n        commandObj.where = where;\n    } \n}\n\nmsg.payload = commandObj;\nreturn msg;","outputs":1,"noerr":0,"initialize":"","finalize":"","libs":[],"x":320,"y":140,"wires":[["2663f9a6c8a681a3"]]},{"id":"2663f9a6c8a681a3","type":"debug","z":"9b2c3983f8ebadfa","name":"debug 1","active":true,"tosidebar":true,"console":false,"tostatus":false,"complete":"payload","targetType":"msg","statusVal":"","statusType":"auto","x":500,"y":140,"wires":[]},{"id":"407a01e4.6b637","type":"mqtt-broker","broker":"localhost","port":"1883","clientid":"","usetls":false,"compatmode":true,"keepalive":"60","cleansession":true,"birthTopic":"","birthQos":"0","birthPayload":"","willTopic":"","willQos":"0","willPayload":""}]
```

</details>

This flow assumes voice commands of the pattern:

```text
<Operation> <Device> <...Args>
```

Where args can be a location or any other metadata.

First, on load, the flow injects a few functions into the flow context. This is where you define
`operations`, `locations` and `devices`.
Next, it intercepts `voicy/raw` messages and analyses the transcript text.

Note: this is a basic flow to build on, and it is not fully operational. Once it determines, for
example, "Open covers salon", you should translate that into the proper entity and call the
relevant Home Assistant service.

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| Log shows `Command not found, fallback to default` | The transcript did not exactly match any `text` value. Matching is exact and case-sensitive; copy the transcript from the bot reply into `commands.yaml` and restart. |
| Log shows `MQTT details are missing` / `Mqtt broker is not connected` | One of `mqtt.host`, `mqtt.port`, `mqtt.username`, `mqtt.password` is empty. All four are required. |
| Reply says `result.ok` but nothing arrives on the broker | MQTT publish errors are logged, not reported: an `mqtt` action always returns `result.ok`. Check the logs for MQTT connection errors. |
| MQTT connection fails on a broker that is not on port 1883 | `mqtt.port` is ignored; the broker must listen on 1883. |
| `Connection refused – bad username or password` / `not authorised` | Check the MQTT credentials and the broker ACLs. |
| No reply after sending a voice message | Check the container logs. Common causes: Google returned no transcript (silence or wrong `speech.language`), `key-file.json` is missing or invalid, or the Speech-to-Text API / billing is not enabled. |
| No reply to forwarded audio files or music | Only Telegram **voice** messages are supported. |
| A `type: get` command produces no reply | `get` is not implemented in the current code. Use `post` or `mqtt`. |
| A `type: post` command fails although `url` is correct | The code detects `data`/`headers` by searching the whole entry for those words. Avoid the words "data" and "headers" in `name`, `text` or `url` unless the entry has those fields. |
| A `type: post` command always returns the error text | The endpoint did not return HTTP 200, or the entry has neither `data` nor `headers` (at least one is required). |
| Reply shows only the transcript | `result.ok` / `result.error` are empty in `config.ini`. |
| `AttributeError: ... 'readfp'` when running from source | Python 3.12+ removed `configparser.readfp()`; use Python 3.8–3.11. |
| `ValueError: Unsupported callback API version` when running from source | `requirements.txt` does not pin `paho-mqtt`, and paho-mqtt 2.x changed the `Client()` constructor. Install `paho-mqtt<2`. |

View logs with:

```bash
docker logs -f voicy
```

## Security and privacy

- **Chat allowlist:** `bot.allowedid` exists in `config.ini`, but the current code does not check
  it, so anyone who finds your bot's username can send it voice commands. Keep the bot username
  private, and only map phrases to actions you are comfortable exposing.
- **Voice data:** every voice message is sent to Google Cloud Speech-to-Text for transcription.
  Review Google's data-logging settings for your project, and keep in mind that transcripts are
  also written to the logs and echoed back in the chat.
- **MQTT:** Voicy connects without TLS. Run it on a trusted network, use a dedicated MQTT user with
  ACLs limited to the topics Voicy needs, and do not expose the broker to the internet.
- **Secrets:** `config.ini` (bot token, MQTT credentials), `key-file.json` (Google key) and
  `commands.yaml` (for example Home Assistant tokens or webhook URLs) contain secrets. Do not commit
  real values to git or share them in screenshots. Give the Google service account the minimum
  access it needs.

## Development

Project layout:

```text
app/
├── voicy.py            # Entry point: Telegram bot, message handlers
├── voicehandler.py     # Audio conversion (pydub/ffmpeg) + Google Speech-to-Text
├── commandhandler.py   # commands.yaml lookup, MQTT / HTTP POST execution
├── mqtthandler.py      # paho-mqtt client
└── config/             # Sample config.ini and commands.yaml
Dockerfile              # ubuntu:18.04 + python3, ffmpeg, portaudio
requirements.txt
VERSION                 # Image version used by the Docker Hub and JCR workflows
screenshots/            # BotFather walkthrough images
```

Build the image locally:

```bash
docker build -t voicy .
```

<!-- TODO: verify that the image still builds: ubuntu:18.04 ships Python 3.6, while requirements.txt pins urllib3>=2.2.2, protobuf>=4.25.8 and pyasn1>=0.6.2, which need Python 3.8+ -->

There are no automated tests.

### GitHub Actions workflows

| Workflow | File | Trigger | Publishes | Platforms |
|----------|------|---------|-----------|-----------|
| Docker Build | `.github/workflows/docker-image.yml` | Manual, or after a workflow named "Create Release" completes | `techblog/voicy:latest` and `techblog/voicy:<VERSION>` on Docker Hub | `linux/amd64`, `linux/arm64` |
| JCR Docker Build | `.github/workflows/jcr-image.yml` | Manual | `<private JFrog registry>/docker/voicy:latest` and `:<VERSION>` | `linux/amd64`, `linux/arm64` |
| Publish to GHCR | `.github/workflows/publish-ghcr.yml` | Manual (optional `tag` input, default `latest`) | `ghcr.io/t0mer/voicy:<tag>` and `:latest` | `linux/amd64`, `linux/arm64`, `linux/arm/v7` |

The GHCR image has not been published yet. The JFrog registry is private.

## Contributing

Issues and pull requests are welcome. Please keep secrets out of commits (see
[Security and privacy](#security-and-privacy)) and describe how you tested your change.

## License

This project is licensed under the [Apache License 2.0](LICENSE.md).
