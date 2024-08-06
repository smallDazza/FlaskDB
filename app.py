from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)

#Connect to Database                    DBMS     DB_DRIVER  DB_USER DB_PWD   URL     PORT  DB_NAME
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://dazza:dazza@localhost:5432/flaskdb"

db = SQLAlchemy(app)
ma = Marshmallow(app)

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
def delete_product(product_id):
    stmt = db.select(Product).filter_by(id=product_id)
    product = db.session.scalar(stmt)

    if product:
        db.session.delete(product)
        db.session.commit()
        return {"message": f"Product with id {product_id} is deleted."}
    else:
        return {"error" : f"Product with id {product_id} doesnt exist"}, 404






