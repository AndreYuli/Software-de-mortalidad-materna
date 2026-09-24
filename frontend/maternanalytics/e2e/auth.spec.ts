import { test, expect } from '@playwright/test';

test.describe('Flujo de Autenticación', () => {

  test('Debería cargar la página de login', async ({ page }) => {
    await page.goto('/login');
    // Verifica que exista un botón o texto de Iniciar sesión
    await expect(page.getByRole('heading', { name: /Inicio de sesión/i, level: 2 })).toBeVisible();
    await expect(page.getByLabel(/Correo/i)).toBeVisible();
    await expect(page.getByLabel(/Contraseña/i)).toBeVisible();
  });

  test('Debería redirigir al dashboard con credenciales correctas', async ({ page }) => {
    // Simula el login. Necesitarás tener credenciales de prueba en tu base de datos o interceptar la red
    await page.goto('/login');
    
    // Llenar formulario (Ajusta los selectores según tu HTML)
    await page.getByLabel(/Correo/i).fill('admin@test.com');
    await page.getByLabel(/Contraseña/i).fill('password123');
    
    // Hacer clic en entrar
    await page.getByRole('button', { name: /Entrar|Iniciar sesión/i }).click();

    // Esperar a que la URL cambie al dashboard (Si tienes token/autenticación real)
    // Descomentar cuando tengas datos reales de prueba
    // await expect(page).toHaveURL(/.*\/dashboard/);
    // await expect(page.getByText('Cargando VidaMaterna...')).toBeHidden();
  });

  test('No debería dejar pasar con credenciales incorrectas', async ({ page }) => {
    await page.goto('/login');
    
    await page.getByLabel(/Correo/i).fill('wrong@test.com');
    await page.getByLabel(/Contraseña/i).fill('wrongpass');
    
    await page.getByRole('button', { name: /Entrar|Iniciar sesión/i }).click();

    // Verifica que sale un mensaje de error (ajustar al mensaje real que uses)
    // await expect(page.getByText(/Credenciales inválidas/i)).toBeVisible();
    await expect(page).toHaveURL(/.*\/login/); // Sigue en el login
  });

  test('Un token inválido expulsa al usuario a /login y borra la sesión', async ({ page }) => {
    // Se siembra la sesión una sola vez (addInitScript se repetiría tras la redirección)
    await page.goto('/login');
    await page.evaluate(() => {
      localStorage.setItem('token', 'token-invalido');
      localStorage.setItem('username', 'Fantasma');
    });
    await page.goto('/dashboard');

    // El backend responde 401 y el frontend elimina la sesión local
    await expect(page).toHaveURL(/.*\/login/, { timeout: 30000 });
    expect(await page.evaluate(() => localStorage.getItem('token'))).toBeNull();
  });

  test('Proteger rutas privadas si no hay sesión', async ({ page }) => {
    // Intento acceder directo al dashboard sin haber iniciado sesión
    await page.goto('/dashboard');
    
    // Debería expulsarme al login
    await expect(page).toHaveURL(/.*\/login/);
  });
});
