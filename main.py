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


def setup_logging():
    # Configuración del logger.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(processName)s] [%(threadName)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )


def replenish_for(i,n,materials_queue):
    materials_queue.put(f"Material-{i + 1}")
    time.sleep(1)
    i+=1
    replenish_for(i,n,materials_queue) if i<n else None


def replenish_while(materials_queue, lock):
    logging.info(f"Repositor: Verificando stock.")
    lock.acquire()  # Adquirir el Lock antes de verificar el stock
    try:
        if materials_queue.empty():
            logging.info("Repositor: Reponiendo stock... Ningún trabajador puede ingresar aun.")
            # Si la cola está vacía, agregar 5 materiales
            replenish_for(0,5,materials_queue)
            logging.info(f"Repositor: Stock actual: {materials_queue.qsize()} materiales. Acceso liberado.")
    finally:
        lock.release()  # Liberar el Lock después de reponer los materiales
    time.sleep(5)  # Verificar la cola cada 5 segundos
    replenish_while(materials_queue, lock)


def replenish(materials_queue, lock):
    setup_logging()
    replenish_while(materials_queue, lock)


def process_order(order, employee_id, materials_queue, lock):
    logging.info(f"Empleado {employee_id} recibió el pedido {order.order_id} con {len(order.items)} artículos...")

    for _ in range(len(order.items)):
        while True:
            if not materials_queue.empty():
                lock.acquire()  # Adquirir el Lock antes de tomar el material
                try:
                    if not materials_queue.empty():
                        material = materials_queue.get()
                        logging.info(
                            f"Empleado {employee_id} está procesando el material: {material}. Stock restante: {materials_queue.qsize()}")
                finally:
                    lock.release()  # Liberar el Lock después de tomar el material
                    break
            else:
                time.sleep(1)  # Esperar un segundo antes de revisar nuevamente la cola

    time_to_process = len(order.items)
    time.sleep(time_to_process)
    logging.info(f"Pedido {order.order_id} completado en {time_to_process} segundos por el empleado {employee_id}.")


def work(orders_queue, employee_id, materials_queue, lock):
    process_order(orders_queue.get(), employee_id, materials_queue, lock)
    orders_queue.task_done()
    work(orders_queue, employee_id, materials_queue, lock) if not orders_queue.empty() else None


def run_work_subprocess(oq, eid, mq, lock):
    setup_logging()
    work(oq, eid, mq, lock)


if __name__ == "__main__":
    try:
        setup_logging()

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

        # Crear el Lock
        lock = multiprocessing.Lock()

        # Crear la cola para los materiales
        materials_queue = multiprocessing.Queue()

        # Crear el proceso del productor de materiales
        producer_process = multiprocessing.Process(
            target=replenish,
            args=(materials_queue, lock),
            name="Productor de Materiales",
            daemon=True
        )
        producer_process.start()


        # El número de artículos por pedidos es preferible que sea fijo para poder comparar los tiempos de
        # procesamiento de los pedidos.
        def build_items(items):
            return ["articulo" + str(item_id) for item_id in range(items)]


        def build_order(order_id, items):
            return Order(order_id, build_items(items))


        # Crear los pedidos.
        orders = map(lambda order_id: build_order(order_id, items_number), range(orders_number))

        # Agregar los pedidos a la cola.
        [orders_queue.put(order) for order in orders]

        # Crear los procesos workers.
        processes = map(lambda employee_id: multiprocessing.Process(
            name=f"Empleado {employee_id}",
            target=run_work_subprocess,
            args=(orders_queue, employee_id, materials_queue, lock),
            daemon=True,
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
