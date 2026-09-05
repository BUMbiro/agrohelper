import http.server
import socketserver
import urllib.parse
import os
import re

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

ROUTES = {
    '/': 'index.html',
    '/declaration': 'declaration.html',
    '/training': 'training.html',
    '/knowledge': 'knowledge.html',
    '/blog': 'blog.html',
    '/contacts': 'contacts.html',
}


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    # noinspection PyPep8Naming
    def log_message(self, fmt: str, *args):
        pass

    @staticmethod
    def render_template(template_name: str) -> str:
        filepath = os.path.join(TEMPLATES_DIR, template_name)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return f"<h1>404 - Template {template_name} not found</h1>"

        extends_match = re.search(r'{%\s*extends\s*"([^"]+)"\s*%}', content)
        if extends_match:
            base_name = extends_match.group(1)
            base_path = os.path.join(TEMPLATES_DIR, base_name)
            try:
                with open(base_path, 'r', encoding='utf-8') as f:
                    base_content = f.read()
            except FileNotFoundError:
                return f"<h1>404 - Base template {base_name} not found</h1>"

            blocks = {}
            for match in re.finditer(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', content, re.DOTALL):
                block_name = match.group(1)
                block_content = match.group(2)
                blocks[block_name] = block_content

            def replace_block(m):
                name = m.group(1)
                return blocks.get(name, m.group(2))

            result = re.sub(r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}', replace_block, base_content, flags=re.DOTALL)
            result = re.sub(r'{%\s*block\s+\w+\s*%}', '', result)
            result = re.sub(r'{%\s*endblock\s*%}', '', result)
            return result
        else:
            return content

    # noinspection PyPep8Naming
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith('/static/'):
            self.serve_static(path)
            return

        if path in ROUTES:
            html = self.render_template(ROUTES[path])
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            html = self.render_template('404.html')
            self.send_response(404)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

    # noinspection PyPep8Naming
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = urllib.parse.parse_qs(post_data.decode('utf-8'))

            print("\n" + "=" * 40)
            print(f"📩 Получен POST-запрос на {path}:")
            for key, value in data.items():
                print(f"  {key}: {value[0]}")
            print("=" * 40 + "\n")

            if path == '/declaration':
                self.send_response(303)
                self.send_header('Location', '/declaration')
                self.end_headers()
            elif path == '/training':
                self.send_response(303)
                self.send_header('Location', '/training')
                self.end_headers()
            elif path == '/contacts':
                self.send_response(303)
                self.send_header('Location', '/contacts')
                self.end_headers()
            else:
                html = self.render_template('404.html')
                self.send_response(404)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
        except (ValueError, KeyError, IndexError, TypeError) as e:
            print(f"Ошибка при обработке POST: {e}")
            html = self.render_template('500.html')
            self.send_response(500)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            html = self.render_template('500.html')
            self.send_response(500)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

    def serve_static(self, path):
        filepath = os.path.join(BASE_DIR, path[1:])
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            ext = os.path.splitext(filepath)[1].lower()
            content_type = {
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.svg': 'image/svg+xml',
            }.get(ext, 'application/octet-stream')
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
        except (OSError, PermissionError) as e:
            print(f"Ошибка при обслуживании статики: {e}")
            self.send_response(500)
            self.end_headers()


def run():
    try:
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:  # type: ignore[arg-type]
            print(f"🚀 Сервер запущен на http://localhost:{PORT}")
            print("Нажмите Ctrl+C для остановки")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
    except Exception as e:
        print(f"Ошибка запуска сервера: {e}")


if __name__ == "__main__":
    run()
