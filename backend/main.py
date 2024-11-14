from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kiarie:Georgeluke2018#@localhost/erp'
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this to a strong secret key in production
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin' or 'employee'

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    clock_in_status = db.Column(db.String(50), default='Not Clocked In')
    job_schedule = db.Column(db.String(200), nullable=True)
    attendance = db.Column(db.Text, nullable=True)  # Store attendance as JSON strings or use another table
    leave_days = db.Column(db.Integer, default=0)
    warnings = db.Column(db.Text, nullable=True)  # Store warnings as JSON strings or use another table
    skills = db.Column(db.Text, nullable=True)  # Store skills as JSON strings

# Create the tables
with app.app_context():
    db.create_all()

# Register a new user (Admin creates user accounts)
@app.route('/register', methods=['POST'])
@jwt_required()  # Admin only route
def register():
    current_user = get_jwt_identity()
    # Ensure that only admins can create new accounts
    admin_user = User.query.filter_by(id=current_user).first()
    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'employee')  # Default role is 'employee'

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully!'}), 201

# User login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(days=1))
        return jsonify({'access_token': access_token, 'role': user.role}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Employee Profile (Protected)
@app.route('/employee/profile', methods=['GET'])
@jwt_required()
def get_employee_profile():
    current_user = get_jwt_identity()
    employee = Employee.query.filter_by(id=current_user).first()

    if employee:
        return jsonify({
            'name': employee.name,
            'clock_in_status': employee.clock_in_status,
            'job_schedule': employee.job_schedule,
            'attendance': employee.attendance,
            'leave_days': employee.leave_days,
            'warnings': employee.warnings,
            'skills': employee.skills
        }), 200
    return jsonify({'message': 'Employee not found'}), 404

# Mark attendance (via QR code)
@app.route('/employee/clock-in', methods=['POST'])
@jwt_required()
def clock_in():
    current_user = get_jwt_identity()
    employee = Employee.query.filter_by(id=current_user).first()

    if employee:
        employee.clock_in_status = 'Clocked In'
        db.session.commit()
        return jsonify({'message': 'Clocked In successfully!'}), 200
    return jsonify({'message': 'Employee not found'}), 404

# Admin Dashboard: View attendance and recommendations
@app.route('/admin/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    current_user = get_jwt_identity()
    admin_user = User.query.filter_by(id=current_user).first()

    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    employees = Employee.query.all()
    attendance = [{'name': emp.name, 'skills': emp.skills, 'clock_in_status': emp.clock_in_status} for emp in employees]
    recommendations = [{'message': 'Reallocate Alice Smith to Line A'}]  # Replace with actual logic

    return jsonify({'attendance': attendance, 'recommendations': recommendations}), 200

# Add skill to employee (Admin only)
@app.route('/employee/<int:employee_id>/add-skill', methods=['POST'])
@jwt_required()
def add_skill(employee_id):
    current_user = get_jwt_identity()
    admin_user = User.query.filter_by(id=current_user).first()

    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    skill = data.get('skill')
    employee = Employee.query.filter_by(id=employee_id).first()

    if employee:
        skills = employee.skills.split(",") if employee.skills else []
        skills.append(skill)
        employee.skills = ",".join(skills)
        db.session.commit()
        return jsonify({'message': f'Skill "{skill}" added to {employee.name}'}), 200

    return jsonify({'message': 'Employee not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
