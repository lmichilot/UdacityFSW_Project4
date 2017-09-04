#!/usr/bin/env python3
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime
import os
import sys

Base = declarative_base()


class Category(Base):
    """ Category Table """
    def __init__(self, name):
        self.name = name

    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    date = Column(DateTime,
                  default=datetime.datetime.now(),
                  onupdate=datetime.datetime.now()
                  )

    @property
    def serialize(self):
        """Serialize Category"""
        return {
            'name': self.name,
            'id': self.id,
        }


class CategoryItem(Base):
    """ Category Item Table """
    def __init__(self, title, description, category_id, user_id):
        self.title = title
        self.description = description
        self.category_id = category_id
        self.user_id = user_id

    __tablename__ = 'category_item'

    id = Column(Integer, primary_key=True)
    title = Column(String(45), nullable=False)
    description = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    user_id = Column(String(250), nullable=False)
    date = Column(DateTime,
                  default=datetime.datetime.now(),
                  onupdate=datetime.datetime.now()
                  )

    @property
    def serialize(self):
        """Serialize CategoryItem"""
        return {
           'id': self.id,
           'title': self.title,
           'cat_id': self.category_id,
           'description': self.description,
        }

engine = create_engine('sqlite:///dbcatalog.db')

Base.metadata.create_all(engine)
