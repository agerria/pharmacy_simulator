from pydantic import BaseModel
from enum import Enum
from .base import IDaily
import random

class HashableMixin:
    """
    Миксин для автоматической генерации __hash__ и __eq__ на основе полей модели.
    """
    def __hash__(self) -> int:
        # Получаем все поля модели и их значения
        fields = self.__dict__
        # Создаем кортеж из значений полей
        field_values = tuple(fields[field] for field in sorted(fields))
        return hash(field_values)

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        # Сравниваем все поля модели
        return self.__dict__ == other.__dict__

class MedicineType(str, Enum):
    DROPS       = "Капли"
    SPRAY       = "Спрей"
    OINTMENT    = "Мазь"
    TABLETS     = "Таблетки"

class MedicineGroup(str, Enum):
    ANTIBIOTIC  = "Антибиотики"
    PAINKILLER  = "Обезболивающие"
    HEART       = "Сердечные"


class Medicine(HashableMixin, BaseModel):
    name                : str
    dosage              : int
    type                : MedicineType
    group               : MedicineGroup
    wholesale           : float
    expiration_days     : int
    purchase_quantity   : int
    min_quantity        : int

class BatchOfMedicines(IDaily):
    def __init__(self, count, expiration_days):
        self.count = count
        self.expiration_days = expiration_days

    @property
    def is_discounted(self) -> bool:
        return self.expiration_days <= 30

    @property
    def is_expired(self) -> bool:
        return self.expiration_days <= 0

    def start_day(self):
        return None

    def end_day(self):
        self.expiration_days -= 1

    def sell(self, cnt) -> int:
        can_sell = min(self.count, cnt)
        self.count -= can_sell
        return can_sell

    @property
    def is_empty(self) -> bool:
        return self.count <= 0
    
    def __str__(self):
        return f'{self.count}: {self.expiration_days} дн.'

class WarehouseMedicineOrder(BaseModel):
    count : int = 0
    cost : float = 0

class WarehouseMedicine(IDaily):
    def __init__(self, medicine : Medicine, count):
        self.medicine = medicine
        self.batches : list[BatchOfMedicines] = [BatchOfMedicines(count, self.medicine.expiration_days)]
        self.count = count

        self.awaiting_batch = None
        self.awaiting_days = 0

    def has_discounted(self) -> bool:
        return any(map(lambda x: x.is_discounted, self.batches))

    def sell(self, cnt : int) -> WarehouseMedicineOrder:
        order = WarehouseMedicineOrder()
        for batch in self.batches:
            if batch.is_expired:
                continue

            multiplier = 0.5 if batch.is_discounted else 1
            can_sell = batch.sell(cnt)

            order.cost += self.medicine.wholesale * can_sell * multiplier
            order.count += can_sell

            cnt -= can_sell

        self.count -= order.count

        return order

    def _process_purchase_batch(self):
        if self.count < self.medicine.min_quantity and self.awaiting_batch is None:
            self.awaiting_batch = BatchOfMedicines(self.medicine.purchase_quantity, self.medicine.expiration_days)
            self.awaiting_days = random.randint(1, 3)

        if self.awaiting_batch:
            self.awaiting_days -= 1

    def start_day(self):
        if self.awaiting_batch and self.awaiting_days == 0:
            self.batches.append(self.awaiting_batch)
            self.count += self.awaiting_batch.count
            self.awaiting_batch = None

    def end_day(self) -> float:
        losses = 0
        for batch in self.batches:
            batch.end_day()
            if batch.is_expired:
                losses += batch.count * self.medicine.wholesale
                self.count -= batch.count

        self.batches = [
            batch
            for batch in self.batches
            if not batch.is_expired and not batch.is_empty
        ]

        self._process_purchase_batch()

        return losses


    def str_batches(self) -> str:
        return ', '.join(map(str, self.batches))
    
    def str_awiting(self) -> str:
        if not self.awaiting_batch:
            return ''
        return f'{self.awaiting_batch.count}: {self.awaiting_days} дн.'