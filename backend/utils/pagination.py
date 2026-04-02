"""SmartSafety+ - Pagination & Query utilities"""
from typing import Optional, List, Any
from fastapi import Query


class PaginationParams:
    """Standard pagination parameters for list endpoints."""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Número de página"),
        page_size: int = Query(50, ge=1, le=200, description="Items por página"),
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size


async def paginated_find(
    collection,
    query: dict = None,
    projection: dict = None,
    sort_field: str = "created_at",
    sort_order: int = -1,
    page: int = 1,
    page_size: int = 50,
):
    """
    Paginated MongoDB find with total count.
    Returns: {"items": [...], "total": N, "page": P, "page_size": S, "pages": T}
    """
    query = query or {}
    projection = projection or {"_id": 0}
    skip = (page - 1) * page_size

    total = await collection.count_documents(query)
    cursor = collection.find(query, projection).sort(sort_field, sort_order).skip(skip).limit(page_size)
    items = await cursor.to_list(page_size)

    pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
