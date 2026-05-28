import socket, threading, json, bcrypt
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
        print(f"[*] Serwer wystartowal na {self.host}:{self.port}")

        try:
            self.db.register_user(
                "admin", "admin123", "Główny Admin", "00000000000", "admin"
            )
            self.db.register_user(
                "user1", "user123", "Jan Kowalski", "11111111111", "user"
            )
            self.db.register_user(
                "user2", "user222", "Anna Nowak", "22222222222", "user"
            )
        except:
            pass

        while True:
            c, addr = self.s.accept()
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
                "SELECT password_hash, role, id, is_active FROM users WHERE username = ?",
                (req.get("username"),),
            )
            u = cursor.fetchone()
            if u and bcrypt.checkpw(
                req.get("password").encode("utf-8"), u[0].encode("utf-8")
            ):
                if u[3] == 0:
                    return {
                        "status": "ERROR",
                        "message": "Konto zostalo usuniete/dezaktywowane.",
                    }
                return {"status": "SUCCESS", "role": u[1], "user_id": u[2]}
            return {"status": "ERROR", "message": "Bledne dane logowania."}

        with self.lock:
            if act == "TRANSFER":
                s, m = self.db.process_transfer(
                    req.get("from"), req.get("to"), float(req.get("amount"))
                )
                return {"status": "SUCCESS" if s else "ERROR", "message": m}

            if act == "GET_BALANCE":
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "SELECT balance, account_number FROM accounts WHERE user_id = ?",
                    (req.get("user_id"),),
                )
                b = cursor.fetchone()
                if b:
                    return {
                        "status": "SUCCESS",
                        "balance": b[0],
                        "account_number": b[1],
                    }
                return {"status": "ERROR", "message": "Nie znaleziono konta."}

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

            if act == "ADMIN_REGISTER" and req.get("role") == "admin":
                ok, msg = self.db.register_user(
                    req["username"], req["password"], req["full_name"], req["pesel"]
                )
                return {
                    "status": "SUCCESS" if ok else "ERROR",
                    "message": "Zarejestrowano poprawnie" if ok else msg,
                }

            if act == "ADMIN_UPDATE" and req.get("role") == "admin":
                ok = self.db.update_user(
                    req["target_username"], req["new_name"], req["new_pesel"]
                )
                return {"status": "SUCCESS" if ok else "ERROR"}

            if act == "ADMIN_DEACTIVATE" and req.get("role") == "admin":
                ok = self.db.deactivate_user(req["target_username"])
                return {"status": "SUCCESS" if ok else "ERROR"}

        return {"status": "ERROR", "message": "Nieznana akcja"}


if __name__ == "__main__":
    BankServer().start()
