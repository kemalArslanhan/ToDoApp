from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Kullanıcı modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Görev modeli
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Integer, nullable=False)  # Gün cinsinden süre
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    assigned_user = db.relationship('User', backref=db.backref('tasks', lazy=True))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['is_admin']:
        tasks = Task.query.all()
        users = User.query.filter_by(is_admin=False).all()  # Tüm mitarbeiter kullanıcıları al
        return render_template('dashboard_admin.html', tasks=tasks, users=users)
    else:
        tasks = Task.query.filter_by(assigned_to=session['user_id']).all()
        return render_template('dashboard.html', tasks=tasks)

@app.route('/assign_task/<int:user_id>', methods=['GET', 'POST'])
def assign_task(user_id):
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        duration = int(request.form['duration'])  # Süreyi formdan al
        due_date = datetime.utcnow() + timedelta(days=duration)  # Bitiş tarihini hesapla
        new_task = Task(title=title, description=description, assigned_to=user_id, duration=duration, due_date=due_date)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    return render_template('assign_task.html', user=user)

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = Task.query.get_or_404(task_id)
    if task.assigned_to != session['user_id']:
        return redirect(url_for('dashboard'))
    task.completed = True
    task.completion_date = datetime.utcnow()  # Tamamlanma tarihini kaydet
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/reassign_task/<int:task_id>', methods=['GET', 'POST'])
def reassign_task(task_id):
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        new_user_id = request.form['new_user_id']
        task.assigned_to = new_user_id
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    users = User.query.filter_by(is_admin=False).all()  # Admin olmayan tüm kullanıcıları al
    return render_template('reassign_task.html', task=task, users=users)

if __name__ == '__main__':
    app.run(debug=True)