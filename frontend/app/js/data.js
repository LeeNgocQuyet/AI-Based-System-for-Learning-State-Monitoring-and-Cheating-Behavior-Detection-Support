/**
 * EduFocus — Mock Data & LocalStorage Persistence
 */

const STORAGE_KEY = 'edufocus-v1';

export const MOCK_ACCOUNTS = [
  {
    email: 'teacher@demo.test',
    password: '12345678',
    role: 'teacher',
    name: 'ThS. Nguyễn Minh Khôi',
    id: 'T001'
  },
  {
    email: 'student@demo.test',
    password: '12345678',
    role: 'student',
    name: 'Nguyễn Minh An',
    id: '2420001'
  }
];

const VIETNAMESE_NAMES = [
  'Nguyễn Thị Lan', 'Trần Văn Hùng', 'Lê Thị Mai', 'Phạm Minh Tuấn',
  'Hoàng Thị Hoa', 'Vũ Văn Đức', 'Đặng Thị Thu', 'Bùi Minh Khoa',
  'Phan Thị Hạnh', 'Ngô Văn Nam', 'Dương Thị Lan', 'Trịnh Văn Bình',
  'Nguyễn Minh An', 'Lý Thị Nga', 'Mai Văn Long', 'Trương Thị Phương',
  'Đinh Văn Tú', 'Hà Thị Linh', 'Tạ Minh Khải', 'Lưu Thị Thanh',
  'Vương Văn Hải', 'Doan Thị Ngọc', 'Cao Minh Trí', 'Lại Thị Hương',
  'Ngo Văn Hiếu', 'Chu Thị Bích', 'Từ Minh Nhật', 'Khúc Thị Thu',
  'Mã Văn Phúc', 'Ninh Thị Hà', 'Trần Minh Quân', 'Lê Thị Yến',
  'Phạm Thị Thúy', 'Hoàng Văn Lâm', 'Vũ Thị Duyên', 'Đặng Minh Hiệp',
  'Bùi Thị Nhung', 'Phan Văn Thành', 'Ngô Thị Cúc', 'Dương Văn Sơn',
  'Trịnh Thị Hồng', 'Nguyễn Văn Khoa', 'Lý Minh Tâm', 'Mai Thị Sen',
  'Trương Văn Khoa', 'Đinh Thị Thảo'
];

function generateStudents(courseId, count, offset = 0) {
  const students = [];
  for (let i = 0; i < count; i++) {
    const idx = (offset + i) % VIETNAMESE_NAMES.length;
    const name = VIETNAMESE_NAMES[idx];
    const sid = `242${String(i + 1 + offset * 10).padStart(4, '0')}`;
    students.push({ id: sid, name, courseId });
  }
  return students;
}

