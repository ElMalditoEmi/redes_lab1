#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import optparse
import socket
import connection
import threading
from constants import *


class Server(object):
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(self, addr=DEFAULT_ADDR, port=DEFAULT_PORT,
                 directory=DEFAULT_DIR):
        self.addr = addr
        self.port = port
        self.directory = directory
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crear el socket servidor
        try:
            self.s.bind((self.addr, self.port))
        except OSError:
            print("El puerto estaba ocupado, terminando el programa")
            quit()


    def serve(self):
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        self.s.listen(1000) # Pone el socket en escucha
        while True: # Aceptar todas las conecciones entrantes
            client_socket, client_addr = self.s.accept() # Al encontrar una conexion en la escucha se recibe el socket al cliente y su ip

            threading.Thread(target=self.create_connection, args=(client_socket, client_addr)).start()

    def create_connection(self, client_socket,client_addr):
            try:
                conn = connection.Connection(client_socket,self.directory) # Creo un nuevo objeto Connection que atiende la peticion
                print("Sirviendo una peticion de:{}".format(client_addr))
                conn.handle()
            except Exception as excep:
                print("La conexion con {}, sufrio un error fatal {}",format(client_addr,excep))
            finally:
                # En caso de que haya habido un problema durante el codigo de conn, cerramos el socket aca en cualquier caso
                client_socket.close()


def main():
    """Parsea los argumentos y lanza el server"""

    parser = optparse.OptionParser()
    parser.add_option(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar", default=DEFAULT_PORT)
    parser.add_option(
        "-a", "--address",
        help="Dirección donde escuchar", default=DEFAULT_ADDR)
    parser.add_option(
        "-d", "--datadir",
        help="Directorio compartido", default=DEFAULT_DIR)

    options, args = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(1)
    try:
        port = int(options.port)
    except ValueError:
        sys.stderr.write(
            "Numero de puerto invalido: %s\n" % repr(options.port))
        parser.print_help()
        sys.exit(1)
        
    server = Server(options.address, port, options.datadir)
    server.serve()


if __name__ == '__main__':
    main()
