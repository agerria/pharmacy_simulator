import numpy as np
import random

from pydantic import BaseModel

from .base import IDaily
from .customer import Customer
from .medicine import Medicine, MedicineGroup, MedicineType
from .order import Order, OrderType
from .paymaster import PayMaster
from .pharmacy import Pharmacy, PharmacyDayStatistics
from .warehouse import Warehouse


class SimulationParams(BaseModel):
    days            : int
    couriers        : int
    retail_margin   : float
    card_discount   : float
    base_orders     : int
    sensitivity     : float

    @property
    def order_intensity(self):
        return self.base_orders / (1 + self.sensitivity * self.retail_margin)


class Simulation:
    def __init__(self, params : SimulationParams, medicines_data, customers_data):
        self.params = params

        self.warehouse, self._medicines_by_name = self.parse_medicines(medicines_data)
        self.pharmacy = Pharmacy(
            warehouse = self.warehouse,
            paymaster = PayMaster(retail_margin=params.retail_margin),
            regular_customers = self.parse_customers(customers_data),
            couriers = params.couriers,
        )

    def generate_order(self):
        medicines = self.pharmacy.warehouse.medicines
        num_items = random.randint(1, 5)

        weights = [2.0 if wm.has_discounted else 1.0 for wm in medicines.values()]
        total = sum(weights)
        probs = [w / total for w in weights]

        order_medicines = np.random.choice(list(medicines.keys()), size=num_items, p=probs, replace=False)
        medicines_amount = {
            med : random.randint(1, 5)
            for med in order_medicines
        }

        return Order(
            Customer.generate_customer(),
            medicines_amount,
            OrderType.RANDOM
        )

    def generate_orders(self):
        num_orders = np.random.poisson(self.params.order_intensity)
        orders = [
            self.generate_order()
            for _ in range(num_orders)
        ]
        return orders


    def run(self):
        statistics: list[PharmacyDayStatistics] = []
        for day in range(1, self.params.days + 1):
            orders = self.generate_orders()
            statistics.append(
                self.pharmacy.process_day(day, orders)
            )

        return statistics

    def parse_customers(self, customers_data: list[list]) -> list[Customer]:
        customers = []
        for row in customers_data:
            med_cnts = [
                med.split(':')
                for med in row[4].split(', ')
            ]

            meds = {
                self._medicines_by_name[name]: int(cnt)
                for name, cnt in med_cnts
            }

            c = Customer(
                name = row[0],
                phone = row[1],
                address = row[2],
                discount_card = row[3] == 'Да',
                regular_medicines = meds,
                regularity = int(row[5]),
            )
            customers.append(c)
        return customers

    def parse_medicines(self, medicines_data: list[list]) -> Warehouse:
        medicines = {}
        medicines_by_name = {}
        for row in medicines_data:
            count = int(row[1])
            m = Medicine(
                name = row[0],
                dosage = row[2],
                type = MedicineType(row[3]),
                expiration_days = int(row[4]),
                wholesale = float(row[5]),
                group = MedicineGroup(row[6]),
                purchase_quantity = int(row[7]),
                min_quantity = int(row[8]),
            )
            medicines[m] = count
            medicines_by_name[m.name] = m

        warehouse = Warehouse(medicines)
        return warehouse, medicines_by_name
    