from enum import Enum
from .medicine import Medicine, WarehouseMedicineOrder
from typing import Self
from .customer import Customer

class OrderType(Enum, str):
    REGULAR     = "Регулярный"
    RANDOM      = "Случайный"

class OrderStatus(Enum, str):
    DELIVERED       = "Доставлен"
    PARTIALLY       = "Доставлен частично"
    NO_MEDICINES    = "Нет товара"
    NO_COURIER      = "Нет курьеров"

class Order:
    def __init__(self, customer : Customer, medicines : dict[Medicine, int], order_type : OrderType):
        self.customer = customer
        self.requested_medicines = medicines
        self.status = OrderStatus.NO_COURIER
        self.type = order_type

        self.preliminary_reciept = None
        self.summary = None

    def set_preliminary_reciept(self, preliminary_reciept : WarehouseMedicineOrder):
        self.preliminary_reciept = preliminary_reciept

    def set_summary(self, summary : float):
        self.summary = summary

    @classmethod
    def create_regular_order(cls, customer : Customer) -> Self:
        return cls(
            customer,
            customer.regular_medicines,
            OrderType.REGULAR
        )
