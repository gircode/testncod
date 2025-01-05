"""Fixtures模块"""

from typing import Any, AsyncGenerator, Protocol, TypeVar, runtime_checkable

from pytest import FixtureRequest

T = TypeVar("T")


@runtime_checkable
class AsyncFixture(Protocol[T]):
    async def __call__(self, request: FixtureRequest) -> AsyncGenerator[T, None]: ...


FixtureResult = AsyncGenerator[T, None]
