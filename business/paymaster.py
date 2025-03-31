from pydantic import BaseModel

from .order import Order, OrderType


class PayMaster(BaseModel):
    retail_margin       : float
    card_discount       : float = 0.05
    regular_discount    : float = 0.05
    discount            : float = 0.03
    discount_threshold  : float = 1000
    max_discount        : float = 0.09

    def count_summary(self, order : Order) -> float:
        if order.preliminary_reciept is None:
            raise ValueError("Получен заказ без обработки складом")

        base_cost = order.preliminary_reciept.cost * (1 + self.retail_margin)
        sum_discount = .0

        if order.type == OrderType.REGULAR:
            sum_discount += self.regular_discount
        if order.customer.discount_card:
            sum_discount += self.card_discount
        if base_cost > self.discount_threshold:
            sum_discount += self.discount

        base_cost *= (1 - min(sum_discount, self.max_discount))

        order.set_summary(base_cost)

        return base_cost
