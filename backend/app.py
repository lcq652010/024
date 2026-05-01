from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime, date, timedelta
from functools import wraps
import calendar
import jwt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

STANDARD_CHECK_IN_TIME = (9, 0)
STANDARD_CHECK_OUT_TIME = (18, 0)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app)


def calculate_attendance_status(check_in_time, check_out_time):
    status = '正常'
    if check_in_time:
        check_in_hour = check_in_time.hour
        check_in_minute = check_in_time.minute
        if check_in_hour > STANDARD_CHECK_IN_TIME[0] or \
           (check_in_hour == STANDARD_CHECK_IN_TIME[0] and check_in_minute > STANDARD_CHECK_IN_TIME[1]):
            status = '迟到'
    
    if check_out_time:
        check_out_hour = check_out_time.hour
        check_out_minute = check_out_time.minute
        if check_out_hour < STANDARD_CHECK_OUT_TIME[0] or \
           (check_out_hour == STANDARD_CHECK_OUT_TIME[0] and check_out_minute < STANDARD_CHECK_OUT_TIME[1]):
            if status == '迟到':
                status = '迟到早退'
            else:
                status = '早退'
    
    return status


def generate_token(admin_id, username):
    payload = {
        'admin_id': admin_id,
        'username': username,
        'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'success': False, 'message': 'Token 缺失，请先登录'}), 401
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_admin = {
                'admin_id': data['admin_id'],
                'username': data['username']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token 已过期，请重新登录'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token 无效'}), 401
        
        return f(current_admin, *args, **kwargs)
    return decorated


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
        token = generate_token(admin.id, admin.username)
        return jsonify({
            'success': True, 
            'message': '登录成功', 
            'token': token,
            'admin': {'id': admin.id, 'username': admin.username}
        })
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401


@app.route('/api/check-token', methods=['GET'])
@token_required
def check_token(current_admin):
    return jsonify({'success': True, 'admin': current_admin})


@app.route('/api/employees', methods=['GET'])
@token_required
def get_employees(current_admin):
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
@token_required
def create_employee(current_admin):
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
@token_required
def get_employee(current_admin, employee_id):
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
@token_required
def update_employee(current_admin, employee_id):
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
@token_required
def delete_employee(current_admin, employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    Attendance.query.filter_by(employee_id=employee_id).delete()
    
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'success': True, 'message': '员工删除成功'})


@app.route('/api/attendance/checkin', methods=['POST'])
@token_required
def check_in(current_admin):
    data = request.json
    employee_id = data.get('employee_id')
    employee = Employee.query.get_or_404(employee_id)
    
    today = date.today()
    existing_attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()
    current_time = datetime.now().time()
    
    if existing_attendance:
        if existing_attendance.check_in:
            return jsonify({'success': False, 'message': '今日已打卡'}), 400
        else:
            existing_attendance.check_in = current_time
            existing_attendance.status = calculate_attendance_status(current_time, existing_attendance.check_out)
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': '签到成功', 
                'check_in': existing_attendance.check_in.isoformat(),
                'status': existing_attendance.status
            })
    else:
        status = calculate_attendance_status(current_time, None)
        new_attendance = Attendance(
            employee_id=employee_id,
            date=today,
            check_in=current_time,
            status=status
        )
        db.session.add(new_attendance)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': '签到成功', 
            'check_in': new_attendance.check_in.isoformat(),
            'status': new_attendance.status
        })


@app.route('/api/attendance/checkout', methods=['POST'])
@token_required
def check_out(current_admin):
    data = request.json
    employee_id = data.get('employee_id')
    employee = Employee.query.get_or_404(employee_id)
    
    today = date.today()
    attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()
    current_time = datetime.now().time()
    
    if not attendance or not attendance.check_in:
        return jsonify({'success': False, 'message': '今日未签到，无法签退'}), 400
    
    if attendance.check_out:
        return jsonify({'success': False, 'message': '今日已签退'}), 400
    
    attendance.check_out = current_time
    attendance.status = calculate_attendance_status(attendance.check_in, current_time)
    db.session.commit()
    return jsonify({
        'success': True, 
        'message': '签退成功', 
        'check_out': attendance.check_out.isoformat(),
        'status': attendance.status
    })


@app.route('/api/attendance/records', methods=['GET'])
@token_required
def get_attendance_records(current_admin):
    employee_id = request.args.get('employee_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', type=int, default=1)
    page_size = request.args.get('page_size', type=int, default=10)
    status = request.args.get('status')
    
    query = Attendance.query
    
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    
    if status:
        query = query.filter(Attendance.status == status)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Attendance.date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Attendance.date <= end)
    
    total = query.count()
    
    pagination = query.order_by(Attendance.date.desc()).paginate(
        page=page, 
        per_page=page_size, 
        error_out=False
    )
    
    records = pagination.items
    
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
    
    return jsonify({
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': pagination.pages,
        'data': result
    })


@app.route('/api/attendance/monthly-stats', methods=['GET'])
@token_required
def get_monthly_stats(current_admin):
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
        
        normal_count = 0
        late_count = 0
        early_count = 0
        late_early_count = 0
        
        for record in attendances:
            if record.status == '正常':
                normal_count += 1
            elif record.status == '迟到':
                late_count += 1
            elif record.status == '早退':
                early_count += 1
            elif record.status == '迟到早退':
                late_early_count += 1
        
        stats = {
            'employee_id': employee_id,
            'employee_name': employee.name if employee else '未知',
            'year': year,
            'month': month,
            'total_days': num_days,
            'attendance_days': len(set(a.date for a in attendances if a.check_in)),
            'normal_count': normal_count,
            'late_count': late_count,
            'early_count': early_count,
            'late_early_count': late_early_count,
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
            
            normal_count = 0
            late_count = 0
            early_count = 0
            late_early_count = 0
            
            for record in emp_attendances:
                if record.status == '正常':
                    normal_count += 1
                elif record.status == '迟到':
                    late_count += 1
                elif record.status == '早退':
                    early_count += 1
                elif record.status == '迟到早退':
                    late_early_count += 1
            
            all_stats.append({
                'employee_id': emp.id,
                'employee_name': emp.name,
                'department': emp.department,
                'attendance_days': len(set(a.date for a in emp_attendances if a.check_in)),
                'normal_count': normal_count,
                'late_count': late_count,
                'early_count': early_count,
                'late_early_count': late_early_count
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
