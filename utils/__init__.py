from itertools import tee
from typing import Iterable, TypeVar

T = TypeVar("T")


def pairwise(iterable: Iterable[T]) -> Iterable[tuple[T, T]]:
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
