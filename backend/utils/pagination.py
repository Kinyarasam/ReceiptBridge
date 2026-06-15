#!/usr/bin/env python3
"""Pagination utilities for consistent paginated responses
"""
import base64
from dataclasses import dataclass, asdict
from math import ceil
from typing import Dict, Optional, Any, List, Callable

from flask import request, g, make_response, jsonify
from sqlalchemy import or_, desc


@dataclass
class PaginationParams:
    """Pagination parameters for consistent paginated responses
    """
    page: int = 1
    per_page: int = 20
    max_per_page: int = 100
    offset: int = 0

    def __post_init__(self):
        """Validate and normalize pagination parameters
        """
        self.page = max(1, self.page)
        self.per_page = min(self.max_per_page, max(1, self.per_page))
        self.offset = (self.page - 1) * self.per_page

    @classmethod
    def from_request(cls, default_per_page: int = 20, max_per_page: int = 100):
        """Create paginationParams from request query parameters
        """
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', default_per_page, type=int)
        return cls(page=page, per_page=per_page, max_per_page=max_per_page)

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary
        """
        return {
            'page': self.page,
            'per_page': self.per_page,
            'offset': self.offset,
        }

@dataclass
class PaginationMetadata:
    """Pagination metadata for response
    """
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_prev: bool
    has_next: bool
    prev_page: Optional[int] = None
    next_page: Optional[int] = None

    @classmethod
    def from_params(cls, params: PaginationParams, total_items: int):
        """Create metadata from pagination parameters and total count
        """
        total_pages = ceil(total_items / params.per_page) if total_items > 0 else 1

        return cls(
            current_page=params.page,
            per_page=params.per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_prev=params.page > 1,
            has_next=params.page < total_pages,
            prev_page=params.page - 1 if params.page > 1 else None,
            next_page=params.page + 1 if params.page < total_pages else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary
        """
        return asdict(self)

    def store_in_g(self):
        """Store pagination metadata in Flask's g object for middleware
        """
        g.pagination = self.to_dict()

class Pagination:
    """Handle pagination for database queries
    """
    def __init__(self, page: int = 1, per_page: int = 20, max_per_page: int = 100):
        """Initialize pagination parameters

        Args:
            page (int): current page number (1-indexed)
            per_page (int): number of items per page
            max_per_page (int): maximum number of items per page
        """
        self.page = max(1, page)
        self.per_page = min(max_per_page, max(1, per_page))
        self.offset = (self.page - 1) * self.per_page

    @classmethod
    def from_request(cls, default_per_page: int = 20, max_per_page: int = 100):
        """Create pagination instance from request query parameters

        Args:
            default_per_page (int): default items per page
            max_per_page (int): maximum number of items per page

        Returns:
            Pagination: pagination instance
        """
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', default_per_page, type=int)
        return cls(page, per_page, max_per_page)

    def apply_to_query(self, query):
        """Apply pagination to SQLAchemy query

        Args:
            query (SQLAlchemy query): SQLAlchemy query object

        Returns:
            query: Paginated query
        """
        return query.offset(self.offset).limit(self.per_page)

    def get_pagination_dict(self, total_count: int) -> dict:
        """Get pagination metadata dictionary

        Args:
            total_count (int): total number of items

        Returns:
            dict: Pagination metadata
        """
        total_pages = ceil(total_count / self.per_page) if total_count > 0 else 1

        pagination = {
            'current_page': self.page,
            'per_page': self.per_page,
            'total_pages': total_pages,
            'total_items': total_count,
            'has_prev': self.page > 1,
            'has_next': self.page < total_pages,
            'prev_page': self.page - 1 if self.page > 1 else None,
            'next_page': self.page + 1 if self.page < total_pages else None,
        }

        # Store in flask's g object for response middleware
        g.pagination = pagination

        return pagination

class PaginatedResponse:
    """Build paginated response"""

    def __init__(self, items: List[Any], params: PaginationParams, total_items: int):
        """Initialize paginated response

        Args:
            items (list): list of items for current page
            params (PaginationParams): pagination parameters
            total_items (int): total number of items
        """
        self.items = items
        self.params = params
        self.total_items = total_items
        self.metadata = PaginationMetadata.from_params(params, total_items)

    def to_dict(self, item_serializer: Optional[Callable] = None) -> Dict:
        """Convert to dictionary

        Args:
            item_serializer (callable): Function to serialize each item

        Returns:
            dict: Dictionary with paginated response structure
        """
        if item_serializer:
            items = [item_serializer(item) for item in self.items]
        else:
            items = self.items

        return {
            'success': True,
            'items': items,
            'pagination': self.metadata.to_dict(),
            'total_count': self.total_items,
        }

    def to_response(self, item_serializer: Optional[Callable] = None):
        """Create Flask JSON response

        Args:
            item_serializer (callable): Function to serialize each item

        Returns:
            tuple: (response_dict, status_code)
        """
        return make_response(jsonify(self.to_dict(item_serializer=item_serializer)), 200)

