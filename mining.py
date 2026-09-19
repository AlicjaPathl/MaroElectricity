import random
import time
import json
import os
import asyncio


class Mining:
    def __init__(self):
        self.privetID = "#0F"
        self.timer = time.time()

        self.config = {
            "power": 20_000
        }

        self.energy = 0
        self.balance = 1000

        self.faktury = {}
        self.zlecenia = {}
        self.magazin = {}

    def generate_id(self):
        while True:
            id = f"#{random.randint(0, 0xFFFFFFFF):08X}"

            if id not in self.zlecenia and id not in self.faktury:
                return id

    def mining_cost(self, kg):
        fixed_cost = 5000
        production_cost = 15
        minimum_price = 18

        cost = fixed_cost + kg * production_cost
        minimum_cost = kg * minimum_price

        return max(cost, minimum_cost)

    def addZlecenie(self, nazwa, typ, quantity):
        id = self.generate_id()

        status = (
            "paid"
            if self.faktury.get(id) == "miningPaid"
            else "waitForPay"
        )

        self.zlecenia[nazwa] = {
            "id": id,
            "type": typ,
            "quantity": quantity,
            "rewards": self.mining_cost(quantity),
            "status": status
        }

    def pay(self, id, idZlecenia, kwota, odbiorca, paid="unPaid"):
        self.faktury[id] = {
            "id": id,
            "idZlecenia": idZlecenia,
            "kwota": kwota,
            "odbiorca": odbiorca,
            "status": paid
        }

    def save(self):
        os.makedirs("storage", exist_ok=True)

        data = {
            "config": self.config,
            "energy": self.energy,
            "balance": self.balance,
            "faktury": self.faktury,
            "zlecenia": self.zlecenia,
            "magazin": self.magazin
        }

        with open("storage/mining.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def load(self):
        path = "storage/mining.json"

        if not os.path.exists(path):
            return False

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self.config = data.get("config", {})
        self.energy = data.get("energy", 0)
        self.balance = data.get("balance", 0)
        self.faktury = data.get("faktury", {})
        self.zlecenia = data.get("zlecenia", {})
        self.magazin = data.get("magazin", {
            "uranium": 0,
            "stone": 0,
            "coal": 0
        })

        return True

    async def mining_loop(self):
        while True:
            self.timer = time.time()

            for zlecenie in self.zlecenia.values():
                print(zlecenie)

            await asyncio.sleep(1)

    async def save_loop(self):
        while True:
            self.save()

            await asyncio.sleep(10)

    async def energy_loop(self):
        while True:
            # tutaj później logika energii
            await asyncio.sleep(1)

    async def order_loop(self):
        while True:
            # tutaj później obsługa zleceń
            await asyncio.sleep(1)

    async def run(self):
        self.load()

        await asyncio.gather(
            self.save_loop(),
            self.mining_loop(),
            self.energy_loop(),
            self.order_loop()
        )


async def main():
    mining = Mining()

    await mining.run()


asyncio.run(main())