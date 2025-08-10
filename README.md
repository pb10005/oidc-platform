# OIDC Authentication Server

A production-ready OpenID Connect (OIDC) compliant authentication and authorization server built with Python FastAPI, PostgreSQL, and Docker.

## Features

- ✅ **OIDC Compliant**: Full OpenID Connect specification support
- 🔐 **Authorization Code Flow with PKCE**: Secure authentication flow
- 🛡️ **JWT Tokens**: Stateless authentication with proper signing
- 🌐 **Web UI**: Login, registration, and consent pages
- 🐳 **Containerized**: Docker and Docker Compose ready
- 📊 **Database**: PostgreSQL with proper migrations
- 🔒 **Security**: bcrypt password hashing, CSRF protection, rate limiting
- 📖 **API Documentation**: Automatic OpenAPI/Swagger docs

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  OIDC Server    │───▶│   PostgreSQL    │
│                 │    │                 │    │                 │
│ - Web App       │    │ - FastAPI       │    │ - User Data     │
│ - Mobile App    │    │ - JWT Tokens    │    │ - Clients       │
│ - SPA           │    │ - PKCE Support  │    │ - Tokens        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (if running locally)

### Using Docker Compose (Recommended)

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd oidc-platform
   ```

2. **Start the services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the server**:
   - OIDC Server: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - pgAdmin (optional): http://localhost:5050

4. **Test the setup**:
   ```bash
   curl http://localhost:8000/.well-known/openid-configuration
   ```

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start PostgreSQL** (using Docker):
   ```bash
   docker run -d \
     --name oidc-postgres \
     -e POSTGRES_DB=oidc_db \
     -e POSTGRES_USER=oidc_user \
     -e POSTGRES_PASSWORD=oidc_password \
     -p 5432:5432 \
     postgres:15-alpine
   ```

4. **Run the server**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## OIDC Endpoints

### Discovery Document
```
GET /.well-known/openid-configuration
```

### Authorization Endpoint
```
GET /auth?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&scope=openid profile email&state=STATE&code_challenge=CHALLENGE&code_challenge_method=S256
```

### Token Endpoint
```
POST /token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=CODE&redirect_uri=REDIRECT_URI&client_id=CLIENT_ID&code_verifier=VERIFIER
```

### UserInfo Endpoint
```
GET /userinfo
Authorization: Bearer ACCESS_TOKEN
```

### JWKS Endpoint
```
GET /jwks
```

## Sample OAuth2 Client

The server automatically creates a sample client for testing:

- **Client ID**: `sample-client`
- **Client Secret**: `sample-secret`
- **Redirect URIs**: 
  - `http://localhost:3000/callback`
  - `http://localhost:8080/callback`
- **Scopes**: `openid`, `profile`, `email`

### サンプルクライアントの使用方法

1. **OIDCサーバーを起動**:
   ```bash
   docker-compose up -d
   ```

2. **サンプルクライアントを起動**:
   ```bash
   cd client-example
   python3 server.py
   ```

3. **ブラウザでテスト**:
   - http://localhost:3000 にアクセス
   - 「OIDCサーバーでログイン」ボタンをクリック
   - OIDCサーバーでユーザー登録/ログイン
   - 認証フローを完了してトークンを取得
   - ユーザー情報を取得

### 完全なOAuth2/OIDCフローのテスト

サンプルクライアントでは以下のフローを体験できます：

1. **Authorization Code Flow開始** - OIDCサーバーの認証エンドポイントにリダイレクト
2. **ユーザー認証** - ログイン画面でユーザー認証
3. **認証コード取得** - クライアントのコールバックURLに認証コードが返される
4. **トークン交換** - 認証コードをアクセストークンとIDトークンに交換
5. **ユーザー情報取得** - アクセストークンを使ってUserInfoエンドポイントからユーザー情報を取得

## Usage Examples

### 1. Authorization Code Flow with PKCE