class CursorPagination:
    """Cursor-based for better performance on large datasets"""

    def __init__(self, cursor: str = None, limit: int = 20, max_limit: int = 100):
        """Initialize cursor pagination

        Args:
            cursor (str): cursor string for pagination
            limit (int): Number of items to return
            max_limit(int): Maximum number of items to return
        """
        self.cursor = cursor
        self.limit = min(max_limit, max(1, limit))
        self.next_cursor = None

    @classmethod
    def from_request(cls, default_limit: int = 20, max_limit: int = 100):
        """Create CursorPagination from request query parameters"""
        cursor = request.args.get('cursor', None)
        limit = request.args.get('limit', default_limit, type=int)
        return cls(cursor, limit, max_limit)

    def apply_to_query(self, query, id_column, cursor_column='created_at'):
        """Apply cursor pagination to query

        Args:
            query: SQLAlchemy query object
            id_column (str): column name for unique identifier
            cursor_column (str): column name for ordering

        Returns:
            query: paginated query
        """
        query = query.order_by(desc(getattr(query.column_descriptions[0]['type'], cursor_column)))
        query = query.order_by(desc(id_column))

        if self.cursor:
            # Decode cursor (format: timestamp: id)
            try:
                cursor_decoded = base64.b64decode(self.cursor).decode('utf-8')
                timestamp, item_id = cursor_decoded.split(':')
                # Add filter for cursor

            except:
                pass

        return query.limit(self.limit + 1)

    def get_cursor_response(self, items, id_column, cursor_column='created_at'):
        """Get cursor-based response

        Args:
            items (list): list of items
            id_column (str): column name for unique identifier
            cursor_column (str): column for ordering

        Returns:
            dict: Response with next_cursor
        """
        has_more = len(items) > self.limit
        if has_more:
            items = items[:-1]
            last_item = items[-1]

            # Generate next cursor
            cursor_value = f"{getattr(last_item, cursor_column)}:{getattr(last_item, id_column)}"
            self.next_cursor = base64.b64encode(cursor_value.encode('utf-8')).decode('utf-8')

        return {
            'items': items,
            'next_cursor': self.next_cursor,
            'has_more': has_more,
            'limit': self.limit,
        }

class FilterBuilder:
    """Build filters for paginated queries"""

    def __init__(self):
        self.filters = []

    def add_filter(self, field: str, value: Any, operator: str = 'eq'):
        """Add a filter condition

        Args:
            field (str): field name
            value (Any): value to filter by
            operator (str): Comparison operator (eq, ne, gt, lt, gte, lte, contains, starts_with, ends_with, in)
        """
        if value is None or value == '':
            return self

        if operator == 'eq':
            self.filters.append(getattr(self.model, field) == value)
        elif operator == 'ne':
            self.filters.append(getattr(self.model, field) != value)
        elif operator == 'gt':
            self.filters.append(getattr(self.model, field) > value)
        elif operator == 'lt':
            self.filters.append(getattr(self.model, field) < value)
        elif operator == 'gte':
            self.filters.append(getattr(self.model, field) >= value)
        elif operator == 'lte':
            self.filters.append(getattr(self.model, field) <= value)
        elif operator == 'contains':
            self.filters.append(getattr(self.model, field).contains(value))
        elif operator == 'starts_with':
            self.filters.append(getattr(self.model, field).startswith(value))
        elif operator == 'ends_with':
            self.filters.append(getattr(self.model, field).endswith(value))
        elif operator == 'in':
            self.filters.append(getattr(self.model, field).in_(value))

        return self

    def add_search(self, search_fields: List[str], search_term: str):
        """Add search filter across multiple fields"""
        if not search_term:
            return self

        search_filters = []
        for field in search_fields:
            search_field = field.append(getattr(self.model, field).ilike(f'%{search_term}%'))

        self.filters.append(or_(*search_filters))
        return self

    def build(self, model):
        """Build the filters"""
        self.model = model
        return self.filters



