from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Create a model for To-Do items
class ToDo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create model for User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    
# Route for User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        new_user = User(username=username, password=password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')
        except:
            return 'Username already exists'
    else:
        return render_template('register.html')
    
# Route for User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
        else:
            return 'Invalid username or password'
    else:
        return render_template('login.html')
    
# Route for User Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# Protecting the main route with login_required
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        task_title = request.form['task']
        task_desc = request.form['description']
        new_task = ToDo(
            title=task_title,
            description=task_desc,
            user_id=current_user.id
        )
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your task'
    else:
        tasks = ToDo.query.filter_by(user_id=current_user.id).all()
        return render_template('index.html', tasks=tasks)

# Route for Task Update
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = ToDo.query.get_or_404(id)
    if task.user_id != current_user.id:
        return "Unauthorized"
    if request.method == 'POST':
        task.title = request.form['task']
        task.description = request.form['description']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('update.html', task=task)
    
# Route for Task Deletion
@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = ToDo.query.get_or_404(id)
    if task_to_delete.user_id != current_user.id:
        return "Unauthorized"
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that task'
 

    
if __name__ == '__main__':
    with app.app_context():
        db.drop_all()  # Drop existing tables for a clean slate
        db.create_all()
    app.run(debug=True)