from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from datetime import timedelta


app = Flask(__name__)

#Connect to Database                    DBMS     DB_DRIVER  DB_USER DB_PWD   URL     PORT  DB_NAME
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://dazza:dazza@localhost:5432/flaskdb"
app.config["JWT_SECRET_KEY"] = "secret"

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

#Create a Model of a table
class Product(db.Model):
    #Define the name of the table
    __tablename__ = "products"
    # Define a primary key
    id = db.Column(db.Integer, primary_key=True)
    # Define other attributes
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)

# Creating a schema
class ProductSchema(ma.Schema):
    class Meta:
        # Fields
        fields = ("id", "name", "description", "price", "stock")
# 2ways for a schema object
#to handle multiple products
products_schema = ProductSchema(many=True)
#to handle a single product
product_schema = ProductSchema() 

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "email", "password", "is_admin" )

users_schema = UserSchema(many=True, exclude=["password"])

user_schema = UserSchema(exclude=["password"])

@app.route("/auth/register", methods=["POST"])
def register_user():
    try:
        #body of request
        body_data = request.get_json()
        #extracting the password from the body of the request
        password = body_data.get("password")
        #Hashing the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
        #create a user , using the User model
        user = User(
            name = body_data.get("name"),
            email = body_data.get("email"),
            password = hashed_password
        )
        #add it to the db session
        db.session.add(user)
        #commit
        db.session.commit()
        # Return something
        return user_schema.dump(user), 201
    except IntegrityError:
        return {"error": "This email already exists"}, 400
    
@app.route("/auth/login", methods=["POST"])
def login_user():
    #Find the user with tht email
    body_data = request.get_json()
    #If the user exists and the password matches

    stmt = db.select(User).filter_by(email=body_data.get("email"))
    user = db.session.scalar(stmt)
    #Create a jwt token
    if user and bcrypt.check_password_hash(user.password, body_data.get("password")):
        token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
        return {"token": token, "email": user.email, "is_admin": user.is_admin}
    else:
        return {"error": "Invalid email or password"}, 401

    # return the token

    #else
    #return an error message
        
# CLI Commands - Custom
@app.cli.command("create")
def create_table():
    db.create_all()
    print ("create all tables")

# Create another command to seed values to the table
@app.cli.command("seed")
def seed_tables():
    # Create a product object theres two ways
    product1 = Product(
        name = "Fruits",
        description = "fresh fruits",
        price = 15.99,
        stock = 100
    )
    #2
    product2 = Product()
    product2.name = "Vegetables"
    product2.description = "Fresh Vegetables"
    product2.price = 10.99
    product2.stock = 200

    # Add to session
    db.session.add(product1)
    db.session.add(product2)
    #2nd way could be
    # products = [product1, product2]
    # db.session.add_all(products)

    users = [
        User(
            name = "User 1",
            email = "user1@gmail.com",
            password = bcrypt.generate_password_hash("123456").decode('utf8')
        ),
        User(
            
            email = "admin1@gmail.com",
            password = bcrypt.generate_password_hash("abc123").decode('utf8'),
            is_admin = True
        )
    ]

    db.session.add_all(users)

    # Commit it
    db.session.commit()
    print ("tables seeded")

# to drop the tables
@app.cli.command("drop")
def drop_tables():
    db.drop_all()
    print("dropped all tables successfully")

# working with routes
# Define the routes
@app.route("/products")
def get_products():
    # select * from products;
    stmt = db.select(Product)
    products_list = db.session.scalars(stmt)
    data = products_schema.dump(products_list)
    return data

# Dynamic routing
@app.route("/products/<int:product_id>")
def get_product(product_id):
    # select * from products where id = product_id
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)
    if product:
        data = product_schema.dump(product)
        return data
    else:
        return {"error" : f"Product with id {product_id} does not exist"}, 404

# RECAP ABOVE
# /products, GET --> getting all products
# /product/id, GET --> get a specific product
# BELOW:
# /products, POST --> Adding a product
# /products/id, PUT/PATCH --> Edit a product
# /products/id, DELETE --> delete a specific product
#ADD
@app.route("/products", methods=["POST"])
@jwt_required()
def add_products():
    product_fields = request.get_json()
    new_product = Product(
        name = product_fields.get("name"),
        description = product_fields.get("description"),
        price = product_fields.get("price"),
        stock = product_fields.get("stock"),
    )
    db.session.add(new_product)
    db.session.commit()
    return product_schema.dump(new_product), 201
#UPDATE
@app.route("/products/<int:product_id>", methods=["PUT", "PATCH"])
def update_product(product_id):
    # Find the product from the db with the id
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)

    # Retrieve the data from the body of the request
    body_data = request.get_json()
    #Then Update
    if product:
        product.name = body_data.get("name") or product.name
        product.description = body_data.get("description") or product.description
        product.price = body_data.get("price") or product.price
        product.stock = body_data.get("stock") or product.stock

    #Then Commit
        db.session.commit()
        return product_schema.dump(product)
    else:
        return {"error" : f"Product with id {product_id} doesnt exist"}, 404
    
# DELETE
@app.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):

    is_admin = authoriseAsAdmin()
    if not is_admin:
        return {"error": "Not authorised to delete a product"}, 403
    
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)

    if product:
        db.session.delete(product)
        db.session.commit()
        return {"message": f"Product with id {product_id} is deleted."}
    else:
        return {"error" : f"Product with id {product_id} doesnt exist"}, 404
    
def authoriseAsAdmin():
    #get the id of the user from the jwt token
    user_id = get_jwt_identity()
    # find the user in the db with the id
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)
    #check whether the user is an admin or not
    return user.is_admin






