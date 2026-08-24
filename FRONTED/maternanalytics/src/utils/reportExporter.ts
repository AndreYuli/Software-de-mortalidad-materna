import * as XLSX from 'xlsx'
import { getCie10Description } from '../constants/dashboardConstants'

export interface ReportExportData {
  titulo: string
  fechaGeneracion: string
  periodo: {
    anio: string
    mes: string
    segmento: string
  }
  kpis: {
    totalDefunciones: number
    totalMorbilidad: number
    casosTotales: number
    tasaLetalidad: string
    promedioEdad: string
    ingresosUci?: number
  }
  evolucionMensual: {
    meses: string[]
    mortalidad: number[]
    morbilidad: number[]
  }
  causasPrincipales: {
    causas: string[]
    valores: number[]
  }
  demoras: {
    nombres: string[]
    valores: number[]
  }
  distribucionEdad: {
    grupos: string[]
    mortalidad: number[]
    morbilidad: number[]
  }
  fallasOrganicas?: {
    nombre: string
    casos: number
  }[]
  aiSummary?: string
}

/**
 * Exporta los datos consolidados del análisis a un archivo Excel (.xlsx) con múltiples hojas.
 */
export function exportReportToExcel(data: ReportExportData, filename?: string) {
  const wb = XLSX.utils.book_new()

  // 1. Hoja de Resumen Ejecutivo y KPIs
  const resumenRows = [
    { Parámetro: 'Reporte', Valor: data.titulo },
    { Parámetro: 'Fecha de Generación', Valor: data.fechaGeneracion },
    { Parámetro: 'Año Filtrado', Valor: data.periodo.anio || 'Todos los años' },
    { Parámetro: 'Mes Filtrado', Valor: data.periodo.mes || 'Todos los meses' },
    { Parámetro: 'Segmento', Valor: data.periodo.segmento.toUpperCase() },
    { Parámetro: 'Total Defunciones (Mortalidad)', Valor: data.kpis.totalDefunciones },
    { Parámetro: 'Total Morbilidad Materna Extrema', Valor: data.kpis.totalMorbilidad },
    { Parámetro: 'Total de Casos Evaluados', Valor: data.kpis.casosTotales },
    { Parámetro: 'Tasa / Razón de Letalidad', Valor: data.kpis.tasaLetalidad },
    { Parámetro: 'Edad Promedio', Valor: data.kpis.promedioEdad },
    { Parámetro: 'Síntesis Epidemiológica IA', Valor: data.aiSummary || 'No generada' },
  ]
  const wsResumen = XLSX.utils.json_to_sheet(resumenRows)
  XLSX.utils.book_append_sheet(wb, wsResumen, 'Resumen y KPIs')

  // 2. Hoja de Evolución Mensual
  const evolucionRows = data.evolucionMensual.meses.map((mes, idx) => ({
    Mes: mes,
    'Casos Mortalidad': data.evolucionMensual.mortalidad[idx] || 0,
    'Casos Morbilidad': data.evolucionMensual.morbilidad[idx] || 0,
    'Total Mes': (data.evolucionMensual.mortalidad[idx] || 0) + (data.evolucionMensual.morbilidad[idx] || 0),
  }))
  const wsEvolucion = XLSX.utils.json_to_sheet(evolucionRows)
  XLSX.utils.book_append_sheet(wb, wsEvolucion, 'Evolución Temporal')

  // 3. Hoja de Causas Principales
  const totalCausas = data.causasPrincipales.valores.reduce((a, b) => a + b, 0) || 1
  const causasRows = data.causasPrincipales.causas.map((c, idx) => {
    const casos = data.causasPrincipales.valores[idx] || 0
    return {
      'Causa / Criterio': getCie10Description(c),
      Código: c,
      Casos: casos,
      'Porcentaje (%)': `${Math.round((casos / totalCausas) * 100)}%`,
    }
  })
  const wsCausas = XLSX.utils.json_to_sheet(causasRows)
  XLSX.utils.book_append_sheet(wb, wsCausas, 'Top Causas CIE-10')

  // 4. Hoja de Demoras Obstétricas
  const totalDemoras = data.demoras.valores.reduce((a, b) => a + b, 0) || 1
  const demorasRows = data.demoras.nombres.map((d, idx) => {
    const casos = data.demoras.valores[idx] || 0
    return {
      'Tipo de Demora Obstétrica': d,
      Casos: casos,
      'Porcentaje (%)': `${Math.round((casos / totalDemoras) * 100)}%`,
    }
  })
  const wsDemoras = XLSX.utils.json_to_sheet(demorasRows)
  XLSX.utils.book_append_sheet(wb, wsDemoras, 'Demoras Obstétricas')

  // 5. Hoja de Distribución por Edad
  const edadRows = data.distribucionEdad.grupos.map((grupo, idx) => {
    const mort = data.distribucionEdad.mortalidad[idx] || 0
    const morb = data.distribucionEdad.morbilidad[idx] || 0
    return {
      'Grupo Etario': grupo,
      Mortalidad: mort,
      Morbilidad: morb,
      'Total Pacientes': mort + morb,
    }
  })
  const wsEdad = XLSX.utils.json_to_sheet(edadRows)
  XLSX.utils.book_append_sheet(wb, wsEdad, 'Distribución Etaria')

  // 6. Hoja de Fallas Orgánicas si existen
  if (data.fallasOrganicas && data.fallasOrganicas.length > 0) {
    const totalFallas = data.fallasOrganicas.reduce((a, b) => a + b.casos, 0) || 1
    const fallasRows = data.fallasOrganicas.map((f) => ({
      'Falla Orgánica': f.nombre,
      Casos: f.casos,
      'Porcentaje (%)': `${Math.round((f.casos / totalFallas) * 100)}%`,
    }))
    const wsFallas = XLSX.utils.json_to_sheet(fallasRows)
    XLSX.utils.book_append_sheet(wb, wsFallas, 'Fallas Orgánicas MME')
  }

  // Nombre de archivo por defecto
  const name = filename || `Reporte_Epidemiologico_VidaMaterna_${data.periodo.anio || 'Consolidado'}.xlsx`
  XLSX.writeFile(wb, name)
}

