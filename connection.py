# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
from tkinter import E
from constants import *
from base64 import b64encode
from os import listdir as ldir, stat # Para ver los archivos de un directorio y los tamaños
import os.path

BUFF_SIZE = 1024 # Tamaño del buffer que recive las requests de los clientes

class SocketBufferOverflow(Exception):
    "Raised when the socket exceded BUFF_SIZE and haven't recived EOL"
    pass

class BadEOLRecieved(Exception):
    "Raised when the socket exceded BUFF_SIZE and haven't recived EOL"
    pass

class Connection(object):
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """
    def __init__(self, socket, directory=DEFAULT_DIR):
        self.client_socket = socket
        self.directory = directory
        self.connection_active = True
        self.buffer = ''

    def socket_is_full(self,request):
        return len(request) >= BUFF_SIZE
 
    def parse_request(self):
        request = ''
        while request.count(EOL) == 0:
            request += self.client_socket.recv(BUFF_SIZE).decode("ascii") #Recive 1024 bytes del stream y los decodea como ascii

        print("Client requested: '{}'".format(request))
        cant_eol = request.count(EOL) #Puede servir más adelante para el manejo de varios comandos


        if EOL in request: # Limpia la request para que sea facil parsearla
            parse = request.split(EOL, -1) # Separa todo por EOL's ["get_file_listing","get_metadata file1"]

        for p in parse: #Busca malos EOL's que se puedan haber parseado en cada comando
            if '\n' in p:
                raise BadEOLRecieved

        commands = [i.split(' ') for i in parse] # A cada string que es comando y sus args, los transforma en una lista de los strings separados por espacios
        commands = commands[:len(commands)-1] # Siempre queda un string vacio o basura despues del ultimo EOL
        # commands = [["get_file_listing"],["get_metadata","file1"]]

        return commands

    def handle(self):
        """
        Se encarga de limpiar una peticion entrante
        y llama a las funciones que se encargan
        de servir la correspondiente
        """
        while self.connection_active:
            try:
                parsed_commands = self.parse_request()
            except SocketBufferOverflow:
                self.disconnect_on_failure()
            except BadEOLRecieved:
                self.send_response_code(BAD_EOL)

            # En una version de varios comandos parse devuelve una lista de listas que representan comandos y argumentos
            # commands [["get_file_listing"],["get_metadata","file1"]]
            try:
                for command in parsed_commands:
                    self.exec_command(command)


            except Exception as ex:
                print(ex)
                self.disconnect_on_failure()

    def exec_command(self,parse): #Recibe una lista que tiene un solo comando y sus argumentos como elementos
        if (parse[0] == "get_file_listing"):
            self.serve_file_listing()

        elif (parse[0] == "get_metadata"):
            if len(parse) == 2:
                filename = parse[1]
                self.serve_file_metadata(filename)
            else:
                self.send_response_code(INVALID_ARGUMENTS)

        elif(parse[0] == "get_slice"):
            start = parse[2]
            end = parse[3]
            if start.isdigit() and end.isdigit(): #Es para test_bad_argument_type
                self.serve_file_slice(parse[1],int(start),int(end))
            else: 
                self.send_response_code(INVALID_ARGUMENTS)
        elif (parse[0] == "quit"):
            if (len(parse) == 1):
                self.client_quits()
                self.connection_active = False
            else:
                self.send_response_code(INVALID_ARGUMENTS)

        else:
            self.send_response_code(INVALID_COMMAND)

    def disconnect_on_failure(self):
        """
        Enviarle al cliente codigo de error por server internal error y cerrar la coneccion
        """
        try:
            self.send_response_code(INTERNAL_ERROR)
        finally:
            self.connection_active = False
        

    def client_quits(self):
        print("client {} quitted".format(self.client_socket.getpeername()))
        self.send_response_code(CODE_OK)
        
    def serve_file_listing(self):
        """
        Envia al cliente ,la lista de archivos disponibles en el servidor
        """
        try:
            available_files = ldir(self.directory)
        except OSError:
            print("No se pudo listar el directorio")
            self.disconnect_on_failure()

        #Enviar todos los nombres de archivos disponibles
        self.send_response_code(CODE_OK)
        for i in available_files:
            self.send(i)

        self.send_EOL()

    def serve_file_metadata(self,filename):
        """
        Le manda al cliente una respuesta que incluye la metadata del archivo
        """
        try:
            available_files = ldir(self.directory)
        except OSError:
            print("No se pudo listar el directorio")
            self.disconnect_on_failure()

        if filename in available_files:
            self.send_response_code(CODE_OK)
            filesize = stat("{}/{}".format(self.directory ,filename)).st_size # <- ó st_rsize?
            self.send(str(filesize))    
        else:
            self.send_response_code(FILE_NOT_FOUND)
    
    def serve_file_slice(self,filename,start,size):
        """
        Enviarle al cliente parte del archivo
        """

        if not os.path.isfile(os.path.join(self.directory, filename)):
            self.send_response_code(FILE_NOT_FOUND)

        file_size = os.path.getsize(os.path.join(self.directory, filename))
        if (start + size > file_size) or (start < 0) or (size <= 0):
            self.send_response_code(BAD_OFFSET)
        else:
            try:
                self.send_response_code(CODE_OK)
                f=open(os.path.join(self.directory, filename), 'rb')
                f.seek(start)
                data = f.read(size)
                encoded_data = b64encode(data).decode('ascii')
                self.send(encoded_data)
            except:
                self.disconnect_on_failure()


    # Esta parte modulariza las 'operaciones' de enviar mensajes y los codigos de error
    def send_response_code(self,CODE):
        msg = "{code} {m}".format(code=CODE,m=error_messages[CODE])
        print(msg)
        self.send(msg)

    def send_EOL(self): # Sirve cuando queremos indicar que es el fin del mensaje
        msg = EOL
        self.send("")

    def send(self, message):
        """
        Envía el mensaje 'message' al server, seguido por el terminador de
        línea del protocolo(CUIDADO NO LO AGREGUEN OTRA VEZ O SE FINALIZA EL MENSAJE PREMATURAMENTE).

        Si se da un timeout, puede abortar con una excepción socket.timeout.

        También puede fallar con otras excepciones de socket.
        """
        message += EOL  # Completar el mensaje con un fin de línea
        while message:
            bytes_sent = self.client_socket.send(message.encode("ascii"))
            assert bytes_sent > 0
            message = message[bytes_sent:] # Cuando se consuma todo el mensaje se rompe el bucle