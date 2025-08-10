# OIDC Authentication Server - API Documentation

## 概要

このドキュメントは、OIDC Authentication Serverが提供するすべてのAPIエンドポイントの詳細な仕様を説明します。このサーバーは、OpenID Connect 1.0およびOAuth 2.0仕様に準拠した認証・認可サービスを提供します。

## ベースURL

```
http://localhost:8000
```

本番環境では、適切なHTTPSドメインに置き換えてください。

## 認証方式

### セッション認証
- Webインターフェース用
- HTTPOnlyクッキーを使用

### Bearer Token認証
- API用
- `Authorization: Bearer <access_token>` ヘッダーを使用

## エラーレスポンス

すべてのAPIエンドポイントは、エラー時に以下の形式でレスポンスを返します：

```json
{
  "detail": "エラーメッセージ"
}
```

一般的なHTTPステータスコード：
- `400 Bad Request`: 不正なリクエストパラメータ
- `401 Unauthorized`: 認証が必要または無効
- `403 Forbidden`: アクセス権限なし
- `404 Not Found`: リソースが見つからない
- `500 Internal Server Error`: サーバー内部エラー

---

## 1. システム情報エンドポイント

### 1.1 ヘルスチェック

サーバーの稼働状況を確認します。

**エンドポイント:** `GET /health`

**レスポンス:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 1.2 クライアント設定取得

フロントエンドアプリケーション用の設定情報を取得します。

**エンドポイント:** `GET /config`

**レスポンス:**
```json
{
  "issuer": "http://localhost:8000",
  "clientId": "sample-client",
  "clientSecret": "sample-secret",
  "redirectUris": [
    "http://localhost:3000/callback",
    "http://localhost:8080/callback"
  ],
  "scopes": ["openid", "profile", "email"],
  "alertAutoHideSeconds": 5,
  "formLoadingTimeoutSeconds": 10,
  "clientExamplePort": 3000
}
```

---

## 2. OpenID Connect Discovery

### 2.1 Discovery Document

OpenID Connect Discovery仕様に準拠した設定情報を提供します。

**エンドポイント:** `GET /.well-known/openid-configuration`

**レスポンス:**
```json
{
  "issuer": "http://localhost:8000",
  "authorization_endpoint": "http://localhost:8000/oauth2/authorize",
  "token_endpoint": "http://localhost:8000/oauth2/token",
  "userinfo_endpoint": "http://localhost:8000/oauth2/userinfo",
  "jwks_uri": "http://localhost:8000/jwks",
  "scopes_supported": ["openid", "profile", "email"],
  "response_types_supported": ["code"],
  "response_modes_supported": ["query"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["HS256"],
  "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
  "code_challenge_methods_supported": ["S256", "plain"],
  "claims_supported": [
    "sub", "iss", "aud", "exp", "iat", "auth_time",
    "name", "given_name", "family_name", "email", "email_verified"
  ]
}
```

### 2.2 JSON Web Key Set (JWKS)

トークン検証用の公開鍵情報を提供します。

**エンドポイント:** `GET /jwks`

**レスポンス:**
```json
{
  "keys": [
    {
      "kty": "oct",
      "use": "sig",
      "kid": "1",
      "alg": "HS256"
    }
  ]
}
```

---

## 3. 認証エンドポイント

### 3.1 ログインページ表示

ユーザーログイン用のHTMLページを表示します。

**エンドポイント:** `GET /login`

**クエリパラメータ:**
- `redirect_uri` (optional): ログイン後のリダイレクト先URL

**レスポンス:** HTML ページ

### 3.2 ログイン処理

ユーザーの認証を行います。

**エンドポイント:** `POST /login`

**Content-Type:** `application/x-www-form-urlencoded`

**パラメータ:**
- `email` (required): ユーザーのメールアドレス
- `password` (required): パスワード
- `redirect_uri` (optional): ログイン後のリダイレクト先URL

