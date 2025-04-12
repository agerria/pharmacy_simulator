import random

from typing import Self
from pydantic import BaseModel

from .medicine import Medicine


RND_STREETS = ["Ленина", "Гагарина", "Советская"]

class Customer(BaseModel):
    name : str
    phone : str
    address : str
    discount_card : bool
    regular_medicines : dict[Medicine, int] | None = None
    regularity : int | None = None

    @classmethod
    def generate_customer(cls) -> Self:
        return cls(
            name=f"Клиент {random.randint(1, 100)}",
            phone=f"+7{random.randint(9000000000, 9999999999)}",
            address=f"ул. {random.choice(RND_STREETS)}, {random.randint(1, 100)}",
            discount_card=random.random() > 0.7
        )

    @classmethod
    def generate_regular_customer(cls, medicines : list[Medicine]) -> Self:
        generated_customer = cls.generate_customer()

        generated_customer.regular_medicines = {
            random.choice(medicines) : random.randint(1,5)
            for _ in range(random.randint(1,3))
        }
        generated_customer.regularity = random.randint(2,7)
        generated_customer.discount_card = random.random() > 0.4

        return generated_customer
