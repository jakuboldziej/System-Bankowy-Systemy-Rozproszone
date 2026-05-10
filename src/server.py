import socket, threading, json
from db_manager import DBManager


class BankServer:
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.db = DBManager()
        self.lock = threading.Lock()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.s.bind((self.host, self.port))
        self.s.listen(10)

        print(f"[*] Serwer wystartował: {self.host}:{self.port}")

        while True:
            c, _ = self.s.accept()
            threading.Thread(target=self.handle, args=(c,)).start()

    def handle(self, c):
        try:
            while True:
                data = c.recv(4096).decode("utf-8")
                if not data:
                    break
                req = json.loads(data)
                res = self.process(req)
                c.send(json.dumps(res).encode("utf-8"))
        except:
            pass
        finally:
            c.close()

    def process(self, req):
        act = req.get("action")
        if act == "LOGIN":
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT password_hash, role, id FROM users WHERE username = ?",
                (req.get("username"),),
            )
            u = cursor.fetchone()
            if u and bcrypt.checkpw(
                req.get("password").encode("utf-8"), u[0].encode("utf-8")
            ):
                return {"status": "SUCCESS", "role": u[1], "user_id": u[2]}
            return {"status": "ERROR", "message": "Bledne dane"}

        with self.lock:
            if act == "TRANSFER":
                s, m = self.db.process_transfer(
                    req.get("from"), req.get("to"), float(req.get("amount"))
                )
                return {"status": "SUCCESS" if s else "ERROR", "message": m}
            if act == "GET_BALANCE":
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "SELECT balance FROM accounts WHERE user_id = ?",
                    (req.get("user_id"),),
                )
                b = cursor.fetchone()
                return {"status": "SUCCESS", "balance": b[0] if b else 0.0}
            if act == "GET_LOGS":
                cursor = self.db.conn.cursor()
                if req.get("role") == "admin":
                    cursor.execute(
                        "SELECT l.timestamp, l.operation_type, l.amount, a.account_number FROM logs l JOIN accounts a ON l.account_id = a.id ORDER BY l.timestamp DESC"
                    )
                else:
                    cursor.execute(
                        "SELECT l.timestamp, l.operation_type, l.amount, a.account_number FROM logs l JOIN accounts a ON l.account_id = a.id WHERE a.user_id = ? ORDER BY l.timestamp DESC",
                        (req.get("user_id"),),
                    )
                return {"status": "SUCCESS", "logs": cursor.fetchall()}
        return {"status": "ERROR"}


if __name__ == "__main__":
    import bcrypt

    BankServer().start()
