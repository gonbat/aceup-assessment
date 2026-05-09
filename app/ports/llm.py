from pydantic import BaseModel
from abc import ABC, abstractmethod


class LLm(ABC):
    @abstractmethod
    def run_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[BaseModel],
    ) -> BaseModel:
        pass

    @abstractmethod
    async def run_completion_async(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[BaseModel],
    ) -> BaseModel:
        pass
