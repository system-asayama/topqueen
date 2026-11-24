# TOP QUEEN

フィリピンパブ「TOP QUEEN」公式ホームページ（Flask + Docker Compose）

## 管理画面（/admin）
- 初回は `/admin` にアクセスすると最初の管理者アカウントを作成する画面が出ます（管理者が1人もいないときだけ）
- 店舗情報・お店について・料金・キャスト（写真付き）・イベント／お知らせ・求人・管理者アカウントをブラウザから編集できます
- データと写真は PostgreSQL に保存されます（初回起動時にサンプルデータを投入）
- 環境変数 `SECRET_KEY` を設定しない場合はDBに自動生成した鍵を使います
- デザイン: `static/css/style.css` / ページ構成: `templates/index.html`

## ローカル起動
```
docker compose up --build   # http://localhost:8080
```