**成功時:** 指定されたURLまたは `/` にリダイレクト
**失敗時:** エラーメッセージ付きでログインページを再表示

### 3.3 ユーザー登録ページ表示

新規ユーザー登録用のHTMLページを表示します。

**エンドポイント:** `GET /register`

**レスポンス:** HTML ページ

### 3.4 ユーザー登録処理

新規ユーザーを登録します。

**エンドポイント:** `POST /register`

**Content-Type:** `application/x-www-form-urlencoded`

**パラメータ:**
- `email` (required): メールアドレス
- `password` (required): パスワード
- `confirm_password` (required): パスワード確認
- `first_name` (required): 名前
- `last_name` (required): 姓

**成功時:** `/login` にリダイレクト
**失敗時:** エラーメッセージ付きで登録ページを再表示

### 3.5 ログアウト

ユーザーセッションを終了します。

**エンドポイント:** `GET /logout`

**レスポンス:** `/login` にリダイレクト

---

## 4. OAuth 2.0 / OpenID Connect エンドポイント

### 4.1 認可エンドポイント

OAuth 2.0 Authorization Code Flowの開始点です。

**エンドポイント:** `GET /oauth2/authorize`

**クエリパラメータ:**
- `response_type` (required): `code` のみサポート
- `client_id` (required): クライアントID
- `redirect_uri` (required): コールバックURL
- `scope` (required): 要求するスコープ（例: `openid profile email`）
- `state` (optional): CSRF攻撃防止用のランダム文字列
- `code_challenge` (optional): PKCE用のコードチャレンジ
- `code_challenge_method` (optional): `S256` または `plain`
- `nonce` (optional): リプレイ攻撃防止用

**レスポンス:**
- 未認証の場合: ログインページにリダイレクト
- 認証済みの場合: 同意ページを表示

**例:**
```
GET /oauth2/authorize?response_type=code&client_id=sample-client&redirect_uri=http://localhost:3000/callback&scope=openid%20profile%20email&state=xyz&code_challenge=abc&code_challenge_method=S256
```

### 4.2 同意処理

ユーザーの同意を処理します。

**エンドポイント:** `POST /auth/consent`

**Content-Type:** `application/x-www-form-urlencoded`

**パラメータ:**
- `action` (required): `allow` または `deny`
- `response_type` (required): `code`
- `client_id` (required): クライアントID
- `redirect_uri` (required): コールバックURL
- `scope` (required): 要求するスコープ
- `state` (optional): 状態パラメータ
- `code_challenge` (optional): PKCEコードチャレンジ
- `code_challenge_method` (optional): PKCEメソッド
- `nonce` (optional): ナンス

**成功時（allow）:**
```
HTTP/1.1 302 Found
Location: http://localhost:3000/callback?code=AUTH_CODE&state=xyz
```

**拒否時（deny）:**
```
HTTP/1.1 302 Found
Location: http://localhost:3000/callback?error=access_denied&state=xyz
```

### 4.3 トークンエンドポイント

認可コードをアクセストークンに交換します。

**エンドポイント:** `POST /oauth2/token`

**Content-Type:** `application/x-www-form-urlencoded`

**パラメータ:**
- `grant_type` (required): `authorization_code`
- `code` (required): 認可コード
- `redirect_uri` (required): 認可時と同じリダイレクトURI
- `client_id` (required): クライアントID
- `client_secret` (optional): クライアントシークレット（機密クライアントの場合）
- `code_verifier` (optional): PKCEコードベリファイア

**成功レスポンス:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 1800,
  "refresh_token": "def50200...",
  "scope": "openid profile email",
  "id_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**エラーレスポンス:**
```json
{
  "error": "invalid_grant",
  "error_description": "Invalid authorization code"
}
```

### 4.4 UserInfo エンドポイント

アクセストークンを使用してユーザー情報を取得します。

**エンドポイント:** `GET /oauth2/userinfo`

