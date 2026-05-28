import customtkinter as ctk
import json, socket
from tkinter import messagebox


class BankApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("System Bankowy TK/TB")
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
            return {"status": "ERROR", "message": "Blad polaczenia z serwerem"}

    def show_login(self):
        for w in self.winfo_children():
            w.destroy()

        ctk.CTkLabel(self, text="Logowanie", font=("Roboto", 24)).pack(pady=20)
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
            self.current_user = {
                "id": res["user_id"],
                "role": res["role"],
                "account_number": None,
            }
            self.show_dash()
        else:
            messagebox.showerror("Blad", res.get("message", "Niepoprawny login/haslo"))

    def show_dash(self):
        user = self.current_user
        if not user:
            self.show_login()
            return

        for w in self.winfo_children():
            w.destroy()

        res = self.send_request({"action": "GET_BALANCE", "user_id": user["id"]})
        if res.get("status") == "SUCCESS":
            bal = res.get("balance", 0.0)
            user["account_number"] = res.get("account_number")
        else:
            bal = 0.0

        ctk.CTkLabel(
            self, text=f"Twoje konto: {user['account_number']}", font=("Roboto", 14)
        ).pack(pady=10)
        ctk.CTkLabel(
            self,
            text=f"Saldo: {bal} PLN",
            font=("Roboto", 24, "bold"),
            text_color="green",
        ).pack(pady=10)

        ctk.CTkButton(self, text="Przelew", command=self.do_transfer).pack(pady=10)
        ctk.CTkButton(self, text="Historia (Logi)", command=self.show_logs).pack(
            pady=10
        )

        if user.get("role") == "admin":
            ctk.CTkLabel(self, text="--- PANEL BANKIERA ---", text_color="red").pack(
                pady=(20, 5)
            )
            ctk.CTkButton(
                self,
                text="Zarządzaj Klientami",
                fg_color="red",
                hover_color="darkred",
                command=self.show_admin_panel,
            ).pack(pady=5)

        ctk.CTkButton(self, text="Wyloguj", command=self.logout, fg_color="gray").pack(
            pady=30
        )

    def logout(self):
        self.current_user = None
        self.show_login()

    def do_transfer(self):
        user = self.current_user
        if not user:
            return

        t = ctk.CTkInputDialog(
            text="Numer konta odbiorcy:", title="Przelew"
        ).get_input()
        a = ctk.CTkInputDialog(text="Kwota:", title="Przelew").get_input()

        if t and a:
            res = self.send_request(
                {
                    "action": "TRANSFER",
                    "from": user["account_number"],
                    "to": t,
                    "amount": a,
                }
            )
            messagebox.showinfo("Info", res.get("message"))
            self.show_dash()

    def show_logs(self):
        user = self.current_user
        if not user:
            return

        win = ctk.CTkToplevel(self)
        win.title("Logi operacji")
        win.geometry("450x350")
        win.attributes("-topmost", True)

        txt = ctk.CTkTextbox(win, width=430, height=330)
        txt.pack(pady=10)

        res = self.send_request(
            {
                "action": "GET_LOGS",
                "user_id": user["id"],
                "role": user["role"],
            }
        )

        for l in res.get("logs", []):
            txt.insert("end", f"[{l[0]}] {l[3]} | {l[1]} | {l[2]} PLN\n")

    def show_admin_panel(self):
        user = self.current_user
        if not user or user["role"] != "admin":
            return

        win = ctk.CTkToplevel(self)
        win.title("Zarządzanie Klientami")
        win.geometry("300x300")
        win.attributes("-topmost", True)

        def btn_register():
            u = ctk.CTkInputDialog(
                text="Podaj nowy login:", title="Rejestracja"
            ).get_input()
            p = ctk.CTkInputDialog(text="Podaj hasło:", title="Rejestracja").get_input()
            n = ctk.CTkInputDialog(
                text="Podaj imię i nazwisko:", title="Rejestracja"
            ).get_input()
            pe = ctk.CTkInputDialog(
                text="Podaj PESEL:", title="Rejestracja"
            ).get_input()
            if u and p and n and pe:
                r = self.send_request(
                    {
                        "action": "ADMIN_REGISTER",
                        "role": "admin",
                        "username": u,
                        "password": p,
                        "full_name": n,
                        "pesel": pe,
                    }
                )
                messagebox.showinfo(
                    "Info", r.get("message", f"Status: {r.get('status')}")
                )

        def btn_edit():
            u = ctk.CTkInputDialog(
                text="Podaj login klienta do edycji:", title="Edycja"
            ).get_input()
            n = ctk.CTkInputDialog(
                text="Nowe imię i nazwisko:", title="Edycja"
            ).get_input()
            pe = ctk.CTkInputDialog(text="Nowy PESEL:", title="Edycja").get_input()
            if u and n and pe:
                r = self.send_request(
                    {
                        "action": "ADMIN_UPDATE",
                        "role": "admin",
                        "target_username": u,
                        "new_name": n,
                        "new_pesel": pe,
                    }
                )
                messagebox.showinfo("Info", f"Status: {r.get('status')}")

        def btn_delete():
            u = ctk.CTkInputDialog(
                text="Podaj login klienta do DEZAKTYWACJI (Soft Delete):",
                title="Usuwanie",
            ).get_input()
            if u:
                r = self.send_request(
                    {
                        "action": "ADMIN_DEACTIVATE",
                        "role": "admin",
                        "target_username": u,
                    }
                )
                messagebox.showinfo("Info", f"Status: {r.get('status')}")

        ctk.CTkButton(win, text="Zarejestruj Nowego", command=btn_register).pack(
            pady=10
        )
        ctk.CTkButton(win, text="Edytuj Dane Klienta", command=btn_edit).pack(pady=10)
        ctk.CTkButton(
            win,
            text="Dezaktywuj Klienta",
            fg_color="darkred",
            hover_color="red",
            command=btn_delete,
        ).pack(pady=10)


if __name__ == "__main__":
    BankApp().mainloop()
