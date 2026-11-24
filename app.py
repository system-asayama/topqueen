from flask import Flask, render_template

app = Flask(__name__)

# ------------------------------------------------------------
# 店舗情報（※サンプル値です。実際の情報に書き換えてください）
# ------------------------------------------------------------
SHOP = {
    "name": "TOP QUEEN",
    "kana": "トップクイーン",
    "genre": "フィリピンパブ",
    "tel": "000-0000-0000",
    "tel_link": "00000000000",
    "address": "〒000-0000 ○○県○○市○○町1-2-3 ○○ビル 2F",
    "station": "○○駅 徒歩3分",
    "hours": "20:00 〜 LAST",
    "holiday": "年中無休",
    "line_url": "#",
    "instagram_url": "#",
    "x_url": "#",
    "map_query": "Tokyo Station",  # Googleマップの検索ワード（住所に変更）
}

# 料金システム（※サンプル値）
SYSTEM = [
    {"title": "SET 60分", "price": "¥4,000", "note": "飲み放題（焼酎・ウイスキー・ビール・ソフトドリンク）"},
    {"title": "延長 30分", "price": "¥2,000", "note": "自動延長はございません"},
    {"title": "指名料", "price": "¥1,000", "note": "場内指名 ¥1,000"},
    {"title": "レディースドリンク", "price": "¥1,000〜", "note": ""},
]
SYSTEM_OPTIONS = [
    ("VIPルーム", "¥5,000〜"),
    ("カラオケ", "無料"),
    ("ボトルキープ", "¥8,000〜"),
    ("シャンパン", "¥15,000〜"),
]

# キャスト（※サンプル。画像は static/img/cast/ に置いて image を指定）
CAST = [
    {"name": "ANNA", "age": 22, "from_": "Manila", "comment": "歌うのが大好き！一緒にカラオケしよう♪", "image": None, "new": True},
    {"name": "MARIA", "age": 24, "from_": "Cebu", "comment": "笑顔で元気にお迎えします！", "image": None, "new": False},
    {"name": "JASMINE", "age": 21, "from_": "Davao", "comment": "日本語勉強中です。たくさん話してね", "image": None, "new": True},
    {"name": "CHERRY", "age": 25, "from_": "Pampanga", "comment": "ダンスが得意！ショータイムも見てね", "image": None, "new": False},
    {"name": "BELLA", "age": 23, "from_": "Manila", "comment": "楽しい時間を一緒に過ごしましょう", "image": None, "new": False},
    {"name": "NICOLE", "age": 22, "from_": "Iloilo", "comment": "初めての方も大歓迎です♡", "image": None, "new": False},
    {"name": "RICA", "age": 26, "from_": "Baguio", "comment": "お酒好きな方、乾杯しましょう！", "image": None, "new": False},
    {"name": "LOVELY", "age": 20, "from_": "Laguna", "comment": "名前の通りラブリーに接客します", "image": None, "new": True},
]

# イベント・ニュース（※サンプル）
EVENTS = [
    {"date": "2026.12.24", "title": "クリスマスパーティー", "body": "サンタコスでお出迎え。ご来店の方にプレゼントあり！"},
    {"date": "2026.12.31", "title": "カウントダウンイベント", "body": "年越しをTOP QUEENで。シャンパンタワーも開催！"},
    {"date": "毎週金曜", "title": "ショータイム", "body": "23:00〜 キャストによるダンスショーを開催中。"},
]


@app.route("/")
def index():
    return render_template(
        "index.html",
        shop=SHOP,
        system=SYSTEM,
        options=SYSTEM_OPTIONS,
        cast=CAST,
        events=EVENTS,
    )


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=8000)
