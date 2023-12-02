import socket
import threading
from typing import Callable
from protocol import Request
from communication import Communication


class Server:
    def __init__(
        self,
        clientCallback: Callable[[Request, socket.socket, tuple], None],
        host: str = "127.0.0.1",
        port: int = 3339,
        backlog: int = 5,
        maxClients: int = 100,
        timeout: float = 1.0,
    ):
        if host == "" or port < 1000:
            return

        self.host: str = host
        self.port: int = port
        self.backlog: int = backlog

        self.serverThread: threading.Thread = threading.Thread(target=self.run)
        self.maxClients: int = maxClients
        self.clients: list[socket.socket] = []
        self.threads: list[threading.Thread] = []
        self.socket: socket.socket = socket.socket()

        self.shouldRun: bool = True
        self.hasStopped: bool = False

        self.clientCallback = clientCallback
        self.timeout = timeout

        self.socket.settimeout(timeout)

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.backlog)

            self.serverThread.start()
        except Exception as e:
            print("Error while trying to start server: \n" + str(e))

    def run(self) -> None:
        while self.shouldRun:
            if len(self.clients) > self.maxClients:
                print("Max clients reached, waiting for clients to disconnect...")
                break

            try:
                self.accept()
            except socket.timeout:
                pass

        if not self.hasStopped:
            self.stop()

    def accept(self) -> None:
        clientSocket, clientAddress = self.socket.accept()
        self.clients.append(clientSocket)

        t = threading.Thread(
            target=self.handleClient, args=(clientSocket, clientAddress)
        )

        self.threads.append(t)
        t.start()

    def stop(self):
        self.shouldRun = False
        self.hasStopped = True

        self.serverThread.join()
        self.socket.close()

        for thread in self.threads:
            thread.join()

    def handleClient(self, clientSocket: socket.socket, clientAddress: tuple) -> None:
        request = Request(Communication.getData(clientSocket, self.timeout))

        self.clientCallback(
            request,
            clientSocket,
            clientAddress,
        )

        self.clients.remove(clientSocket)
        clientSocket.close()
