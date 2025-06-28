import requests
import unittest
import json
from datetime import datetime, timedelta

class AttendanceSystemAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        self.base_url = "https://ccac1a2d-9c60-43e5-8cd2-fae9614e8d81.preview.emergentagent.com"
        self.token = None
        self.teacher = None
        self.class_id = None
        self.students = []
    
    def login(self):
        """Test login functionality and get token"""
        print("\n🔍 Testing login...")
        
        # Test with valid credentials
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "teacher1", "password": "password123"}
            )
            
            print(f"Login response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return False
                
            data = response.json()
            if "access_token" not in data or "teacher" not in data:
                print(f"Unexpected response format: {data}")
                return False
            
            # Save token and teacher data for subsequent tests
            self.token = data["access_token"]
            self.teacher = data["teacher"]
            print("✅ Login successful")
            print(f"Teacher: {self.teacher['username']} ({self.teacher['full_name']})")
            
            # Test with invalid credentials
            print("🔍 Testing login with invalid credentials...")
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "teacher1", "password": "wrongpassword"}
            )
            
            if response.status_code == 401:
                print("✅ Invalid credentials correctly rejected")
            else:
                print(f"⚠️ Unexpected status code for invalid credentials: {response.status_code}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error during login test: {str(e)}")
            return False
    
    def test_teacher_profile(self):
        """Test getting teacher profile"""
        print("\n🔍 Testing teacher profile retrieval...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/teacher/profile", headers=headers)
        
        self.assertEqual(response.status_code, 200, "Failed to get teacher profile")
        data = response.json()
        self.assertEqual(data["id"], self.teacher["id"], "Teacher ID mismatch")
        self.assertEqual(data["username"], self.teacher["username"], "Username mismatch")
        print("✅ Teacher profile retrieved successfully")
    
    def test_get_classes(self):
        """Test getting teacher's classes"""
        print("\n🔍 Testing class retrieval...")
        
        if not self.token:
            if not self.login():
                print("❌ Cannot test classes without login")
                return
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/classes", headers=headers)
            
            print(f"Classes response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return
            
            classes = response.json()
            print(f"Response type: {type(classes)}")
            print(f"Response content: {classes[:100]}...")  # Print first part to avoid huge output
            
            if not isinstance(classes, list):
                print(f"❌ Expected classes to be a list, got {type(classes)}")
                return
            
            if len(classes) > 0:
                # Save first class ID for subsequent tests
                self.class_id = classes[0]["id"]
                print(f"✅ Retrieved {len(classes)} classes")
                print(f"First class: {classes[0]['name']} (ID: {self.class_id})")
            else:
                print("⚠️ No classes found for this teacher")
                
        except Exception as e:
            print(f"❌ Error during class retrieval test: {str(e)}")
    
    def test_get_students(self):
        """Test getting students for a class"""
        print("\n🔍 Testing student retrieval...")
        
        if not self.token:
            if not self.login():
                print("❌ Cannot test students without login")
                return
                
        if not self.class_id:
            self.test_get_classes()
            if not self.class_id:
                print("❌ No classes available to test students")
                return
        
        try:
            print(f"Testing student retrieval for class ID: {self.class_id}...")
            
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/api/classes/{self.class_id}/students", headers=headers)
            
            print(f"Students response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return
            
            students = response.json()
            
            if not isinstance(students, list):
                print(f"❌ Expected students to be a list, got {type(students)}")
                return
            
            if len(students) > 0:
                # Save students for attendance tests
                self.students = students
                print(f"✅ Retrieved {len(students)} students")
                print(f"First student: {students[0]['full_name']} (ID: {students[0]['id']})")
            else:
                print("⚠️ No students found for this class")
                
        except Exception as e:
            print(f"❌ Error during student retrieval test: {str(e)}")
    
    def test_attendance_workflow(self):
        """Test the full attendance workflow"""
        print("\n🔍 Testing attendance workflow...")
        
        if not self.token:
            if not self.login():
                print("❌ Cannot test attendance without login")
                return
                
        if not self.class_id:
            self.test_get_classes()
            if not self.class_id:
                print("❌ No classes available to test attendance")
                return
        
        if not self.students:
            self.test_get_students()
            if not self.students:
                print("❌ No students available to test attendance")
                return
        
        # Use tomorrow's date to avoid conflicts with existing records
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        session = "morning"
        
        print(f"Testing attendance for date: {tomorrow}, session: {session}...")
        
        try:
            # 1. Check if attendance exists (should not exist for tomorrow)
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/classes/{self.class_id}/attendance?date={tomorrow}&session={session}",
                headers=headers
            )
            
            print(f"Check attendance response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return
            
            existing_attendance = response.json()
            
            if not isinstance(existing_attendance, list):
                print(f"❌ Expected attendance to be a list, got {type(existing_attendance)}")
                return
            
            if len(existing_attendance) > 0:
                print("⚠️ Attendance already exists for tomorrow (unexpected)")
                return
            else:
                print("✅ Verified no existing attendance for tomorrow")
                
                # 2. Submit attendance
                attendance_data = []
                for i, student in enumerate(self.students):
                    # Mark alternating students as present/absent
                    status = "present" if i % 2 == 0 else "absent"
                    attendance_data.append({
                        "student_id": student["id"],
                        "status": status
                    })
                
                submission = {
                    "class_id": self.class_id,
                    "date": tomorrow,
                    "session": session,
                    "attendance_data": attendance_data
                }
                
                print("🔍 Submitting attendance...")
                response = requests.post(
                    f"{self.base_url}/api/classes/{self.class_id}/attendance",
                    headers={**headers, "Content-Type": "application/json"},
                    json=submission
                )
                
                print(f"Submit attendance response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Error response: {response.text}")
                    return
                
                result = response.json()
                print(f"Submit response: {result}")
                
                if "message" not in result or "records_count" not in result:
                    print(f"❌ Unexpected response format: {result}")
                    return
                
                print(f"✅ Attendance submitted successfully: {result['message']}")
                
                # 3. Verify attendance was recorded
                response = requests.get(
                    f"{self.base_url}/api/classes/{self.class_id}/attendance?date={tomorrow}&session={session}",
                    headers=headers
                )
                
                print(f"Verify attendance response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Error response: {response.text}")
                    return
                
                recorded_attendance = response.json()
                
                if not isinstance(recorded_attendance, list):
                    print(f"❌ Expected recorded attendance to be a list, got {type(recorded_attendance)}")
                    return
                
                if len(recorded_attendance) != len(attendance_data):
                    print(f"⚠️ Number of attendance records ({len(recorded_attendance)}) doesn't match submission ({len(attendance_data)})")
                else:
                    print(f"✅ Verified {len(recorded_attendance)} attendance records were saved")
                
                # 4. Try to submit again (should fail)
                print("🔍 Testing duplicate submission prevention...")
                response = requests.post(
                    f"{self.base_url}/api/classes/{self.class_id}/attendance",
                    headers={**headers, "Content-Type": "application/json"},
                    json=submission
                )
                
                print(f"Duplicate submission response status: {response.status_code}")
                
                if response.status_code == 400:
                    print("✅ Duplicate submission correctly prevented")
                else:
                    print(f"⚠️ Unexpected status code for duplicate submission: {response.status_code}")
                    print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error during attendance workflow test: {str(e)}")

def main():
    tester = AttendanceSystemAPITest()
    tester.login()
    tester.test_get_classes()
    tester.test_get_students()
    tester.test_attendance_workflow()
    print("\n✅ All tests completed")

if __name__ == "__main__":
    main()