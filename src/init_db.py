from db_manager import DBManager


def seed():
    db = DBManager()
    db.register_user("admin", "admin123", "Główny Admin", "00000000000", "admin")
    db.register_user("user1", "user123", "Jan Kowalski", "11111111111", "user")
    db.register_user("user2", "user222", "Anna Nowak", "22222222222", "user")
    print("Baza danych zainicjalizowana: admin (1001), user1 (1002), user2 (1003)")


if __name__ == "__main__":
    seed()
