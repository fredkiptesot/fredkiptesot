import datetime
import json
import os
from typing import Dict, List, Optional

DATA_FILE = "leave_management_data.json"

class Employee:
    def __init__(self, emp_id: str, name: str, department: str, email: str, joining_date: str):
        self.emp_id = emp_id
        self.name = name
        self.department = department
        self.email = email
        self.joining_date = joining_date  # Format: YYYY-MM-DD
        
        # Initial leave balances
        self.leave_balance = {
            "casual": 15,
            "sick": 10,
            "earned": 0  # Earned leave accrues after 1 year
        }
        self.leave_history: List[Dict] = []
        self.total_leaves_requested = 0

    def to_dict(self):
        return {
            "emp_id": self.emp_id,
            "name": self.name,
            "department": self.department,
            "email": self.email,
            "joining_date": self.joining_date,
            "leave_balance": self.leave_balance,
            "leave_history": self.leave_history,
            "total_leaves_requested": self.total_leaves_requested
        }

    @classmethod
    def from_dict(cls, data):
        emp = cls(
            data["emp_id"], 
            data["name"], 
            data["department"], 
            data["email"], 
            data["joining_date"]
        )
        emp.leave_balance = data.get("leave_balance", {"casual": 15, "sick": 10, "earned": 0})
        emp.leave_history = data.get("leave_history", [])
        emp.total_leaves_requested = data.get("total_leaves_requested", 0)
        return emp

    def get_service_years(self) -> float:
        try:
            joining = datetime.datetime.strptime(self.joining_date, "%Y-%m-%d")
            today = datetime.datetime.now()
            delta = today - joining
            return delta.days / 365.25
        except:
            return 0

    def accrue_earned_leave(self):
        """Accrue earned leave after 1 year of service"""
        years = self.get_service_years()
        if years >= 1:
            # Example: 20 days earned leave per year
            entitled = int(years) * 20
            # For simplicity, set minimum after 1 year
            if self.leave_balance["earned"] < 20 and years >= 1:
                self.leave_balance["earned"] = 20


