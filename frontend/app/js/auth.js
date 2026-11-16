/**
 * EduFocus — Authentication
 */

import { MOCK_ACCOUNTS, findUser, addUser } from './data.js';

const SESSION_KEY = 'edufocus-user';

export function login(email, password) {
  if (!email || !password) {
    return { success: false, error: 'Vui lòng nhập đầy đủ thông tin.' };
  }

  // Check mock accounts
  const mock = MOCK_ACCOUNTS.find(
    a => a.email === email && a.password === password
  );
  if (mock) {
    const user = { id: mock.id, name: mock.name, email: mock.email, role: mock.role };
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
    return { success: true, user };
  }

  // Check registered users
  const registeredUser = findUser(email);
  if (registeredUser && registeredUser.password === password) {
    const user = {
      id: registeredUser.id,
      name: registeredUser.name,
      email: registeredUser.email,
      role: registeredUser.role
    };
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
    return { success: true, user };
  }

  return { success: false, error: 'Email hoặc mật khẩu không đúng.' };
}

export function logout() {
  sessionStorage.removeItem(SESSION_KEY);
}

export function getCurrentUser() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.warn('getCurrentUser error', e);
  }
  return null;
}

export function register(name, email, password, role = 'student') {
  if (!name || !email || !password) {
    return { success: false, error: 'Vui lòng điền đầy đủ thông tin.' };
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return { success: false, error: 'Email không hợp lệ.' };
  }
  if (password.length < 6) {
    return { success: false, error: 'Mật khẩu phải có ít nhất 6 ký tự.' };
  }

  const existing = findUser(email);
  if (existing) {
    return { success: false, error: 'Email đã được sử dụng.' };
  }

  const newUser = {
    id: 'U' + Date.now(),
    name,
    email,
    password,
    role
  };
  addUser(newUser);

  const user = { id: newUser.id, name: newUser.name, email: newUser.email, role: newUser.role };
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
  return { success: true, user };
}

export function sendForgotPassword(email) {
  if (!email) {
    return { success: false, error: 'Vui lòng nhập email.' };
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return { success: false, error: 'Email không hợp lệ.' };
  }
  // Mock: always succeed
  return { success: true };
}