```javascript
// Generate PKCE parameters
const codeVerifier = generateRandomString(128);
const codeChallenge = await sha256(codeVerifier);

// Step 1: Redirect to authorization endpoint
const authUrl = `http://localhost:8000/auth?` +
  `response_type=code&` +
  `client_id=sample-client&` +
  `redirect_uri=http://localhost:3000/callback&` +
  `scope=openid profile email&` +
  `state=${generateRandomString(32)}&` +
  `code_challenge=${codeChallenge}&` +
  `code_challenge_method=S256`;

window.location.href = authUrl;

// Step 2: Exchange code for tokens (in your callback handler)
const tokenResponse = await fetch('http://localhost:8000/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: authorizationCode,
    redirect_uri: 'http://localhost:3000/callback',
    client_id: 'sample-client',
    code_verifier: codeVerifier,
  }),
});

const tokens = await tokenResponse.json();
// tokens.access_token, tokens.id_token, tokens.refresh_token
```

### 2. Get User Information

```javascript
const userInfoResponse = await fetch('http://localhost:8000/userinfo', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
  },
});

const userInfo = await userInfoResponse.json();
// { sub, name, given_name, family_name, email, email_verified }
```

### 3. Validate ID Token

```javascript
import jwt from 'jsonwebtoken';

// Get JWKS for token validation
const jwksResponse = await fetch('http://localhost:8000/jwks');
const jwks = await jwksResponse.json();

// Decode and verify ID token
const decoded = jwt.verify(idToken, getKey, {
  algorithms: ['HS256'],
  audience: 'sample-client',
  issuer: 'http://localhost:8000',
});
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://oidc_user:oidc_password@localhost:5432/oidc_db` |
| `SECRET_KEY` | JWT signing secret | `your-super-secret-key-change-this-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `7` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `True` |
| `APP_TITLE` | Application title | `OIDC Authentication Server` |
| `APP_DESCRIPTION` | Application description | `OpenID Connect compliant authentication and authorization server` |
| `APP_VERSION` | Application version | `1.0.0` |
| `ISSUER` | OIDC issuer URL | `http://localhost:8000` |
| `SUPPORTED_SCOPES` | Supported OAuth2 scopes | `["openid", "profile", "email"]` |
| `SUPPORTED_RESPONSE_TYPES` | Supported response types | `["code"]` |
| `SUPPORTED_RESPONSE_MODES` | Supported response modes | `["query"]` |
| `SUPPORTED_GRANT_TYPES` | Supported grant types | `["authorization_code", "refresh_token"]` |
| `SUPPORTED_SUBJECT_TYPES` | Supported subject types | `["public"]` |
| `SUPPORTED_ID_TOKEN_SIGNING_ALGS` | Supported ID token signing algorithms | `["HS256"]` |
| `SUPPORTED_TOKEN_ENDPOINT_AUTH_METHODS` | Supported token endpoint auth methods | `["client_secret_post", "client_secret_basic"]` |
| `SUPPORTED_CODE_CHALLENGE_METHODS` | Supported PKCE code challenge methods | `["S256", "plain"]` |
| `SUPPORTED_CLAIMS` | Supported claims | `["sub", "iss", "aud", "exp", "iat", "auth_time", "name", "given_name", "family_name", "email", "email_verified"]` |
| `SAMPLE_CLIENT_ID` | Sample client ID | `sample-client` |
| `SAMPLE_CLIENT_SECRET` | Sample client secret | `sample-secret` |
| `SAMPLE_CLIENT_NAME` | Sample client name | `Sample OIDC Client` |
| `SAMPLE_CLIENT_REDIRECT_URIS` | Sample client redirect URIs | `["http://localhost:3000/callback", "http://localhost:8080/callback"]` |
| `SAMPLE_CLIENT_SCOPES` | Sample client scopes | `["openid", "profile", "email"]` |
| `SAMPLE_CLIENT_TYPE` | Sample client type | `confidential` |
| `CLIENT_EXAMPLE_PORT` | Client example server port | `3000` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["http://localhost:3000", "http://localhost:8080"]` |
| `ALERT_AUTO_HIDE_SECONDS` | UI alert auto-hide timeout | `5` |
| `FORM_LOADING_TIMEOUT_SECONDS` | UI form loading timeout | `10` |

### Security Considerations

1. **Change the SECRET_KEY** in production
2. **Use HTTPS** in production
3. **Configure proper CORS** origins
4. **Set up rate limiting**
5. **Use strong passwords** for database
6. **Regular security updates**

## API Documentation

### Interactive Documentation
When running in debug mode, interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Complete API Reference
Comprehensive API documentation is available in multiple formats:

1. **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - 詳細なAPIリファレンス（日本語）
   - 全エンドポイントの詳細仕様
   - リクエスト/レスポンス例
   - OAuth 2.0フローの完全ガイド
   - セキュリティ考慮事項
   - エラーハンドリング
   - 本番環境設定

2. **[openapi_schema.json](./openapi_schema.json)** - OpenAPI 3.0仕様書
   - 機械可読なAPI仕様
   - Swagger UIやPostmanでインポート可能
   - 自動コード生成に対応

3. **[OIDC_Platform_API.postman_collection.json](./OIDC_Platform_API.postman_collection.json)** - Postmanコレクション
   - すぐに使えるAPIテストコレクション
   - 完全なOAuth 2.0フローテスト
   - エラーシナリオテスト
   - 自動テストスクリプト付き

### ドキュメントの使用方法

#### Postmanコレクションのインポート
```bash
# Postmanでコレクションをインポート
1. Postmanを開く
2. Import > File > OIDC_Platform_API.postman_collection.json を選択
3. 変数を確認・設定
4. テストを実行
```

#### OpenAPIスキーマの活用
```bash
# Swagger UIでスキーマを表示
npx swagger-ui-serve openapi_schema.json

