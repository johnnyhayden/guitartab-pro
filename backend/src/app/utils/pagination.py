"""Advanced pagination utilities for the GuitarTab Pro API."""

from typing import Any, Dict, List, Optional, Tuple, Generic, TypeVar
from dataclasses import dataclass
from sqlalchemy import func
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import Select

T = TypeVar('T')


@dataclass
class PaginationInfo:
    """Information about pagination state."""
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int]
    prev_page: Optional[int]


@dataclass
class PaginatedResult(Generic[T]):
    """Result container for paginated data."""
    items: List[T]
    pagination: PaginationInfo
    total: int


class AdvancedPagination:
    """Advanced pagination utilities with cursor-based and offset-based options."""

    @staticmethod
    def offset_based_paginate(
        query: Query,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
    ) -> Tuple[List[Any], PaginationInfo]:
        """
        Perform offset-based pagination.
        
        Args:
            query: SQLAlchemy query object
            page: Current page number (1-based)
            per_page: Number of items per page
            max_per_page: Maximum allowed items per page
            
        Returns:
            Tuple of (items, pagination_info)
        """
        # Validate and limit per_page
        per_page = min(per_page, max_per_page)
        per_page = max(1, per_page)
        page = max(1, page)

        # Get total count
        total = query.count()

        # Calculate pagination info
        pages = (total + per_page - 1) // per_page
        has_next = page < pages
        has_prev = page > 1
        next_page = page + 1 if has_next else None
        prev_page = page - 1 if has_prev else None

        pagination_info = PaginationInfo(
            page=page,
            per_page=per_page,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=next_page,
            prev_page=prev_page
        )

        # Get items for current page
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        return items, pagination_info

    @staticmethod
    def cursor_based_paginate(
        query: Query,
        cursor_field: str,
        cursor_value: Optional[Any] = None,
        limit: int = 20,
        reverse: bool = False
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Perform cursor-based pagination for better performance with large datasets.
        
        Args:
            query: SQLAlchemy query object
            cursor_field: Field to use for cursor pagination (e.g., 'created_at')
            cursor_value: Current cursor value
            limit: Number of items to retrieve
            reverse: Whether to paginate backwards
            
        Returns:
            Tuple of (items, cursor_info)
        """
        # Apply cursor filter
        if cursor_value:
            cursor_column = getattr(query.column_descriptions[0]['entity'], cursor_field)
            if reverse:
                query = query.filter(cursor_column < cursor_value)
            else:
                query = query.filter(cursor_column > cursor_value)

        # Apply ordering
        cursor_column = getattr(query.column_descriptions[0]['entity'], cursor_field)
        if reverse:
            query = query.order_by(cursor_column.desc())
        else:
            query = query.order_by(cursor_column.asc())

        # Get one extra item to determine if there are more pages
        items = query.limit(limit + 1).all()

        # Check if there are more pages
        has_next = len(items) > limit
        if has_next:
            items = items[:limit]

        # Prepare cursor info for next page
        cursor_info = {}
        if items:
            last_item = items[-1]
            cursor_info['next_cursor'] = getattr(last_item, cursor_field)
            cursor_info['has_next'] = has_next
        else:
            cursor_info['next_cursor'] = None
            cursor_info['has_next'] = False

        # Since we don't know the total count in cursor-based pagination,
        # we can't provide previous page info
        cursor_info['has_prev'] = cursor_value is not None

        return items, cursor_info


class PaginationBuilder:
    """Builder pattern for constructing pagination queries."""

    def __init__(self, query: Query):
        self.query = query
        self._filters = []
        self._sorts = []
        self._paginated = False
        self._page = 1
        self._per_page = 20

    def filter_by(self, **filters) -> 'PaginationBuilder':
        """Add filters to the query."""
        for field, value in filters.items():
            if value is not None:
                column = getattr(self.query.column_descriptions[0]['entity'], field)
                if isinstance(value, (list, tuple)):
                    self._filters.append(column.in_(value))
                elif isinstance(value, str) and '%' in value:
                    self._filters.append(column.ilike(value))
                else:
                    self._filters.append(column == value)
        return self

    def filter_range(self, field: str, min_value: Optional[Any] = None, max_value: Optional[Any] = None) -> 'PaginationBuilder':
        """Add range filter to the query."""
        if min_value is not None or max_value is not None:
            column = getattr(self.query.column_descriptions[0]['entity'], field)
            if min_value is not None:
                self._filters.append(column >= min_value)
            if max_value is not None:
                self._filters.append(column <= max_value)
        return self

    def filter_search(self, *fields: str, search_term: str) -> 'PaginationBuilder':
        """Add search across multiple fields."""
        if search_term:
            conditions = []
            for field in fields:
                column = getattr(self.query.column_descriptions[0]['entity'], field)
                conditions.append(column.ilike(f"%{search_term}%"))
            if conditions:
                from sqlalchemy import or_
                self._filters.append(or_(*conditions))
        return self

    def sort_by(self, field: str, ascending: bool = True) -> 'PaginationBuilder':
        """Add sort to the query."""
        column = getattr(self.query.column_descriptions[0]['entity'], field)
        if ascending:
            self._sorts.append(column.asc())
        else:
            self._sorts.append(column.desc())
        return self

    def paginate(self, page: int = 1, per_page: int = 20, pagination_type: str = 'offset') -> 'PaginationBuilder':
        """Set pagination parameters."""
        self._paginated = True
        self._page = page
        self._per_page = per_page
        return self

    def execute(self) -> Tuple[List[Any], PaginationInfo]:
        """Execute the built query with pagination."""
        # Apply filters
        for filter_condition in self._filters:
            self.query = self.query.filter(filter_condition)

        # Apply sorts
        if self._sorts:
            self.query = self.query.order_by(*self._sorts)

        # Apply pagination
        if self._paginated:
            return AdvancedPagination.offset_based_paginate(
                self.query, self._page, self._per_page
            )
        else:
            # Return all results without pagination
            items = self.query.all()
            pagination_info = PaginationInfo(
                page=1,
                per_page=len(items),
                total=len(items),
                pages=1,
                has_next=False,
                has_prev=False,
                next_page=None,
                prev_page=None
            )
            return items, pagination_info


class PageCache:
    """Simple in-memory cache for pagination results."""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, PaginatedResult] = {}
        self.max_size = max_size
        self.access_order: List[str] = []

    def _make_key(self, query_params: Dict[str, Any]) -> str:
        """Create a cache key from query parameters."""
        sorted_params = sorted(query_params.items())
        return str(hash(tuple(sorted_params)))

    def get(self, query_params: Dict[str, Any]) -> Optional[PaginatedResult]:
        """Get cached pagination result."""
        key = self._make_key(query_params)
        
        if key in self.cache:
            # Move to end of access order (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        
        return None

    def set(self, query_params: Dict[str, Any], result: PaginatedResult) -> None:
        """Cache pagination result."""
        key = self._make_key(query_params)
        
        # Remove oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = result
        self.access_order.append(key)

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()


# Global cache instance
pagination_cache = PageCache(max_size=200)


def get_paginated_result(
    query: Query,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100,
    cache_key: Optional[Dict[str, Any]] = None
) -> Tuple[List[Any], PaginationInfo]:
    """
    Get paginated results with optional caching.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        max_per_page: Maximum allowed items per page
        cache_key: Parameters to use for cache key
        
    Returns:
        Tuple of (items, pagination_info)
    """
    if cache_key is not None:
        cache_key['page'] = page
        cache_key['per_page'] = per_page
        cached_result = pagination_cache.get(cache_key)
        if cached_result:
            return cached_result.items, cached_result.pagination

    items, pagination_info = AdvancedPagination.offset_based_paginate(
        query, page, per_page, max_per_page
    )

    # Cache the result
    if cache_key is not None:
        paginated_result = PaginatedResult(
            items=items,
            pagination=pagination_info,
            total=pagination_info.total
        )
        pagination_cache.set(cache_key, paginated_result)

    return items, pagination_info
