#!/bin/bash
# Fly.io Deployment Script for OIDC Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="oidc-platform"
DB_NAME="oidc-platform-db"
REGION="nrt"

echo -e "${BLUE}🚀 Fly.io デプロイメント開始...${NC}"

# 1. 環境チェック
echo -e "${YELLOW}📋 環境をチェックしています...${NC}"
if ! command -v fly &> /dev/null; then
    echo -e "${RED}❌ Fly CLI がインストールされていません${NC}"
    echo "インストール方法: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# 2. ログイン確認
echo -e "${YELLOW}🔐 Fly.io ログイン状態を確認しています...${NC}"
if ! fly auth whoami &> /dev/null; then
    echo -e "${YELLOW}ログインが必要です...${NC}"
    fly auth login
fi

# 3. アプリ存在確認
echo -e "${YELLOW}📱 アプリケーションを確認しています...${NC}"
if ! fly apps list | grep -q "$APP_NAME"; then
    echo -e "${BLUE}新しいアプリを作成します: $APP_NAME${NC}"
    fly apps create "$APP_NAME" --org personal
else
    echo -e "${GREEN}✅ アプリ '$APP_NAME' が見つかりました${NC}"
fi

# 4. データベース確認・作成
echo -e "${YELLOW}🗄️ データベースを確認しています...${NC}"
if ! fly apps list | grep -q "$DB_NAME"; then
    echo -e "${BLUE}PostgreSQLデータベースを作成します: $DB_NAME${NC}"
    fly postgres create --name "$DB_NAME" --region "$REGION"
    
    echo -e "${BLUE}データベースをアプリに接続します...${NC}"
    fly postgres attach --app "$APP_NAME" "$DB_NAME"
else
    echo -e "${GREEN}✅ データベース '$DB_NAME' が見つかりました${NC}"
fi

# 5. シークレット設定
echo -e "${YELLOW}🔐 シークレットを設定しています...${NC}"

# Generate strong secret key
SECRET_KEY=$(openssl rand -base64 32)
fly secrets set SECRET_KEY="$SECRET_KEY" --app "$APP_NAME"

# Set issuer URL
ISSUER_URL="https://$APP_NAME.fly.dev"
fly secrets set ISSUER="$ISSUER_URL" --app "$APP_NAME"

# Set sample client redirect URIs for production
SAMPLE_CLIENT_REDIRECT_URIS='["https://your-client-app.com/callback", "http://localhost:3000/callback"]'
fly secrets set SAMPLE_CLIENT_REDIRECT_URIS="$SAMPLE_CLIENT_REDIRECT_URIS" --app "$APP_NAME"

# Set allowed origins for CORS
ALLOWED_ORIGINS='["https://your-client-app.com", "http://localhost:3000"]'
fly secrets set ALLOWED_ORIGINS="$ALLOWED_ORIGINS" --app "$APP_NAME"

echo -e "${GREEN}✅ シークレット設定完了${NC}"

# 6. デプロイ実行
echo -e "${YELLOW}🚀 アプリケーションをデプロイしています...${NC}"
fly deploy --dockerfile Dockerfile.fly

# 7. デプロイ状態確認
echo -e "${YELLOW}📊 デプロイ状態を確認しています...${NC}"
fly status --app "$APP_NAME"

# 8. ヘルスチェック
echo -e "${YELLOW}🏥 ヘルスチェックを実行しています...${NC}"
sleep 15

HEALTH_URL="$ISSUER_URL/health"
if curl -f "$HEALTH_URL" &> /dev/null; then
    echo -e "${GREEN}✅ ヘルスチェック成功!${NC}"
else
    echo -e "${RED}❌ ヘルスチェック失敗${NC}"
    echo "ログを確認してください: fly logs --app $APP_NAME"
    exit 1
fi

# 9. OIDC Discovery Document確認
echo -e "${YELLOW}🔍 OIDC Discovery Documentを確認しています...${NC}"
DISCOVERY_URL="$ISSUER_URL/.well-known/openid-configuration"
if curl -f "$DISCOVERY_URL" &> /dev/null; then
    echo -e "${GREEN}✅ OIDC Discovery Document確認成功!${NC}"
else
    echo -e "${RED}❌ OIDC Discovery Document確認失敗${NC}"
fi

# 10. 完了メッセージ
echo -e "${GREEN}🎉 デプロイメント完了!${NC}"
echo ""
echo -e "${BLUE}📋 アプリケーション情報:${NC}"
echo -e "  🌐 アプリケーションURL: $ISSUER_URL"
echo -e "  📖 API ドキュメント: $ISSUER_URL/docs"
echo -e "  🔍 Discovery Document: $DISCOVERY_URL"
echo -e "  🏥 ヘルスチェック: $HEALTH_URL"
echo ""
echo -e "${BLUE}🛠️ 管理コマンド:${NC}"
echo -e "  📊 ステータス確認: fly status --app $APP_NAME"
echo -e "  📝 ログ確認: fly logs --app $APP_NAME"
echo -e "  🔧 SSH接続: fly ssh console --app $APP_NAME"
echo -e "  📈 メトリクス: fly metrics --app $APP_NAME"
echo ""
echo -e "${YELLOW}⚠️ 次のステップ:${NC}"
echo -e "  1. 本番用クライアントアプリのドメインを ALLOWED_ORIGINS に追加"
echo -e "  2. SAMPLE_CLIENT_REDIRECT_URIS を実際のクライアントURLに更新"
echo -e "  3. 監視・アラート設定"
echo -e "  4. バックアップ戦略の実装"