function getDefaultDB() {
  const courses = [
    {
      id: 'C001',
      code: 'INT3306',
      name: 'Tương tác người máy',
      semester: 'HK1 2024-2025',
      studentCount: 42,
      teacherId: 'T001'
    },
    {
      id: 'C002',
      code: 'INT2204',
      name: 'Lập trình hướng đối tượng',
      semester: 'HK1 2024-2025',
      studentCount: 38,
      teacherId: 'T001'
    },
    {
      id: 'C003',
      code: 'INT2210',
      name: 'Cơ sở dữ liệu',
      semester: 'HK1 2024-2025',
      studentCount: 45,
      teacherId: 'T001'
    },
    {
      id: 'C004',
      code: 'INT3308',
      name: 'Phát triển ứng dụng Web',
      semester: 'HK1 2024-2025',
      studentCount: 36,
      teacherId: 'T001'
    }
  ];

  // Students: student demo (2420001) is in C001, C002
  const rosterC001 = generateStudents('C001', 42, 0);
  // Ensure our demo student is in roster
  rosterC001[0] = { id: '2420001', name: 'Nguyễn Minh An', courseId: 'C001' };

  const rosterC002 = generateStudents('C002', 38, 4);
  rosterC002[1] = { id: '2420001', name: 'Nguyễn Minh An', courseId: 'C002' };

  const rosterC003 = generateStudents('C003', 45, 8);
  const rosterC004 = generateStudents('C004', 36, 12);

  const sessions = [
    {
      id: 'S001',
      courseId: 'C001',
      type: 'Phiên học',
      title: 'Bài giảng: Nguyên tắc thiết kế UX',
      duration: 90,
      status: 'Đã kết thúc',
      startedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      startedLabel: '3 ngày trước',
      participants: [],
      events: [],
      attendanceSeeded: true
    },
    {
      id: 'S002',
      courseId: 'C002',
      type: 'Phiên thi',
      title: 'Kiểm tra giữa kỳ',
      duration: 60,
      status: 'Đã kết thúc',
      startedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      startedLabel: '7 ngày trước',
      participants: [],
      events: [],
      attendanceSeeded: true
    }
  ];

  // Seed participants for finished sessions
  sessions[0].participants = seededParticipants(rosterC001, 'S001');
  sessions[1].participants = seededParticipants(rosterC002, 'S002');

  return {
    courses,
    rosters: {
      C001: rosterC001,
      C002: rosterC002,
      C003: rosterC003,
      C004: rosterC004
    },
    sessions,
    users: []
  };
}

function seededParticipants(roster, sessionId) {
  return roster.map((s, i) => {
    const roll = Math.random();
    let status;
    if (roll < 0.1) status = 'absent';
    else if (roll < 0.2) status = 'technical';
    else if (roll < 0.4) status = 'attention';
    else status = 'stable';

    const events = [];
    if (status === 'attention') {
      const types = ['Nhìn lệch', 'Nhắm mắt', 'Rời khỏi màn hình'];
      const count = Math.floor(Math.random() * 3) + 1;
      for (let k = 0; k < count; k++) {
        events.push({
          type: types[k % types.length],
          time: new Date(Date.now() - (60 - k * 15) * 60 * 1000).toISOString(),
          description: types[k % types.length]
        });
      }
    }

    return {
      studentId: s.id,
      studentName: s.name,
      sessionId,
      status,
      joinedAt: new Date(Date.now() - 80 * 60 * 1000).toISOString(),
      events
    };
  });
}

// ---- Storage helpers ----

export function getData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.warn('getData error', e);
  }
  const db = getDefaultDB();
  saveData(db);
  return db;
}

export function saveData(db) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
  } catch (e) {
    console.warn('saveData error', e);
  }
}

export function resetData() {
  const db = getDefaultDB();
  saveData(db);
  return db;
}

// ---- Convenience getters ----

export function getCourses(teacherId) {
  const db = getData();
  if (teacherId) return db.courses.filter(c => c.teacherId === teacherId);
  return db.courses;
}

export function getCourse(id) {
  const db = getData();
  return db.courses.find(c => c.id === id) || null;
}

export function getSessions(courseId) {
  const db = getData();
  if (courseId) return db.sessions.filter(s => s.courseId === courseId);
  return db.sessions;
}

export function getSession(id) {
  const db = getData();
  return db.sessions.find(s => s.id === id) || null;
}

export function getActiveSession(courseId) {
  const db = getData();
  const sessions = courseId
    ? db.sessions.filter(s => s.courseId === courseId)
    : db.sessions;
  return sessions.find(s => s.status === 'Đang diễn ra') || null;
}

export function getRoster(courseId) {
  const db = getData();
  return (db.rosters && db.rosters[courseId]) || [];
}

export function getStudentCourses(studentId) {
  const db = getData();
  const result = [];
  for (const [courseId, roster] of Object.entries(db.rosters || {})) {
    if (roster.some(s => s.id === studentId)) {
      const course = db.courses.find(c => c.id === courseId);
      if (course) result.push(course);
    }
  }
  return result;
}

export function getStudentSessions(studentId) {
  const db = getData();
  return db.sessions.filter(s =>
    s.participants.some(p => p.studentId === studentId)
  );
}

