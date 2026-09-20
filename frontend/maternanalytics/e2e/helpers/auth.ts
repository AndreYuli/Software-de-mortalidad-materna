import type { Page } from '@playwright/test';

// Las rutas protegidas exigen un JWT real: el backend responde 401 a tokens falsos y el
// frontend cierra la sesión. Este helper crea (si no existe) un usuario de pruebas y deja
// la sesión iniciada. Requiere el backend en marcha.
const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000/api';
const E2E_USER = {
  nombre: 'Usuario E2E',
  email: process.env.E2E_EMAIL ?? 'e2e@vidamaterna.co',
  password: process.env.E2E_PASSWORD ?? 'e2e-clave-segura',
};

export async function loginByApi(page: Page): Promise<void> {
  // 201 si se crea; 400 si ya existía: ambos valen.
  await page.request.post(`${API_URL}/auth/register/`, { data: E2E_USER });
  const res = await page.request.post(`${API_URL}/auth/login/`, {
    data: { email: E2E_USER.email, password: E2E_USER.password },
  });
  if (!res.ok()) {
    throw new Error(`No se pudo iniciar sesión de pruebas (${res.status()}). ¿Está el backend en marcha?`);
  }
  const body = await res.json();
  await page.addInitScript((session) => {
    localStorage.setItem('token', session.token);
    localStorage.setItem('username', session.nombre);
    localStorage.setItem('user_email', session.email);
  }, { token: body.access_token as string, nombre: body.nombre as string, email: body.email as string });
}
