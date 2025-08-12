# Fly.io デプロイメントガイド

このドキュメントでは、OIDC Platform を Fly.io にデプロイする方法を詳しく説明します。

## 📋 前提条件

### 必要なツール
- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) がインストールされていること
- Git がインストールされていること
- curl がインストールされていること（ヘルスチェック用）
- jq がインストールされていること（オプション、JSON検証用）

### アカウント
- [Fly.io アカウント](https://fly.io/app/sign-up) が作成済みであること
- クレジットカードが登録されていること（無料枠あり）

## 🚀 クイックスタート

### 1. Fly CLI のインストール・ログイン

```bash
# Fly CLI のインストール（macOS）
brew install flyctl

# または curl でインストール
curl -L https://fly.io/install.sh | sh

# ログイン
fly auth login
```

### 2. 自動デプロイ

```bash
# デプロイスクリプトを実行
./scripts/deploy-fly.sh
```

このスクリプトが以下を自動実行します：
- アプリケーション作成
- PostgreSQL データベース作成・接続
- シークレット設定
- デプロイ実行
- ヘルスチェック

### 3. デプロイ確認

```bash
# ヘルスチェック実行
./scripts/health-check-fly.sh

# または手動確認
curl https://oidc-platform.fly.dev/health
curl https://oidc-platform.fly.dev/.well-known/openid-configuration
```

## 🔧 手動デプロイ手順

### 1. アプリケーション作成

```bash
# アプリ作成
fly apps create oidc-platform --org personal

# 設定確認
fly apps list
```

### 2. PostgreSQL データベース設定

```bash
# PostgreSQL アプリ作成
fly postgres create --name oidc-platform-db --region nrt

# データベース接続
fly postgres attach --app oidc-platform oidc-platform-db

# 接続確認
fly postgres connect --app oidc-platform-db
```

### 3. シークレット設定

```bash
# 強力なシークレットキー生成・設定
fly secrets set SECRET_KEY="$(openssl rand -base64 32)" --app oidc-platform

# Issuer URL 設定
fly secrets set ISSUER="https://oidc-platform.fly.dev" --app oidc-platform

# CORS 設定
fly secrets set ALLOWED_ORIGINS='["https://your-client-app.com"]' --app oidc-platform

# サンプルクライアント設定
fly secrets set SAMPLE_CLIENT_REDIRECT_URIS='["https://your-client-app.com/callback"]' --app oidc-platform

# シークレット確認
fly secrets list --app oidc-platform
```

### 4. デプロイ実行

```bash
# デプロイ
fly deploy --dockerfile Dockerfile.fly

# ステータス確認
fly status --app oidc-platform
```

## 📊 監視・管理

### ログ確認

```bash
# リアルタイムログ
fly logs --app oidc-platform

# 過去のログ
fly logs --app oidc-platform --since 1h
```

### メトリクス確認

```bash
# アプリケーションメトリクス
fly metrics --app oidc-platform

# データベースメトリクス
fly metrics --app oidc-platform-db
```

### SSH接続

```bash
# アプリケーションコンテナに接続
fly ssh console --app oidc-platform

# データベースに接続
fly postgres connect --app oidc-platform-db
```

## 🔄 CI/CD 設定

### GitHub Actions 設定

1. **Fly.io API トークン取得**
   ```bash
   fly auth token
   ```

2. **GitHub Secrets 設定**
   - リポジトリの Settings > Secrets and variables > Actions
   - `FLY_API_TOKEN` を追加

3. **自動デプロイ**
   - `main` ブランチへのプッシュで自動デプロイ
   - 手動デプロイも可能（Actions タブから）

### ワークフロー確認

```bash
# GitHub Actions の状況確認
# https://github.com/your-username/oidc-platform/actions
```

## 🔧 設定カスタマイズ

### アプリ名変更

`fly.toml` を編集：
```toml
app = "your-custom-app-name"
```

### リージョン変更

```toml
primary_region = "sin"  # シンガポール
# primary_region = "lax"  # ロサンゼルス
# primary_region = "fra"  # フランクフルト
```

### リソース調整

```toml
[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 1024
```

### 環境変数追加

```bash
fly secrets set YOUR_CUSTOM_VAR="value" --app oidc-platform
```

## 🔒 セキュリティ設定

### 本番用設定

```bash
# 本番用ドメイン設定
fly secrets set ISSUER="https://auth.yourdomain.com" --app oidc-platform
fly secrets set ALLOWED_ORIGINS='["https://yourdomain.com", "https://app.yourdomain.com"]' --app oidc-platform

# サンプルクライアント無効化（本番環境）
fly secrets set SAMPLE_CLIENT_ID="" --app oidc-platform
```

### カスタムドメイン設定

```bash
# カスタムドメイン追加
fly certs create auth.yourdomain.com --app oidc-platform

# DNS設定確認
fly certs show auth.yourdomain.com --app oidc-platform
```

## 🚨 トラブルシューティング

### よくある問題

#### 1. デプロイ失敗

```bash
# ログ確認
fly logs --app oidc-platform

# ステータス確認
fly status --app oidc-platform

# 再デプロイ
fly deploy --dockerfile Dockerfile.fly
```

#### 2. データベース接続エラー

```bash
# データベース状態確認
fly status --app oidc-platform-db

# 接続テスト
fly postgres connect --app oidc-platform-db

# 接続文字列確認
fly secrets list --app oidc-platform | grep DATABASE_URL
```

#### 3. ヘルスチェック失敗

```bash
# 詳細ヘルスチェック
./scripts/health-check-fly.sh

# 手動確認
curl -v https://oidc-platform.fly.dev/health
```

#### 4. メモリ不足

```bash
# リソース使用量確認
fly metrics --app oidc-platform

# メモリ増量
fly scale memory 1024 --app oidc-platform
```

### ログレベル設定

```bash
# デバッグログ有効化
fly secrets set DEBUG="true" --app oidc-platform

# 本番環境では無効化
fly secrets set DEBUG="false" --app oidc-platform
```

## 📈 スケーリング

### 水平スケーリング

```bash
# インスタンス数増加
fly scale count 3 --app oidc-platform

# リージョン追加
fly regions add sin lax --app oidc-platform
```

### 垂直スケーリング

```bash
# CPU/メモリ増強
fly scale vm shared-cpu-2x --app oidc-platform
fly scale memory 2048 --app oidc-platform
```

## 💰 コスト管理

### 料金確認

```bash
# 使用量確認
fly dashboard billing

# アプリ別コスト
fly apps list
```

### コスト最適化

- 開発環境は `fly apps suspend` で一時停止
- 不要なリージョンは削除
- 適切なインスタンスサイズを選択

## 🔄 バックアップ・復旧

### データベースバックアップ

```bash
# バックアップ作成
fly postgres backup create --app oidc-platform-db

# バックアップ一覧
fly postgres backup list --app oidc-platform-db
```

### 復旧手順

```bash
# バックアップから復旧
fly postgres backup restore <backup-id> --app oidc-platform-db
```

## 📚 参考リンク

- [Fly.io Documentation](https://fly.io/docs/)
- [Fly.io Postgres](https://fly.io/docs/postgres/)
- [Fly.io Pricing](https://fly.io/docs/about/pricing/)
- [OpenID Connect Specification](https://openid.net/connect/)

## 🆘 サポート

問題が発生した場合：

1. このドキュメントのトラブルシューティングセクションを確認
2. [Fly.io Community](https://community.fly.io/) で質問
3. [GitHub Issues](https://github.com/your-username/oidc-platform/issues) で報告

---

**注意**: 本番環境では必ず適切なシークレット管理、監視、バックアップ戦略を実装してください。
