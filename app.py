from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

from models import db, User, ToDo

app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register
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

    return render_template('register.html')


# Login
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

    return render_template('login.html')


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# Home + Create task
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
            return 'Error adding task'

    tasks = ToDo.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', tasks=tasks)


# Update task
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
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
            return 'Error updating task'

    return render_template('update.html', task=task)


# Delete task
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task = ToDo.query.get_or_404(id)

    if task.user_id != current_user.id:
        return "Unauthorized"

    try:
        db.session.delete(task)
        db.session.commit()
        return redirect('/')
    except:
        return 'Error deleting task'


# Run app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)