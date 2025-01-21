from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_jwt_extended import decode_token
import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kiarie:Georgeluke2018#@localhost/erp'
app.config['JWT_SECRET_KEY'] = 'super-secret'  
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
class Employee(db.Model):
    __tablename__ = 'employee' 
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    clock_in_status = db.Column(db.String(50), default='Not Clocked In')
    clock_out_status = db.Column(db.String(50), default='New Entry')
    machine_line = db.Column(db.String(200), nullable=True)
    attendance = db.Column(db.Text, default=0)
    leave_day = db.Column(db.Integer, default=14)
    warnings = db.Column(db.JSON, default=[])
    contract_details = db.Column(db.Text, nullable=True)
    overtime_hours = db.Column(db.Float, default=0.0)

    # Relationship to User
    user = db.relationship('User', back_populates='employee', uselist=False)  


class User(db.Model):
    __tablename__ = 'users'  
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.String(50), unique=True, nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False) 
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)  

    # Relationship with Employee
    employee = db.relationship('Employee', back_populates='user', uselist=False)


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
            new_admin = User(staff_id="ADM001", email=admin_email, password=hashed_password, role='admin')
            db.session.add(new_admin)
            print(f'Admin user {admin_email} created.')

        # Check if the employee user exists
        employee_user = User.query.filter_by(email=employee_email).first()
        if not employee_user:
            hashed_password = bcrypt.generate_password_hash('employee123').decode('utf-8')
            new_employee = Employee(name='Default Employee', staff_id='EMP001') 
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
    admin_user = User.query.filter_by(id=current_user).first()
    if not admin_user or admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'employee')
    name = data.get('name')
    clock_in_status = data.get('clock_in_status', 'Not Clocked In')
    clock_out_status = data.get('clock_out_status', 'New Entry')
    machine_line = data.get('machine_line')
    leave_day = data.get('leave_day', 14)
    warnings = data.get('warnings', 0)
    contract_details = data.get('contract_details', 'No contract details')
    overtime_hours = data.get('overtime_hours', 0.0)

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 400

    try:
        staff_id = str(uuid.uuid4().hex[:5]).upper()

        # Ensure staff_id is unique
        while User.query.filter_by(staff_id=staff_id).first():
            staff_id = str(uuid.uuid4().hex[:5]).upper()

      
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if role == 'employee':
            new_employee = Employee(
                name=name,
                staff_id=staff_id,
                machine_line=machine_line,
                clock_in_status=clock_in_status,
                clock_out_status=clock_out_status,
                leave_day=leave_day,
                warnings=warnings,
                contract_details=contract_details,
                overtime_hours=overtime_hours
            )
            db.session.add(new_employee)
            db.session.flush()  

            new_user = User(
                email=email,
                password=hashed_password,
                role=role,
                staff_id=staff_id,
                employee_id=new_employee.id
            )
            db.session.add(new_user)

        elif role == 'admin':
            new_user = User(
                email=email,
                password=hashed_password,
                role=role,
                staff_id=staff_id
            )
            db.session.add(new_user)

        else:
            return jsonify({'message': 'Invalid role specified.'}), 400

        db.session.commit()

        # Emit Socket.IO event only after successful commit
        socketio.emit('employee_created', {
            'attendance': {
                'staff_id': staff_id,
                'name': name,
                'clock_in_status': clock_in_status,
                'clock_out_status': clock_out_status,
                'machine_line': machine_line,
                'leave_day': leave_day,
                'warnings': warnings,
                'contract_details': contract_details,
                'overtime_hours': overtime_hours
            }
        })

        return jsonify({'message': 'User created successfully!', 'staff_id': staff_id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500



# User login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    staff_id = data.get('staff_id')
    password = data.get('password')

    user = User.query.filter_by(staff_id=staff_id).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(days=1))
        
        # Update clock-in status if employee logs in
        if user.role == 'employee':
            employee = Employee.query.filter_by(staff_id=staff_id).first()
            if employee:
                employee.clock_in_status = 'Clocked In'
                db.session.commit()
                
                # Emit clock-in event
                socketio.emit('employee_clocked_in', {'employee_id': employee.id, 'name': employee.name})

        return jsonify({'access_token': access_token, 'role': user.role}), 200 
    return jsonify({'message': 'Invalid credentials'}), 401

# Employee Clock-Out
@app.route('/employee/clock-out', methods=['POST'])
@jwt_required()
def clock_out():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    employee = Employee.query.filter_by(id=user.employee_id).first()

    if employee:
        # Calculate overtime
        clock_out_time = datetime.datetime.now()
        shift_end_time = datetime.datetime.combine(clock_out_time.date(), datetime.time(17, 0)) 
        if clock_out_time > shift_end_time:
            overtime = (clock_out_time - shift_end_time).total_seconds() / 3600  
            employee.overtime_hours += overtime

        employee.clock_in_status = 'Not Clocked In'
        db.session.commit()

        # Emit clock-out event
        socketio.emit('employee_clocked_out', {'employee_id': employee.id, 'name': employee.name})

        return jsonify({'message': 'Clocked Out successfully!'}), 200
    return jsonify({'message': 'Employee not found'}), 404

# Admin Dashboard
@app.route('/admin/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    current_user = get_jwt_identity()
    admin_user = User.query.filter_by(id=current_user).first()

    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    # Retrieve all employees
    employees = Employee.query.all()
    print("Employees retrieved:", employees)
    print(f"Found {len(employees)} employees")


    attendance = [{
            'id': emp.id,
            'staff_id': emp.staff_id,
            'name': emp.name,
            'contract_details': emp.contract_details or 'No contract details',
            'clock_in_status': emp.clock_in_status,
            'clock_out_status': emp.clock_out_status,
            'machine_line': emp.machine_line,
            'day': emp.leave_day,
            'warnings_count': len(emp.warnings or []),  
            'warnings_details': emp.warnings,  
            'overtime_hours': emp.overtime_hours
        } for emp in employees]


    return jsonify({'attendance': attendance}), 200

# Add Warnings
@app.route('/employee/<int:employee_id>/add-warning', methods=['POST'])
@jwt_required()
def add_warning(employee_id):
    current_user = get_jwt_identity()
    admin_user = User.query.filter_by(id=current_user).first()

    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    warning_text = data.get('warning', '').strip()

    if not warning_text:
        return jsonify({'message': 'Warning text cannot be empty'}), 400

    employee = Employee.query.filter_by(id=employee_id).first()
    if employee:
        warnings_list = employee.warnings or []
        warnings_list.append(warning_text)
        employee.warnings = warnings_list
        db.session.commit()

        # Emit warning event
        socketio.emit('warning_added', {
            'employee_id': employee.id,
            'warnings': employee.warnings
        })

        return jsonify({'message': 'Warning added successfully!', 'warnings': employee.warnings}), 200

    return jsonify({'message': 'Employee not found'}), 404


# Update Employee Field
@app.route('/employee/<int:employee_id>/edit', methods=['PATCH'])
@jwt_required()
def edit_employee(employee_id):
    current_user = get_jwt_identity()
    admin_user = User.query.filter_by(id=current_user).first()

    if admin_user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    field, value = next(iter(data.items())) 

    employee = Employee.query.filter_by(id=employee_id).first()
    if employee:
        if hasattr(employee, field):
            setattr(employee, field, value)
            db.session.commit()

            # Emit update event
            socketio.emit('employee_field_updated', {'employee_id': employee.id, 'field': field, 'value': value})

            return jsonify({'message': f'{field} updated successfully!', 'field': field, 'value': value}), 200
        return jsonify({'message': f'Invalid field: {field}'}), 400

    return jsonify({'message': 'Employee not found'}), 404


@app.route('/employee/profile', methods=['GET'])
@jwt_required()
def get_employee_profile():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    employee = Employee.query.filter_by(id=user.employee_id).first()

    profile = {
            'staff_id': employee.staff_id,
            'name': employee.name,
            'clock_in_status': employee.clock_in_status,
            'clock_out_status': employee.clock_out_status,
            'machine_line': employee.machine_line, 
            'leave_days': employee.leave_day,
            'warnings': employee.warnings,
            'contract_details': employee.contract_details if employee.contract_details else 'No contract details',
            'overtime_hours': employee.overtime_hours
        }

    return jsonify(profile), 200

@app.route('/employee/apply-leave', methods=['POST'])
@jwt_required()
def apply_leave():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()


    data = request.get_json()
    leave_date = data.get('leave_date')

    socketio.emit('leave_request', {
        'employee_id': user.employee.id,
        'name': user.employee.name,
        'leave_date': leave_date
    })

    return jsonify({'message': 'Leave request submitted successfully!'}), 200

# Apply for Overtime
@app.route('/employee/apply-overtime', methods=['POST'])
@jwt_required()
def apply_overtime():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    data = request.get_json()
    overtime_date = data.get('overtime_date')

    socketio.emit('overtime_request', {
        'employee_id': user.employee.id,
        'name': user.employee.name,
        'overtime_date': overtime_date
    })

    return jsonify({'message': 'Overtime request submitted successfully!'}), 200


if __name__ == '__main__':
    socketio.run(app, debug=True, port=9988)
