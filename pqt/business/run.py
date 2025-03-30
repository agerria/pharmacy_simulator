from .simulation import Simulation, SimulationParams
from .mock import MEDICINES_MOCK, CUSTOMERS_MOCK

params = SimulationParams(
    days = 100,
    couriers = 5,
    retail_margin = 0.25,
    card_discount = 0.05,
    base_orders = 10,
    sensitivity = 0.05,
)

s = Simulation(params, MEDICINES_MOCK)

for stat in s.run():
    print('\n', '-' * 50)
    print(stat)
