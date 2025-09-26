"""Pagination utilities for API responses."""

from typing import Any, Dict, List, Optional, Tuple
from flask import request
from sqlalchemy.orm import Query


class PaginationParams:
    """Pagination parameters for API requests."""
    
    def __init__(
        self,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ):
        self.page = max(1, page)
        self.per_page = min(max(1, per_page), max_per_page)
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order else "asc"
    
    @classmethod
    def from_request(cls, max_per_page: int = 100) -> "PaginationParams":
        """Create pagination parameters from Flask request."""
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        sort_by = request.args.get("sort_by")
        sort_order = request.args.get("sort_order", "asc")
        
        return cls(
            page=page,
            per_page=per_page,
            max_per_page=max_per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )


class PaginatedResponse:
    """Paginated response data structure."""
    
    def __init__(
        self,
        items: List[Any],
        total: int,
        page: int,
        per_page: int,
        pages: int,
        has_prev: bool,
        has_next: bool,
        prev_num: Optional[int],
        next_num: Optional[int]
    ):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = pages
        self.has_prev = has_prev
        self.has_next = has_next
        self.prev_num = prev_num
        self.next_num = next_num
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "per_page": self.per_page,
                "pages": self.pages,
                "has_prev": self.has_prev,
                "has_next": self.has_next,
                "prev_num": self.prev_num,
                "next_num": self.next_num
            }
        }


def paginate_query(
    query: Query,
    pagination: PaginationParams,
    allowed_sort_fields: Optional[List[str]] = None
) -> Tuple[PaginatedResponse, Query]:
    """Paginate a SQLAlchemy query and return paginated response."""
    
    # Apply sorting if specified
    if pagination.sort_by and allowed_sort_fields:
        if pagination.sort_by in allowed_sort_fields:
            sort_column = getattr(query.column_descriptions[0]["entity"], pagination.sort_by)
            if pagination.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
    
    # Get total count
    total = query.count()
    
    # Calculate pagination values
    pages = (total + pagination.per_page - 1) // pagination.per_page
    offset = (pagination.page - 1) * pagination.per_page
    
    # Apply pagination
    paginated_query = query.offset(offset).limit(pagination.per_page)
    
    # Get items
    items = paginated_query.all()
    
    # Calculate pagination metadata
    has_prev = pagination.page > 1
    has_next = pagination.page < pages
    prev_num = pagination.page - 1 if has_prev else None
    next_num = pagination.page + 1 if has_next else None
    
    # Create paginated response
    response = PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pages,
        has_prev=has_prev,
        has_next=has_next,
        prev_num=prev_num,
        next_num=next_num
    )
    
    return response, paginated_query


def create_pagination_links(
    base_url: str,
    page: int,
    pages: int,
    per_page: int,
    **kwargs
) -> Dict[str, Optional[str]]:
    """Create pagination links for API responses."""
    
    def create_url(page_num: Optional[int]) -> Optional[str]:
        if page_num is None:
            return None
        
        params = {"page": page_num, "per_page": per_page}
        params.update(kwargs)
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        return f"{base_url}?{query_string}" if query_string else base_url
    
    return {
        "first": create_url(1) if pages > 0 else None,
        "prev": create_url(page - 1) if page > 1 else None,
        "next": create_url(page + 1) if page < pages else None,
        "last": create_url(pages) if pages > 0 else None
    }
