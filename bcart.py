from flask import Flask, render_template, redirect, url_for, request,flash,abort
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine,DateTime
from flask_migrate import Migrate
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
app = Flask(__name__,template_folder='templates',static_folder='static')
app.config['SECRET_KEY'] = 'your-secret-key'

# 超级用户标识（可以根据具体需求进行修改）
SUPER_USER = 'admin'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Bcart.db'  # 设置数据库连接URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 禁用追踪修改

db = SQLAlchemy(app)
# migrate = Migrate(app, db)
# 配置 Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

engine = create_engine('sqlite:///Bcart.db' )
Session = sessionmaker(bind = engine)
session = Session()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    create_on = db.Column(DateTime, default=datetime.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    @classmethod
    def set_admin(cls,username = 'admin',password = 'admin'):
        User(username = username,password = password,is_superuser = True)
        return '请及时修改密码！'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 定义 Product 表模型
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    catalog = db.Column(db.String(50),)
    size = db.Column(db.String(250),)
    price = db.Column(db.Float,)
    short_description = db.Column(db.Text,)
    long_description = db.Column(db.Text,)
    image_path = db.Column(db.Text,)
    create_on = db.Column(DateTime,default = datetime.now)


    def __repr__(self):
        return f'<Product {self.name}>'




# 定义 Order 表模型
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    user = db.relationship('User', backref='orders')
    product = db.relationship('Product', backref='orders')
    create_on = db.Column(DateTime, default=datetime.now())

    def __repr__(self):
        return f'<Order {self.id}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = StringField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class User_info(UserMixin):
    def __init__(self, username):
        self.username = username

    @staticmethod
    def get(user_id):
        return User(user_id)

@app.route('/',methods=['POST','GET'])
def index():
    # flash(User.set_admin())
    # insert_data()
    products = Product.query.all()
    if request.method == 'POST':
        kw_button = request.form['kw_button']
        if kw_button == 'search':
            keyword = request.form['keyword']
            products = Product.query.filter(Product.name.contains(keyword)).all()
    if products is None:
        flash('未查到记录','info')
    else:
        flash(f'已查到「{len(products)}」条记录！', 'success')
    return render_template('index.html', products=products)


@app.route('/categories')
def categories():
    return render_template('categories.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get(product_id)
    return render_template('product.html', product=product)


@app.route('/cart',methods = ["POST","GET"])
@login_required
def cart():
    # db.drop_all()
    # db.create_all()
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        product = Product.query.get(product_id)
        total_price = product.price * quantity

        order = Order(user=current_user, product=product, quantity=quantity, total_price=total_price)
        db.session.add(order)
        db.session.commit()

        flash('Added to cart successfully!', 'success')
        return redirect(url_for('cart'))
    print(current_user)
    orders = Order.query.filter_by(user_id = current_user.id).all()
    print(orders)
    return render_template('cart.html', orders=orders)


# @app.route('/remove_from_cart/<int:product_id>')
# @login_required
# def remove_from_cart(product_id):
#     product = next((p for p in cart if p['id'] == product_id), None)
#     if product:
#         cart.remove(product)
#     return redirect(url_for('cart'))
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
        except:
            # 回滚事务
            db.session.rollback()

            # 显示错误消息给用户
            flash('你易经注册过了，请直接登录！')
        finally:
            return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    # 登录逻辑
    # ...

    if request.method == 'GET':
        return render_template('login.html',)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_type = 'admin' if request.form['username'] == 'admin' else 'normal'
        user = User.query.filter_by(username=username).first()
        # print(1,user,User.query.first().password)
        if user and user.password == password:
            login_user(user)
            flash('Login successful!', 'success')
            if user_type == SUPER_USER:
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
        return redirect(url_for('register'))
    # 模拟用户类型，可以根据实际情况进行修改

    # form = LoginForm()
    # if form.validate_on_submit():
    #     username = form.username.data
    #     password = form.password.data
    #     users = User.query.filter_by(username=username).first()
    #     if username in users and users[username]['password'] == password:
    #         user = User(username)
    #         login_user(user)
    #         if user_type == SUPER_USER:
    #             return render_template('admin.html')
    #         return redirect(url_for('index'))
    # return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))
@app.route('/user')
@login_required
def user():
    return render_template('user.html')
@app.route('/orders')
@login_required
def orders():
    orders = current_user.orders
    return render_template('orders.html', orders=orders)

@app.route('/cart/<order_id>',methods =['POST','GET'])
@login_required
def remove_from_cart(order_id):
    order = Order.query.get(order_id)
    # print(current_user,order.user)
    if current_user != order.user:

        flash('你不能删除!', 'danger')
        return redirect(url_for('user'), )
    db.session.delete(order)
    db.session.commit()
    flash('成功删除!', 'success')
    return redirect(url_for('cart'))


@app.route('/place_order')
@login_required
def place_order():
    orders.extend(cart)
    cart.clear()
    return redirect(url_for('orders'))

@app.route('/create_product', methods=['GET', 'POST'])
@login_required
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        short_description = request.form.get('short_description')
        long_description = request.form.get('long_description')

        # 创建新商品
        new_product = Product(name=name, price=price,
                              short_description=short_description,
                              long_description=long_description)
        db.session.add(new_product)
        db.session.commit()

    flash('New product added successfully.', 'success')
    return render_template('create_product.html')

@app.route('/edit_product/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.short_description = request.form['short_description']
        product.long_description = request.form['long_description']
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin', product_id=product.id))
    return render_template('edit_product.html',product=product)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    products = Product.query.all()
    # if not current_user.is_superuser:
    #     return abort(403)  # 非超级用户无权限访问



    #     # 进行订单数据统计的逻辑
    #     order = db.session.query(
    #     Order.order_id,
    #     Order.customer_name,
    #     Product.name.label('product_name'),
    #     Order.quantity,
    #     (Product.price * Order.quantity).label('total_price')
    # ).join(Product).all()
    #     orders_count = Order.query.count()
    #     total_sales = db.session.query(db.func.sum(Order.total_price)).scalar()
    #     return render_template('admin.html', orders_count=orders_count, total_sales=total_sales)
    return render_template('admin.html',products = products)


if __name__ == 'main':
    # with app.app_context():
    #     # db.drop_all()
    #     db.create_all()
    #     insert_data()

    app.run(debug=True)



