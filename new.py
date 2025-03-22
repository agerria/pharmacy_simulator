import random
import numpy as np

from copy import deepcopy
from enum import Enum
from pydantic import BaseModel

from .base import IDaily
from .customer import Customer
from .medicine import Medicine
from .order import Order, OrderType
from .paymaster import PayMaster
from .pharmacy import Pharmacy, PharmacyDayStatistics
from .utils import logger
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
        return self.base_orders / (1 + self.sensitivity * self.retail_margin / 100)

class Simulation:
    def __init__(self, params : SimulationParams):
        self.params = params

        # self.medicines : dict[Medicine, WarehouseMedicine]
        # self.warehouse
        # self.paymaster
        self.pharmacy = Pharmacy()

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
        statistics = list(PharmacyDayStatistics)
        for day in range(1, self.params.days + 1):
            orders = self.generate_orders()
            statistics.append(self.pharmacy.process_day(day, orders))

        return statistics
