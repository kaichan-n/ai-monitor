import urllib.request
import xml.etree.ElementTree as ET
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google import genai


RSS_URL = "https://news.google.com/rss/search?q=AI&hl=ja&gl=JP&ceid=JP:ja"
DATA_FILE = "seen.json"


# =========================
# 環境変数
# =========================

gemini_api_key = os.environ.get("GEMINI_API_KEY")
gmail_address = os.environ.get("GMAIL_ADDRESS")
gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")

if not gemini_api_key:
    print("GEMINI_API_KEYが設定されていません。")
    exit(1)

if not gmail_address:
    print("GMAIL_ADDRESSが設定されていません。")
    exit(1)

if not gmail_app_password:
    print("GMAIL_APP_PASSWORDが設定されていません。")
    exit(1)


# =========================
# Gemini
# =========================

client = genai.Client(api_key=gemini_api_key)


# =========================
# RSSからニュース取得
# =========================

response = urllib.request.urlopen(RSS_URL)
data = response.read()

root = ET.fromstring(data)


# =========================
# 前回の記憶を読み込み
# =========================

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        seen = set(json.load(f))
else:
    seen = set()


new_articles = []


for item in root.findall(".//item")[:20]:

    title = item.findtext("title")
    link = item.findtext("link")

    if link not in seen:

        new_articles.append({
            "title": title,
            "link": link
        })

        seen.add(link)


# =========================
# 記憶を保存
# =========================

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(list(seen), f, ensure_ascii=False, indent=2)


print("=== AI監視エージェント ===")
print()

if not new_articles:
    print("新しいニュースはありません。")
    exit()


print(f"🆕 新着ニュース：{len(new_articles)}件")
print()


# =========================
# Geminiで分析
# =========================

important_news = []


for article in new_articles:

    prompt = f"""
あなたはニュース監視AIです。

以下のニュースを分析してください。

タイトル：
{article["title"]}

次の形式で必ず回答してください。

重要度：1〜5
要約：50文字程度
重要な理由：50文字程度

特に以下に関係するニュースを重要と判断してください。

・AI技術
・生成AI
・AIエージェント
・AIビジネス
・AI企業
・AIによる社会変化

重要度5または4の場合は、非常に重要なニュースとして扱います。
"""

    try:

        result = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        text = result.text

        print("━━━━━━━━━━━━━━━━━━")
        print("タイトル:", article["title"])
        print("URL:", article["link"])
        print()
        print(text)
        print("━━━━━━━━━━━━━━━━━━")
        print()

        # 重要度4・5だけメール候補にする
        if "重要度：5" in text or "重要度: 5" in text:
            important_news.append({
                "title": article["title"],
                "link": article["link"],
                "analysis": text
            })

        elif "重要度：4" in text or "重要度: 4" in text:
            important_news.append({
                "title": article["title"],
                "link": article["link"],
                "analysis": text
            })

    except Exception as e:

        print("Geminiによる分析に失敗しました。")
        print("エラー:", e)


# =========================
# Gmail通知
# =========================

if not important_news:

    print("重要度4以上のニュースはありません。")

else:

    email_body = "🤖 AI監視エージェント\n\n"
    email_body += f"重要ニュース：{len(important_news)}件\n\n"

    for news in important_news:

        email_body += "━━━━━━━━━━━━━━━━━━\n"
        email_body += f"タイトル：{news['title']}\n\n"
        email_body += f"{news['analysis']}\n\n"
        email_body += f"URL：{news['link']}\n"
        email_body += "━━━━━━━━━━━━━━━━━━\n\n"


    message = MIMEMultipart()

    message["From"] = gmail_address
    message["To"] = gmail_address
    message["Subject"] = f"🤖 AI重要ニュース {len(important_news)}件"

    message.attach(
        MIMEText(email_body, "plain", "utf-8")
    )


    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                gmail_address,
                gmail_app_password
            )

            server.send_message(message)

        print("📧 Gmail通知を送信しました！")

    except Exception as e:

        print("Gmail送信に失敗しました。")
        print("エラー:", e)
