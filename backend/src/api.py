import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db_rollback, db_close_session
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route("/drinks")
def get_drinks():
    drinks = Drink.query.all()
    drinks_list = [d.short() for d in drinks]
    return jsonify({
        'success':True,
        'drinks':drinks_list
    })

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks-detail")
@requires_auth(permission="get:drinks-detail")
def get_drinks_detail(payload):
    drinks = Drink.query.all()
    drinks_list = [d.long() for d in drinks]
    return jsonify({
        'success':True,
        'drinks':drinks_list
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=['Post'])
@requires_auth(permission='post:drinks')
def add_drink(payload):
    body = request.get_json()
    if body['recipe'] == None or len(body['recipe']) == 0:
        abort(400)
    
    title = body['title']
    recipe = body['recipe']
    if type(recipe)  is not list:
        recipe = list(recipe)
    recipe = str(recipe).replace("'", '"')
    
    success = True
    result = []
    try:
        new_drink = Drink(title= title, recipe= recipe)
        new_drink.insert()
        result.append(new_drink.long())
    except Exception as e:
        print(str(e))
        success = False
        db_rollback()
        abort(400)
    
    finally:
        db_close_session()
    
    return jsonify({
        'success':success,
        'drinks': result
    })

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:id>", methods=['PATCH'])
@requires_auth("patch:drinks")
def update_drink(payload, id):
    body = request.get_json()
    drink = Drink.query.get(id)
    if drink == None:
        abort(404)
    
    
    success = True
    result = []
    try:
        if "title" in body:
            drink.title = body['title']
        if "recipe" in body:
            drink.recipe = body['recipe']
        drink.update()
        result = [drink.long()]    
    except Exception as e:
        print(str(e))
        success = False
        db_rollback()
        abort(400)
    
    finally:
        db_close_session()
    
    return jsonify({
        'success':success,
        'drinks': result
    })

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:id>", methods=['DELETE'])
@requires_auth("delete:drinks")
def delete_drink(payload, id):
    body = request.get_json()
    drink = Drink.query.get(id)
    if drink == None:
        abort(404)
    success = True
    try:
        drink.delete()
    except Exception as e:
        print(str(e))
        success = False
        db_rollback()
        abort(400)
    
    finally:
        db_close_session()
    
    return jsonify({
        'success':success,
        'delete': id
    })


## Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
'''
@TODO implement error handler for 404
    error handler should conform to general task above 
'''
@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''
@app.errorhandler(AuthError)
def auth_error(error):
    status_code = error.status_code
    error_dict = error.error
    return jsonify({
        "success":False,
        "error":status_code,
        "message": error_dict['description'],
    }), status_code

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "Bad request"
                    }), 400