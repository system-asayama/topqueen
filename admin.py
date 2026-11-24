import hmac
import secrets
from functools import wraps

from flask import (Blueprint, abort, flash, g, redirect, render_template, request,
                   session, url_for)

from models import (CONCEPT_FIELDS, RECRUIT_FIELDS, SHOP_FIELDS, Admin, Cast, Event, Image, PriceItem,
                    Recruit, Setting, db)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ------------------------------------------------------------
# 共通: CSRF / ログイン
# ------------------------------------------------------------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


@admin_bp.app_context_processor
def inject_csrf():
    return {"csrf_token": csrf_token}


@admin_bp.before_request
def check_csrf_and_load_user():
    if request.method == "POST":
        sent = request.form.get("_csrf", "")
        if not sent or not hmac.compare_digest(sent, session.get("_csrf", "")):
            abort(400, "フォームの有効期限が切れました。ページを再読み込みしてください。")
    g.admin = None
    if session.get("admin_id"):
        g.admin = db.session.get(Admin, session["admin_id"])
        if g.admin is None:
            session.pop("admin_id", None)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.admin is None:
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_next(target):
    if target and target.startswith("/admin") and not target.startswith("//"):
        return target
    return url_for("admin.dashboard")


IMAGE_SIGNATURES = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
]


def _read_image(file_storage):
    """アップロードされた画像を検証して Image を返す。無ければ None。"""
    if not file_storage or not file_storage.filename:
        return None
    data = file_storage.read()
    mimetype = None
    for sig, mt in IMAGE_SIGNATURES:
        if data.startswith(sig):
            mimetype = mt
            break
    if mimetype is None and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        mimetype = "image/webp"
    if mimetype is None:
        raise ValueError("画像は JPEG / PNG / GIF / WebP のみアップロードできます。")
    return Image(data=data, mimetype=mimetype)


