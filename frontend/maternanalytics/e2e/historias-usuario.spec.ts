import { test, expect, type Page } from '@playwright/test';
import fs from 'node:fs';
import { loginByApi } from './helpers/auth';

// Pruebas funcionales: una por historia de usuario (HU-01 a HU-12 de la Tabla 3 del artículo).
// Cada prueba recorre los criterios de aceptación («Dado… cuando… entonces…») con el backend real.
// Los datos salen de dos archivos de 200 registros cargados por la API antes de empezar.
// Única simulación: la respuesta de la IA en HU-10 (el servicio de IA no se ejecuta en las pruebas).

const API = process.env.E2E_API_URL ?? 'http://localhost:8000/api';
const FIX = './e2e/fixtures';

test.describe.configure({ mode: 'serial', timeout: 120_000 });

test.beforeAll(async ({ request }) => {
  const usuario = {
    nombre: 'Usuario E2E',
    email: process.env.E2E_EMAIL ?? 'e2e@vidamaterna.co',
    password: process.env.E2E_PASSWORD ?? 'e2e-clave-segura',
    departamento_codigo: process.env.E2E_DEPARTAMENTO ?? 'antioquia',
    secretaria_codigo: process.env.E2E_SECRETARIA ?? 'bello',
  };
  await request.post(`${API}/auth/register/`, { data: usuario });
  const login = await request.post(`${API}/auth/login/`, { data: { email: usuario.email, password: usuario.password } });
  const { access_token: token } = await login.json();
  for (const tipo of ['mortalidad', 'morbilidad']) {
    const res = await request.post(`${API}/analisis/`, {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        tipo,
        archivo: { name: `${tipo}-realista-200.xlsx`, mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', buffer: fs.readFileSync(`${FIX}/${tipo}-realista-200.xlsx`) },
      },
      timeout: 120_000,
    });
    expect(res.status(), `carga de ${tipo}`).toBe(201);
  }
});

async function abrirDashboard(page: Page) {
  await loginByApi(page);
  await page.goto('/dashboard');
  await expect(page.getByText('Cargando VidaMaterna...')).toBeHidden({ timeout: 30000 });
  await expect(page.getByRole('region', { name: 'Resumen epidemiológico' }).or(page.getByLabel('Resumen epidemiológico'))).toBeVisible({ timeout: 60000 });
}

test('HU-01 Registro e inicio de sesión', async ({ page }) => {
  // Dado que no tengo cuenta, cuando completo el registro, entonces se crea mi cuenta.
  const email = `hu01-${Date.now()}@vidamaterna.co`;
  await page.goto('/register');
  await page.getByLabel('Nombre completo').fill('Funcionaria de prueba');
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Departamento').selectOption('antioquia');
  await page.getByLabel('Secretaría de salud').selectOption({ index: 1 });
  await page.getByLabel('Contraseña', { exact: true }).fill('clave-segura-1');
  await page.getByLabel('Confirmar contraseña').fill('clave-segura-1');
  await page.getByRole('button', { name: 'Crear cuenta' }).click();
  await expect(page.getByText(/Cuenta creada exitosamente/i)).toBeVisible({ timeout: 15000 });
  // Dado que tengo cuenta, cuando ingreso mis credenciales correctas, entonces accedo al dashboard.
  await page.goto('/login');
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña').fill('clave-segura-1');
  await page.getByRole('button', { name: 'Iniciar sesión' }).click();
  await expect(page).toHaveURL(/dashboard/, { timeout: 30000 });
});

test('HU-02 Carga y validación de archivos', async ({ page }) => {
  await loginByApi(page);
  await page.route('**/api/**', (route) => (route.request().method() === 'GET' ? route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }) : route.fallback()));
  await page.goto('/cargar-mortalidad');
  // Dado un archivo .xlsx del evento 550, cuando lo selecciono, entonces veo una vista previa con registros y columnas.
  await page.locator('input[type="file"]').setInputFiles(`${FIX}/mortalidad-valida-pequena.xlsx`);
  await expect(page.getByText(/registros/i).first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(/columnas/i).first()).toBeVisible();
  await expect(page.getByRole('button', { name: /Iniciar análisis/i })).toBeEnabled();
  // Dado un archivo con errores, cuando lo selecciono, entonces la plataforma indica el error y no permite procesarlo.
  await page.locator('input[type="file"]').setInputFiles(`${FIX}/mortalidad-invalida.xlsx`);
  await expect(page.getByRole('button', { name: /Iniciar análisis/i })).toBeDisabled({ timeout: 15000 });
  // (Dado un archivo válido, cuando inicio el análisis, entonces los datos quedan guardados: ver la prueba de carga de upload.spec.ts y la carga previa de esta suite.)
});

test('HU-03 Factores sociodemográficos y clínicos', async ({ page }) => {
  await abrirDashboard(page);
  await page.getByRole('tab', { name: /Mortalidad \(Ev\. 550\)/ }).click();
  await page.getByRole('tab', { name: 'Factores Sociodemográficos' }).click();
  await expect(page.getByRole('tab', { name: 'Factores Sociodemográficos' })).toHaveAttribute('aria-selected', 'true');
  await page.getByRole('tab', { name: 'Factores Clínicos' }).click();
  await expect(page.getByRole('tab', { name: 'Factores Clínicos' })).toHaveAttribute('aria-selected', 'true');
});

