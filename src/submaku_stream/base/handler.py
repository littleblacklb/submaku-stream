from __future__ import annotations

from abc import ABC, abstractmethod


class Handler(ABC):
    """
    The Handler interface declares a method for building the chain of handlers.
    It also declares a method for executing a request.
    """

    def __init__(self, handler: Handler = None):
        self._next_handler = handler

    @abstractmethod
    def set_next(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    async def handle(self, value):
        pass
