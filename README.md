# Project 4: Catalog Item
### by Luis Michilot

## What it is and does

A Python program that provides a list of items within a variety of categories as well as provide 
a user registration and authentication system. 
Registered users will have the ability to post, edit and delete items.

## Required Libraries and Dependencies

Python 3.x is required to run this project.

## Project contents

This project consists for the following files:

* database_setup.py
* database_seed.py
* project.py
* requirements.txt
* client_secrets.json

# Components

- Flask Routing and Templating
- SQLAlchemy to communicate with the back-end database
- API endpoints that return json files
- Google Login for authentication
- Front-end built with boostrap

# To run the application:
- Install the dependency libraries:
  [`Flask`,`Sqlalchemy`,`Requests`,`Oauth2client`]
  by running `pip install -r requirements.txt`
- Create the database by running : `python database_setup.py`
- Seeding the database by running : `python database_seed.py`
- Run `python project.py` (it will run on port 8094)
 
