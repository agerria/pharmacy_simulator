from .base import IDaily
from .medicine import Medicine, WarehouseMedicine, WarehouseMedicineOrder
from .order import Order, OrderStatus

class Warehouse(IDaily):
    def __init__(self, medicines_count : dict[Medicine, int]):
        self.medicines: dict[Medicine, WarehouseMedicine] = {
            medicine: WarehouseMedicine(medicine, count)
            for medicine, count in medicines_count.items()
        }

    def process_order(self, order : Order):
        preliminary_reciept = WarehouseMedicineOrder()

        order.status = OrderStatus.DELIVERED
        for medicine, cnt in order.requested_medicines.items():
            med_bill = self.medicines[medicine].sell(cnt)

            preliminary_reciept.count += med_bill.count
            preliminary_reciept.cost += med_bill.cost

            if med_bill.count < cnt:
                order.status = OrderStatus.PARTIALLY

        if preliminary_reciept.count == 0:
            order.status = OrderStatus.NO_MEDICINES

        order.set_preliminary_reciept(preliminary_reciept)

    def start_day(self):
        for _, warehouse_medicine in self.medicines.items():
            warehouse_medicine.start_day()

    def end_day(self):
        losses = 0
        for _, warehouse_medicine in self.medicines.items():
            losses += warehouse_medicine.end_day()

        return losses
    

    def to_table(self):
        rows = []
        for med, wm in self.medicines.items():
            rows.append([
                med.name,
                wm.count,
                wm.batches[0].expiration_days if wm.batches else '',
            ])
        return rows