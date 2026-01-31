
import os
import json
import random
import time
import requests
import datetime
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# =======================
# CONFIG
# =======================

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
UNSPLASH_KEY = os.environ.get("UNSPLASH_KEY")
BLOG_ID = os.environ.get("BLOG_ID")

SCOPES = ["https://www.googleapis.com/auth/blogger"]

POSTED_FILE = "posted_urls.json"

# Allowed posting time (IST)
START_HOUR = 9     # 9 AM
END_HOUR = 20      # 8 PM

# Random delay (minutes)
MIN_DELAY = 5
MAX_DELAY = 20

# =======================
# TIME CHECK (IST)
# =======================

def is_day_time():
    now = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
    return START_HOUR <= now.hour < END_HOUR

# =======================
# LOAD / SAVE POSTED URLS
# =======================

def load_posted():
    if not os.path.exists(POSTED_FILE):
        return []
    with open(POSTED_FILE, "r") as f:
        return json.load(f)

def save_posted(data):
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f, indent=2)

# =======================
# FETCH NEWS
# =======================

def fetch_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "in",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json().get("articles", [])

# =======================
# FETCH IMAGE (UNSPLASH)
# =======================

def fetch_image(query):
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
    params = {"query": query, "per_page": 5}

    r = requests.get(url, headers=headers, params=params, timeout=10)
    data = r.json()

    if data.get("results"):
        return data["results"][0]["urls"]["regular"]
    return None

# =======================
# CONTENT GENERATION (SAFE)
# =======================

def generate_content(article):
    title = article["title"]

    description = article.get("description") or ""
    source = article["source"]["name"]

    content = f"""
<h2>{title}</h2>

<p><b>Source:</b> {source}</p>

<p>{description}</p>

<h3>Key Highlights</h3>
<ul>
  <li>This news is currently gaining attention across media.</li>
  <li>It may have a significant impact in the coming days.</li>
  <li>Experts are closely watching further developments.</li>
</ul>

<h3>Why This Matters</h3>
<p>
This update is important because it reflects ongoing trends and decisions
that can influence the public, businesses, or technology sector.
Staying informed helps readers understand the broader impact.
</p>

<h3>Final Thoughts</h3>
<p>
As more details emerge, the situation is expected to evolve.
Readers are encouraged to follow verified sources for updates.
</p>
"""
    return title, content

# =======================
# BLOGGER AUTH
# =======================

def get_blogger_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("blogger", "v3", credentials=creds)

# =======================
# POST TO BLOGGER
# =======================

def post_to_blogger(service, title, content, image_url):
    if image_url:
        content = f'<img src="{image_url}" /><br/>' + content

    post = {
        "kind": "blogger#post",
        "title": title,
        "content": content
    }

    service.posts().insert(
        blogId=BLOG_ID,
        body=post,
        isDraft=False
    ).execute()

# =======================
# MAIN LOGIC
# =======================

def main():
    if not is_day_time():
        print("🌙 Night time (IST). Skipping post.")
        return

    delay = random.randint(MIN_DELAY, MAX_DELAY)
    print(f"⏳ Waiting {delay} minutes for random timing...")
    time.sleep(delay * 60)

    posted_urls = load_posted()
    articles = fetch_news()

    for article in articles:
        url = article.get("url")
        if not url or url in posted_urls:
            continue

        title, content = generate_content(article)
        image = fetch_image(title)

        service = get_blogger_service()
        post_to_blogger(service, title, content, image)

        posted_urls.append(url)
        save_posted(posted_urls)

        print("✅ Posted:", title)
        break

if __name__ == "__main__":
    main()