# コード生成（例：JavaScript SDK）
npx @openapitools/openapi-generator-cli generate \
  -i openapi_schema.json \
  -g javascript \
  -o ./generated-sdk
```

## Database Management

### Using pgAdmin (included in Docker Compose)

1. Access pgAdmin at http://localhost:5050
2. Login with:
   - Email: `admin@oidc.local`
   - Password: `admin123`
3. Add server connection:
   - Host: `postgres`
   - Port: `5432`
   - Database: `oidc_db`
   - Username: `oidc_user`
   - Password: `oidc_password`

### Manual Database Operations

```bash
# Connect to database
docker exec -it oidc-postgres psql -U oidc_user -d oidc_db

# View tables
\dt

# View users
SELECT * FROM users;

# View OAuth2 clients
SELECT * FROM oauth2_clients;
```

## Testing

### Manual Testing

1. **Register a user**:
   - Go to http://localhost:8000/register
   - Create a new account

2. **Test OAuth2 flow**:
   - Use the authorization URL with sample client
   - Complete login and consent
   - Exchange code for tokens

3. **Test API endpoints**:
   ```bash
   # Discovery document
   curl http://localhost:8000/.well-known/openid-configuration
   
   # Health check
   curl http://localhost:8000/health
   ```

### Integration Testing

```bash
# Run with test client
python -m pytest tests/ -v
```

## Deployment

### Production Deployment

1. **Update environment variables**:
   ```bash
   # Use strong secrets
   SECRET_KEY=your-production-secret-key-here
   
   # Use HTTPS
   ISSUER=https://your-domain.com
   
   # Disable debug
   DEBUG=false
   ```

2. **Use production database**:
   ```bash
   DATABASE_URL=postgresql://user:password@prod-db:5432/oidc_db
   ```

3. **Deploy with Docker**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Kubernetes Deployment

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oidc-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: oidc-server
  template:
    metadata:
      labels:
        app: oidc-server
    spec:
      containers:
      - name: oidc-server
        image: oidc-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: oidc-secrets
              key: database-url
```

## Troubleshooting

### Common Issues

1. **Database connection failed**:
   - Check PostgreSQL is running
   - Verify connection string
   - Check network connectivity

2. **Token validation errors**:
   - Verify SECRET_KEY is consistent
   - Check token expiry
   - Validate JWKS endpoint

3. **CORS errors**:
   - Add client domain to `allowed_origins`
   - Check request headers

### Logs

```bash
# View application logs
docker-compose logs oidc-server

# View database logs
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f oidc-server
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs for error details
