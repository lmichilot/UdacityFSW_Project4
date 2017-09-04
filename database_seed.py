from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import *
from database_setup import Base, Category, CategoryItem
from sqlalchemy.orm import sessionmaker

# Create repository
engine = create_engine('sqlite:///dbcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Clear the tables
session.query(Category).delete()
session.query(CategoryItem).delete()

# Add categories
sample_categories = [
    'Soccer',
    'Basketball',
    'BaseBall',
    'Frisbee',
    'Snowboarding',
    'Rock Climbing',
    'Foosball',
    'Skating',
    'Hockey']

for category_name in sample_categories:
    category = Category(category_name)
    session.add(category)
session.commit()
