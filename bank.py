import socket
import sqlite3
import hashlib


class Bank:
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port

        self.db = sqlite3.connect("bank.db", check_same_thread=False)

        self.init_database()

    def init_database(self):
        cursor = self.db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                receiver TEXT,
                amount INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.db.commit()

    def hash_password(self, password):
        return hashlib.sha256(
            password.encode("utf-8")
        ).hexdigest()

    def create_account(self, account_id, password, balance=0):
        cursor = self.db.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO accounts (id, password, balance)
                VALUES (?, ?, ?)
                """,
                (
                    account_id,
                    self.hash_password(password),
                    balance
                )
            )

            self.db.commit()
            return True

        except sqlite3.IntegrityError:
            return False

    def login(self, account_id, password):
        cursor = self.db.cursor()

        cursor.execute(
            """
            SELECT password
            FROM accounts
            WHERE id = ?
            """,
            (account_id,)
        )

        result = cursor.fetchone()

        if result is None:
            return False

        return result[0] == self.hash_password(password)

    def get_balance(self, account_id):
        cursor = self.db.cursor()

        cursor.execute(
            """
            SELECT balance
            FROM accounts
            WHERE id = ?
            """,
            (account_id,)
        )

        result = cursor.fetchone()

        if result is None:
            return None

        return result[0]

    def deposit(self, account_id, amount):
        if amount <= 0:
            return False

        cursor = self.db.cursor()

        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance + ?
            WHERE id = ?
            """,
            (amount, account_id)
        )

        self.db.commit()

        return cursor.rowcount == 1

    def withdraw(self, account_id, amount):
        if amount <= 0:
            return False

        cursor = self.db.cursor()

        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance - ?
            WHERE id = ?
            AND balance >= ?
            """,
            (amount, account_id, amount)
        )

        self.db.commit()

        return cursor.rowcount == 1

    def transfer(self, sender, receiver, amount):
        if amount <= 0:
            return False

        if sender == receiver:
            return False

        cursor = self.db.cursor()

        cursor.execute(
            """
            SELECT balance
            FROM accounts
            WHERE id = ?
            """,
            (sender,)
        )

        sender_data = cursor.fetchone()

        if sender_data is None or sender_data[0] < amount:
            return False

        cursor.execute(
            """
            SELECT id
            FROM accounts
            WHERE id = ?
            """,
            (receiver,)
        )

        if cursor.fetchone() is None:
            return False

        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance - ?
            WHERE id = ?
            """,
            (amount, sender)
        )

        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance + ?
            WHERE id = ?
            """,
            (amount, receiver)
        )

        cursor.execute(
            """
            INSERT INTO transactions
            (sender, receiver, amount)
            VALUES (?, ?, ?)
            """,
            (sender, receiver, amount)
        )

        self.db.commit()

        return True

    def handle_command(self, account_id, command):
        parts = command.split()

        if not parts:
            return "ERROR empty command"

        command_name = parts[0].upper()

        if command_name == "BALANCE":
            balance = self.get_balance(account_id)

            if balance is None:
                return "ERROR account"

            return f"BALANCE {balance}"

        if command_name == "DEPOSIT":
            if len(parts) != 2:
                return "ERROR usage: DEPOSIT amount"

            amount = int(parts[1])

            if self.deposit(account_id, amount):
                return "OK"

            return "ERROR deposit"

        if command_name == "WITHDRAW":
            if len(parts) != 2:
                return "ERROR usage: WITHDRAW amount"

            amount = int(parts[1])

            if self.withdraw(account_id, amount):
                return "OK"

            return "ERROR withdraw"

        if command_name == "TRANSFER":
            if len(parts) != 3:
                return "ERROR usage: TRANSFER account amount"

            receiver = parts[1]
            amount = int(parts[2])

            if self.transfer(account_id, receiver, amount):
                return "OK"

            return "ERROR transfer"

        if command_name == "LOGOUT":
            return "LOGOUT"

        return "ERROR unknown command"

    def startServer(self):
        server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        server.bind((self.host, self.port))
        server.listen()

        print(f"Bank server: {self.host}:{self.port}")

        while True:
            client, address = server.accept()

            print(f"Connection: {address}")

            self.handle_client(client)

    def handle_client(self, client):
        authenticated = False
        account_id = None

        try:
            while True:
                data = client.recv(4096)

                if not data:
                    break

                command = data.decode("utf-8").strip()
                parts = command.split()

                if not authenticated:

                    if len(parts) == 3 and parts[0].upper() == "LOGIN":
                        account_id = parts[1]
                        password = parts[2]

                        if self.login(account_id, password):
                            authenticated = True
                            response = "LOGIN OK"
                        else:
                            response = "LOGIN ERROR"

                    else:
                        response = "ERROR LOGIN REQUIRED"

                else:
                    response = self.handle_command(
                        account_id,
                        command
                    )

                    if response == "LOGOUT":
                        authenticated = False
                        account_id = None
                        response = "LOGOUT OK"

                client.sendall(
                    (response + "\n").encode("utf-8")
                )

        finally:
            client.close()


bank = Bank()

bank.create_account("#0F", "1234", 500)

bank.startServer()