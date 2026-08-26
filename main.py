import urllib.request
import xml.etree.ElementTree as ET

RSS_URL = "https://news.google.com/rss/search?q=AI&hl=ja&gl=JP&ceid=JP:ja"

response = urllib.request.urlopen(RSS_URL)
data = response.read()

root = ET.fromstring(data)

print("=== AI監視エージェント ===")
print("新着情報")
print()

for item in root.findall(".//item")[:10]:
    title = item.findtext("title")
    link = item.findtext("link")

    print("タイトル:", title)
    print("URL:", link)
    print()
