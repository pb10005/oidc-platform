#!/bin/bash
# Health Check Script for Fly.io Deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="oidc-platform"
BASE_URL="https://$APP_NAME.fly.dev"

echo -e "${BLUE}🏥 Fly.io ヘルスチェック開始...${NC}"

# Function to check endpoint
check_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -e "${YELLOW}🔍 $description をチェック中...${NC}"
    
    response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$url" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✅ $description: OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ $description: FAILED (HTTP $response)${NC}"
        if [ -f /tmp/response.json ]; then
            echo "Response body:"
            cat /tmp/response.json
            echo ""
        fi
        return 1
    fi
}

# Function to check JSON response
check_json_endpoint() {
    local url=$1
    local description=$2
    local key_to_check=$3
    
    echo -e "${YELLOW}🔍 $description をチェック中...${NC}"
    
    response=$(curl -s "$url" || echo "{}")
    
    if echo "$response" | jq -e ".$key_to_check" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $description: OK${NC}"
        return 0
    else
        echo -e "${RED}❌ $description: FAILED${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️ jq がインストールされていません。JSON検証をスキップします。${NC}"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

# Health checks
FAILED_CHECKS=0

# 1. Basic health endpoint
if ! check_endpoint "$BASE_URL/health" "基本ヘルスチェック"; then
    ((FAILED_CHECKS++))
fi

# 2. OIDC Discovery Document
if ! check_endpoint "$BASE_URL/.well-known/openid-configuration" "OIDC Discovery Document"; then
    ((FAILED_CHECKS++))
fi

# 3. JWKS endpoint
if ! check_endpoint "$BASE_URL/jwks" "JWKS エンドポイント"; then
    ((FAILED_CHECKS++))
fi

# 4. API Documentation
if ! check_endpoint "$BASE_URL/docs" "API ドキュメント"; then
    ((FAILED_CHECKS++))
fi

# 5. Check OIDC Discovery Document content (if jq is available)
if [ "$JQ_AVAILABLE" = true ]; then
    if ! check_json_endpoint "$BASE_URL/.well-known/openid-configuration" "OIDC Discovery Document 内容" "issuer"; then
        ((FAILED_CHECKS++))
    fi
    
    if ! check_json_endpoint "$BASE_URL/.well-known/openid-configuration" "認証エンドポイント" "authorization_endpoint"; then
        ((FAILED_CHECKS++))
    fi
    
    if ! check_json_endpoint "$BASE_URL/.well-known/openid-configuration" "トークンエンドポイント" "token_endpoint"; then
        ((FAILED_CHECKS++))
    fi
    
    if ! check_json_endpoint "$BASE_URL/.well-known/openid-configuration" "ユーザー情報エンドポイント" "userinfo_endpoint"; then
        ((FAILED_CHECKS++))
    fi
fi

# 6. Check application status via Fly CLI (if available)
if command -v fly &> /dev/null; then
    echo -e "${YELLOW}🔍 Fly.io アプリケーションステータスをチェック中...${NC}"
    
    if fly status --app "$APP_NAME" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Fly.io アプリケーションステータス: OK${NC}"
        
        # Show brief status
        echo -e "${BLUE}📊 アプリケーション情報:${NC}"
        fly status --app "$APP_NAME" | head -10
    else
        echo -e "${RED}❌ Fly.io アプリケーションステータス: FAILED${NC}"
        ((FAILED_CHECKS++))
    fi
else
    echo -e "${YELLOW}⚠️ Fly CLI が利用できません。アプリケーションステータスチェックをスキップします。${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}📋 ヘルスチェック結果:${NC}"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 すべてのヘルスチェックが成功しました!${NC}"
    echo ""
    echo -e "${BLUE}🌐 アプリケーション情報:${NC}"
    echo -e "  📍 ベースURL: $BASE_URL"
    echo -e "  🏥 ヘルスチェック: $BASE_URL/health"
    echo -e "  📖 API ドキュメント: $BASE_URL/docs"
    echo -e "  🔍 Discovery Document: $BASE_URL/.well-known/openid-configuration"
    echo -e "  🔑 JWKS: $BASE_URL/jwks"
    echo ""
    echo -e "${BLUE}🛠️ 管理コマンド:${NC}"
    echo -e "  📊 ステータス: fly status --app $APP_NAME"
    echo -e "  📝 ログ: fly logs --app $APP_NAME"
    echo -e "  📈 メトリクス: fly metrics --app $APP_NAME"
    
    exit 0
else
    echo -e "${RED}❌ $FAILED_CHECKS 個のヘルスチェックが失敗しました${NC}"
    echo ""
    echo -e "${YELLOW}🔧 トラブルシューティング:${NC}"
    echo -e "  1. ログを確認: fly logs --app $APP_NAME"
    echo -e "  2. アプリケーションステータス: fly status --app $APP_NAME"
    echo -e "  3. 環境変数確認: fly secrets list --app $APP_NAME"
    echo -e "  4. データベース接続確認: fly postgres connect --app $APP_NAME-db"
    
    exit 1
fi