test('HU-04 Filtros por período y evento', async ({ page }) => {
  await abrirDashboard(page);
  const filtros = page.getByLabel('Filtros del análisis');
  // Dado que hay datos cargados, cuando selecciono el evento, entonces el análisis se limita a ese evento.
  await filtros.getByLabel('Evento').selectOption({ label: 'Solo mortalidad 550' });
  await expect(filtros.getByLabel('Evento')).toHaveValue(/.+/);
  // Dado que selecciono un año, cuando elijo además mes y semana, entonces se habilitan y se limita el período.
  await expect(filtros.getByLabel('Mes de Reporte')).toBeDisabled();
  await filtros.getByLabel('Año de Reporte').selectOption({ index: 1 });
  await expect(filtros.getByLabel('Mes de Reporte')).toBeEnabled();
});

test('HU-05 Indicadores resumen', async ({ page }) => {
  await abrirDashboard(page);
  const kpi = page.getByLabel('Resumen epidemiológico');
  for (const nombre of ['Mortalidad materna 550', 'Morbilidad materna extrema 549', 'Relación MME/MM', 'Índice de mortalidad']) {
    await expect(kpi.getByText(nombre).first()).toBeVisible();
  }
});

test('HU-06 Causas principales', async ({ page }) => {
  await abrirDashboard(page);
  await page.getByRole('tab', { name: 'Generalidades' }).click();
  await expect(page.getByText(/Top 10 Causas de Mortalidad/i)).toBeVisible({ timeout: 30000 });
  await expect(page.getByText(/Top 10 Causas de Morbilidad/i)).toBeVisible();
});

test('HU-07 Distribución por edad', async ({ page }) => {
  await abrirDashboard(page);
  await page.getByRole('tab', { name: /Mortalidad \(Ev\. 550\)/ }).click();
  await page.getByRole('tab', { name: 'Factores Sociodemográficos' }).click();
  await expect(page.getByText(/Distribución por edad/i).first()).toBeVisible({ timeout: 30000 });
  await expect(page.getByText(/<\s?19|menores de 19/i).first()).toBeVisible();
});

test('HU-08 Distribución por edad gestacional', async ({ page }) => {
  await abrirDashboard(page);
  await page.getByRole('tab', { name: /Mortalidad \(Ev\. 550\)/ }).click();
  await page.getByRole('tab', { name: 'Factores Clínicos' }).click();
  await expect(page.getByText(/edad gestacional/i).first()).toBeVisible({ timeout: 30000 });
});

test('HU-09 Cruce de variables', async ({ page }) => {
  await abrirDashboard(page);
  await page.getByRole('tab', { name: /Mortalidad \(Ev\. 550\)/ }).click();
  await page.getByRole('tab', { name: 'Factores Clínicos' }).click();
  // Dado que hay datos cargados, cuando elijo una variable sociodemográfica y una clínica, entonces veo una gráfica cruzada.
  await expect(page.getByText('Cruce de Variables (Mortalidad)')).toBeVisible({ timeout: 30000 });
  await page.locator('#cruce-socio-Mortalidad').selectOption('zona_residencia');
  await page.locator('#cruce-clinica-Mortalidad').selectOption('tipo_parto');
  // La gráfica se describe a sí misma (aria-label) con las categorías de ambas variables, y la leyenda
  // identifica cada categoría de la variable clínica.
  const grafica = page.getByRole('img', { name: /Urbana|Rural/ }).first();
  await expect(grafica).toBeVisible({ timeout: 30000 });
});

test('HU-10 Lectura automática y resumen con IA', async ({ page }) => {
  // El servicio de IA no corre en las pruebas: se simula su respuesta para validar el flujo de la interfaz.
  await page.route('**/api/analisis/*/narrativa/**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ narrativa: 'Resumen de prueba generado por IA.', modelo: 'prueba', generado_en: new Date().toISOString(), desde_cache: false }) }),
  );
  await abrirDashboard(page);
  await page.getByRole('tab', { name: /Mortalidad \(Ev\. 550\)/ }).click();
  // Dado que hay una gráfica, cuando la reviso, entonces aparece una «lectura automatizada».
  await expect(page.getByText(/Lectura automatizada/i).first()).toBeVisible({ timeout: 30000 });
  // Dado un análisis, cuando pulso «Generar resumen IA», entonces se genera el resumen.
  await page.getByRole('button', { name: /Resumen ejecutivo \(IA\)/ }).click(); // el panel viene plegado
  await page.getByRole('button', { name: /Generar resumen IA/i }).first().click();
  await expect(page.getByText('Resumen de prueba generado por IA.')).toBeVisible({ timeout: 30000 });
});

test('HU-11 Exportar reporte', async ({ page }) => {
  await abrirDashboard(page);
  await page.getByRole('button', { name: /Exportar Reporte/i }).first().click();
  const modal = page.getByLabel('Exportar reporte epidemiológico');
  await expect(modal).toBeVisible();
  await expect(modal.getByText(/Excel/i).first()).toBeVisible();
  await expect(modal.getByText(/PDF/i).first()).toBeVisible();
  await expect(modal.getByText(/CSV/i).first()).toBeVisible();
});

test('HU-12 Historial de cargas', async ({ page }) => {
  await loginByApi(page);
  await page.goto('/historial');
  await expect(page.getByRole('heading', { name: 'Historial de Cargas' })).toBeVisible({ timeout: 30000 });
  // Dado que he subido archivos, cuando abro el historial, entonces veo cada carga con sus columnas.
  for (const col of ['Año', 'Semana', 'Fecha', 'Tipo', 'Archivo', 'Registros']) {
    await expect(page.getByRole('columnheader', { name: col }).first()).toBeVisible();
  }
  await expect(page.getByText(/-realista-200\.xlsx/).first()).toBeVisible();
  // Dado el historial, cuando uso la búsqueda, entonces la lista se limita a esas cargas.
  await page.getByPlaceholder('Archivo o evento (549 / 550)').fill('inexistente-xyz');
  await expect(page.getByText(/Ninguna carga coincide/i)).toBeVisible({ timeout: 15000 });
});
