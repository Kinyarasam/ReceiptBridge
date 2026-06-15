#!/usr/bin/env python3
from sqlalchemy import Column, String, Boolean, Text

from models.base_model import BaseModel, Base


class ShopifyStore(BaseModel, Base):
    __tablename__ = "shopify_store"

    shop_domain = Column(String(120), unique=True, index=True, nullable=False)
    access_token = Column(String(120))
    scope = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)