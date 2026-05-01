from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime, date
import calendar

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    position = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    join_date = db.Column(db.Date, nullable=False)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    status = db.Column(db.String(20), default='正常')
    
    employee = db.relationship('Employee', backref=db.backref('attendances', lazy=True))


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and bcrypt.check_password_hash(admin.password, password):
        return jsonify({'success': True, 'message': '登录成功', 'admin': {'id': admin.id, 'username': admin.username}})
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401


@app.route('/api/employees', methods=['GET'])
def get_employees():
    employees = Employee.query.all()
    result = []
    for emp in employees:
        result.append({
            'id': emp.id,
            'name': emp.name,
            'department': emp.department,
            'position': emp.position,
            'phone': emp.phone,
            'email': emp.email,
            'join_date': emp.join_date.isoformat()
        })
    return jsonify(result)


@app.route('/api/employees', methods=['POST'])
def create_employee():
    data = request.json
    join_date = datetime.strptime(data.get('join_date'), '%Y-%m-%d').date()
    
    new_employee = Employee(
        name=data.get('name'),
        department=data.get('department'),
        position=data.get('position'),
        phone=data.get('phone'),
        email=data.get('email'),
        join_date=join_date
    )
    
    db.session.add(new_employee)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '员工添加成功', 'id': new_employee.id}), 201


@app.route('/api/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    return jsonify({
        'id': employee.id,
        'name': employee.name,
        'department': employee.department,
        'position': employee.position,
        'phone': employee.phone,
        'email': employee.email,
        'join_date': employee.join_date.isoformat()
    })


@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    data = request.json
    
    employee.name = data.get('name', employee.name)
    employee.department = data.get('department', employee.department)
    employee.position = data.get('position', employee.position)
    employee.phone = data.get('phone', employee.phone)
    employee.email = data.get('email', employee.email)
    
    if data.get('join_date'):
        employee.join_date = datetime.strptime(data.get('join_date'), '%Y-%m-%d').date()
    
    db.session.commit()
    return jsonify({'success': True, 'message': '员工信息更新成功'})


@app.route('/api/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    Attendance.query.filter_by(employee_id=employee_id).delete()
    
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'success': True, 'message': '员工删除成功'})


@app.route('/api/attendance/checkin', methods=['POST'])
def check_in():
    data = request.json
    employee_id = data.get('employee_id')
    employee = Employee.query.get_or_404(employee_id)
    
    today = date.today()
    existing_attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()
    
    if existing_attendance:
        if existing_attendance.check_in:
            return jsonify({'success': False, 'message': '今日已打卡'}), 400
        else:
            existing_attendance.check_in = datetime.now().time()
            db.session.commit()
            return jsonify({'success': True, 'message': '签到成功', 'check_in': existing_attendance.check_in.isoformat()})
    else:
        new_attendance = Attendance(
            employee_id=employee_id,
            date=today,
            check_in=datetime.now().time()
        )
        db.session.add(new_attendance)
        db.session.commit()
        return jsonify({'success': True, 'message': '签到成功', 'check_in': new_attendance.check_in.isoformat()})


@app.route('/api/attendance/checkout', methods=['POST'])
def check_out():
    data = request.json
    employee_id = data.get('employee_id')
    employee = Employee.query.get_or_404(employee_id)
    
    today = date.today()
    attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()
    
    if not attendance or not attendance.check_in:
        return jsonify({'success': False, 'message': '今日未签到，无法签退'}), 400
    
    if attendance.check_out:
        return jsonify({'success': False, 'message': '今日已签退'}), 400
    
    attendance.check_out = datetime.now().time()
    db.session.commit()
    return jsonify({'success': True, 'message': '签退成功', 'check_out': attendance.check_out.isoformat()})


@app.route('/api/attendance/records', methods=['GET'])
def get_attendance_records():
    employee_id = request.args.get('employee_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Attendance.query
    
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Attendance.date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Attendance.date <= end)
    
    records = query.order_by(Attendance.date.desc()).all()
    
    result = []
    for record in records:
        result.append({
            'id': record.id,
            'employee_id': record.employee_id,
            'employee_name': record.employee.name,
            'date': record.date.isoformat(),
            'check_in': record.check_in.isoformat() if record.check_in else None,
            'check_out': record.check_out.isoformat() if record.check_out else None,
            'status': record.status
        })
    
    return jsonify(result)


@app.route('/api/attendance/monthly-stats', methods=['GET'])
def get_monthly_stats():
    employee_id = request.args.get('employee_id', type=int)
    year = request.args.get('year', type=int, default=date.today().year)
    month = request.args.get('month', type=int, default=date.today().month)
    
    _, num_days = calendar.monthrange(year, month)
    first_day = date(year, month, 1)
    last_day = date(year, month, num_days)
    
    query = Attendance.query.filter(
        Attendance.date >= first_day,
        Attendance.date <= last_day
    )
    
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    attendances = query.all()
    
    if employee_id:
        employee = Employee.query.get(employee_id)
        stats = {
            'employee_id': employee_id,
            'employee_name': employee.name if employee else '未知',
            'year': year,
            'month': month,
            'total_days': num_days,
            'attendance_days': len(set(a.date for a in attendances if a.check_in)),
            'records': []
        }
        
        for record in attendances:
            stats['records'].append({
                'date': record.date.isoformat(),
                'check_in': record.check_in.isoformat() if record.check_in else None,
                'check_out': record.check_out.isoformat() if record.check_out else None,
                'status': record.status
            })
        
        return jsonify(stats)
    else:
        employees = Employee.query.all()
        all_stats = []
        
        for emp in employees:
            emp_attendances = [a for a in attendances if a.employee_id == emp.id]
            all_stats.append({
                'employee_id': emp.id,
                'employee_name': emp.name,
                'attendance_days': len(set(a.date for a in emp_attendances if a.check_in))
            })
        
        return jsonify({
            'year': year,
            'month': month,
            'total_days': num_days,
            'stats': all_stats
        })


def init_db():
    db.create_all()
    
    if not Admin.query.first():
        hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = Admin(username='admin', password=hashed_password)
        db.session.add(admin)
        db.session.commit()
        print('默认管理员已创建: 用户名=admin, 密码=admin123')


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