**ヘッダー:**
```
Authorization: Bearer <access_token>
```

**成功レスポンス:**
```json
{
  "sub": "123",
  "name": "田中 太郎",
  "given_name": "太郎",
  "family_name": "田中",
  "email": "tanaka@example.com",
  "email_verified": true
}
```

---

## 5. ユーザー管理API

### 5.1 現在のユーザー情報取得

認証済みユーザーの情報を取得します。

**エンドポイント:** `GET /api/users/me`

**認証:** セッション認証が必要

**成功レスポンス:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "太郎",
  "last_name": "田中",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 5.2 ユーザー情報取得（ID指定）

指定されたIDのユーザー情報を取得します。

**エンドポイント:** `GET /api/users/{user_id}`

**パスパラメータ:**
- `user_id`: ユーザーID

**認証:** セッション認証が必要（自分の情報のみアクセス可能）

**成功レスポンス:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "太郎",
  "last_name": "田中",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## 6. 完全なOAuth 2.0フロー例

### 6.1 Authorization Code Flow with PKCE

```javascript
// 1. PKCEパラメータ生成
const codeVerifier = generateRandomString(128);
const codeChallenge = await sha256(codeVerifier);

// 2. 認可エンドポイントにリダイレクト
const authUrl = new URL('http://localhost:8000/oauth2/authorize');
authUrl.searchParams.set('response_type', 'code');
authUrl.searchParams.set('client_id', 'sample-client');
authUrl.searchParams.set('redirect_uri', 'http://localhost:3000/callback');
authUrl.searchParams.set('scope', 'openid profile email');
authUrl.searchParams.set('state', generateRandomString(32));
authUrl.searchParams.set('code_challenge', codeChallenge);
authUrl.searchParams.set('code_challenge_method', 'S256');

window.location.href = authUrl.toString();

// 3. コールバック処理（認可コード受信）
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
const state = urlParams.get('state');

// 4. トークン交換
const tokenResponse = await fetch('http://localhost:8000/oauth2/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: code,
    redirect_uri: 'http://localhost:3000/callback',
    client_id: 'sample-client',
    code_verifier: codeVerifier,
  }),
});

const tokens = await tokenResponse.json();

// 5. ユーザー情報取得
const userInfoResponse = await fetch('http://localhost:8000/oauth2/userinfo', {
  headers: {
    'Authorization': `Bearer ${tokens.access_token}`,
  },
});

const userInfo = await userInfoResponse.json();
```

### 6.2 IDトークン検証

```javascript
import jwt from 'jsonwebtoken';

// JWKSから公開鍵を取得
const jwksResponse = await fetch('http://localhost:8000/jwks');
const jwks = await jwksResponse.json();

// IDトークンを検証
try {
  const decoded = jwt.verify(tokens.id_token, secret, {
    algorithms: ['HS256'],
    audience: 'sample-client',
    issuer: 'http://localhost:8000',
  });
  
  console.log('User ID:', decoded.sub);
  console.log('User Name:', decoded.name);
  console.log('Email:', decoded.email);
} catch (error) {
  console.error('Token validation failed:', error);
}
```

---

## 7. セキュリティ考慮事項

### 7.1 PKCE (Proof Key for Code Exchange)

すべてのクライアントでPKCEの使用を強く推奨します：

```javascript
// コードベリファイア生成（43-128文字のランダム文字列）
const codeVerifier = base64URLEncode(crypto.getRandomValues(new Uint8Array(32)));

// コードチャレンジ生成
const codeChallenge = base64URLEncode(await crypto.subtle.digest('SHA-256', 
  new TextEncoder().encode(codeVerifier)));
```

### 7.2 State パラメータ

CSRF攻撃を防ぐため、必ずstateパラメータを使用してください：

```javascript
const state = base64URLEncode(crypto.getRandomValues(new Uint8Array(32)));
// 認可リクエスト時にstateを送信
// コールバック時にstateを検証
```

