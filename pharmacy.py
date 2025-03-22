from pydantic import BaseModel
from copy import deepcopy

from .order import Order
from .utils import logger
from .base import IDaily
from .customer import Customer
from .warehouse import Warehouse
from .paymaster import PayMaster


class PharmacyDayStatistics(BaseModel):
    revenue     : float = .0
    profit      : float = .0
    losses      : float = .0
    orders      : list[Order] | None = None
    warehouse   : Warehouse | None = None


class Pharmacy(IDaily):
    COURIER_MAX_ORDERS = 15
    def __init__(self, warehouse : Warehouse, paymaster : PayMaster, regular_customers : list[Customer], couriers : int):
        self.warehouse = warehouse
        self.paymaster = paymaster
        self.regular_customers = regular_customers
        self.couriers = couriers

        self.orders = None
        self.statistics = None

    def start_day(self):
        self.orders = list()
        self.statistics = PharmacyDayStatistics()
        self.warehouse.start_day()

    def add_regular_orders(self, day : int):
        for customer in self.regular_customers:
            if day % customer.regularity == 0:
                self.orders.append(Order.create_regular_order(customer))

    def add_ordes(self, orders : list[Order]):
        self.orders += orders

    def deliver_orders(self):
        can_deliver = min(len(self.orders), self.couriers * self.COURIER_MAX_ORDERS)
        for order_num in range(can_deliver):
            order = self.orders[order_num]
            self.warehouse.process_order(order)

            revenue = self.paymaster.count_summary(order)
            self.statistics.revenue += revenue
            self.statistics.profit += (revenue - order.preliminary_reciept.cost)

    def end_day(self):
        self.statistics.losses = self.warehouse.end_day()
        self.statistics.warehouse = deepcopy(self.warehouse)
        self.statistics.orders = self.orders

    def get_statistics(self):
        return self.statistics

    def process_day(self, day, orders):
        self.start_day()
        self.add_regular_orders(day)
        self.add_ordes(orders)
        self.deliver_orders()
        self.end_day()
        return self.get_statistics()
