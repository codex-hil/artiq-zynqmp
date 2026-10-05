from abc import ABC, abstractmethod
from logging import getLogger
from socket import AF_INET6, SHUT_RDWR, create_server, socket
from threading import Semaphore, Thread

_LOGGER = getLogger(__name__)


class Server(ABC):
    def __init__(self, name: str, port: int) -> None:
        super().__init__()
        self._name = name
        self._port = port

    @property
    def name(self) -> str:
        return self._name

    @property
    def port(self) -> int:
        return self._port

    def handle_client(self, c_sock: socket) -> None:
        try:
            _LOGGER.info("New client: %s", c_sock.getpeername())
            self._handle_client(c_sock)
        finally:
            try:
                c_sock.shutdown(SHUT_RDWR)
            except OSError:
                pass
            c_sock.close()
            _LOGGER.info("Session ended")

    @abstractmethod
    def _handle_client(self, c_sock: socket) -> None: ...


class _SocketThread:
    def __init__(self, sock: socket, thread: Thread) -> None:
        self._sem = Semaphore()
        self._sock: socket | None = sock
        self._thread = thread
        self._thread.start()

    @property
    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def shutdown(self) -> None:
        with self._sem:
            if self._sock is not None:
                try:
                    self._sock.shutdown(SHUT_RDWR)
                except OSError:
                    pass
                self._sock.close()
                self._sock = None
        self._thread.join()


class SocketPool:
    def __init__(self) -> None:
        self._sem = Semaphore()
        self._sock_threads: list[_SocketThread] = []
        self._next_id = 1

    def add_server(self, server: Server) -> None:
        s_sock = create_server(("", server.port), family=AF_INET6, dualstack_ipv6=True)
        with self._sem:
            self._sock_threads.append(
                _SocketThread(
                    s_sock,
                    Thread(
                        target=self._handle_server,
                        name=f"s{self._next_id}-{server.name}-server",
                        args=[server, s_sock],
                    ),
                )
            )
            self._next_id += 1

    def collect_garbage(self) -> None:
        with self._sem:
            garbage_indices = [i for i, st in enumerate(self._sock_threads) if not st.is_alive]
            garbage = [self._sock_threads.pop(i) for i in reversed(garbage_indices)]
        for sock_thread in garbage:
            sock_thread.shutdown()

    def shutdown(self) -> None:
        with self._sem:
            garbage = self._sock_threads.copy()
            self._sock_threads.clear()
        for sock_thread in garbage:
            sock_thread.shutdown()

    def _handle_server(self, server: Server, s_sock: socket) -> None:
        try:
            _LOGGER.info("Listening; port=%d", s_sock.getsockname()[1])
            while True:
                c_sock, _ = s_sock.accept()
                with self._sem:
                    self._sock_threads.append(
                        _SocketThread(
                            c_sock,
                            Thread(
                                target=server.handle_client,
                                name=f"s{self._next_id}-{server.name}-client",
                                args=[c_sock],
                            ),
                        )
                    )
                    self._next_id += 1
        except OSError:
            pass
