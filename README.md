# Google Nest Camera Video - Sync To Storage

Store your Nest event history to local storage and keep more than 60 days of footage. This module is for personal use only, especially as it uses unpublished APIs. Use it at your own risk!

## Features

- Syncs **Google Nest camera events** to local storage
- Downloads **full-quality MP4 clips**
- Organizes videos by `device_name/YYYY/MM/DD/*.mp4`
- **Telegram notifications** on auth failure (optional)
- **Automatic cleanup** of old videos based on age/size (optional)
- Runs in **Docker** with minimal config

## Requirements

- Python 3.10+ (or use the provided Docker image)
- Docker & Docker Compose (recommended)

## How It Works
1. Gets your **Google Home devices using HomeGraph**
2. Retrieves your recent **Google Nest events**
3. **Downloads full-quality Google Nest video clips**
4. Stores those clips to a local storage directory by `device_name` and into subdirectories with the format `YYYY/MM/DD/*.mp4`

## Setup

### 1. Obtain a Google Master Token

A master token (`aas_et/...`) is required to authenticate against the Google/Nest APIs. It is long-lived and is generated from your Google account credentials.

The methods below (gpsoauth-java, glocaltokens, Docker containers) are worth trying first, but they often fail when 2FA is enabled. The following alternative flow — adapted from julianpitt/gpsoauth-gist — works with 2FA enabled.

#### Token types
- **OAuth token** — `oauth2_4/...`, very short lived. Needs an OAuth sign-in for an app.
- **Master token** — `aas_et/...`, long lived. Needs Google username and password.
- **Access token** — `ya29...`, lasts ~1 hour. Generated from the master token.

#### Steps

1. Create a new project directory and initialize a Python project. Using `uv`:
   ```bash
   uv init && uv venv && source .venv/bin/activate
   ```

2. Add the `gpsoauth` dependency:
   ```bash
   uv add gpsoauth
   ```

3. Save the following script as `get_master_token.py` and replace `{Your gmail address}` with your Google account email:
   ```python
   import json
   import gpsoauth

   email = '{Your gmail address}'  # your Google username
   android_id = '0123456789abcdef'  # leave as-is
   token = 'oauth2_4/XXXXXXXXXX'  # paste oauth_token here

   master_response = gpsoauth.exchange_token(email, token, android_id)

   print("Full response for debugging:")
   print(json.dumps(master_response))

   master_token = master_response['Token']
   print(f"\nMaster token {master_token}")
   ```

4. Open [https://accounts.google.com/EmbeddedSetup](https://accounts.google.com/EmbeddedSetup) in your browser.

5. Sign in to your Google account and complete any 2FA prompts.

6. Click **I agree** when prompted. The page may appear to hang on a loading screen — that's fine, proceed to the next step.

7. Copy the value of the `oauth_token` cookie from `accounts.google.com`. Two ways in Chrome (other browsers are similar):

   **Method 1 — Site settings (lock icon):**
   - Click the lock icon in the address bar.
   - Open the **Cookies** section.
   - Expand the `accounts.google.com` dropdown.
   - Locate `oauth_token` and copy the value from the **Content** field.

   **Method 2 — DevTools:**
   - Open Developer Tools (`F12` or `Cmd/Ctrl + Shift + I`).
   - Go to the **Application** tab.
   - Under **Storage → Cookies**, click `https://accounts.google.com`.
   - Find the `oauth_token` row and copy its **Cookie Value**.

8. Paste the `oauth_token` value into the `token` variable in `get_master_token.py`.

9. Run the script:
   ```bash
   uv run get_master_token.py
   ```

   The printed `aas_et/...` string is your master token. Set it as `google_master_token` in your `nest.ini`.

#### Troubleshooting
- Make sure you've replaced both the email and the token in the script.
- The `oauth_token` is **single-use** and expires quickly — use it within a few minutes of obtaining it.
- After extended use, Google may flag "suspicious activity" on the account generating the token. This is a known limitation of the approach.

### 2. Create the Configuration File

Create a folder on your system for the config (e.g., `/path/to/config`), then create a `nest.ini` file inside it:

```ini
[nest]
# Your local timezone for video filenames
timezone = America/Los_Angeles

# How often to fetch new video data (in minutes)
refresh_interval = 60

# How many minutes of video history to fetch each sync (default: 240 = 4 hours)
fetch_range = 240

# Your Google account email
google_username = youremail@gmail.com

# The master token from step 1
google_master_token = YOUR_MASTER_TOKEN_HERE

# Cleanup: delete videos older than N days (optional)
cleanup_enabled = false
max_age_days = 60
# Max total size in MB before removing oldest videos (default: 100000 = 100GB)
max_size_mb = 100000

# Telegram notifications on auth failure (optional)
# Leave empty to disable
telegram_token =
telegram_chat_id =
# Minimum interval between messages (minutes)
telegram_message_interval = 60
```

A sample config is provided in `config/sample_config_nest.ini`.

### 3. Run with Docker

**Using Docker Compose (recommended):**

Create a `docker-compose.yaml`:

```yaml
version: '3'
services:
  google-nest-cam:
    image: derycklong/google-nest-cam:latest
    container_name: google-nest-cam
    restart: unless-stopped
    volumes:
      - /path/to/config:/config
      - /path/to/videos:/videos
```

Then start the container:
```bash
docker-compose up -d
```

**Using Docker CLI:**
```bash
docker run -d \
  --name google-nest-cam \
  --restart unless-stopped \
  -v /path/to/config:/config \
  -v /path/to/videos:/videos \
  derycklong/google-nest-cam:latest
```

## Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `timezone` | Yes | - | Your local timezone (e.g., `America/Los_Angeles`) |
| `refresh_interval` | Yes | - | How often to sync new videos, in minutes |
| `fetch_range` | No | `240` | Minutes of video history to fetch per sync |
| `google_username` | Yes | - | Google account email with Nest cameras |
| `google_master_token` | Yes | - | Master token from step 1 |
| `cleanup_enabled` | No | `false` | Enable automatic video cleanup |
| `max_age_days` | No | `60` | Max age of videos before cleanup (days) |
| `max_size_mb` | No | `100000` | Max total storage before cleanup (MB) |
| `telegram_token` | No | `` | Telegram bot token for auth failure alerts |
| `telegram_chat_id` | No | `` | Telegram chat ID for alerts |
| `telegram_message_interval` | No | `60` | Min interval between Telegram messages (min) |

## Credits

Most of the work is credited to the original author [TamirMa](https://github.com/TamirMa/google-nest-telegram-sync), I just modified it to sync to local NAS storage instead, and putting it into a Docker container to make it easier to deploy.

You can find his original research [here](https://medium.com/@tamirmayer/google-nest-camera-internal-api-fdf9dc3ce167)

Much credits for the authors of the [**glocaltokens**](https://github.com/leikoilja/glocaltokens) module

Thanks also for the authors of the docker [**ha-google-home_get-token**](https://hub.docker.com/r/breph/ha-google-home_get-token)
