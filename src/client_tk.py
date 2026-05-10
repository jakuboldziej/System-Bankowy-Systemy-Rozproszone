import customtkinter as ctk
import json, socket
from tkinter import messagebox


class BankApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("System Bankowy")
        self.geometry("400x550")
        self.current_user = None
        self.show_login()

    def send_request(self, payload):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 5000))
            s.send(json.dumps(payload).encode("utf-8"))
            res = json.loads(s.recv(4096).decode("utf-8"))
            s.close()
            return res
        except:
            return {"status": "ERROR", "message": "Blad polaczenia"}

    def show_login(self):
        for w in self.winfo_children():
            w.destroy()
        self.u_e = ctk.CTkEntry(self, placeholder_text="Login")
        self.u_e.pack(pady=10)
        self.p_e = ctk.CTkEntry(self, placeholder_text="Haslo", show="*")
        self.p_e.pack(pady=10)
        ctk.CTkButton(self, text="Zaloguj", command=self.login).pack(pady=20)

    def login(self):
        res = self.send_request(
            {"action": "LOGIN", "username": self.u_e.get(), "password": self.p_e.get()}
        )
        if res.get("status") == "SUCCESS":
            self.current_user = {"id": res["user_id"], "role": res["role"]}
            self.show_dash()
        else:
            messagebox.showerror("Blad", "Niepoprawny login/haslo")

    def show_dash(self):
        if not self.current_user:
            self.show_login()
            return
        for w in self.winfo_children():
            w.destroy()
        res = self.send_request(
            {"action": "GET_BALANCE", "user_id": self.current_user["id"]}
        )
        bal = res.get("balance", 0.0)
        ctk.CTkLabel(self, text=f"Saldo: {bal} PLN", font=("Roboto", 20)).pack(pady=20)
        ctk.CTkButton(self, text="Przelew", command=self.do_transfer).pack(pady=5)
        ctk.CTkButton(self, text="Logi", command=self.show_logs).pack(pady=5)
        ctk.CTkButton(self, text="Wyloguj", command=self.logout).pack(pady=20)

    def logout(self):
        self.current_user = None
        self.show_login()

    def do_transfer(self):
        f = ctk.CTkInputDialog(text="Numer konta nadawcy:", title="Przelew").get_input()
        t = ctk.CTkInputDialog(
            text="Numer konta odbiorcy:", title="Przelew"
        ).get_input()
        a = ctk.CTkInputDialog(text="Kwota:", title="Przelew").get_input()
        if f and t and a:
            res = self.send_request(
                {"action": "TRANSFER", "from": f, "to": t, "amount": a}
            )
            messagebox.showinfo("Info", res.get("message"))
            self.show_dash()

    def show_logs(self):
        if not self.current_user:
            return
        win = ctk.CTkToplevel(self)
        win.attributes("-topmost", True)
        txt = ctk.CTkTextbox(win, width=400, height=300)
        txt.pack()
        res = self.send_request(
            {
                "action": "GET_LOGS",
                "user_id": self.current_user["id"],
                "role": self.current_user["role"],
            }
        )
        for l in res.get("logs", []):
            txt.insert("end", f"[{l[0]}] {l[1]} | {l[2]} PLN\n")


if __name__ == "__main__":
    BankApp().mainloop()