# ------------------------------------------------------------
# ログイン・初期設定
# ------------------------------------------------------------
@admin_bp.route("/setup", methods=["GET", "POST"])
def setup():
    if Admin.query.count() > 0:
        return redirect(url_for("admin.login"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        pw = request.form.get("password", "")
        pw2 = request.form.get("password2", "")
        if not username:
            error = "ユーザー名を入力してください。"
        elif len(pw) < 8:
            error = "パスワードは8文字以上にしてください。"
        elif pw != pw2:
            error = "確認用パスワードが一致しません。"
        else:
            admin = Admin(username=username)
            admin.set_password(pw)
            db.session.add(admin)
            db.session.commit()
            session.clear()
            session["admin_id"] = admin.id
            flash("管理者アカウントを作成しました。")
            return redirect(url_for("admin.dashboard"))
    return render_template("admin/setup.html", error=error)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if Admin.query.count() == 0:
        return redirect(url_for("admin.setup"))
    if g.admin:
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        admin = Admin.query.filter_by(username=request.form.get("username", "").strip()).first()
        if admin and admin.check_password(request.form.get("password", "")):
            session.clear()
            session["admin_id"] = admin.id
            session.permanent = True
            return redirect(_safe_next(request.args.get("next")))
        error = "ユーザー名またはパスワードが違います。"
    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        cast_count=Cast.query.count(),
        cast_visible=Cast.query.filter_by(visible=True).count(),
        event_count=Event.query.count(),
        price_count=PriceItem.query.count(),
        recruit_count=Recruit.query.filter_by(visible=True).count(),
    )


def _save_settings(keys):
    for key in keys:
        row = db.session.get(Setting, key) or Setting(key=key)
        row.value = request.form.get(key, "").strip()
        db.session.add(row)
    db.session.commit()


def _setting_values():
    return {s.key: s.value for s in Setting.query.all()}


# ------------------------------------------------------------
# 店舗情報
# ------------------------------------------------------------
@admin_bp.route("/shop", methods=["GET", "POST"])
@login_required
def shop():
    if request.method == "POST":
        _save_settings([k for k, _l, _d in SHOP_FIELDS])
        flash("店舗情報を保存しました。")
        return redirect(url_for("admin.shop"))
    return render_template("admin/shop.html", fields=SHOP_FIELDS, values=_setting_values())


# ------------------------------------------------------------
# お店について（CONCEPT）
# ------------------------------------------------------------
@admin_bp.route("/concept", methods=["GET", "POST"])
@login_required
def concept():
    if request.method == "POST":
        _save_settings([k for k, _l, _d, _t in CONCEPT_FIELDS])
        flash("「お店について」を保存しました。")
        return redirect(url_for("admin.concept"))
    return render_template("admin/concept.html", fields=CONCEPT_FIELDS, values=_setting_values())


# ------------------------------------------------------------
# キャスト
# ------------------------------------------------------------
@admin_bp.route("/casts")
@login_required
def casts():
    items = Cast.query.order_by(Cast.sort_order, Cast.id).all()
    return render_template("admin/casts.html", items=items)


@admin_bp.route("/casts/new", methods=["GET", "POST"])
@admin_bp.route("/casts/<int:cast_id>", methods=["GET", "POST"])
@login_required
def cast_edit(cast_id=None):
    item = db.session.get(Cast, cast_id) if cast_id else Cast(visible=True, sort_order=Cast.query.count())
    if item is None:
        abort(404)
    error = None
    if request.method == "POST":
        item.name = request.form.get("name", "").strip()
        item.age = _int(request.form.get("age"), None) if request.form.get("age") else None
        item.origin = request.form.get("origin", "").strip()
        item.comment = request.form.get("comment", "").strip()
        item.is_new = bool(request.form.get("is_new"))
        item.visible = bool(request.form.get("visible"))
        item.sort_order = _int(request.form.get("sort_order"))
        try:
            img = _read_image(request.files.get("image"))
        except ValueError as e:
            img, error = None, str(e)
        if not item.name:
            error = "名前を入力してください。"
        if error is None:
            old_image = None
            if img is not None:
                old_image = item.image
                db.session.add(img)
                item.image = img
            elif request.form.get("remove_image") and item.image is not None:
                old_image = item.image
                item.image = None
            db.session.add(item)
            db.session.flush()
            if old_image is not None:
                db.session.delete(old_image)
            db.session.commit()
            flash(f"キャスト「{item.name}」を保存しました。")
            return redirect(url_for("admin.casts"))
        db.session.rollback()
    return render_template("admin/cast_form.html", item=item, error=error)


@admin_bp.route("/casts/<int:cast_id>/delete", methods=["POST"])
@login_required
def cast_delete(cast_id):
    item = db.session.get(Cast, cast_id) or abort(404)
    image = item.image
    db.session.delete(item)
    db.session.flush()
    if image is not None:
        db.session.delete(image)
    db.session.commit()
    flash(f"キャスト「{item.name}」を削除しました。")
    return redirect(url_for("admin.casts"))


# ------------------------------------------------------------
# イベント
# ------------------------------------------------------------
@admin_bp.route("/events")
@login_required
def events():
    items = Event.query.order_by(Event.sort_order, Event.id).all()
    return render_template("admin/events.html", items=items)


@admin_bp.route("/events/new", methods=["GET", "POST"])
@admin_bp.route("/events/<int:event_id>", methods=["GET", "POST"])
@login_required
def event_edit(event_id=None):
    item = db.session.get(Event, event_id) if event_id else Event(visible=True, sort_order=Event.query.count())
    if item is None:
        abort(404)
    error = None
    if request.method == "POST":
        item.date_label = request.form.get("date_label", "").strip()
        item.title = request.form.get("title", "").strip()
        item.body = request.form.get("body", "").strip()
        item.visible = bool(request.form.get("visible"))
        item.sort_order = _int(request.form.get("sort_order"))
        if not item.date_label or not item.title:
            error = "日付とタイトルを入力してください。"
        else:
            db.session.add(item)
            db.session.commit()
            flash(f"イベント「{item.title}」を保存しました。")
            return redirect(url_for("admin.events"))
        db.session.rollback()
    return render_template("admin/event_form.html", item=item, error=error)


@admin_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def event_delete(event_id):
    item = db.session.get(Event, event_id) or abort(404)
    db.session.delete(item)
    db.session.commit()
    flash(f"イベント「{item.title}」を削除しました。")
    return redirect(url_for("admin.events"))


# ------------------------------------------------------------
# 求人
# ------------------------------------------------------------
@admin_bp.route("/recruits", methods=["GET", "POST"])
@login_required
def recruits():
    if request.method == "POST":
        _save_settings([k for k, _l, _d, _t in RECRUIT_FIELDS])
        flash("求人の注意書きを保存しました。")
        return redirect(url_for("admin.recruits"))
    items = Recruit.query.order_by(Recruit.sort_order, Recruit.id).all()
    return render_template("admin/recruits.html", items=items, fields=RECRUIT_FIELDS, values=_setting_values())


@admin_bp.route("/recruits/new", methods=["GET", "POST"])
@admin_bp.route("/recruits/<int:recruit_id>", methods=["GET", "POST"])
@login_required
def recruit_edit(recruit_id=None):
    item = db.session.get(Recruit, recruit_id) if recruit_id else Recruit(visible=True, sort_order=Recruit.query.count())
    if item is None:
        abort(404)
    error = None
    if request.method == "POST":
        item.title = request.form.get("title", "").strip()
        item.salary = request.form.get("salary", "").strip()
        item.hours = request.form.get("hours", "").strip()
        item.benefits = request.form.get("benefits", "").strip()
        item.detail = request.form.get("detail", "").strip()
        item.visible = bool(request.form.get("visible"))
        item.sort_order = _int(request.form.get("sort_order"))
        if not item.title:
            error = "職種名を入力してください。"
        else:
            db.session.add(item)
            db.session.commit()
            flash(f"求人「{item.title}」を保存しました。")
            return redirect(url_for("admin.recruits"))
        db.session.rollback()
    return render_template("admin/recruit_form.html", item=item, error=error)


@admin_bp.route("/recruits/<int:recruit_id>/delete", methods=["POST"])
@login_required
def recruit_delete(recruit_id):
    item = db.session.get(Recruit, recruit_id) or abort(404)
    db.session.delete(item)
    db.session.commit()
    flash(f"求人「{item.title}」を削除しました。")
    return redirect(url_for("admin.recruits"))


# ------------------------------------------------------------
# 料金
# ------------------------------------------------------------
@admin_bp.route("/prices")
@login_required
def prices():
    items = PriceItem.query.order_by(PriceItem.kind.desc(), PriceItem.sort_order, PriceItem.id).all()
    return render_template("admin/prices.html", items=items)


@admin_bp.route("/prices/new", methods=["GET", "POST"])
@admin_bp.route("/prices/<int:price_id>", methods=["GET", "POST"])
@login_required
def price_edit(price_id=None):
    item = db.session.get(PriceItem, price_id) if price_id else PriceItem(
        kind=request.args.get("kind", "set"), sort_order=PriceItem.query.count())
    if item is None:
        abort(404)
    error = None
    if request.method == "POST":
        item.kind = "option" if request.form.get("kind") == "option" else "set"
        item.title = request.form.get("title", "").strip()
        item.price = request.form.get("price", "").strip()
        item.note = request.form.get("note", "").strip()
        item.sort_order = _int(request.form.get("sort_order"))
        if not item.title or not item.price:
            error = "項目名と料金を入力してください。"
        else:
            db.session.add(item)
            db.session.commit()
            flash(f"料金「{item.title}」を保存しました。")
            return redirect(url_for("admin.prices"))
        db.session.rollback()
    return render_template("admin/price_form.html", item=item, error=error)


@admin_bp.route("/prices/<int:price_id>/delete", methods=["POST"])
@login_required
def price_delete(price_id):
    item = db.session.get(PriceItem, price_id) or abort(404)
    db.session.delete(item)
    db.session.commit()
    flash(f"料金「{item.title}」を削除しました。")
    return redirect(url_for("admin.prices"))


# ------------------------------------------------------------
# 管理者アカウント
# ------------------------------------------------------------
@admin_bp.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts():
    error = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "password":
            if not g.admin.check_password(request.form.get("current", "")):
                error = "現在のパスワードが違います。"
            elif len(request.form.get("new", "")) < 8:
                error = "新しいパスワードは8文字以上にしてください。"
            elif request.form.get("new") != request.form.get("new2"):
                error = "確認用パスワードが一致しません。"
            else:
                g.admin.set_password(request.form["new"])
                db.session.commit()
                flash("パスワードを変更しました。")
                return redirect(url_for("admin.accounts"))
        elif action == "add":
            username = request.form.get("username", "").strip()
            pw = request.form.get("password", "")
            if not username or len(pw) < 8:
                error = "ユーザー名と8文字以上のパスワードを入力してください。"
            elif Admin.query.filter_by(username=username).first():
                error = "そのユーザー名は既に使われています。"
            else:
                a = Admin(username=username)
                a.set_password(pw)
                db.session.add(a)
                db.session.commit()
                flash(f"管理者「{username}」を追加しました。")
                return redirect(url_for("admin.accounts"))
        elif action == "delete":
            target = db.session.get(Admin, _int(request.form.get("id")))
            if target is None or target.id == g.admin.id:
                error = "自分自身は削除できません。"
            else:
                db.session.delete(target)
                db.session.commit()
                flash(f"管理者「{target.username}」を削除しました。")
                return redirect(url_for("admin.accounts"))
    return render_template("admin/accounts.html", admins=Admin.query.order_by(Admin.id).all(), error=error)
