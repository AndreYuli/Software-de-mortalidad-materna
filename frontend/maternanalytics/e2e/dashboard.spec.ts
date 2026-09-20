import { test, expect } from '@playwright/test';
import { loginByApi } from './helpers/auth';

test.describe('Flujo de Dashboard y Análisis (IA)', () => {

  test.beforeEach(async ({ page }) => {
    // Sesión real: el backend rechaza tokens falsos con 401 (ver helpers/auth.ts)
    await loginByApi(page);
  });

  test('Debería cargar el Dashboard principal por defecto', async ({ page }) => {
    test.setTimeout(120000); // 2 minutos de tiempo global para este test

    await page.goto('/dashboard');
    
    // Esperamos a que la pantalla de carga desaparezca
    await expect(page.getByText('Cargando VidaMaterna...')).toBeHidden({ timeout: 30000 });
    
    // El texto dependerá de tu componente AnalysisHomeSection
    await expect(page.getByRole('main')).toBeVisible();
    
    // El dashboard puede estar en dos estados:
    // 1. Tiene datos: Muestra los filtros (combobox)
    // 2. No tiene datos: Muestra la pantalla de bienvenida
    const filtroCombobox = page.getByRole('combobox').first();
    const mensajeBienvenida = page.getByText(/Aún no hay datos para analizar/i);
    
    await expect(filtroCombobox.or(mensajeBienvenida)).toBeVisible({ timeout: 60000 });
  });

  // test('Debería poder solicitar una narrativa a la IA', async ({ page }) => {
  //   // Esta prueba idealmente requiere que mockees la respuesta del backend para no consumir tokens reales
  //   // o asegurarte de usar un backend de pruebas.
  //   
  //   // Interceptar la llamada a la red y responder con datos falsos (Mocking)
  //   await page.route('**/api/analisis/*/narrativa/*', route => {
  //     route.fulfill({
  //       status: 200,
  //       contentType: 'application/json',
  //       body: JSON.stringify({
  //         narrativa: 'Esta es una narrativa generada por IA en un entorno de pruebas.',
  //         modelo: 'test-model',
  //         desde_cache: true
  //       })
  //     });
  //   });
  //
  //   await page.goto('/dashboard');
  //   
  //   // Buscar y presionar el botón de IA
  //   const botonIa = page.getByRole('button', { name: /Resumen Ejecutivo|IA/i });
  //   if (await botonIa.isVisible()) {
  //     await botonIa.click();
  //     
  //     // Verificar que el texto simulado aparezca en la pantalla
  //     await expect(page.getByText('Esta es una narrativa generada por IA en un entorno de pruebas.')).toBeVisible();
  //   }
  // });
});
