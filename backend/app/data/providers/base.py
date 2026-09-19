import time as _time
from abc import ABC, abstractmethod

from ..models import RawFinancials


class ProviderError(Exception):
    pass


class FinancialProvider(ABC):
    name = "base"

    @abstractmethod
    def fetch(self, ticker: str) -> RawFinancials:
        raise NotImplementedError


_cache: dict = {}
_CACHE_TTL = 300  # 5 分钟


def fetch_with_fallback(providers: list, ticker: str) -> RawFinancials:
    cache_key = ticker.strip().upper()
    if cache_key in _cache:
        ts, result = _cache[cache_key]
        if _time.time() - ts < _CACHE_TTL:
            return result
    errors = []
    for provider in providers:
        try:
            result = provider.fetch(ticker)
            _cache[cache_key] = (_time.time(), result)
            return result
        except Exception as exc:
            errors.append(f"{provider.name}: {exc}")
    raise ProviderError("all providers failed | " + " | ".join(errors))