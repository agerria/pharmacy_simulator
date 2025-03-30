from enum import Enum
from .medicine import Medicine, WarehouseMedicineOrder
from typing import Self
from .customer import Customer

from enum import Enum

class OrderType(str, Enum):
    REGULAR     = "🔄 Регулярный"        
    RANDOM      = "🎲 Случайный"         

class OrderStatus(str, Enum):
    DELIVERED       = "✅ Доставлен"          
    PARTIALLY       = "🟡 Доставлен частично" 
    NO_MEDICINES    = "❌ Нет товара"         
    NO_COURIER      = "🚫 Нет курьеров"       

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
    
    def __str__(self):
        return f'<Order: {self.customer}\t| {self.status.value}\t| {self.type.value}\t| {self.requested_medicines}>'
    
    def to_row(self):
        med_count = [
            f'{med.name}: {count}'
            for med, count in self.requested_medicines.items()
        ]
        return [
            self.customer.name,
            self.customer.address,
            self.type.value,
            ', '.join(med_count),
            self.summary,
            self.status.value
        ]

    @property
    def is_delivered(self):
        return self.status in (OrderStatus.DELIVERED, OrderStatus.PARTIALLY)
    
    @property
    def is_regular(self):
        return self.type == OrderType.REGULAR