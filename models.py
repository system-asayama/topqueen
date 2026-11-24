from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Setting(db.Model):
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=False, default="")


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Cast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    age = db.Column(db.Integer)
    origin = db.Column(db.String(64), default="")
    comment = db.Column(db.Text, default="")
    is_new = db.Column(db.Boolean, default=False)
    visible = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    image_id = db.Column(db.Integer, db.ForeignKey("image.id", ondelete="SET NULL"))
    image = db.relationship("Image")


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_label = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    body = db.Column(db.Text, default="")
    visible = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)


class Recruit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    salary = db.Column(db.String(255), default="")
    hours = db.Column(db.String(255), default="")
    benefits = db.Column(db.String(255), default="")
    detail = db.Column(db.Text, default="")
    visible = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)


class PriceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(16), nullable=False, default="set")  # set / option
    title = db.Column(db.String(64), nullable=False)
    price = db.Column(db.String(64), nullable=False)
    note = db.Column(db.String(255), default="")
    sort_order = db.Column(db.Integer, default=0)


# ------------------------------------------------------------
# 店舗情報の項目（管理画面の「店舗情報」で編集）
# ------------------------------------------------------------
SHOP_FIELDS = [
    ("name", "店名", "TOP QUEEN"),
    ("kana", "店名（カナ）", "トップクイーン"),
    ("genre", "ジャンル", "フィリピンパブ"),
    ("tel", "電話番号", "000-0000-0000"),
    ("address", "住所", "〒000-0000 ○○県○○市○○町1-2-3 ○○ビル 2F"),
    ("station", "最寄駅", "○○駅 徒歩3分"),
    ("hours", "営業時間", "20:00 〜 LAST"),
    ("holiday", "定休日", "年中無休"),
    ("map_query", "地図の検索ワード（住所など）", "Tokyo Station"),
    ("service_note", "料金の注意書き", "※ 表示価格は税込です。別途サービス料 20% を頂戴いたします。\n※ 各種クレジットカードご利用いただけます。"),
    ("line_url", "LINE のURL", "#"),
    ("instagram_url", "Instagram のURL", "#"),
    ("x_url", "X のURL", "#"),
]


# お店について（CONCEPT）
CONCEPT_FIELDS = [
    ("concept_lead", "見出し", "陽気で明るいフィリピーナが\n心を込めておもてなし。", "textarea"),
    ("concept_body", "本文", "TOP QUEENは、本場フィリピン出身の明るく可愛いキャストが在籍するフィリピンパブです。"
     "カラオケ・ダンスショー・季節のイベントなど、日常を忘れて楽しめる時間をご用意しています。"
     "初めての方、お一人様、会社帰りのグループ様も大歓迎。安心の明朗会計でお待ちしております。", "textarea"),
    ("feature1_title", "特徴1 タイトル", "明朗会計", "input"),
    ("feature1_body", "特徴1 説明", "セット料金で飲み放題。追加料金も事前にご案内します。", "input"),
    ("feature2_title", "特徴2 タイトル", "カラオケ無料", "input"),
    ("feature2_body", "特徴2 説明", "最新機種完備。キャストとデュエットも！", "input"),
    ("feature3_title", "特徴3 タイトル", "ショータイム", "input"),
    ("feature3_body", "特徴3 説明", "週末はキャストによるダンスショーを開催。", "input"),
    ("feature4_title", "特徴4 タイトル", "VIPルーム", "input"),
    ("feature4_body", "特徴4 説明", "接待や記念日にも使える特別なお席をご用意。", "input"),
]

# 求人ページ下の注意書き
RECRUIT_FIELDS = [
    ("recruit_note", "求人の注意書き",
     "※ 就労可能な在留資格をお持ちの方に限ります。お気軽にお電話・LINEでお問い合わせください。", "textarea"),
]

ALL_SETTING_DEFAULTS = (
    [(k, d) for k, _l, d in SHOP_FIELDS]
    + [(k, d) for k, _l, d, _t in CONCEPT_FIELDS]
    + [(k, d) for k, _l, d, _t in RECRUIT_FIELDS]
)


