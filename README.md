# TOP QUEEN

フィリピンパブ「TOP QUEEN」公式ホームページ（Flask + Docker Compose）

## 内容の編集
- 店舗情報・料金・キャスト・イベント: `app.py` の `SHOP` / `SYSTEM` / `SYSTEM_OPTIONS` / `CAST` / `EVENTS`
- キャスト写真: `static/img/cast/` に画像を置き、`CAST` の `image` にファイル名を指定
- デザイン: `static/css/style.css` / ページ構成: `templates/index.html`

## ローカル起動
```
docker compose up --build   # http://localhost:8080
```
