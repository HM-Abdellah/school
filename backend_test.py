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
        
        # Login to get token for subsequent requests
        self.login()
    
    def login(self):
        """Test login functionality and get token"""
        print("\n🔍 Testing login...")
        
        # Test with valid credentials
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "teacher1", "password": "password123"}
        )
        
        self.assertEqual(response.status_code, 200, "Login failed with valid credentials")
        data = response.json()
        self.assertIn("access_token", data, "Token not found in response")
        self.assertIn("teacher", data, "Teacher data not found in response")
        
        # Save token and teacher data for subsequent tests
        self.token = data["access_token"]
        self.teacher = data["teacher"]
        print("✅ Login successful")
        
        # Test with invalid credentials
        print("🔍 Testing login with invalid credentials...")
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": "teacher1", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 401, "Should reject invalid credentials")
        print("✅ Invalid credentials correctly rejected")
    
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
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/classes", headers=headers)
        
        self.assertEqual(response.status_code, 200, "Failed to get classes")
        classes = response.json()
        self.assertIsInstance(classes, list, "Classes should be a list")
        
        if len(classes) > 0:
            # Save first class ID for subsequent tests
            self.class_id = classes[0]["id"]
            print(f"✅ Retrieved {len(classes)} classes")
        else:
            print("⚠️ No classes found for this teacher")
    
    def test_get_class_details(self):
        """Test getting details of a specific class"""
        if not self.class_id:
            self.test_get_classes()
            if not self.class_id:
                self.skipTest("No classes available to test")
        
        print(f"\n🔍 Testing class details retrieval for class ID: {self.class_id}...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/classes/{self.class_id}", headers=headers)
        
        self.assertEqual(response.status_code, 200, "Failed to get class details")
        class_data = response.json()
        self.assertEqual(class_data["id"], self.class_id, "Class ID mismatch")
        print("✅ Class details retrieved successfully")
    
    def test_get_students(self):
        """Test getting students for a class"""
        if not self.class_id:
            self.test_get_classes()
            if not self.class_id:
                self.skipTest("No classes available to test")
        
        print(f"\n🔍 Testing student retrieval for class ID: {self.class_id}...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/classes/{self.class_id}/students", headers=headers)
        
        self.assertEqual(response.status_code, 200, "Failed to get students")
        students = response.json()
        self.assertIsInstance(students, list, "Students should be a list")
        
        if len(students) > 0:
            # Save students for attendance tests
            self.students = students
            print(f"✅ Retrieved {len(students)} students")
        else:
            print("⚠️ No students found for this class")
    
    def test_attendance_workflow(self):
        """Test the full attendance workflow"""
        if not self.class_id:
            self.test_get_classes()
            if not self.class_id:
                self.skipTest("No classes available to test")
        
        if not self.students:
            self.test_get_students()
            if not self.students:
                self.skipTest("No students available to test")
        
        # Use tomorrow's date to avoid conflicts with existing records
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        session = "morning"
        
        print(f"\n🔍 Testing attendance workflow for date: {tomorrow}, session: {session}...")
        
        # 1. Check if attendance exists (should not exist for tomorrow)
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/api/classes/{self.class_id}/attendance?date={tomorrow}&session={session}",
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200, "Failed to check attendance")
        existing_attendance = response.json()
        self.assertIsInstance(existing_attendance, list, "Attendance should be a list")
        
        if len(existing_attendance) > 0:
            print("⚠️ Attendance already exists for tomorrow (unexpected)")
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
            
            self.assertEqual(response.status_code, 200, f"Failed to submit attendance: {response.text}")
            result = response.json()
            self.assertIn("message", result, "Response should contain a message")
            self.assertIn("records_count", result, "Response should contain records_count")
            print(f"✅ Attendance submitted successfully: {result['message']}")
            
            # 3. Verify attendance was recorded
            response = requests.get(
                f"{self.base_url}/api/classes/{self.class_id}/attendance?date={tomorrow}&session={session}",
                headers=headers
            )
            
            self.assertEqual(response.status_code, 200, "Failed to verify attendance")
            recorded_attendance = response.json()
            self.assertIsInstance(recorded_attendance, list, "Recorded attendance should be a list")
            self.assertEqual(len(recorded_attendance), len(attendance_data), 
                             "Number of attendance records doesn't match submission")
            print(f"✅ Verified {len(recorded_attendance)} attendance records were saved")
            
            # 4. Try to submit again (should fail)
            print("🔍 Testing duplicate submission prevention...")
            response = requests.post(
                f"{self.base_url}/api/classes/{self.class_id}/attendance",
                headers={**headers, "Content-Type": "application/json"},
                json=submission
            )
            
            self.assertEqual(response.status_code, 400, "Should prevent duplicate submission")
            print("✅ Duplicate submission correctly prevented")

if __name__ == "__main__":
    # Create a test suite with all tests
    test_suite = unittest.TestSuite()
    test_suite.addTest(AttendanceSystemAPITest("login"))
    test_suite.addTest(AttendanceSystemAPITest("test_teacher_profile"))
    test_suite.addTest(AttendanceSystemAPITest("test_get_classes"))
    test_suite.addTest(AttendanceSystemAPITest("test_get_class_details"))
    test_suite.addTest(AttendanceSystemAPITest("test_get_students"))
    test_suite.addTest(AttendanceSystemAPITest("test_attendance_workflow"))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)