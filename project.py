#!/usr/bin/env python3
# Flask
from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify, flash, Response
from flask import session as catalog_session
from flask import make_response
# DataBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, func
from database_setup import Base, Category, CategoryItem
# Others
from functools import wraps
import random
import string
import httplib2
import json
import requests

# Authentication
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

# ----------------------------------------------------------------------------
#                       App Configuration
# ----------------------------------------------------------------------------
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read()
)['web']['client_id']

APPLICATION_NAME = "Item Catalog App"
app = Flask(__name__)
engine = create_engine('sqlite:///dbcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# ----------------------------------------------------------------------------
#                       Helper Methods
# ----------------------------------------------------------------------------


def authGranted(f):
    """ Checks if the user is logged in or not """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in catalog_session:
            return f(*args, **kwargs)
        else:
            flash("You need to be logged to manage the catalog.")
            return routeToUrl('getHomePage')
    return decorated_function


def identityExist(title):
    """ Checks if an item exists with the same unique title in db """
    results = session.query(CategoryItem).filter_by(title=title).all()
    return len(results) > 0


def createdBy(Item):
    """ Checks if an item exists with the same unique title in db """
    results = session.query(CategoryItem.user_id).filter_by(id=Item.id).one()
    return results[0]


def routeToUrl(sPage):
    """ Main Page """
    return redirect(url_for(sPage))


def mkResponse(text, number):
    """ Return response """
    return make_response(json.dumps(text), 401)


def lostSession():
    """ Clean response """
    del catalog_session['access_token']
    del catalog_session['gplus_id']
    del catalog_session['username']
    del catalog_session['authid']
    return routeToUrl('getHomePage')


def queryitems(mquery):
    query = None
    if mquery == 'latest':
        query = session.query(CategoryItem.id,
                              CategoryItem.title,
                              CategoryItem.description,
                              Category.name,
                              CategoryItem.user_id,) \
            .join(Category, Category.id == CategoryItem.category_id) \
            .order_by(desc(CategoryItem.date)).all()
    elif mquery == 'categories':
        query = session.query(Category.name,
                              func.count(CategoryItem.category_id)
                              .label("conta")) \
            .outerjoin(CategoryItem, CategoryItem.category_id == Category.id) \
            .group_by(Category.name) \
            .order_by(Category.name)
    elif mquery == 'allcategories':
        query = session.query(Category).all()
    else:
        query = None

    return query


# ----------------------------------------------------------------------------
#                             Program
# ----------------------------------------------------------------------------
@app.route('/')
def routeToHome():
    """ Main Page """
    return routeToUrl('getHomePage')


@app.route('/catalog', methods=['GET', 'POST'])
def getHomePage():
    """ Main Page, it shows the latest items added """

    try:
        user = catalog_session['username']
        authid = catalog_session['authid']
    except KeyError:
        user = None
        authid = ''

    if (request.method == 'GET'):
        STATE = ''.join(random.choice(string.ascii_uppercase +
                                      string.digits) for x in range(32))

        catalog_session['state'] = STATE
        latest_items = queryitems('latest')
        categories = queryitems('categories')

        return render_template(
            'home.html',
            categories=categories,
            items=latest_items,
            category_names='',
            user=user,
            authid=authid,
            STATE=STATE,
            itemscount=len(latest_items)
        )
    else:
        # Get authorization code
        if request.args.get('state') != catalog_session['state']:
            lostSession()

        code = request.data

        try:
            # Asign code into credentials object
            oauth_flow = flow_from_clientsecrets(
                'client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = mkResponse(
                'Failed to upgrade the authorization code.', 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Access token is valid ?
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
               % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])

        # Error ?
        if result.get('error') is not None:
            lostSession()

        # Token valid for user ?
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            lostSession()

        # Token valid for App ?
        if result['issued_to'] != CLIENT_ID:
            lostSession()

        stored_credentials = catalog_session.get('credentials')
        stored_gplus_id = catalog_session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            lostSession()

        # Store the access info in the session
        catalog_session['access_token'] = credentials.access_token
        catalog_session['gplus_id'] = gplus_id

        # Get user information for header
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)
        data = answer.json()
        catalog_session['username'] = data['name']
        catalog_session['authid'] = data['id']
        return routeToUrl('getHomePage')


@app.route('/catalog.json')
def getCatalog():
    """ Returns catalog in json format """
    output_json = []
    categories = queryitems('allcategories')
    for category in categories:
        items = session.query(CategoryItem).filter_by(category_id=category.id)
        category_output = {}
        category_output["id"] = category.id
        category_output["name"] = category.name
        category_output["Item"] = [i.serialize for i in items]
        output_json.append(category_output)
    return jsonify(Categories=output_json)


