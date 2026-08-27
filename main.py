import urllib.request
import xml.etree.ElementTree as ET
import json
import os

from google import genai

RSS_URL = "https://news.google.com/rss/search?q=AI&hl=ja&gl=JP&ceid=JP:ja"
DATA_FILE = "seen.json"

# Gemini APIを設定
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEYが設定されていません。")
    exit(1)

client = genai.Client(api_key=api_key)


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


print("=== AI監視エージェント ===")
print()

if not new_articles:
    print("新しいニュースはありません。")
    exit()


print(f"🆕 新着ニュース：{len(new_articles)}件")
print()


# 新着ニュースをGeminiに渡す
for article in new_articles:

    prompt = f"""
あなたはニュース監視AIです。

以下のニュースを分析してください。

タイトル：
{article["title"]}

次の形式で回答してください。

重要度：1〜5
要約：50文字程度
重要な理由：50文字程度

特に「AI技術」「AIビジネス」「AIエージェント」
「生成AI」に関係するニュースを重要と判断してください。
"""

    try:
        result = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        print("━━━━━━━━━━━━━━━━━━")
        print("タイトル:", article["title"])
        print("URL:", article["link"])
        print()
        print(result.text)
        print("━━━━━━━━━━━━━━━━━━")
        print()

    except Exception as e:
        print("Geminiによる分析に失敗しました。")
        print("エラー:", e)
