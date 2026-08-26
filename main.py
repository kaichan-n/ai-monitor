import urllib.request
import xml.etree.ElementTree as ET
import json
import os

RSS_URL = "https://news.google.com/rss/search?q=AI&hl=ja&gl=JP&ceid=JP:ja"
DATA_FILE = "seen.json"

# RSSからニュースを取得
response = urllib.request.urlopen(RSS_URL)
data = response.read()

root = ET.fromstring(data)

# 前回までに見たニュースを読み込む
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        seen = set(json.load(f))
else:
    seen = set()

new_articles = []

# 最新20件を確認
for item in root.findall(".//item")[:20]:
    title = item.findtext("title")
    link = item.findtext("link")

    # ニュースを識別するためにURLを使用
    article_id = link

    if article_id not in seen:
        new_articles.append({
            "title": title,
            "link": link
        })

        seen.add(article_id)

# 記憶を保存
with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(list(seen), f, ensure_ascii=False, indent=2)

# 結果を表示
print("=== AI監視エージェント ===")
print()

if new_articles:
    print(f"🆕 新着ニュース：{len(new_articles)}件")
    print()

    for article in new_articles:
        print("タイトル:", article["title"])
        print("URL:", article["link"])
        print()
else:
    print("新しいニュースはありません。")