@app.route('/catalog/categories/<path:category_name>/')
def getCategoryItems(category_name):
    """ Returns items for a given category name """
    categories = queryitems('categories')

    selected_category = session.query(
        Category).filter_by(name=category_name).one()
    items = session.query(CategoryItem).filter_by(
        category_id=selected_category.id).all()

    try:
        user = catalog_session['username']
        authid = catalog_session['authid']
    except KeyError:
        user = None
        authid = ''

    return render_template(
        'category_detail.html',
        selected_category=selected_category,
        user=user,
        authid=authid,
        items=items,
        categories=categories,
        itemscount=len(items)
    )


@app.route('/catalog/items/<path:item_title>/')
def getItemDetails(item_title):
    """ Returns a category item given its title """
    item = session.query(CategoryItem).filter_by(title=item_title).one()
    category = session.query(Category).filter_by(id=item.category_id).one()
    return render_template(
        'item_detail.html', item=item, category=category
    )


@app.route('/catalog/items/new', methods=['GET', 'POST'])
@authGranted
def getCreateItem():
    """ Handles creation of a new category item """
    categories = queryitems('allcategories')
    try:
        user = catalog_session['username']
    except KeyError:
        user = None
    if request.method == 'POST':
        title = None
        description = None
        mchk = None
        try:
            title = request.form['title']
        except KeyError:
            title = ''

        try:
            description = request.form['description']
        except KeyError:
            description = ''

        try:
            mchk = request.form['chksavenew']
        except KeyError:
            mchk = 'off'

        if title == '' or description == '':
            flash("Please complete all fields")
            return redirect(url_for('getCreateItem'))

        if identityExist(title):
            flash("Please enter a different title. Item " +
                  title + " already exists.")
            return redirect(url_for('getCreateItem'))
        category_id = request.form['category_id']
        authid = catalog_session['authid']
        oCategoryItem = CategoryItem(title, description, category_id, authid)
        session.add(oCategoryItem)
        session.commit()

        mpage = None
        if (mchk == 'on'):
            mpage = 'getCreateItem'
        else:
            mpage = 'getHomePage'

        return routeToUrl(mpage)
    else:
        return render_template(
            'create_item.html', categories=categories, user=user
        )


@app.route('/catalog/items/<path:item_title>/edit', methods=['GET', 'POST'])
@authGranted
def getEditItem(item_title):
    """ Handles updating an existing catalog item """
    editedItem = session.query(CategoryItem).filter_by(title=item_title).one()
    category = session.query(Category).filter_by(
        id=editedItem.category_id).one()
    actualuser = catalog_session['authid']
    registerby = createdBy(editedItem)
    if (actualuser != registerby):
        flash("You have access to manage your own items, please review.")
        return routeToUrl('getHomePage')

    categories = queryitems('allcategories')
    if request.method == 'POST':
        if request.form['title']:
            title = request.form['title']
            if item_title != title and identityExist(title):
                flash("Please enter a different title. Item " +
                      title + " already exists.")
                return redirect(url_for('getEditItem', item_title=item_title))
            editedItem.title = title
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category_id']:
            editedItem.category_id = request.form['category_id']
        session.add(editedItem)
        session.commit()
        return routeToUrl('getHomePage')
    else:
        user = catalog_session['username']
        return render_template(
            'edit_item.html', item=editedItem, category=category,
            categories=categories, user=user
        )


@app.route('/catalog/items/<path:item_title>/delete', methods=['POST'])
@authGranted
def deleteItem(item_title):
    """ Deletes a category item """
    itemToDelete = session.query(
        CategoryItem).filter_by(title=item_title).one()
    actualuser = catalog_session['authid']
    registerby = createdBy(itemToDelete)
    if actualuser != registerby:
        flash("You have access to manage your own items, please review.")
        return routeToUrl('getHomePage')

    session.delete(itemToDelete)
    session.commit()
    return routeToUrl('getHomePage')


@app.route('/gdisconnect')
def gdisconnect():
    """ Helper for disconnecting from Google Auth """
    access_token = catalog_session['access_token']
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    murl = 'https://accounts.google.com/o/oauth2/revoke?token=%s'
    url = murl % catalog_session['access_token']

    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del catalog_session['access_token']
        del catalog_session['gplus_id']
        del catalog_session['username']
        del catalog_session['authid']
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return routeToUrl('getHomePage')
    else:
        lostSession()
        return routeToUrl('getHomePage')

if __name__ == '__main__':
    app.secret_key = 'secret'
    app.debug = True
    app.run(host='0.0.0.0', port=8094)
