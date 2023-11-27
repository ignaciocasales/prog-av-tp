import logging
import multiprocessing
import sys
import time


# Estructura de un pedido (order)
class Order:
    def __init__(self, order_id, items):
        self.order_id = order_id
        self.items = items


def process_order(order, employee_id):
    logging.info(f"Procesando pedido {order.order_id} con {len(order.items)} artículos...")
    # Simular el tiempo de procesamiento de un pedido. Cada artículo toma 1 segundo.
    time_to_process = len(order.items)
    time.sleep(time_to_process)
    logging.info(f"Pedido {order.order_id} completado en {time_to_process} segundos por el empleado {employee_id}.")


def work(orders_queue, employee_id):
    while not orders_queue.empty():
        process_order(
            orders_queue.get(),
            employee_id
        )

        orders_queue.task_done()


# TODO: Hacer el código funcional.
if __name__ == "__main__":
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ],
        )

        start_time = time.time()

        # TODO: Tomar el número de pedidos y empleados desde la línea de comandos y tener valores por defecto.
        # Número de pedidos
        orders_number = 10

        # TODO: Tomar el número de empleados (hilos) desde la línea de comandos y tener valores por defecto.
        # Número de empleados (hilos de procesamiento de los pedidos)
        employees_number = 2

        orders_queue = multiprocessing.JoinableQueue()

        for i in range(orders_number):
            order = Order(i, ["articulo1", "articulo2", "articulo3"])

            orders_queue.put(order)

        for i in range(employees_number):
            process = multiprocessing.Process(
                target=work,
                args=(orders_queue, i),
                daemon=True
            )

            process.start()

        orders_queue.join()

        total_time = time.time() - start_time
        logging.info(f"Todos los pedidos han sido procesados en {total_time} segundos.")
    except KeyboardInterrupt:
        logging.info("El programa ha sido detenido por el usuario.")
