from .base import IDaily
from .medicine import Medicine, WarehouseMedicine, WarehouseMedicineOrder
from .order import Order, OrderStatus

class Warehouse(IDaily):
    def __init__(self, medicines : dict[Medicine, WarehouseMedicine]):
        self.medicines = medicines

    def process_order(self, order : Order):
        preliminary_reciept = WarehouseMedicineOrder(0, 0)

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