export function createSession(courseId, type, title, duration) {
  const db = getData();
  const id = 'S' + Date.now();
  const now = new Date();
  const session = {
    id,
    courseId,
    type,
    title,
    duration,
    status: 'Đang diễn ra',
    startedAt: now.toISOString(),
    startedLabel: 'Vừa bắt đầu',
    participants: [],
    events: [],
    attendanceSeeded: false
  };
  db.sessions.push(session);
  saveData(db);
  return session;
}

export function updateSession(id, patch) {
  const db = getData();
  const idx = db.sessions.findIndex(s => s.id === id);
  if (idx === -1) return null;
  db.sessions[idx] = { ...db.sessions[idx], ...patch };
  saveData(db);
  return db.sessions[idx];
}

export function seedAttendance(sessionId) {
  const db = getData();
  const session = db.sessions.find(s => s.id === sessionId);
  if (!session || session.attendanceSeeded) return session;

  const roster = db.rosters[session.courseId] || [];
  const eventTypes = ['Nhìn lệch', 'Nhắm mắt', 'Rời khỏi màn hình', 'Điện thoại'];
  const now = Date.now();

  session.participants = roster.map(s => {
    const roll = Math.random();
    let status;
    if (roll < 0.1) status = 'absent';
    else if (roll < 0.2) status = 'technical';
    else if (roll < 0.4) status = 'attention';
    else status = 'stable';

    const events = [];
    if (status === 'attention') {
      const count = Math.floor(Math.random() * 3) + 1;
      for (let k = 0; k < count; k++) {
        const eType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
        events.push({
          type: eType,
          time: new Date(now - (Math.random() * 50 * 60 * 1000)).toISOString(),
          description: eType
        });
      }
    }

    return {
      studentId: s.id,
      studentName: s.name,
      sessionId,
      status,
      joinedAt: new Date(now - Math.random() * 10 * 60 * 1000).toISOString(),
      events
    };
  });

  // Also create session-level events
  session.events = [];
  const sessionEventTypes = [
    'Phát hiện nhìn lệch',
    'Sinh viên rời màn hình',
    'Sinh viên tham gia muộn',
    'Mất kết nối camera',
    'Điện thoại xuất hiện'
  ];
  for (let i = 0; i < 8; i++) {
    const eType = sessionEventTypes[Math.floor(Math.random() * sessionEventTypes.length)];
    const participant = session.participants[Math.floor(Math.random() * session.participants.length)];
    session.events.push({
      type: eType,
      time: new Date(now - Math.random() * 60 * 60 * 1000).toISOString(),
      description: `${participant.studentName}: ${eType}`
    });
  }
  session.events.sort((a, b) => new Date(b.time) - new Date(a.time));

  session.attendanceSeeded = true;

  const idx = db.sessions.findIndex(s => s.id === sessionId);
  db.sessions[idx] = session;
  saveData(db);
  return session;
}

export function studentJoinSession(sessionId, studentId, studentName) {
  const db = getData();
  const session = db.sessions.find(s => s.id === sessionId);
  if (!session) return null;

  // Remove existing entry for this student if any
  session.participants = session.participants.filter(p => p.studentId !== studentId);
  session.participants.push({
    studentId,
    studentName,
    sessionId,
    status: 'stable',
    joinedAt: new Date().toISOString(),
    events: []
  });

  const idx = db.sessions.findIndex(s => s.id === sessionId);
  db.sessions[idx] = session;
  saveData(db);
  return session;
}

export function addUser(user) {
  const db = getData();
  if (!db.users) db.users = [];
  db.users.push(user);
  saveData(db);
}

export function findUser(email) {
  const db = getData();
  // Check mock accounts first
  const mock = MOCK_ACCOUNTS.find(a => a.email === email);
  if (mock) return mock;
  if (!db.users) return null;
  return db.users.find(u => u.email === email) || null;
}
