#!/usr/bin/env python3
"""Contains class BaseModel
"""
import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

import models


Base = declarative_base()
t_format = '%Y-%m-%d %H:%M:%S%z'


class BaseModel:
    """The BaseModel class from which future classes will be derived
    """
    id = Column(String(60), primary_key=True, unique=True, index=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __init__(self, *args, **kwargs):
        """Initialization of the base model
        """
        if kwargs:
            for key, value in kwargs.items():
                if key != '__class__':
                    setattr(self, key, value)
            if kwargs.get('created_at', None) and type(self.created_at) is str:
                self.created_at = datetime.strptime(kwargs['created_at'], t_format)
            if kwargs.get('updated_at', None) and type(self.updated_at) is str:
                self.updated_at = datetime.strptime(kwargs['updated_at'], t_format)

        else:
            self.id = str(uuid.uuid4())
            self.created_at = datetime.now(UTC)
            self.updated_at = self.created_at

    def __str__(self):
        """String representation of the BaseModel
        """
        return '[{:s}] ({:s}) {}'.format(self.__class__.__name__,
                                         self.id,
                                         self.__dict__)

    def save(self):
        """updates the attribute 'updated_at' with the current datetime
        """
        try:
            self.updated_at = datetime.strptime(self.updated_at, t_format)
        except Exception as e:
            ...
        models.storage.new(self)
        models.storage.save()

    def to_dict(self, save_fs=None):
        """returns a dictionary containing all key/values of the instance
        """
        new_dict = self.__dict__.copy()
        if 'created_at' in new_dict:
            new_dict['created_at'] = new_dict['created_at'].strftime(t_format)
        if 'updated_at' in new_dict:
            new_dict['updated_at'] = new_dict['updated_at'].strftime(t_format)
        if 'completed_at' in new_dict and new_dict['completed_at'] is not None:
            new_dict['completed_at'] = new_dict['completed_at'].strftime(t_format)
        if 'failed_at' in new_dict and new_dict['failed_at'] is not None:
            new_dict['failed_at'] = new_dict['failed_at'].strftime(t_format)
        if 'assigned_at' in new_dict and new_dict['assigned_at'] is not None:
            new_dict['assigned_at'] = new_dict['assigned_at'].strftime(t_format)
        if 'registered_at' in new_dict and new_dict['registered_at'] is not None:
            new_dict['registered_at'] = new_dict['registered_at'].strftime(t_format)

        new_dict['__class__'] = self.__class__.__name__
        if '_sa_instance_state' in new_dict:
            del new_dict['_sa_instance_state']

        if save_fs is None:
            if 'password' in new_dict:
                del new_dict['password']
        return new_dict

    def delete(self):
        """delete the current instance from the storage
        """
        models.storage.delete(self)

    @classmethod
    def find(cls, *args, **kwargs):
        """Find a record based on the parameters
        """
        return models.storage.find(cls, *args, **kwargs)