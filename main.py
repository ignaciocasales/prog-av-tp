import logging
import multiprocessing
import sys
import time
from argparse import ArgumentParser


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


if __name__ == "__main__":
    try:
        # Configuración del logger.
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ],
        )

        # Configuración de los argumentos de la línea de comandos.
        parser = ArgumentParser()
        parser.add_argument("-e", "--employees", dest="employees_number", type=int, )
        parser.add_argument("-o", "--orders", dest="orders_number", type=int, default=10)
        parser.add_argument("-i", "--items", dest="items_number", type=int, default=3)
        args = parser.parse_args()

        # Número de pedidos
        orders_number = args.orders_number
        logging.info(f"Se crearán {orders_number} pedidos.")

        # Número de artículos por pedido
        items_number = args.items_number
        logging.info(f"Cada pedido tendrá {items_number} artículos.")

        # Número de empleados (hilos de procesamiento de los pedidos)
        employees_number = args.employees_number if args.employees_number else multiprocessing.cpu_count()
        logging.info(f"Se utilizarán {employees_number} empleados para procesar los pedidos.")

        orders_queue = multiprocessing.JoinableQueue()

        # El número de artículos por pedidos es preferible que sea fijo para poder comparar los tiempos de
        # procesamiento de los pedidos.
        def build_items(n): return ["articulo" + str(item_id) for item_id in range(n)]

        def build_order(order_id, items): return Order(order_id, items)

        # Crear los pedidos.
        orders = map(lambda order_id: build_order(order_id, build_items(items_number)), range(orders_number))

        # Agregar los pedidos a la cola.
        [orders_queue.put(order) for order in orders]

        # Crear los procesos.
        processes = map(lambda employee_id: multiprocessing.Process(
            target=work,
            args=(orders_queue, employee_id),
            daemon=True
        ), range(employees_number))

        start_time = time.time()

        # Iniciar los procesos.
        [process.start() for process in processes]

        # Esperar a que todos los pedidos sean procesados.
        orders_queue.join()

        total_time = time.time() - start_time
        logging.info(f"Todos los pedidos han sido procesados en {total_time} segundos.")
    except KeyboardInterrupt:
        logging.info("El programa ha sido detenido por el usuario.")
    except Exception as e:
        logging.error(f"Ha ocurrido un error: {e}")