### 7.3 Nonce パラメータ

リプレイ攻撃を防ぐため、OpenIDスコープを使用する場合はnonceを使用してください：

```javascript
const nonce = base64URLEncode(crypto.getRandomValues(new Uint8Array(32)));
// IDトークン内のnonceクレームを検証
```

---

## 8. エラーコード一覧

### 8.1 OAuth 2.0 エラー

| エラーコード | 説明 |
|-------------|------|
| `invalid_request` | リクエストパラメータが不正 |
| `unauthorized_client` | クライアントが認可されていない |
| `access_denied` | ユーザーがアクセスを拒否 |
| `unsupported_response_type` | サポートされていないレスポンスタイプ |
| `invalid_scope` | 不正なスコープ |
| `server_error` | サーバー内部エラー |
| `temporarily_unavailable` | サーバーが一時的に利用不可 |

### 8.2 トークンエンドポイントエラー

| エラーコード | 説明 |
|-------------|------|
| `invalid_request` | リクエストパラメータが不正 |
| `invalid_client` | クライアント認証に失敗 |
| `invalid_grant` | 認可コードが無効または期限切れ |
| `unauthorized_client` | クライアントが認可されていない |
| `unsupported_grant_type` | サポートされていないグラントタイプ |
| `invalid_scope` | 不正なスコープ |

---

## 9. レート制限

現在のバージョンではレート制限は実装されていませんが、本番環境では以下の制限を推奨します：

- 認証エンドポイント: 1分間に10リクエスト/IP
- トークンエンドポイント: 1分間に60リクエスト/クライアント
- UserInfoエンドポイント: 1分間に100リクエスト/トークン

---

## 10. サンプルクライアント

### 10.1 デフォルト設定

サーバー起動時に自動的に作成されるサンプルクライアント：

```json
{
  "client_id": "sample-client",
  "client_secret": "sample-secret",
  "name": "Sample OIDC Client",
  "redirect_uris": [
    "http://localhost:3000/callback",
    "http://localhost:8080/callback"
  ],
  "scopes": ["openid", "profile", "email"],
  "client_type": "confidential"
}
```

### 10.2 サンプルクライアントの実行

```bash
# サンプルクライアントを起動
cd client-example
python3 server.py

# ブラウザでアクセス
open http://localhost:3000
```

---

## 11. トラブルシューティング

### 11.1 よくある問題

**問題:** `invalid_client` エラー
**解決:** クライアントIDとシークレットを確認

**問題:** `invalid_redirect_uri` エラー
**解決:** リダイレクトURIがクライアント設定と一致するか確認

**問題:** `invalid_grant` エラー
**解決:** 認可コードの有効期限（通常10分）を確認

**問題:** CORS エラー
**解決:** `allowed_origins` 設定にクライアントドメインを追加

### 11.2 ログの確認

```bash
# アプリケーションログ
docker-compose logs oidc-server

# リアルタイムログ
docker-compose logs -f oidc-server
```

---

## 12. 本番環境での設定

### 12.1 必須の環境変数

```bash
# セキュリティ
SECRET_KEY=your-production-secret-key-here
DEBUG=false

# HTTPS設定
ISSUER=https://your-domain.com

# データベース
DATABASE_URL=postgresql://user:password@prod-db:5432/oidc_db

# CORS
ALLOWED_ORIGINS=["https://your-client-app.com"]
```

### 12.2 セキュリティチェックリスト

- [ ] SECRET_KEYを本番用の強力なキーに変更
- [ ] HTTPSを有効化
- [ ] データベースパスワードを強力なものに変更
- [ ] CORS設定を本番ドメインに限定
- [ ] レート制限を実装
- [ ] ログ監視を設定
- [ ] 定期的なセキュリティ更新

---

このAPIドキュメントは、OIDC Authentication Serverの完全な機能を網羅しています。追加の質問や詳細な実装例が必要な場合は、お気軽にお問い合わせください。