def seed_initial_data():
    """初回起動時にサンプルデータを入れる（既にデータがあれば何もしない）。"""
    for key, default in ALL_SETTING_DEFAULTS:
        if db.session.get(Setting, key) is None:
            db.session.add(Setting(key=key, value=default))

    if PriceItem.query.count() == 0:
        items = [
            ("set", "SET 60分", "¥4,000", "飲み放題（焼酎・ウイスキー・ビール・ソフトドリンク）"),
            ("set", "延長 30分", "¥2,000", "自動延長はございません"),
            ("set", "指名料", "¥1,000", "場内指名 ¥1,000"),
            ("set", "レディースドリンク", "¥1,000〜", ""),
            ("option", "VIPルーム", "¥5,000〜", ""),
            ("option", "カラオケ", "無料", ""),
            ("option", "ボトルキープ", "¥8,000〜", ""),
            ("option", "シャンパン", "¥15,000〜", ""),
        ]
        for i, (kind, title, price, note) in enumerate(items):
            db.session.add(PriceItem(kind=kind, title=title, price=price, note=note, sort_order=i))

    if Cast.query.count() == 0:
        casts = [
            ("ANNA", 22, "Manila", "歌うのが大好き！一緒にカラオケしよう♪", True),
            ("MARIA", 24, "Cebu", "笑顔で元気にお迎えします！", False),
            ("JASMINE", 21, "Davao", "日本語勉強中です。たくさん話してね", True),
            ("CHERRY", 25, "Pampanga", "ダンスが得意！ショータイムも見てね", False),
            ("BELLA", 23, "Manila", "楽しい時間を一緒に過ごしましょう", False),
            ("NICOLE", 22, "Iloilo", "初めての方も大歓迎です♡", False),
            ("RICA", 26, "Baguio", "お酒好きな方、乾杯しましょう！", False),
            ("LOVELY", 20, "Laguna", "名前の通りラブリーに接客します", True),
        ]
        for i, (name, age, origin, comment, is_new) in enumerate(casts):
            db.session.add(Cast(name=name, age=age, origin=origin, comment=comment, is_new=is_new, sort_order=i))

    if Event.query.count() == 0:
        events = [
            ("2026.12.24", "クリスマスパーティー", "サンタコスでお出迎え。ご来店の方にプレゼントあり！"),
            ("2026.12.31", "カウントダウンイベント", "年越しをTOP QUEENで。シャンパンタワーも開催！"),
            ("毎週金曜", "ショータイム", "23:00〜 キャストによるダンスショーを開催中。"),
        ]
        for i, (d, t, b) in enumerate(events):
            db.session.add(Event(date_label=d, title=t, body=b, sort_order=i))

    if Recruit.query.count() == 0:
        db.session.add(Recruit(title="ホールスタッフ・ボーイ", salary="時給 1,300円〜（経験・能力により優遇）",
                               hours="19:30〜LAST（週2日〜OK）", benefits="交通費支給・まかない有・昇給随時", sort_order=0))
        db.session.add(Recruit(title="フロア・キャスト", salary="時給 2,500円〜 ＋ 各種バック",
                               hours="20:00〜LAST（シフト自由）", benefits="日払いOK・送り有・寮完備（要相談）", sort_order=1))

    db.session.commit()


def get_shop():
    shop = dict(ALL_SETTING_DEFAULTS)
    for s in Setting.query.all():
        if not s.key.startswith("_"):
            shop[s.key] = s.value
    shop["features"] = [
        {"title": shop.get(f"feature{i}_title", ""), "body": shop.get(f"feature{i}_body", "")}
        for i in range(1, 5) if shop.get(f"feature{i}_title", "").strip()
    ]
    shop["tel_link"] = "".join(ch for ch in shop.get("tel", "") if ch.isdigit() or ch == "+")
    return shop
