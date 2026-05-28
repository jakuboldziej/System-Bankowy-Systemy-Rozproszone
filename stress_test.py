import threading, json, socket, time, random


def send_request(payload):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 5000))
        s.send(json.dumps(payload).encode("utf-8"))
        res = json.loads(s.recv(4096).decode("utf-8"))
        s.close()
        return res
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def client_routine(client_name, username, password, target_acc, transfer_amt):
    print(f"[{client_name}] Rozpoczynam symulacje...")
    time.sleep(random.uniform(0.5, 2.0))

    # 1. Logowanie
    print(f"[{client_name}] Proba logowania...")
    auth = send_request({"action": "LOGIN", "username": username, "password": password})

    if auth.get("status") != "SUCCESS":
        print(f"[{client_name}] Logowanie nieudane!")
        return
    user_id = auth["user_id"]

    time.sleep(random.uniform(0.2, 1.0))

    print(f"[{client_name}] Pobieram balans...")
    bal_res = send_request({"action": "GET_BALANCE", "user_id": user_id})
    my_account = bal_res.get("account_number")

    time.sleep(random.uniform(0.5, 1.5))

    if my_account:
        print(
            f"[{client_name}] Wykonuje przelew na {target_acc} ({transfer_amt} PLN)..."
        )
        res = send_request(
            {
                "action": "TRANSFER",
                "from": my_account,
                "to": target_acc,
                "amount": transfer_amt,
            }
        )
        print(
            f"[{client_name}] Wynik przelewu: {res.get('status')} - {res.get('message')}"
        )

    time.sleep(random.uniform(0.1, 0.5))

    print(f"[{client_name}] Pobieram logi...")
    logs = send_request({"action": "GET_LOGS", "user_id": user_id, "role": "user"})
    print(f"[{client_name}] Zakończono. Pobrano {len(logs.get('logs', []))} logów.")


if __name__ == "__main__":
    print("Start automatycznych testów dla 3 klientów jednoczesnie...\n")

    threads = [
        threading.Thread(
            target=client_routine, args=("KLIENT_A", "user1", "user123", "1003", 50)
        ),
        threading.Thread(
            target=client_routine, args=("KLIENT_B", "user2", "user222", "1002", 15)
        ),
        threading.Thread(
            target=client_routine, args=("KLIENT_C", "admin", "admin123", "1002", 9999)
        ),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("\nTesty automatyczne zakończone.")
