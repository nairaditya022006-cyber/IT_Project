import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key_for_taskflow' # Replace with os.urandom(24) in prod
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- App Context Setup ---
with app.app_context():
    db.create_all()

# --- Middleware ---
@app.before_request
def check_authentication():
    # Allow access to static files and auth routes without login
    allowed_routes = ['index', 'login', 'register', 'static']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

# --- Routes ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists.', 'danger')
            return redirect(url_for('register'))

        hashed_pwd = generate_password_hash(password)
        new_user = User(full_name=full_name, email=email, password_hash=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['full_name'] = user.full_name
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('full_name', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    user_tasks = Task.query.filter_by(user_id=user_id).order_by(Task.due_date.asc()).all()
    
    today = date.today()
    
    # Calculate stats
    total_tasks = len(user_tasks)
    completed_tasks = len([t for t in user_tasks if t.status == 'Completed'])
    pending_tasks = total_tasks - completed_tasks
    overdue_tasks = len([t for t in user_tasks if t.status == 'Pending' and t.due_date < today])
    
    # Categorize tasks
    tasks_today = [t for t in user_tasks if t.due_date == today and t.status == 'Pending']
    tasks_upcoming = [t for t in user_tasks if t.due_date > today and t.status == 'Pending']
    recent_tasks = sorted(user_tasks, key=lambda x: x.created_at, reverse=True)[:5]
    
    stats = {
        'total': total_tasks,
        'pending': pending_tasks,
        'completed': completed_tasks,
        'overdue': overdue_tasks
    }
    
    return render_template('dashboard.html', 
                           stats=stats, 
                           tasks_today=tasks_today, 
                           tasks_upcoming=tasks_upcoming,
                           recent_tasks=recent_tasks)

@app.route('/task/add', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority')
        
        try:
            due_date = date.fromisoformat(due_date_str)
            new_task = Task(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                user_id=session['user_id']
            )
            db.session.add(new_task)
            db.session.commit()
            flash('Task added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Invalid date format.', 'danger')
            
    return render_template('task_form.html', action="Add")

@app.route('/task/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.priority = request.form.get('priority')
        task.status = request.form.get('status')
        
        try:
            task.due_date = date.fromisoformat(request.form.get('due_date'))
            db.session.commit()
            flash('Task updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Invalid date format.', 'danger')
            
    return render_template('task_form.html', action="Edit", task=task)

@app.route('/task/complete/<int:id>')
def complete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))
        
    task.status = 'Completed'
    db.session.commit()
    flash('Task marked as completed!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/task/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))
        
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
