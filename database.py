import sqlalchemy
from databases import Database

# URL для підключення. Замініть 'your_password' на ваш пароль.
DATABASE_URL = "mysql+aiomysql://root:h9srjui0YPNrOdx6@localhost:3306/microservices_db"

database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("total_amount", sqlalchemy.Numeric(10, 2)),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
    sqlalchemy.Column("delivery_date", sqlalchemy.Date)
)

order_items = sqlalchemy.Table(
    "order_items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("order_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("orders.id")),
    sqlalchemy.Column("product_id", sqlalchemy.Integer),
    sqlalchemy.Column("quantity", sqlalchemy.Integer),
)