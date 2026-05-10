import threading, json, socket, time


def run_test(name, f, t, a):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 5000))
        s.send(
            json.dumps({"action": "TRANSFER", "from": f, "to": t, "amount": a}).encode(
                "utf-8"
            )
        )
        res = json.loads(s.recv(4096).decode("utf-8"))
        print(f"[{name}] {res.get('message')}")
        s.close()
    except Exception as e:
        print(f"[{name}] Blad: {e}")


if __name__ == "__main__":
    threads = [
        threading.Thread(target=run_test, args=(f"T{i}", "1002", "1003", 10))
        for i in range(5)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
