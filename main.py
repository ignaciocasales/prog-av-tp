import multiprocessing
import time


class Order:
    def __init__(self, order_id, items):
        self.order_id = order_id
        self.items = items


def process_order(order, employee_id):
    print(f"Procesando pedido {order.order_id} con {len(order.items)} artículos...")
    # Simular el tiempo de procesamiento de un pedido.
    time_to_process = len(order.items)
    time.sleep(time_to_process)
    print(f"Pedido {order.order_id} completado en {time_to_process} segundos por el empleado {employee_id}.")


def work(orders_queue, employee_id):
    while not orders_queue.empty():
        process_order(
            orders_queue.get(),
            employee_id
        )

        orders_queue.task_done()


if __name__ == "__main__":
    try:
        orders_number = 10
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

        print("Todos los pedidos han sido procesados.")
    except KeyboardInterrupt:
        print("El programa ha sido detenido por el usuario.")
