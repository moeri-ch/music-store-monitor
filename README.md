# 🎸 5つの楽器店統合監視システム (GitHub Actions版)

5つの楽器店（イケベ楽器店、黒澤楽器店、島村楽器、QSic、J-Guitar）の新商品を週1回自動で監視し、メール通知するシステムです。  
GitHub Actionsを使用して無料でクラウド実行されます。

## ✨ 特徴

- 🕘 **週1回自動実行**: 毎週土曜日 日本時間9:00に自動で商品チェック
- 🆓 **完全無料**: GitHub Actionsの無料枠を使用
- 📧 **メール通知**: 新商品発見時に自動でメール送信
- 🔒 **セキュア**: 機密情報はGitHub Secretsで安全に管理
- 📱 **PC不要**: クラウドで実行されるためPCの電源状態に依存しない
- 💰 **価格情報必須**: 価格が取得できた商品のみを対象にして信頼性を向上
- 🏪 **5サイト対応**: 複数の楽器店を一括監視

## 🎯 対象サイト

1. **イケベ楽器店** - クラシックギター
2. **黒澤楽器店** - クラシックギター  
3. **島村楽器** - クラシックギター
4. **QSic** - クラシックギター
5. **J-Guitar** - クラシックギター

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
- 週1回の自動実行が設定されていること

## 📅 実行スケジュール

- **自動実行**: 毎週土曜日 日本時間 9:00 (UTC 0:00)
- **手動実行**: Actionsタブから随時実行可能

## 📧 通知メール例

```
🎸 新商品が7件見つかりました - 5サイト統合監視（週1回・価格付きのみ） [GitHub Actions]

5つの楽器店サイトで新商品 7件を検出しました！
（価格情報が取得できた商品のみ）

============================================================

🏪 【イケベ楽器店】 新商品 2件
----------------------------------------

1. 📦 YAMAHA CG142S Classical Guitar
   💰 ¥35,000
   🔗 https://www.ikebe-gakki.com/ProductDetail.aspx?pid=123456

2. 📦 Juan Hernandez Estudio Classical Guitar
   💰 ¥260,000
   🔗 https://www.ikebe-gakki.com/ProductDetail.aspx?pid=789012

🏪 【黒澤楽器店】 新商品 3件
----------------------------------------

1. 📦 Gibson Antonio Sanchez Model 1025
   💰 ¥180,000
   🔗 https://shop.kurosawagakki.com/items/456789

...
```

## 🔧 カスタマイズ

### 実行時刻の変更

`.github/workflows/monitor.yml` の cron 設定を変更：

```yaml
schedule:
  # 毎週日曜日21:00 JST (12:00 UTC) に変更する場合
  - cron: '0 12 * * 0'
```

### 実行頻度の変更

```yaml
schedule:
  # 毎日実行する場合
  - cron: '0 0 * * *'
  # 月2回（1日と15日）実行する場合  
  - cron: '0 0 1,15 * *'
```

### 監視対象の変更

`music_store_monitor.py` の `self.stores` 設定を変更することで、異なる商品カテゴリや店舗を監視できます。

## 📊 実行ログの確認

**Actions**タブ → 最新の実行 → **monitor-logs** から以下をダウンロード可能：
- `multi_store_monitor_price_required.log`: 実行ログ
- `multi_store_products_price_required.json`: 商品データ

## 🧪 ローカルテスト

本番実行前にローカルでテストできます：

1. **設定ファイル作成**:
   ```bash
   cp config.json.template config.json
   # config.jsonにメール設定を記入
   ```

2. **依存関係インストール**:
   ```bash
   pip install -r requirements.txt
   ```

3. **テスト実行**:
   ```bash
   python test_multi_store.py  # 詳細テスト（メール送信なし）
   python music_store_monitor.py  # 本番と同じ処理
   ```

## ⚠️ 注意事項

- Gmail以外のメールサービスを使用する場合は、SMTP設定を調整してください
- 無料プランでは月2,000分までの実行時間制限があります（週1回数分の実行なら十分）
- サイトの構造変更により、商品抽出が正常に動作しない場合があります
- 価格情報が取得できない商品は対象外となります
- 各サイトへの負荷軽減のため、適切な間隔を空けて実行しています

## 🆘 トラブルシューティング

### メールが送信されない
1. GitHub Secretsの設定を確認
2. Gmailアプリパスワードを再生成
3. Actionsログでエラー内容を確認

### 商品が検出されない
1. 対象サイトのメンテナンス状況を確認
2. サイト構造の変更を確認
3. `test_multi_store.py` でローカルテスト実行
4. 手動実行でテスト

### 特定のサイトでエラーが発生
1. Actionsログで詳細なエラー内容を確認
2. そのサイトの構造変更をチェック
3. 必要に応じてスクレイピングロジックを調整

## 📈 改良点（v2.0）

- **J-Guitarの価格抽出を大幅改善**: より多くの商品で価格を正確に取得
- **価格必須条件を強化**: 価格情報がない商品を確実に除外
- **ログ出力を詳細化**: デバッグしやすくなりました
- **エラーハンドリング強化**: より安定した動作を実現

## 📜 ライセンス

MIT License

## 🤝 コントリビューション

Issue、Pull Request歓迎です！新しい楽器店の追加や機能改善のご提案をお待ちしています。