class LeaveManagementSystem:
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.leave_requests: List[Dict] = []  # Store as dict for simplicity
        self.next_request_id = 1
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    for emp_data in data.get("employees", []):
                        emp = Employee.from_dict(emp_data)
                        self.employees[emp.emp_id] = emp
                    self.leave_requests = data.get("leave_requests", [])
                    self.next_request_id = data.get("next_request_id", 1)
            except Exception:
                pass

    def save_data(self):
        data = {
            "employees": [emp.to_dict() for emp in self.employees.values()],
            "leave_requests": self.leave_requests,
            "next_request_id": self.next_request_id
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def add_employee(self, emp_id: str, name: str, department: str, email: str, joining_date: str):
        if emp_id in self.employees:
            print("Employee ID already exists!")
            return False
        
        self.employees[emp_id] = Employee(emp_id, name, department, email, joining_date)
        self.save_data()
        print(f"Employee {name} added successfully!")
        return True

    def list_employees(self):
        print("\n=== Employee List ===")
        print(f"{'ID':<10} {'Name':<25} {'Department':<15} {'Joining Date':<12} {'Service (yrs)':<12}")
        print("-" * 75)
        for emp in sorted(self.employees.values(), key=lambda x: x.name):
            service = f"{emp.get_service_years():.1f}"
            print(f"{emp.emp_id:<10} {emp.name:<25} {emp.department:<15} {emp.joining_date:<12} {service:<12}")

    def apply_leave(self, emp_id: str, leave_type: str, start_date: str, end_date: str, reason: str):
        emp = self.employees.get(emp_id)
        if not emp:
            print("Employee not found!")
            return False

        emp.accrue_earned_leave()  # Auto accrue if eligible

        try:
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            days = (end - start).days + 1
        except:
            print("Invalid dates!")
            return False

        if days <= 0:
            print("Invalid date range!")
            return False

        if emp.leave_balance.get(leave_type, 0) < days:
            print(f"Insufficient {leave_type} leave balance!")
            return False

        request = {
            "request_id": self.next_request_id,
            "emp_id": emp_id,
            "emp_name": emp.name,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
            "reason": reason,
            "status": "Pending",
            "applied_date": datetime.datetime.now().strftime("%Y-%m-%d")
        }

        self.leave_requests.append(request)
        self.next_request_id += 1
        emp.total_leaves_requested += 1
        self.save_data()
        
        print(f"Leave request #{request['request_id']} submitted successfully!")
        return True

    def view_employee_details(self, emp_id: str):
        emp = self.employees.get(emp_id)
        if not emp:
            print("Employee not found!")
            return
        
        emp.accrue_earned_leave()
        
        print(f"\n=== Employee Details: {emp.name} ===")
        print(f"Employee ID     : {emp.emp_id}")
        print(f"Department      : {emp.department}")
        print(f"Email           : {emp.email}")
        print(f"Date of Joining : {emp.joining_date}")
        print(f"Service Period  : {emp.get_service_years():.2f} years")
        print(f"Total Leaves Requested: {emp.total_leaves_requested}")
        
        print("\nLeave Balance:")
        for lt, bal in emp.leave_balance.items():
            print(f"   {lt.capitalize():<8}: {bal} days")
        
        print("\nLeave Due After 1 Year: Yes" if emp.get_service_years() >= 1 else "\nLeave Due After 1 Year: Not yet eligible")

    def view_all_pending_requests(self):
        print("\n=== Pending Leave Requests ===")
        pending = [r for r in self.leave_requests if r["status"] == "Pending"]
        if not pending:
            print("No pending requests.")
            return
        for r in pending:
            print(f"#{r['request_id']} | {r['emp_name']} ({r['emp_id']}) | {r['leave_type']} | "
                  f"{r['start_date']} to {r['end_date']} ({r['days']} days)")

    def approve_reject_leave(self, request_id: int, action: str):
        for req in self.leave_requests:
            if req["request_id"] == request_id and req["status"] == "Pending":
                emp = self.employees.get(req["emp_id"])
                if not emp:
                    print("Employee not found!")
                    return
                
                if action.lower() == "approve":
                    if emp.leave_balance.get(req["leave_type"], 0) >= req["days"]:
                        emp.leave_balance[req["leave_type"]] -= req["days"]
                        req["status"] = "Approved"
                        req["approval_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                        print(f"Request #{request_id} APPROVED")
                        self.save_data()
                        return
                else:
                    req["status"] = "Rejected"
                    req["approval_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
                    print(f"Request #{request_id} REJECTED")
                    self.save_data()
                    return
        print("Request not found or already processed!")

    def generate_report(self):
        print("\n" + "="*60)
        print("EMPLOYEE LEAVE MANAGEMENT REPORT")
        print("="*60)
        print(f"Total Employees          : {len(self.employees)}")
        print(f"Total Pending Requests   : {len([r for r in self.leave_requests if r['status'] == 'Pending'])}")
        print(f"Total Leave Requests     : {len(self.leave_requests)}")
        print("-" * 60)
        
        print(f"{'ID':<8} {'Name':<20} {'Joining':<12} {'Service':<8} {'Casual':<8} {'Sick':<8} {'Earned':<8} {'Requested':<8}")
        print("-" * 80)
        for emp in sorted(self.employees.values(), key=lambda x: x.name):
            emp.accrue_earned_leave()
            print(f"{emp.emp_id:<8} {emp.name[:19]:<20} {emp.joining_date:<12} "
                  f"{emp.get_service_years():<8.1f} "
                  f"{emp.leave_balance['casual']:<8} {emp.leave_balance['sick']:<8} "
                  f"{emp.leave_balance['earned']:<8} {emp.total_leaves_requested:<8}")


def main():
    system = LeaveManagementSystem()
    
    while True:
        print("\n" + "="*55)
        print("   EMPLOYEE LEAVE MANAGEMENT SYSTEM")
        print("="*55)
        print("1. Add New Employee")
        print("2. List All Employees")
        print("3. View Employee Details")
        print("4. Apply for Leave")
        print("5. View Pending Requests (Admin)")
        print("6. Approve/Reject Leave (Admin)")
        print("7. Generate Full Report")
        print("8. Exit")
        
        choice = input("\nEnter choice (1-8): ").strip()

        if choice == "1":
            emp_id = input("Employee ID: ").strip()
            name = input("Name: ").strip()
            dept = input("Department: ").strip()
            email = input("Email: ").strip()
            jdate = input("Joining Date (YYYY-MM-DD): ").strip()
            system.add_employee(emp_id, name, dept, email, jdate)
            
        elif choice == "2":
            system.list_employees()
            
        elif choice == "3":
            emp_id = input("Enter Employee ID: ").strip()
            system.view_employee_details(emp_id)
            
        elif choice == "4":
            emp_id = input("Employee ID: ").strip()
            print("Leave Types: casual / sick / earned")
            ltype = input("Leave Type: ").strip().lower()
            sdate = input("Start Date (YYYY-MM-DD): ").strip()
            edate = input("End Date (YYYY-MM-DD): ").strip()
            reason = input("Reason: ").strip()
            system.apply_leave(emp_id, ltype, sdate, edate, reason)
            
        elif choice == "5":
            system.view_all_pending_requests()
            
        elif choice == "6":
            rid = int(input("Request ID: "))
            act = input("Approve or Reject? ").strip()
            system.approve_reject_leave(rid, act)
            
        elif choice == "7":
            system.generate_report()
            
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid option!")

if __name__ == "__main__":
    main()
