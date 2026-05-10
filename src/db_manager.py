import sqlite3, bcrypt, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bank.db")


class DBManager:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, full_name TEXT, pesel TEXT UNIQUE, role TEXT, is_active INTEGER DEFAULT 1)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, account_number TEXT UNIQUE, user_id INTEGER, balance REAL DEFAULT 0.0, FOREIGN KEY(user_id) REFERENCES users(id))"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER, operation_type TEXT, amount REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        self.conn.commit()

    def register_user(self, u, p, n, ps, role="user"):
        try:
            pw_hash = bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, pesel, role) VALUES (?, ?, ?, ?, ?)",
                (u, pw_hash, n, ps, role),
            )
            uid = cursor.lastrowid
            cursor.execute(
                "INSERT INTO accounts (account_number, user_id, balance) VALUES (?, ?, 1000.0)",
                (f"100{uid}", uid),
            )
            self.conn.commit()
            return True
        except:
            return False

    def process_transfer(self, s_acc, r_acc, amt):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT balance, id FROM accounts WHERE account_number = ?", (s_acc,)
            )
            s = cursor.fetchone()
            if not s or s[0] < amt:
                return False, "Brak srodkow"
            cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (r_acc,))
            if not cursor.fetchone():
                return False, "Odbiorca nie istnieje"
            cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE account_number = ?",
                (amt, s_acc),
            )
            cursor.execute(
                "UPDATE accounts SET balance = balance + ? WHERE account_number = ?",
                (amt, r_acc),
            )
            cursor.execute(
                "INSERT INTO logs (account_id, operation_type, amount) VALUES (?, ?, ?)",
                (s[1], f"TO {r_acc}", amt),
            )
            self.conn.commit()
            return True, "Sukces"
        except:
            return False, "Blad transakcji"
