#!/usr/bin/env python3
"""Contains the class DBStorage
"""
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker, scoped_session

from config import config
from models.base_model import Base
from models.device.device import Device
from models.shopify.shopify_store import ShopifyStore
from models.print.print_job import PrintJob


classes = {
    'ShopifyStore': ShopifyStore,
    'PrintJob': PrintJob,
    'Device': Device,
}


class DBStorage:
    """interacts with the database
    """
    _engine = None
    _session = None

    def __init__(self) -> None:
        """instantiates a DBStorage object
        """
        self._engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        # Base.metadata.drop_all(self._engine)

    def query(self, cls=None):
        if cls not in classes.values():
            return
        return self._session.query(cls)

    def all(self, cls=None):
        temp = {}
        for clss in classes:
            if cls is None or cls is classes[clss] or cls is clss:
                objs = self._session.query(cls).all()
                for obj in objs:
                    key = '{}.{}'.format(obj.__class__.__name__, obj.id)
                    temp[key] = obj
        return temp

    def new(self, obj=None):
        if obj is None:
            return

        try:
            self._session.add(obj)
            self._session.flush()
            self._session.refresh(obj)
        except Exception as e:
            self._session.rollback()
            raise e

    def save(self):
        self._session.commit()

    def delete(self, obj=None):
        if obj is None:
            return
        self._session.delete(obj)

    def reload(self):
        Base.metadata.create_all(self._engine)

        sess_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        session = scoped_session(sess_factory)
        self._session = session

    def close(self):
        self._session.remove()

    def get(self, cls=None, id=None):
        if cls not in classes.values():
            return None

        all_clss = self.all(cls)
        key = '{}.{}'.format(all_clss.__class__.__name__, id)
        return all_clss.get(key)

    def find_first(self, cls=None, order_by='created_at', descending=True, **kwargs):
        if cls not in classes.values():
            return None

        query = self.query(cls)
        if kwargs:
            query = query.filter_by(**kwargs)

        if descending:
            query = query.order_by(desc(getattr(cls, order_by)))
        else:
            query = query.order_by(asc(getattr(cls, order_by)))

        return query.first()

    def find(self, cls=None, *args, **kwargs):
        if cls is None or cls not in classes.values():
            return None

        if 'id' in kwargs.keys():
            kwargs['id'] = str(kwargs['id'])

        return self.find_first(cls=cls, **kwargs)

    def find_all(self, cls=None, order_by='created_at', descending=True, **kwargs):
        if cls not in classes.values():
            return None
        if 'id' in kwargs.keys():
            kwargs['id'] = str(kwargs['id'])
        query = self.query(cls)
        if kwargs:
            query = query.filter_by(**kwargs)

        if descending:
            query = query.order_by(desc(getattr(cls, order_by)))
        else:
            query = query.order_by(asc(getattr(cls, order_by)))

        return query.all()

    def paginate(self, cls=None, page:int=1, per_page:int=20,
                 order_by='created_at', descending=True, **kwargs):
        if cls not in classes.values():
            return [], 0
        query = self.query(cls)

        # Apply filters
        if kwargs:
            query = query.filter_by(**kwargs)

        # Get total count
        total_count = query.count()

        # Apply ordering
        order_column = getattr(cls, order_by, 'created_at')
        if descending:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # Apply pagination
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        return items, total_count