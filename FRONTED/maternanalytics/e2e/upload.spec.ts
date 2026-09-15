import { test, expect } from '@playwright/test';

// NOTA: Para estas pruebas, usualmente se genera un estado de login previo 
// o se inyecta el token en localStorage antes de cada test.
test.describe('Flujo de Carga SIVIGILA', () => {

  test.beforeEach(async ({ page }) => {
    // Truco para saltar el login en las pruebas: inyectar sesión falsa
    await page.addInitScript(() => {
      localStorage.setItem('token', 'fake-token');
      localStorage.setItem('username', 'Test User');
    });

    // Mockeamos SOLO las peticiones GET (para que el frontend no nos expulse al ver un token falso).
    // Las peticiones POST (como la subida del Excel) sí deben llegar al backend real.
    await page.route('**/api/**', route => {
      if (route.request().method() === 'GET') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      } else {
        route.fallback();
      }
    });
  });

  test('Debería poder navegar a Carga de Mortalidad y ver el formulario', async ({ page }) => {
    await page.goto('/cargar-mortalidad');
    
    // Vite puede demorar compilando los módulos, esperamos a que la pantalla de carga desaparezca
    await expect(page.getByText('Cargando VidaMaterna...')).toBeHidden({ timeout: 30000 });
    
    // Verifica el título de la sección
    await expect(page.getByText('Cargar Datos de Mortalidad Materna')).toBeVisible({ timeout: 30000 });
    
    // Verifica que exista el botón o zona para subir archivo
    await expect(page.locator('input[type="file"]')).toBeAttached({ timeout: 10000 });
  });

  test('Debería poder navegar a Carga de Morbilidad y ver el formulario', async ({ page }) => {
    await page.goto('/cargar-morbilidad');
    
    // Esperamos a que la pantalla de carga desaparezca
    await expect(page.getByText('Cargando VidaMaterna...')).toBeHidden({ timeout: 30000 });
    
    // Verifica el título de la sección
    await expect(page.getByText('Cargar Datos de Morbilidad Materna Extrema')).toBeVisible({ timeout: 30000 });
    
    // Verifica que exista el input de archivo
    await expect(page.locator('input[type="file"]')).toBeAttached({ timeout: 10000 });
  });

  test('Debería rechazar un archivo Excel inválido o con formato incorrecto', async ({ page }) => {
    await page.goto('/cargar-mortalidad');
    
    // Subimos un archivo que sabemos que es incorrecto
    await page.locator('input[type="file"]').setInputFiles('./e2e/fixtures/mortalidad-invalida.xlsx');
    
    // El sistema deshabilita el botón de analizar automáticamente si hay error de validación
    await expect(page.getByRole('button', { name: /Iniciar análisis/i })).toBeDisabled({ timeout: 10000 });
  });

  test('Debería procesar exitosamente un archivo Excel válido', async ({ page }) => {
    // Le damos más tiempo a la prueba porque el backend toma varios segundos procesando
    test.setTimeout(120000);

    await page.goto('/cargar-mortalidad');
    
    // Subimos un archivo Excel que sabemos que está perfecto
    await page.locator('input[type="file"]').setInputFiles('./e2e/fixtures/mortalidad-valida.xlsx');
    
    // El botón debería estar habilitado y le damos click
    await expect(page.getByRole('button', { name: /Iniciar análisis/i })).toBeEnabled({ timeout: 10000 });
    await page.getByRole('button', { name: /Iniciar análisis/i }).click();

    // Verificamos el mensaje de éxito real del componente UploadSection
    // Le damos hasta 90 segundos porque sabemos que el botón se queda en "Procesando registros..."
    await expect(page.getByText(/Análisis guardado correctamente/i)).toBeVisible({ timeout: 90000 });
  });
});
