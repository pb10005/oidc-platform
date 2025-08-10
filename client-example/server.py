#!/usr/bin/env python3
"""
Simple HTTP server for OIDC client example
"""
import http.server
import socketserver
import webbrowser
import os
import sys

# Try to read port from environment variable, fallback to default
PORT = int(os.environ.get('CLIENT_EXAMPLE_PORT', 3000))

class Handler(http.server.SimpleHTTPRequestHandler):
    """
    Custom HTTP request handler for serving static files and handling OIDC callback
    """
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def do_GET(self):
        # /callback パスの場合、index.html を提供（URLパラメータを保持）
        if self.path.startswith('/callback'):
            # URLパラメータを保持してindex.htmlにリダイレクト
            query_params = ''
            if '?' in self.path:
                query_params = self.path.split('?', 1)[1]
            self.path = '/index.html'
            if query_params:
                self.path += '?' + query_params
        super().do_GET()
    
    def end_headers(self):
        # CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def main():
    """
    Main function to start the HTTP server
    """
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🚀 OIDC Client Example サーバーを起動しました")
            print(f"📍 URL: http://localhost:{PORT}")
            print(f"📍 Callback URL: http://localhost:{PORT}/callback")
            print(f"🔗 ブラウザで http://localhost:{PORT} を開いてください")
            print(f"⚠️  終了するには Ctrl+C を押してください")
            print()
            
            # ブラウザを自動で開く
            try:
                webbrowser.open(f'http://localhost:{PORT}')
            except:
                pass
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しました")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ ポート {PORT} は既に使用されています")
            print(f"💡 他のアプリケーションを停止するか、別のポートを使用してください")
        else:
            print(f"❌ サーバー起動エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
