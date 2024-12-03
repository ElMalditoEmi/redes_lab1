## Preguntas
1. ¿Qué estrategias existen para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente? Investigue y responda brevemente qué cambios serían necesarios en el diseño del código.

Para implementar este mismo servidor pero pudiendo atender a multiples clientes simultaneamente, hay varias implementaciones para resolver este problema:

- **Múltiples procesos:** Crear procesos hijos por medio de la syscall `fork`, esto hará que cada subprocesos se dedique a atender a los clientes individualmente. Pero esto es poco eficiente pues genera una carga excesiva, ya que cada cliente genera un nuevo subproceso que consume los mismos recursos que el principal; esto mismo hace que este método sea poco escalable. Para este método se debe incluir la librería os puede emplearse para generar estos subprocesos. Sin embargo, este enfoque carece de escalabilidad.



- **Con hilos de ejecución:** La idea sería implementar hilos de ejecución donde cada uno se encarga de atender a un cliente en particular. En Python, existen varias librerías que proporcionan estas abstracciones, como `threading`, `concurrent.futures`, `multiprocessing`, entre otras. Este enfoque es menos costoso que el anterior, ya que aprovecha los recursos del único proceso en ejecución. Se puede crear múltiples hilos, haciendo uno nuevo cada vez que llega un cliente o manteniendo un grupo de hilos previamente creados que se reparten el trabajo.

- **Con Corrutinas:** Otra alternativa para gestionar las diferentes ejecuciones es mediante el uso de corrutinas, donde cada una se encarga de una conexión específica. Esto presenta la ventaja de operar en un único hilo, lo que reduce más el uso de recursos. Pero este enfoque tiene la desventaja de que el control de corrutinas junto con los sockets es mucho más complejo. Aunque es altamente escalable, no es recomendable asumir esta complejidad adicional a menos que se deban manejar numerosos clientes de forma concurrente. Para implementar este método, se puede utilizar la librería `asyncio`.

2. Pruebe ejecutar el servidor en una máquina del laboratorio, mientras utiliza el cliente desde otra, hacia la ip de la máquina servidor. ¿Qué diferencia hay si se corre el servidor desde la IP “localhost”, “127.0.0.1” o la ip “0.0.0.0”?

Las IP `localhost` y `127.0.0.1` son equivalentes y se refieren a la misma dirección, Cuando un servidor se ejecuta en cualquiera de estas solo acepta conexiones desde la misma máquina en la que se está ejecutando. Las solicitudes desde fuera de esa máquina no se aceptarán. Quiere decir que el cliente no puede conectarse al
servidor si este ha sido lanzado en una máquina distinta.

La IP `0.0.0.0` es una dirección especial que indica que el servidor está escuchando en todas las interfaces de red disponibles en la máquina, haciendo que acepte conexiones que provengan de
cualquier dirección IP. Así que en este caso el cliente sí puede conectarse al
servidor incluso si este ha sido lanzado en una máquina distinta, 

