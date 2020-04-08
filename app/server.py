#
#Серверное приложение для соединения
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    #pass #Заглушка, обозначает, что нужно дописать код

    login: str = None
    server: 'Server'
    transport: transports.Transport
    login_users: list = []
    history_message: list = []

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)
        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
            self.send_history(decoded)
        else:
            if decoded.startswith("login:"):
                tmp_login = decoded.replace("login:", "").replace("\t\r\n","")
                for logins in self.login_users:
                    if tmp_login == logins:
                        self.transport.write(f"Логин {tmp_login} занят, попробуйте другой\n".encode())
                        self.server.clients.clear(self)
                        self.transport.close()
                        break
                else:
                    self.login = tmp_login
                    self.login_users.append(self.login)
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    if self.send_history().__len__() > 0:
                        self.transport.write(
                            f"Последние 10 сообщений чата:\n".encode()
                        )
                        for send in self.send_history()[-10:-1]:
                            self.transport.write(
                                f"{send}".encode()
                            )
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print(f"Клиент {self.login} вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n".replace("\t","")
        for users in self.server.clients:
            users.transport.write(message.encode())

    def send_history(self, content: str = None):
        content = f"{content}".replace("\r\n", "")
        if not content and not content == None and not content.startswith("login:"):
            self.history_message.append(f"{self.login}: {content}\n")
        return self.history_message


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop() #вернуть работающий цикл

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print('Start server ...')

        await coroutine.serve_forever()

process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")