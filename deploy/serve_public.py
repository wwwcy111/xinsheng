"""同源反向代理：托管前端 dist，并将 /api、/uploads 转发到 FastAPI。

用法：
    python serve_public.py
然后访问 http://127.0.0.1:8080
"""

import http.server
import urllib.error
import urllib.request
from pathlib import Path

DIST = Path(r"D:\APP\HUA Agent\项目\kaifa\frontend\dist")
BACKEND = "http://127.0.0.1:8000"
PORT = 8080


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    def _proxy(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {}
        for key, value in self.headers.items():
            if key.lower() in {"host", "connection", "accept-encoding"}:
                continue
            headers[key] = value

        request = urllib.request.Request(BACKEND + self.path, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() in {"content-length", "transfer-encoding", "connection", "content-encoding"}:
                        continue
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as error:
            data = error.read()
            self.send_response(error.code)
            self.send_header("Content-Type", error.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as error:  # noqa: BLE001
            message = str(error).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

    def do_GET(self):
        if self.path.startswith(("/api/", "/uploads/")):
            return self._proxy()
        rel = self.path.split("?")[0].lstrip("/")
        target = (DIST / rel).resolve()
        if rel and target.is_file():
            return super().do_GET()
        # 单页应用路由回退
        self.path = "/index.html"
        return super().do_GET()

    def do_HEAD(self):
        if self.path.startswith(("/api/", "/uploads/")):
            return self._proxy()
        return super().do_HEAD()

    def do_POST(self):
        return self._proxy()

    def do_PUT(self):
        return self._proxy()

    def do_PATCH(self):
        return self._proxy()

    def do_DELETE(self):
        return self._proxy()

    def do_OPTIONS(self):
        return self._proxy()


class Server(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"STATIC {DIST}", flush=True)
    print(f"API {BACKEND}", flush=True)
    print(f"LISTEN 0.0.0.0:{PORT}", flush=True)
    Server(("0.0.0.0", PORT), Handler).serve_forever()