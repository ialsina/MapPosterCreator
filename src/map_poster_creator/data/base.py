from abc import ABC, abstractmethod
from functools import cache
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseModel(ABC, Generic[T]):
    """
    Base model class that provides a fetch() method and caches the result in .data.

    Subclasses should implement the fetch() method to load or compute the data.
    The result is cached and accessible via the .data property.
    """

    def __init__(self):
        self._data = None
        self._fetched = False

    @abstractmethod
    def fetch(self) -> T:
        """
        Fetch or compute the data. This method should be implemented by subclasses.

        Returns:
            The fetched data of type T.
        """
        pass

    @property
    def data(self) -> T:
        """
        Get the cached data. If not yet fetched, calls fetch() first.

        If fetch() raises an exception, it's not cached, so subsequent calls
        will retry. This allows for retry logic in fetch() implementations.

        Returns:
            The cached data.
        """
        if not self._fetched:
            try:
                self._data = self.fetch()
                self._fetched = True
            except Exception:
                # Don't cache failed fetches - allow retry on next access
                # This is important for handling transient errors (e.g., file not ready)
                raise
        return self._data

    def clear_cache(self):
        """Clear the cached data, forcing a refetch on next access."""
        self._data = None
        self._fetched = False


class CachedModel(BaseModel[T]):
    """
    A model that uses functools.cache for automatic caching.

    Note: functools.cache is equivalent to functools.lru_cache(maxsize=None),
    so this provides the same caching behavior as LRU cache with unlimited size.
    """

    def __init__(self):
        super().__init__()
        # Wrap fetch with cache (which is lru_cache(maxsize=None) under the hood)
        self._cached_fetch = cache(self._fetch_impl)

    def _fetch_impl(self) -> T:
        """Internal implementation that will be cached."""
        return super().fetch()

    @property
    def data(self) -> T:
        """Get the cached data using functools.cache."""
        return self._cached_fetch()
