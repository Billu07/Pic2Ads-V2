from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Agent(ABC, Generic[InputT, OutputT]):
    """Minimal agent contract for typed, testable components."""

    name: str

    @abstractmethod
    async def run(self, payload: InputT) -> OutputT:
        raise NotImplementedError
