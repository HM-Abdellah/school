import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Login Component
const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('teacher', JSON.stringify(data.teacher));
      onLogin(data.teacher);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="glass-card w-full max-w-md p-8 rounded-2xl shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome Back</h1>
          <p className="text-gray-600">Sign in to your teacher account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all duration-200"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all duration-200"
              placeholder="Enter your password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Demo Credentials:</p>
          <p className="font-mono">teacher1 / password123</p>
          <p className="font-mono">teacher2 / password123</p>
        </div>
      </div>
    </div>
  );
};

// Class List Component
const ClassList = ({ teacher, onSelectClass, onLogout }) => {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/classes`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      setClasses(data);
    } catch (error) {
      console.error('Error fetching classes:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupedClasses = classes.reduce((acc, cls) => {
    const key = `${cls.level} - ${cls.stream}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(cls);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="glass-card p-6 rounded-2xl shadow-lg mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">My Classes</h1>
              <p className="text-gray-600 mt-1">Welcome back, {teacher.full_name}</p>
            </div>
            <button
              onClick={onLogout}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        {/* Classes Grid */}
        <div className="space-y-8">
          {Object.entries(groupedClasses).map(([group, classList]) => (
            <div key={group} className="glass-card p-6 rounded-2xl shadow-lg">
              <h2 className="text-xl font-semibold text-gray-800 mb-4 border-b border-gray-200 pb-2">
                {group}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {classList.map((cls) => (
                  <div
                    key={cls.id}
                    onClick={() => onSelectClass(cls)}
                    className="class-card p-4 rounded-xl cursor-pointer hover:shadow-lg transition-all duration-200"
                  >
                    <h3 className="font-medium text-gray-800 mb-2">{cls.name}</h3>
                    <p className="text-sm text-gray-600">Students: {cls.students.length}</p>
                    <div className="mt-3 flex justify-between items-center">
                      <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full">
                        {cls.level}
                      </span>
                      <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                        {cls.stream}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Attendance Sheet Component
const AttendanceSheet = ({ selectedClass, onBack }) => {
  const [students, setStudents] = useState([]);
  const [attendance, setAttendance] = useState({});
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedSession, setSelectedSession] = useState('morning');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  useEffect(() => {
    fetchStudents();
    checkExistingAttendance();
  }, [selectedClass, selectedDate, selectedSession]);

  const fetchStudents = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/classes/${selectedClass.id}/students`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      setStudents(data);
      
      // Initialize attendance state
      const initialAttendance = {};
      data.forEach(student => {
        initialAttendance[student.id] = 'present';
      });
      setAttendance(initialAttendance);
    } catch (error) {
      console.error('Error fetching students:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkExistingAttendance = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_BASE_URL}/api/classes/${selectedClass.id}/attendance?date=${selectedDate}&session=${selectedSession}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      const data = await response.json();
      setIsSubmitted(data.length > 0);
      
      if (data.length > 0) {
        const existingAttendance = {};
        data.forEach(record => {
          existingAttendance[record.student_id] = record.status;
        });
        setAttendance(existingAttendance);
      }
    } catch (error) {
      console.error('Error checking attendance:', error);
    }
  };

  const handleAttendanceChange = (studentId, status) => {
    if (isSubmitted) return; // Prevent changes if already submitted
    
    setAttendance(prev => ({
      ...prev,
      [studentId]: status
    }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const attendanceData = Object.entries(attendance).map(([studentId, status]) => ({
        student_id: studentId,
        status: status
      }));

      const response = await fetch(`${API_BASE_URL}/api/classes/${selectedClass.id}/attendance`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          class_id: selectedClass.id,
          date: selectedDate,
          session: selectedSession,
          attendance_data: attendanceData
        }),
      });

      if (response.ok) {
        setIsSubmitted(true);
        setShowConfirmation(false);
        alert('Attendance submitted successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error submitting attendance:', error);
      alert('Error submitting attendance');
    } finally {
      setSubmitting(false);
    }
  };

  const getSessionTime = (session) => {
    return session === 'morning' ? '08:30 - 12:30' : '14:30 - 18:30';
  };

  const presentCount = Object.values(attendance).filter(status => status === 'present').length;
  const absentCount = Object.values(attendance).filter(status => status === 'absent').length;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="glass-card p-6 rounded-2xl shadow-lg mb-6">
          <div className="flex justify-between items-center mb-4">
            <button
              onClick={onBack}
              className="flex items-center px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              ← Back to Classes
            </button>
            {isSubmitted && (
              <span className="bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium">
                ✓ Submitted
              </span>
            )}
          </div>
          
          <h1 className="text-2xl font-bold text-gray-800 mb-2">{selectedClass.name}</h1>
          <p className="text-gray-600">{selectedClass.level} - {selectedClass.stream}</p>
          
          {/* Date and Session Controls */}
          <div className="flex flex-wrap gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                disabled={isSubmitted}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Session</label>
              <select
                value={selectedSession}
                onChange={(e) => setSelectedSession(e.target.value)}
                disabled={isSubmitted}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="morning">Morning ({getSessionTime('morning')})</option>
                <option value="afternoon">Afternoon ({getSessionTime('afternoon')})</option>
              </select>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="glass-card p-4 rounded-xl text-center">
            <div className="text-2xl font-bold text-blue-600">{students.length}</div>
            <div className="text-sm text-gray-600">Total Students</div>
          </div>
          <div className="glass-card p-4 rounded-xl text-center">
            <div className="text-2xl font-bold text-green-600">{presentCount}</div>
            <div className="text-sm text-gray-600">Present</div>
          </div>
          <div className="glass-card p-4 rounded-xl text-center">
            <div className="text-2xl font-bold text-red-600">{absentCount}</div>
            <div className="text-sm text-gray-600">Absent</div>
          </div>
          <div className="glass-card p-4 rounded-xl text-center">
            <div className="text-2xl font-bold text-purple-600">
              {students.length > 0 ? Math.round((presentCount / students.length) * 100) : 0}%
            </div>
            <div className="text-sm text-gray-600">Attendance Rate</div>
          </div>
        </div>

        {/* Attendance Sheet */}
        <div className="attendance-sheet glass-card p-6 rounded-2xl shadow-lg">
          <div className="border-b border-gray-200 pb-4 mb-6">
            <h2 className="text-xl font-semibold text-gray-800">Attendance Sheet</h2>
            <p className="text-sm text-gray-600 mt-1">
              {selectedSession === 'morning' ? 'Morning Session' : 'Afternoon Session'} - {getSessionTime(selectedSession)}
            </p>
          </div>

          <div className="space-y-2">
            {students.map((student, index) => (
              <div
                key={student.id}
                className="flex items-center justify-between p-4 bg-white/50 rounded-lg border border-gray-200 hover:shadow-sm transition-all duration-200"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-sm font-medium text-indigo-800">
                    {index + 1}
                  </div>
                  <span className="font-medium text-gray-800">{student.full_name}</span>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleAttendanceChange(student.id, 'present')}
                    disabled={isSubmitted}
                    className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                      attendance[student.id] === 'present'
                        ? 'bg-green-500 text-white shadow-md'
                        : 'bg-gray-100 text-gray-600 hover:bg-green-100'
                    } ${isSubmitted ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    Present
                  </button>
                  <button
                    onClick={() => handleAttendanceChange(student.id, 'absent')}
                    disabled={isSubmitted}
                    className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                      attendance[student.id] === 'absent'
                        ? 'bg-red-500 text-white shadow-md'
                        : 'bg-gray-100 text-gray-600 hover:bg-red-100'
                    } ${isSubmitted ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                  >
                    Absent
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Submit Button */}
          {!isSubmitted && (
            <div className="mt-8 text-center">
              <button
                onClick={() => setShowConfirmation(true)}
                className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-lg hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200"
              >
                Submit Attendance
              </button>
              <p className="text-sm text-gray-500 mt-2">
                Note: Once submitted, attendance cannot be modified
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Confirm Attendance Submission</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to submit the attendance? This action cannot be undone.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowConfirmation(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [selectedClass, setSelectedClass] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const teacher = localStorage.getItem('teacher');
    if (token && teacher) {
      setUser(JSON.parse(teacher));
    }
  }, []);

  const handleLogin = (teacher) => {
    setUser(teacher);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('teacher');
    setUser(null);
    setSelectedClass(null);
  };

  const handleSelectClass = (cls) => {
    setSelectedClass(cls);
  };

  const handleBackToClasses = () => {
    setSelectedClass(null);
  };

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  if (selectedClass) {
    return <AttendanceSheet selectedClass={selectedClass} onBack={handleBackToClasses} />;
  }

  return (
    <ClassList
      teacher={user}
      onSelectClass={handleSelectClass}
      onLogout={handleLogout}
    />
  );
};

export default App;