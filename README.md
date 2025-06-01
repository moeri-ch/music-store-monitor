# 🎸 楽器店商品監視システム (GitHub Actions版)

イケベ楽器店の新商品を毎日自動で監視し、メール通知するシステムです。  
GitHub Actionsを使用して無料でクラウド実行されます。

## ✨ 特徴

- 🕘 **毎日自動実行**: 日本時間9:00に自動で商品チェック
- 🆓 **完全無料**: GitHub Actionsの無料枠を使用
- 📧 **メール通知**: 新商品発見時に自動でメール送信
- 🔒 **セキュア**: 機密情報はGitHub Secretsで安全に管理
- 📱 **PC不要**: クラウドで実行されるためPCの電源状態に依存しない

## 🚀 セットアップ手順

### 1. このリポジトリをFork

右上の「Fork」ボタンをクリックして、自分のアカウントにコピーします。

### 2. GitHub Secretsの設定

**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

以下の5つのSecretを設定してください：

| Secret名 | 説明 | 例 |
|----------|------|---|
| `SMTP_SERVER` | SMTPサーバー | `smtp.gmail.com` |
| `SMTP_PORT` | SMTPポート | `587` |
| `SENDER_EMAIL` | 送信元メールアドレス | `your_email@gmail.com` |
| `SENDER_PASSWORD` | アプリパスワード | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | 受信先メールアドレス | `recipient@yahoo.co.jp` |

### 3. Gmailアプリパスワードの取得

1. [Google アカウント管理](https://myaccount.google.com/) にアクセス
2. **セキュリティ** → **2段階認証プロセス** を有効化
3. **アプリパスワード** を生成
4. 生成された16文字のパスワードを `SENDER_PASSWORD` に設定

### 4. 実行確認

**Actions**タブで以下を確認：
- ワークフローが表示されること
- 手動実行（「Run workflow」）が可能なこと
- 毎日の自動実行が設定されていること

## 📅 実行スケジュール

- **自動実行**: 毎日 日本時間 9:00
- **手動実行**: Actionsタブから随時実行可能

## 📧 通知メール例

```
🎸 新商品が3件見つかりました - イケベ楽器店 [GitHub Actions]

GitHub Actionsで自動検出された新商品 3件：

📦 YAMAHA CG142S Classical Guitar
💰 ¥35,000
🔗 https://www.ikebe-gakki.com/ProductDetail.aspx?pid=123456

--------------------------------------------------

📦 Juan Hernandez Estudio Classical Guitar
💰 ¥260,000
🔗 https://www.ikebe-gakki.com/ProductDetail.aspx?pid=789012
```

## 🔧 カスタマイズ

### 実行時刻の変更

`.github/workflows/monitor.yml` の cron 設定を変更：

```yaml
schedule:
  # 毎日21:00 JST (12:00 UTC) に変更する場合
  - cron: '0 12 * * *'
```

### 監視対象の変更

`monitor_github.py` の `self.url` を変更することで、異なる商品カテゴリを監視できます。

## 📊 実行ログの確認

**Actions**タブ → 最新の実行 → **monitor-logs** から以下をダウンロード可能：
- `music_store_monitor.log`: 実行ログ
- `products_data.json`: 商品データ

## ⚠️ 注意事項

- Gmail以外のメールサービスを使用する場合は、SMTP設定を調整してください
- 無料プランでは月2,000分までの実行時間制限があります（1日数分の実行なら十分）
- サイトの構造変更により、商品抽出が正常に動作しない場合があります

## 🆘 トラブルシューティング

### メールが送信されない
1. GitHub Secretsの設定を確認
2. Gmailアプリパスワードを再生成
3. Actionsログでエラー内容を確認

### 商品が検出されない
1. 対象サイトのメンテナンス状況を確認
2. サイト構造の変更を確認
3. 手動実行でテスト

## 📜 ライセンス

MIT License

## 🤝 コントリビューション

Issue、Pull Request歓迎です！
