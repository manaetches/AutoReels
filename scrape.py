
# Scrape Mixkit video links from page 29 to 100 for the 'woman' category
import requests
from bs4 import BeautifulSoup

base_url = "https://mixkit.co/free-stock-video/girl/?page={}"
endpoint = []  # Store links as they are acquired

for page in range(1, 30):
    url = base_url.format(page)
    print(f"Scraping {url} ...")
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Failed to load page {page}")
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        anchors = soup.find_all("a", class_="item-grid-video-player__overlay-link")
        for a in anchors:
            link = a.get("href")
            if link and link.startswith("/free-stock-video/"):
                full_link = "https://mixkit.co" + link
                endpoint.append(full_link)
                print(full_link)
    except Exception as e:
        print(f"Exception while parsing page {page}: {e}")

print(f"\nTotal video links found: {len(endpoint)}")

# Save endpoint list to file
with open("video_links.txt", "w", encoding="utf-8") as f:
    for link in endpoint:
        f.write(link + "\n")
print(f"Saved all links to video_links.txt")