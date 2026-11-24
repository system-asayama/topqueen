import os
import secrets
import time

from flask import Flask, Response, abort, render_template
from sqlalchemy.exc import OperationalError

from admin import admin_bp
from models import Cast, Event, Image, PriceItem, Setting, db, get_shop, seed_initial_data

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL", "sqlite:///topqueen.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 画像アップロード上限 10MB
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db.init_app(app)
app.register_blueprint(admin_bp)


def init_db():
    """DB の起動を待ってテーブル作成・初期データ投入・秘密鍵の用意をする。"""
    for attempt in range(30):
        try:
            with app.app_context():
                db.create_all()
                seed_initial_data()
                key = os.environ.get("SECRET_KEY")
                if not key:
                    row = db.session.get(Setting, "_secret_key")
                    if row is None:
                        row = Setting(key="_secret_key", value=secrets.token_hex(32))
                        db.session.add(row)
                        db.session.commit()
                    key = row.value
                app.secret_key = key
            return
        except OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)


init_db()


@app.route("/")
def index():
    return render_template(
        "index.html",
        shop=get_shop(),
        system=PriceItem.query.filter_by(kind="set").order_by(PriceItem.sort_order, PriceItem.id).all(),
        options=PriceItem.query.filter_by(kind="option").order_by(PriceItem.sort_order, PriceItem.id).all(),
        cast=Cast.query.filter_by(visible=True).order_by(Cast.sort_order, Cast.id).all(),
        events=Event.query.filter_by(visible=True).order_by(Event.sort_order, Event.id).all(),
    )


@app.route("/media/<int:image_id>")
def media(image_id):
    img = db.session.get(Image, image_id)
    if img is None:
        abort(404)
    resp = Response(img.data, mimetype=img.mimetype)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(debug=True, port=8000)
