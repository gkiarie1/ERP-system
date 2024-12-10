from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_jwt_extended import decode_token
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kiarie:Georgeluke2018#@localhost/erp'
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this 
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"], logger=True, engineio_logger=True)

def valid_token(token):
    try:
        decoded_token = decode_token(token)
        print(f"Token decoded successfully: {decoded_token}")
        return True
    except Exception as e:
        print(f"Token validation failed: {e}")
        return False
    
@socketio.on('connect')
def connect():
    token = request.args.get('token')
    if not token or not valid_token(token):
        print("Invalid token. Disconnecting.")
        disconnect()
        return  
    print("Client connected with a valid token")

@socketio.on('message')
def handle_message(data):
    print(f"Message received: {data}")
   

# Database models
class User(db.Model):
    __tablename__ = 'users'  
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False) 
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True) 

    # Relationship with Employee
    employee = db.relationship('Employee', backref='user', uselist=False)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    clock_in_status = db.Column(db.String(50), default='Not Clocked In')
    job_schedule = db.Column(db.String(200), nullable=True)
    attendance = db.Column(db.Text, default=0)  
    leave_days = db.Column(db.Integer, default=14)
    warnings = db.Column(db.Text, default=0)  
    skills = db.Column(db.Text, nullable=True)  

with app.app_context():
    db.create_all()

    # Add default admin and employee users 
    def create_default_users():
        admin_email = 'admin@example.com'
        employee_email = 'employee@example.com'
        
        # Check if the admin user exists
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            new_admin = User(email=admin_email, password=hashed_password, role='admin')
            db.session.add(new_admin)
            print(f'Admin user {admin_email} created.')

        # Check if the employee user exists
        employee_user = User.query.filter_by(email=employee_email).first()
        if not employee_user:
            hashed_password = bcrypt.generate_password_hash('employee123').decode('utf-8')
            new_employee = Employee(name='Default Employee')  
            db.session.add(new_employee)
            db.session.flush() 
            new_employee_user = User(email=employee_email, password=hashed_password, role='employee', employee_id=new_employee.id)
            db.session.add(new_employee_user)
            print(f'Employee user {employee_email} created.')

        db.session.commit()

    create_default_users()

# Register a new user 
@app.route('/register', methods=['POST'])
@jwt_required()  
def register():
    current_user = get_jwt_identity()
    # Ensure that only admins can create new accounts
    admin_user = User.query.filter_by(id=current_user).first()
    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'employee') 
    name = data.get('name')

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    if role == 'employee':
        # Create the employee record
        new_employee = Employee(name=name)
        db.session.add(new_employee)
        db.session.flush()  # To get the employee ID

        # Link employee to the user
        new_user = User(email=email, password=hashed_password, role=role, employee_id=new_employee.id)
    else:
        new_user = User(email=email, password=hashed_password, role=role)

    db.session.add(new_user)
    db.session.commit()

    # Emit Socket.IO event for new employee creation
    socketio.emit('employee_created', {'name': name, 'email': email})

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
    user = User.query.filter_by(id=current_user).first()
    employee = Employee.query.filter_by(id=user.employee_id).first()

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

@app.route('/employee/<int:employee_id>/edit', methods=['PATCH'])
@jwt_required()
def edit_employee(employee_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    
    if user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404

    # Parse incoming JSON data
    data = request.get_json()
    try:
        if 'name' in data:
            employee.name = data['name']
        if 'clock_in_status' in data:
            employee.clock_in_status = data['clock_in_status']
        if 'job_schedule' in data:
            employee.job_schedule = data['job_schedule']
        if 'attendance' in data:
            employee.attendance = data['attendance']
        if 'leave_days' in data:
            employee.leave_days = data['leave_days']
        if 'warnings' in data:
            employee.warnings = data['warnings']
        if 'skills' in data:
            employee.skills = data['skills']

        db.session.commit()

        # Emit a Socket.IO event for real-time updates
        socketio.emit('employee_updated', {
            'employee_id': employee.id,
            'name': employee.name,
            'updated_fields': data
        })

        return jsonify({'message': 'Employee updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to update employee.', 'error': str(e)}), 400


# Mark attendance (via QR code)
@app.route('/employee/clock-in', methods=['POST'])
@jwt_required()
def clock_in():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    employee = Employee.query.filter_by(id=user.employee_id).first()

    if employee:
        employee.clock_in_status = 'Clocked In'
        db.session.commit()

        # Emit Socket.IO event for clock-in
        socketio.emit('employee_clocked_in', {'employee_id': employee.id, 'name': employee.name})

        return jsonify({'message': 'Clocked In successfully!'}), 200
    return jsonify({'message': 'Employee not found'}), 404

# Admin Dashboard: View attendance and recommendations
@app.route('/admin/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    current_user = get_jwt_identity()
    admin_user = User.query.filter_by(id=current_user).first()

    # Ensure the current user is an admin
    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    # Retrieve all employees
    employees = Employee.query.all()

    attendance = [{
        'id': emp.id,  # Include employee ID so we can manage skills by ID
        'name': emp.name,
        'skills': emp.skills if emp.skills else 'No skills added',
        'clock_in_status': emp.clock_in_status,
        'job_schedule': emp.job_schedule,
        'leave_days': emp.leave_days,
        'warnings': emp.warnings
    } for emp in employees]


    return jsonify({'attendance': attendance}), 200

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

        # Emit Socket.IO event for skill addition
        print("Emitting skill event")
        socketio.emit('skill_added', {'employee_id': employee.id, 'name': employee.name, 'skill': skill})

        return jsonify({'message': f'Skill "{skill}" added to {employee.name}'}), 200

    return jsonify({'message': 'Employee not found'}), 404

if __name__ == '__main__':
    socketio.run(app, debug=True, port=9988)
