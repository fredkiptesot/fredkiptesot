import sqlite3
import hashlib
from datetime import datetime
import getpass

# ====================== DATABASE SETUP ======================
def init_db():
    conn = sqlite3.connect('leave_management.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT,
        total_leaves INTEGER DEFAULT 30,
        used_leaves INTEGER DEFAULT 0
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        emp_id INTEGER,
        FOREIGN KEY (emp_id) REFERENCES employees(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY,
        emp_id INTEGER,
        leave_type TEXT,
        start_date TEXT,
        end_date TEXT,
        days INTEGER,
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        applied_date TEXT,
        FOREIGN KEY (emp_id) REFERENCES employees(id)
    )''')
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect('leave_management.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    return stored_hash == hash_password(password)

def calculate_days(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return (end - start).days + 1

# ====================== AUTH ======================
def create_default_users():
    conn = get_db()
    cursor = conn.cursor()
    
    if not cursor.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                      ('admin', hash_password('admin123'), 'admin'))
    
    cursor.execute("SELECT id FROM employees WHERE name='John Doe'")
    emp = cursor.fetchone()
    emp_id = emp[0] if emp else None
    if not emp_id:
        cursor.execute("INSERT INTO employees (name, department) VALUES ('John Doe', 'IT')")
        emp_id = cursor.lastrowid
    
    if not cursor.execute("SELECT 1 FROM users WHERE username='john'").fetchone():
        cursor.execute("INSERT INTO users (username, password_hash, role, emp_id) VALUES (?, ?, ?, ?)",
                      ('john', hash_password('employee123'), 'employee', emp_id))
    
    conn.commit()
    conn.close()

def login():
    print("\n🔐 Login to Leave Management System")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, emp_id, password_hash FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(user[3], password):
        print(f"✅ Login successful! Welcome, {username} ({user[1]})")
        return user[0], user[1], user[2]
    print("❌ Invalid username or password!")
    return None, None, None

# ====================== CORE FUNCTIONS ======================
def add_employee(name, department):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO employees (name, department) VALUES (?, ?)", (name, department))
    conn.commit()
    conn.close()
    print(f"✅ Employee '{name}' added successfully!")

def view_employees():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, department, total_leaves, used_leaves, 
               (total_leaves - used_leaves) as remaining 
        FROM employees
    """)
    employees = cursor.fetchall()
    conn.close()
    
    if not employees:
        print("\nNo employees found.")
        return
    
    print("\n" + "="*85)
    print("EMPLOYEE LIST")
    print("="*85)
    print(f"{'ID':<5} {'Name':<20} {'Department':<15} {'Total':<6} {'Used':<6} {'Remaining':<10}")
    print("-"*85)
    for emp in employees:
        print(f"{emp[0]:<5} {emp[1]:<20} {emp[2]:<15} {emp[3]:<6} {emp[4]:<6} {emp[5]:<10}")
    print("="*85)

def apply_leave(emp_id, leave_type, start_date, end_date, reason):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT total_leaves, used_leaves FROM employees WHERE id=?", (emp_id,))
    result = cursor.fetchone()
    if not result:
        print("❌ Employee not found!")
        return
    total, used = result
    remaining = total - used
    days = calculate_days(start_date, end_date)
    
    if days > remaining:
        print(f"❌ Insufficient balance! Remaining: {remaining} days")
        return
    
    applied_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''INSERT INTO leaves 
        (emp_id, leave_type, start_date, end_date, days, reason, applied_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)''', 
        (emp_id, leave_type, start_date, end_date, days, reason, applied_date))
    conn.commit()
    conn.close()
    print(f"✅ Leave request of {days} days submitted!")

def approve_leave(leave_id, status="Approved"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, days FROM leaves WHERE id=?", (leave_id,))
    leave = cursor.fetchone()
    if not leave:
        print("❌ Leave request not found!")
        return
    if status == "Approved":
        cursor.execute("UPDATE employees SET used_leaves = used_leaves + ? WHERE id=?", (leave[1], leave[0]))
    cursor.execute("UPDATE leaves SET status=? WHERE id=?", (status, leave_id))
    conn.commit()
    conn.close()
    print(f"✅ Leave request #{leave_id} has been {status}!")

def view_leave_requests(status=None, emp_id=None):
    conn = get_db()
    cursor = conn.cursor()
    if emp_id:
        cursor.execute("SELECT * FROM leaves WHERE emp_id=?", (emp_id,))
    elif status:
        cursor.execute("SELECT * FROM leaves WHERE status=?", (status,))
    else:
        cursor.execute("SELECT * FROM leaves")
    leaves = cursor.fetchall()
    conn.close()
    
    if not leaves:
        print("\nNo leave requests found.")
        return
    
    print("\n" + "="*100)
    print("LEAVE REQUESTS")
    print("="*100)
    print(f"{'ID':<4} {'EmpID':<6} {'Type':<12} {'Start':<12} {'End':<12} {'Days':<5} {'Status':<10} {'Applied':<12}")
    print("-"*100)
    for l in leaves:
        print(f"{l[0]:<4} {l[1]:<6} {l[2]:<12} {l[3]:<12} {l[4]:<12} {l[5]:<5} {l[7]:<10} {l[8]:<12}")
    print("="*100)

# ====================== MAIN MENU ======================
def main():
    init_db()
    create_default_users()
    print("🏢 Employee Leave Management System\n")
    
    user_id, role, emp_id = login()
    if not user_id:
        return
    
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        
        if role == 'admin':
            print("1. Add New Employee")
            print("2. View All Employees")
            print("3. View All Leave Requests")
            print("4. Approve/Reject Leave")
            print("5. Logout")
        else:
            print("1. Apply for Leave")
            print("2. View My Leave Requests")
            print("3. Logout")
        
        print("="*60)
        choice = input("\nEnter your choice: ")
        
        if role == 'admin':
            if choice == '1':
                name = input("Enter employee name: ").strip()
                dept = input("Enter department: ").strip()
                if name and dept:
                    add_employee(name, dept)
                    view_employees()   # Auto show updated list
                else:
                    print("❌ Name and Department cannot be empty!")
            elif choice == '2':
                view_employees()
            elif choice == '3':
                status = input("Filter by status (Pending/Approved/Rejected) or press Enter for all: ").strip()
                view_leave_requests(status if status else None)
            elif choice == '4':
                try:
                    leave_id = int(input("Enter Leave Request ID: "))
                    st = input("Approve or Reject? (A/R): ").upper()
                    approve_leave(leave_id, "Approved" if st == 'A' else "Rejected")
                except:
                    print("❌ Invalid input!")
            elif choice == '5':
                print("👋 Logged out successfully!")
                break
            else:
                print("❌ Invalid choice!")
        else:  # Employee
            if choice == '1':
                try:
                    ltype = input("Leave Type: ")
                    start = input("Start Date (YYYY-MM-DD): ")
                    end = input("End Date (YYYY-MM-DD): ")
                    reason = input("Reason: ")
                    apply_leave(emp_id, ltype, start, end, reason)
                except:
                    print("❌ Invalid input!")
            elif choice == '2':
                view_leave_requests(None, emp_id)
            elif choice == '3':
                print("👋 Logged out successfully!")
                break
            else:
                print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
