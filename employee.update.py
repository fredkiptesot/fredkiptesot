import datetime
import json
import os
import getpass
from typing import Dict, Optional

DATA_FILE = "leave_management_data.json"

# ====================== USER AUTHENTICATION ======================
USERS = {
    # Administrators (Full Access)
    "admin1": {"password": "admin123", "role": "admin", "name": "Admin One"},
    "admin2": {"password": "admin123", "role": "admin", "name": "Admin Two"},
    "admin3": {"password": "admin123", "role": "admin", "name": "Admin Three"},
    
    # Employees will be added dynamically using their emp_id
}

class Employee:
    def __init__(self, emp_id: str, name: str, department: str, email: str, joining_date: str):
        self.emp_id = emp_id
        self.name = name
        self.department = department
        self.email = email
        self.joining_date = joining_date
        
        self.leave_balance = {"casual": 15, "sick": 10, "earned": 0}
        self.leave_history: list = []
        self.total_leaves_requested = 0

    def to_dict(self):
        return {**self.__dict__, "leave_balance": self.leave_balance}

    @classmethod
    def from_dict(cls, data):
        emp = cls(data["emp_id"], data["name"], data["department"], 
                 data["email"], data["joining_date"])
        emp.leave_balance = data.get("leave_balance", {"casual": 15, "sick": 10, "earned": 0})
        emp.leave_history = data.get("leave_history", [])
        emp.total_leaves_requested = data.get("total_leaves_requested", 0)
        return emp


class LeaveSystem:
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.leave_requests = []
        self.next_request_id = 1
        self.current_user = None
        self.current_role = None
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    for emp_data in data.get("employees", []):
                        emp = Employee.from_dict(emp_data)
                        self.employees[emp.emp_id] = emp
                        # Add employee to login system
                        USERS[emp.emp_id] = {"password": emp.emp_id, "role": "employee", "name": emp.name}
                    self.leave_requests = data.get("leave_requests", [])
                    self.next_request_id = data.get("next_request_id", 1)
            except:
                pass

    def save_data(self):
        data = {
            "employees": [emp.to_dict() for emp in self.employees.values()],
            "leave_requests": self.leave_requests,
            "next_request_id": self.next_request_id
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def login(self):
        print("\n" + "="*50)
        print("LOGIN TO LEAVE MANAGEMENT SYSTEM")
        print("="*50)
        username = input("Username (emp_id or admin username): ").strip().lower()
        password = getpass.getpass("Password: ")

        if username in USERS and USERS[username]["password"] == password:
            self.current_user = username
            self.current_role = USERS[username]["role"]
            print(f"\nLogin successful! Welcome, {USERS[username]['name']}")
            return True
        else:
            print("Invalid credentials!")
            return False

    def generate_printable_form(self, request):
        """Generate clean printable leave application form"""
        emp = self.employees.get(request["emp_id"])
        if not emp:
            return

        form = f"""
{'='*80}
                    EMPLOYEE LEAVE APPLICATION FORM
{'='*80}

Employee Information:
Name                  : {emp.name}
Employee ID           : {emp.emp_id}
Department            : {emp.department}
Date of Joining       : {emp.joining_date}
Application Date      : {request['applied_date']}

Leave Details:
Leave Type            : {request['leave_type'].upper()}
From                  : {request['start_date']}
To                    : {request['end_date']}
Number of Days        : {request['days']}
Reason                : {request['reason']}

Leave Balance Before Request:
Casual Leave          : {emp.leave_balance['casual']} days
Sick Leave            : {emp.leave_balance['sick']} days
Earned Leave          : {emp.leave_balance['earned']} days

{'='*80}
Status                : {request['status']}
Approved By           : {request.get('approved_by', 'Pending')}
Approval Date         : {request.get('approval_date', 'N/A')}
{'='*80}

Signature:
Employee ___________________________       Manager/Admin ___________________________

**Print this form for records**
"""
        filename = f"Leave_Application_{request['request_id']}_{emp.name.replace(' ', '_')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(form)
        
        print(f"\nForm saved as: {filename}")
        print("You can open and print this file directly on Windows.")
        return filename

    # ... (rest of methods same as previous version with role checks)

    def main_menu(self):
        while True:
            print("\n" + "="*60)
            print(f"LEAVE MANAGEMENT SYSTEM - Logged in as: {USERS[self.current_user]['name']} ({self.current_role.upper()})")
            print("="*60)
            
            if self.current_role == "admin":
                print("1. Add New Employee")
                print("2. List All Employees")
                print("3. View Employee Details")
                print("4. View All Pending Requests")
                print("5. Approve/Reject Leave")
                print("6. Generate Report")
            
            print("7. Apply for Leave")
            print("8. View My Details & Balance")
            print("9. Generate Printable Leave Form")
            print("10. Logout")
            print("11. Exit")

            choice = input("\nEnter choice: ").strip()

            if self.current_role == "admin" and choice == "1":
                # Add employee code...
                emp_id = input("Employee ID: ").strip()
                name = input("Name: ").strip()
                dept = input("Department: ").strip()
                email = input("Email: ").strip()
                jdate = input("Joining Date (YYYY-MM-DD): ").strip()
                if emp_id not in self.employees:
                    self.employees[emp_id] = Employee(emp_id, name, dept, email, jdate)
                    USERS[emp_id] = {"password": emp_id, "role": "employee", "name": name}
                    self.save_data()
                    print("Employee added successfully!")
            
            elif choice == "7":   # Apply for Leave
                emp_id = self.current_user if self.current_role == "employee" else input("Employee ID: ").strip()
                print("Leave Types: casual, sick, earned")
                ltype = input("Leave Type: ").strip().lower()
                sdate = input("Start Date (YYYY-MM-DD): ").strip()
                edate = input("End Date (YYYY-MM-DD): ").strip()
                reason = input("Reason: ").strip()
                # Call apply_leave method...

            elif choice == "9":   # Generate Printable Form
                if self.current_role == "employee":
                    # Show employee's requests
                    my_requests = [r for r in self.leave_requests if r["emp_id"] == self.current_user]
                    if my_requests:
                        print("Your Leave Requests:")
                        for r in my_requests:
                            print(f"#{r['request_id']} - {r['start_date']} to {r['end_date']} ({r['status']})")
                        rid = int(input("Enter Request ID to print form: "))
                        req = next((r for r in my_requests if r["request_id"] == rid), None)
                        if req:
                            self.generate_printable_form(req)
                    else:
                        print("You have no leave requests yet.")
                else:
                    # Admin can print any
                    rid = int(input("Enter Request ID: "))
                    req = next((r for r in self.leave_requests if r["request_id"] == rid), None)
                    if req:
                        self.generate_printable_form(req)

            elif choice in ["10", "11"]:
                if choice == "10":
                    self.current_user = None
                    self.current_role = None
                    if self.login():
                        continue
                else:
                    print("Thank you for using the system!")
                    break

# ====================== RUN THE PROGRAM ======================
if __name__ == "__main__":
    system = LeaveSystem()
    print("Welcome to Employee Leave Management System (Windows Compatible)")
    
    while not system.login():
        pass
    
    system.main_menu()