/**
 * Descarga una tabla de datos en formato CSV con codificación UTF-8 BOM para soporte total en Excel.
 */
export function exportToCsv(filename: string, headers: string[], rows: (string | number)[][]) {
  const csvContent =
    '\uFEFF' +
    [headers.join(';'), ...rows.map((row) => row.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(';'))].join(
      '\r\n',
    )

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Abre una ventana con un informe clínico/epidemiológico formal listo para imprimir o guardar como PDF.
 */
export function printExecutiveMedicalReport(data: ReportExportData) {
  const win = window.open('', '_blank', 'width=950,height=1000')
  if (!win) {
    alert('Por favor permite abrir ventanas emergentes para visualizar el reporte PDF.')
    return
  }

  const causesTableRows = data.causasPrincipales.causas
    .map((c, i) => {
      const val = data.causasPrincipales.valores[i] || 0
      return `<tr>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;"><b>${c}</b> - ${getCie10Description(c)}</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600;">${val}</td>
      </tr>`
    })
    .join('')

  const demorasTableRows = data.demoras.nombres
    .map((d, i) => {
      const val = data.demoras.valores[i] || 0
      return `<tr>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">${d}</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600;">${val}</td>
      </tr>`
    })
    .join('')

  const ageTableRows = data.distribucionEdad.grupos
    .map((g, i) => {
      const mort = data.distribucionEdad.mortalidad[i] || 0
      const morb = data.distribucionEdad.morbilidad[i] || 0
      return `<tr>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0;">${g} años</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">${mort}</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">${morb}</td>
        <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 600;">${mort + morb}</td>
      </tr>`
    })
    .join('')

  const html = `
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>${data.titulo} - VidaMaterna</title>
  <style>
    @page {
      size: A4;
      margin: 18mm 15mm 20mm 15mm;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      line-height: 1.5;
      margin: 0;
      padding: 24px;
      background: #ffffff;
      font-size: 13px;
    }
    .header {
      border-bottom: 2px solid #3b82f6;
      padding-bottom: 16px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .header-title h1 {
      margin: 0 0 4px 0;
      font-size: 20px;
      color: #0f172a;
      font-weight: 800;
    }
    .header-title p {
      margin: 0;
      color: #64748b;
      font-size: 12px;
    }
    .meta-badge {
      background: #f1f5f9;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 11px;
      text-align: right;
      color: #475569;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 12px;
      text-align: center;
    }
    .kpi-card .val {
      font-size: 22px;
      font-weight: 800;
      color: #0f172a;
      margin: 4px 0;
    }
    .kpi-card .lbl {
      font-size: 11px;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
    }
    .ai-box {
      background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
      border: 1px solid #d8b4fe;
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 24px;
    }
    .ai-box-title {
      font-size: 13px;
      font-weight: 700;
      color: #6b21a8;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .ai-box p {
      margin: 0;
      color: #3b0764;
      font-size: 12.5px;
      line-height: 1.6;
    }
    .section-title {
      font-size: 15px;
      font-weight: 700;
      color: #0f172a;
      margin: 20px 0 10px 0;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
      font-size: 12px;
    }
    th {
      background: #f1f5f9;
      padding: 8px 12px;
      text-align: left;
      font-weight: 700;
      color: #334155;
      border-bottom: 2px solid #cbd5e1;
    }
    .two-cols {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    .footer {
      margin-top: 40px;
      padding-top: 12px;
      border-top: 1px solid #e2e8f0;
      font-size: 11px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }
    .print-actions {
      position: fixed;
      top: 16px;
      right: 16px;
      display: flex;
      gap: 10px;
      background: white;
      padding: 8px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      border: 1px solid #cbd5e1;
      z-index: 100;
    }
    .btn {
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      border: none;
    }
    .btn-primary {
      background: #2563eb;
      color: white;
    }
    .btn-secondary {
      background: #f1f5f9;
      color: #334155;
    }
    @media print {
      .print-actions { display: none !important; }
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="print-actions">
    <button class="btn btn-secondary" onclick="window.close()">Cerrar</button>
    <button class="btn btn-primary" onclick="window.print()">🖨️ Imprimir / Guardar como PDF</button>
  </div>

  <div class="header">
    <div class="header-title">
      <h1>Informe Epidemiológico de Vigilancia Materna</h1>
      <p>Sistema Integrado de Análisis SIVIGILA — VidaMaterna</p>
    </div>
    <div class="meta-badge">
      <div><b>Fecha:</b> ${data.fechaGeneracion}</div>
      <div><b>Periodo:</b> ${data.periodo.anio || 'Histórico'} ${data.periodo.mes ? `- Mes ${data.periodo.mes}` : ''}</div>
      <div><b>Segmento:</b> ${data.periodo.segmento.toUpperCase()}</div>
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="lbl">Defunciones (MM)</div>
      <div class="val" style="color: #ef4444;">${data.kpis.totalDefunciones}</div>
    </div>
    <div class="kpi-card">
      <div class="lbl">Morbilidad Extrema (MME)</div>
      <div class="val" style="color: #3b82f6;">${data.kpis.totalMorbilidad}</div>
    </div>
    <div class="kpi-card">
      <div class="lbl">Total Casos Consolidados</div>
      <div class="val">${data.kpis.casosTotales}</div>
    </div>
    <div class="kpi-card">
      <div class="lbl">Razón / Letalidad</div>
      <div class="val">${data.kpis.tasaLetalidad}</div>
    </div>
  </div>

  ${
    data.aiSummary
      ? `
  <div class="ai-box">
    <div class="ai-box-title">✨ Resumen Ejecutivo de Inteligencia Epidemiológica (IA)</div>
    <p>${data.aiSummary}</p>
  </div>`
      : ''
  }

  <div class="two-cols">
    <div>
      <div class="section-title">Principales Causas / Criterios (CIE-10)</div>
      <table>
        <thead>
          <tr>
            <th>Diagnóstico</th>
            <th style="text-align: right;">Casos</th>
          </tr>
        </thead>
        <tbody>
          ${causesTableRows}
        </tbody>
      </table>
    </div>

    <div>
      <div class="section-title">Demoras Críticas en la Atención</div>
      <table>
        <thead>
          <tr>
            <th>Modelo de las 4 Demoras</th>
            <th style="text-align: right;">Ocurrencias</th>
          </tr>
        </thead>
        <tbody>
          ${demorasTableRows}
        </tbody>
      </table>
    </div>
  </div>

  <div class="section-title">Distribución por Rango de Edad</div>
  <table>
    <thead>
      <tr>
        <th>Grupo Etario</th>
        <th style="text-align: center;">Mortalidad</th>
        <th style="text-align: center;">Morbilidad</th>
        <th style="text-align: right;">Total Pacientes</th>
      </tr>
    </thead>
    <tbody>
      ${ageTableRows}
    </tbody>
  </table>

  <div class="footer">
    <span>Documento generado por VidaMaterna - Sistema de Inteligencia Epidemiológica</span>
    <span>Página 1 de 1</span>
  </div>
</body>
</html>
`

  win.document.open()
  win.document.write(html)
  win.document.close()
}
