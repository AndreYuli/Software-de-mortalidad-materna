"""
Procesadores de datos para análisis de Mortalidad y Morbilidad Materna.
Incluye funciones de clustering, análisis estadístico y reglas de negocio.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist


_EXCEL_ORIGIN = pd.Timestamp('1899-12-30')


def _parse_fecha_robusta(serie):
    """Parsea una serie de fechas: datetime, serial Excel (1000-100000) o string DD/MM/YYYY."""
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    resultado = []
    for v in serie:
        ts = pd.NaT
        if v is None:
            pass
        elif hasattr(v, 'year'):
            try:
                ts = pd.Timestamp(v)
            except Exception:
                pass
        else:
            try:
                n = float(v)
                if 1000 < n < 100000:
                    ts = _EXCEL_ORIGIN + pd.Timedelta(days=int(n))
            except (ValueError, TypeError):
                try:
                    ts = pd.to_datetime(str(v), dayfirst=True, errors='coerce')
                except Exception:
                    pass
        resultado.append(ts)
    return pd.Series(resultado, index=serie.index, dtype='datetime64[ns]')


def preparar_dataframe_analisis(df):
    """Normaliza el DataFrame y elimina filas vacias o duplicadas exactas para analisis."""
    normalizado = df.copy()
    total_original = len(normalizado)

    if total_original == 0:
        return normalizado, {'total_original': 0, 'filas_vacias_omitidas': 0, 'filas_duplicadas_omitidas': 0}

    # Calcular Edad si 'Fecha de Nacimiento' y alguna columna de fecha del caso existen
    birth_col = 'Fecha de Nacimiento'
    event_col_candidates = [
        '9.3 Fecha parto (dd/mm/aaaa)', '9.3 Fecha parto',
        '5.2 Fecha de defunción', '5.2 Fecha de defuncion',
        'Fecha de egreso', 'Fecha de egreso (dd/mm/aaaa)',
    ]

    if birth_col in normalizado.columns:
        event_col = next((c for c in event_col_candidates if c in normalizado.columns), None)
        print(f"[EDAD] birth_col={birth_col!r} event_col={event_col!r} cols={list(normalizado.columns)}")

        if event_col:
            try:
                nacs = _parse_fecha_robusta(normalizado[birth_col])
                evs = _parse_fecha_robusta(normalizado[event_col])
                print(f"[EDAD] nacs muestra: {nacs.dropna().head(3).tolist()}")
                print(f"[EDAD] evs  muestra: {evs.dropna().head(3).tolist()}")
                years = evs.dt.year - nacs.dt.year
                before_birthday = (evs.dt.month < nacs.dt.month) | (
                    (evs.dt.month == nacs.dt.month) & (evs.dt.day < nacs.dt.day)
                )
                edades = years - before_birthday.astype(int)
                normalizado['Edad'] = edades.where((edades >= 0) & (edades <= 120))
                print(f"[EDAD] edades válidas: {normalizado['Edad'].dropna().count()} de {len(normalizado)}")
            except Exception as exc:
                print(f"[EDAD] ERROR: {exc}")
    else:
        print(f"[EDAD] '{birth_col}' no está en el dataframe. Columnas: {list(normalizado.columns)}")

    columnas_texto = normalizado.select_dtypes(include=['object']).columns
    for columna in columnas_texto:
        normalizado[columna] = normalizado[columna].apply(
            lambda valor: valor.strip() if isinstance(valor, str) else valor
        )

    sin_vacias = normalizado.dropna(how='all')
    filas_vacias_omitidas = total_original - len(sin_vacias)
    sin_duplicadas = sin_vacias.drop_duplicates().reset_index(drop=True)
    filas_duplicadas_omitidas = len(sin_vacias) - len(sin_duplicadas)

    return sin_duplicadas, {
        'total_original': total_original,
        'filas_vacias_omitidas': filas_vacias_omitidas,
        'filas_duplicadas_omitidas': filas_duplicadas_omitidas,
    }


def es_valor_positivo(valor):
    if pd.isna(valor):
        return False
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return float(valor) != 0

    texto = str(valor).strip().lower()
    return texto in {'1', 'si', 'sí', 's', 'true', 'x', 'yes', 'y'}


class MortalidadProcessor:
    """Procesador de datos de Mortalidad Materna (Evento 550)."""
    
    # Diccionario de datos - Campos clave y sus valores esperados
    MOMENTO_MUERTE = {
        1: 'Durante el embarazo',
        2: 'Durante el parto',
        3: 'Puerperio (hasta 42 días)',
        4: 'Tardía (43 días - 1 año)',
    }
    
    TIPO_PARTO = {
        1: 'Vaginal espontáneo',
        2: 'Vaginal instrumentado',
        3: 'Cesárea',
        4: 'Aborto',
    }
    
    DEMORAS = {
        'demora_1': 'Reconocimiento del problema',
        'demora_2': 'Decisión de buscar atención',
        'demora_3': 'Acceso al centro de salud',
        'demora_4': 'Calidad de atención recibida',
    }
    
    SITIO_DEFUNCION = {
        1: 'Hospital/Clínica',
        2: 'Centro de salud',
        3: 'Domicilio',
        4: 'Vía pública',
        5: 'Otro',
    }
    
    def __init__(self, df):
        """
        Inicializa el procesador con un DataFrame de pandas.
        
        Args:
            df: DataFrame con datos de mortalidad materna
        """
        self.df = df.copy()
        self._limpiar_datos()
    
    def _limpiar_datos(self):
        """Limpia y normaliza los datos."""
        # Convertir columnas numéricas
        numeric_cols = [
            '6.5 Gestaciones', '6.6 Partos Vaginales', '6.7 Cesáreas',
            '6.8 Muertos', '6.9 Vivos', '6.10 Abortos',
            '8.1 No. CPN', '8.2 Semana inicio CPN', '9.2 Semana gestación'
        ]
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Eliminar filas completamente vacías
        self.df = self.df.dropna(how='all')
    
    def calcular_estadisticas_basicas(self):
        """Calcula estadísticas descriptivas básicas."""
        stats = {
            'total_casos': len(self.df),
            'edad_promedio': None,
            'gestaciones_promedio': None,
            'controles_prenatales_promedio': None,
        }
        
        if 'Edad' in self.df.columns:
            edades = self.df['Edad'].dropna()
            if not edades.empty:
                stats['edad_promedio'] = float(edades.mean())

        if '6.5 Gestaciones' in self.df.columns:
            stats['gestaciones_promedio'] = float(self.df['6.5 Gestaciones'].mean())
        
        if '8.1 No. CPN' in self.df.columns:
            stats['controles_prenatales_promedio'] = float(self.df['8.1 No. CPN'].mean())
        
        return stats
    
    def analizar_momento_muerte(self):
        """Analiza la distribución del momento de la muerte."""
        if '9.1 Momento de la muerte' not in self.df.columns:
            return {}
        
        distribucion = self.df['9.1 Momento de la muerte'].value_counts().to_dict()
        
        return {
            'distribucion': {
                self.MOMENTO_MUERTE.get(k, f'Código {k}'): int(v) 
                for k, v in distribucion.items()
            },
            'total': int(sum(distribucion.values()))
        }
    
    def analizar_demoras(self):
        """Analiza las cuatro demoras en la atención."""
        demoras_cols = {
            'demora_1': '10.3.1 Demora 1',
            'demora_2': '10.3.2 Demora 2',
            'demora_3': '10.3.3 Demora 3',
            'demora_4': '10.3.4 Demora 4',
        }
        
        resultado = {}
        for key, col in demoras_cols.items():
            if col in self.df.columns:
                # Contar valores positivos (1, Sí, X, true, etc.)
                total = self.df[col].notna().sum()
                con_demora = self.df[col].apply(es_valor_positivo).sum()
                resultado[key] = {
                    'nombre': self.DEMORAS[key],
                    'casos_con_demora': int(con_demora),
                    'porcentaje': float(con_demora / total * 100) if total > 0 else 0
                }
        
        return resultado
    
    def analizar_causas_cie10(self, top_n=10):
        """Analiza las causas básicas de muerte (CIE-10)."""
        if '10.1 Causa básica CIE-10' not in self.df.columns:
            return {}

        causas = self.df['10.1 Causa básica CIE-10'].value_counts().head(top_n)

        return {
            'top_causas': [
                {'codigo': str(codigo), 'casos': int(casos)}
                for codigo, casos in causas.items()
            ],
            'total_causas_unicas': int(self.df['10.1 Causa básica CIE-10'].nunique())
        }

    def analizar_obstetrico_por_edad(self):
        """Histograma de variables obstétricas comparadas por grupo de edad."""
        variables = [
            ('6.5 Gestaciones', 'Gestaciones'),
            ('6.6 Partos Vaginales', 'Partos vaginales'),
            ('6.7 Cesáreas', 'Cesáreas'),
            ('6.10 Abortos', 'Abortos'),
        ]
        grupos_edad = [
            {'label': '<20', 'min': 0, 'max': 19},
            {'label': '20-29', 'min': 20, 'max': 29},
            {'label': '30-39', 'min': 30, 'max': 39},
            {'label': '≥40', 'min': 40, 'max': 120},
        ]
        tiene_edad = 'Edad' in self.df.columns
        resultado = {}

        for col, nombre in variables:
            if col not in self.df.columns:
                continue
            serie = pd.to_numeric(self.df[col], errors='coerce').dropna()
            if len(serie) < 2:
                continue
            max_val = min(int(serie.max()), 10)
            valores_eje = list(range(0, max_val + 1))
            conteos_total = [int((serie == v).sum()) for v in valores_eje]

            por_edad = {}
            if tiene_edad:
                edades = pd.to_numeric(self.df['Edad'], errors='coerce')
                for grupo in grupos_edad:
                    mask = (edades >= grupo['min']) & (edades <= grupo['max'])
                    subgrupo = pd.to_numeric(self.df.loc[mask, col], errors='coerce').dropna()
                    if len(subgrupo) > 0:
                        por_edad[grupo['label']] = [int((subgrupo == v).sum()) for v in valores_eje]

            resultado[col] = {
                'nombre': nombre,
                'valores_eje': valores_eje,
                'conteos_total': conteos_total,
                'por_edad': por_edad,
                'promedio': float(serie.mean()),
                'total': int(len(serie)),
            }
        return resultado

    def clustering_factores_riesgo(self, n_clusters=3):
        """
        Realiza clustering K-means sobre factores de riesgo.
        
        Args:
            n_clusters: Número de clusters a crear
            
        Returns:
            dict con resultados del clustering
        """
        # Seleccionar características para clustering
        features_cols = [
            '6.5 Gestaciones', '6.6 Partos Vaginales', '6.7 Cesáreas',
            '6.10 Abortos', '8.1 No. CPN', '9.2 Semana gestación'
        ]
        
        # Filtrar columnas que existen
        available_cols = [col for col in features_cols if col in self.df.columns]
        
        if len(available_cols) < 2:
            return {'error': 'Datos insuficientes para clustering'}
        
        # Preparar datos
        df_cluster = self.df[available_cols].dropna()
        
        if len(df_cluster) < n_clusters:
            return {'error': f'Se necesitan al menos {n_clusters} registros completos'}
        
        # Normalizar datos
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_cluster)
        
        # Aplicar K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # Reducción dimensional para visualización (PCA a 2D y 3D)
        pca_2d = PCA(n_components=2)
        X_pca_2d = pca_2d.fit_transform(X_scaled)
        
        pca_3d = PCA(n_components=3)
        X_pca_3d = pca_3d.fit_transform(X_scaled)
        
        # Preparar resultados
        resultado = {
            'n_clusters': n_clusters,
            'n_samples': len(df_cluster),
            'features_used': available_cols,
            'clusters': clusters.tolist(),
            'pca_2d': {
                'x': X_pca_2d[:, 0].tolist(),
                'y': X_pca_2d[:, 1].tolist(),
                'variance_explained': float(pca_2d.explained_variance_ratio_.sum())
            },
            'pca_3d': {
                'x': X_pca_3d[:, 0].tolist(),
                'y': X_pca_3d[:, 1].tolist(),
                'z': X_pca_3d[:, 2].tolist(),
                'variance_explained': float(pca_3d.explained_variance_ratio_.sum())
            },
            'centroids': kmeans.cluster_centers_.tolist(),
            'cluster_sizes': [int((clusters == i).sum()) for i in range(n_clusters)]
        }
        
        # Características promedio por cluster
        df_cluster['cluster'] = clusters
        cluster_profiles = []
        
        for i in range(n_clusters):
            cluster_data = df_cluster[df_cluster['cluster'] == i][available_cols]
            profile = {
                'cluster_id': i,
                'size': int((clusters == i).sum()),
                'features': {
                    col: float(cluster_data[col].mean())
                    for col in available_cols
                }
            }
            cluster_profiles.append(profile)
        
        resultado['cluster_profiles'] = cluster_profiles
        
        return resultado
    
    def clustering_jerarquico(self, method='ward'):
        """
        Realiza clustering jerárquico para dendrograma.
        
        Args:
            method: Método de enlace ('ward', 'complete', 'average', 'single')
            
        Returns:
            dict con datos para dendrograma
        """
        features_cols = [
            '6.5 Gestaciones', '6.6 Partos Vaginales', '6.7 Cesáreas',
            '8.1 No. CPN', '9.2 Semana gestación'
        ]
        
        available_cols = [col for col in features_cols if col in self.df.columns]
        
        if len(available_cols) < 2:
            return {'error': 'Datos insuficientes para clustering jerárquico'}
        
        df_cluster = self.df[available_cols].dropna()
        
        if len(df_cluster) < 3:
            return {'error': 'Se necesitan al menos 3 registros'}
        
        # Limitar a 100 registros para rendimiento
        if len(df_cluster) > 100:
            df_cluster = df_cluster.sample(100, random_state=42)
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_cluster)
        
        # Calcular linkage
        Z = linkage(X_scaled, method=method)
        
        return {
            'linkage_matrix': Z.tolist(),
            'n_samples': len(df_cluster),
            'method': method,
            'features_used': available_cols
        }


class MorbilidadProcessor:
    """Procesador de datos de Morbilidad Materna Extrema (Evento 549)."""
    
    # Diccionario de datos
    MOMENTO_OCURRENCIA = {
        1: 'Durante el embarazo',
        2: 'Durante el parto',
        3: 'Puerperio inmediato (0-7 días)',
        4: 'Puerperio tardío (8-42 días)',
    }
    
    CRITERIOS_INCLUSION = {
        'Eclampsia': 'Eclampsia',
        'Sepsis sistémica severa': 'Sepsis',
        'Hemorragia obstétrica severa': 'Hemorragia',
        'Preeclampsia': 'Preeclampsia severa',
        'Ruptura uterina': 'Ruptura uterina',
    }
    
    def __init__(self, df):
        self.df = df.copy()
        self._limpiar_datos()
    
    def _limpiar_datos(self):
        """Limpia y normaliza los datos."""
        numeric_cols = [
            'N° gestaciones', 'Partos vaginales', 'Cesáreas', 'Abortos',
            'N° controles prenatales', 'Edad gestacional ocurrencia (sem)',
            'Total criterios', 'Días estancia hospitalaria', 'Días estancia UCI'
        ]
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        self.df = self.df.dropna(how='all')
    
    def calcular_estadisticas_basicas(self):
        """Calcula estadísticas descriptivas básicas."""
        stats = {
            'total_casos': len(self.df),
            'edad_promedio': None,
            'estancia_hospitalaria_promedio': None,
            'estancia_uci_promedio': None,
            'criterios_promedio': None,
        }
        
        if 'Edad' in self.df.columns:
            edades = self.df['Edad'].dropna()
            if not edades.empty:
                stats['edad_promedio'] = float(edades.mean())

        if 'Días estancia hospitalaria' in self.df.columns:
            stats['estancia_hospitalaria_promedio'] = float(
                self.df['Días estancia hospitalaria'].mean()
            )
        
        if 'Días estancia UCI' in self.df.columns:
            stats['estancia_uci_promedio'] = float(
                self.df['Días estancia UCI'].mean()
            )
        
        if 'Total criterios' in self.df.columns:
            stats['criterios_promedio'] = float(
                self.df['Total criterios'].mean()
            )
        
        return stats
    
    def analizar_criterios_inclusion(self):
        """Analiza los criterios de inclusión de morbilidad."""
        resultado = {}
        
        for col, nombre in self.CRITERIOS_INCLUSION.items():
            if col in self.df.columns:
                total = self.df[col].notna().sum()
                casos = self.df[col].apply(es_valor_positivo).sum()
                resultado[col] = {
                    'nombre': nombre,
                    'casos': int(casos),
                    'porcentaje': float(casos / total * 100) if total > 0 else 0
                }
        
        return resultado
    
    def analizar_momento_ocurrencia(self):
        """Analiza el momento de ocurrencia de la morbilidad."""
        if 'Momento ocurrencia' not in self.df.columns:
            return {}

        distribucion = self.df['Momento ocurrencia'].value_counts().to_dict()

        return {
            'distribucion': {
                self.MOMENTO_OCURRENCIA.get(k, f'Código {k}'): int(v)
                for k, v in distribucion.items()
            }
        }

    _INST_REF_COLS = [
        'Institución referencia 1', 'Institucion referencia 1',
        'Institución de referencia 1', 'Institucion de referencia 1',
    ]
    _TIEMPO_REM_COLS = [
        'Tiempo remisión (h)', 'Tiempo remision (h)',
        'Tiempo remisión horas', 'Tiempo remision horas',
    ]

    def _find_col(self, candidates):
        for c in candidates:
            if c in self.df.columns:
                return c
        return None

    def analizar_institucion_referencia(self):
        """Distribución de casos por institución de referencia (Evento 549)."""
        col = self._find_col(self._INST_REF_COLS)
        if col is None:
            return {}
        serie = self.df[col].dropna().astype(str).str.strip()
        serie = serie[~serie.str.lower().isin({'', 'nan', 'none', 'null', 'sin dato'})]
        if len(serie) == 0:
            return {}
        top = serie.value_counts().head(15)
        return {
            'instituciones': top.index.tolist(),
            'conteos': [int(v) for v in top.values],
            'total_con_dato': int(len(serie)),
            'total_casos': int(len(self.df)),
        }

    def analizar_tiempo_remision(self):
        """Datos para boxplot de tiempo de remisión en horas."""
        col = self._find_col(self._TIEMPO_REM_COLS)
        if col is None:
            return {}
        serie = pd.to_numeric(self.df[col], errors='coerce').dropna()
        serie = serie[serie >= 0]
        if len(serie) < 3:
            return {}
        q1 = float(serie.quantile(0.25))
        q3 = float(serie.quantile(0.75))
        return {
            'valores': serie.clip(upper=serie.quantile(0.99)).head(500).tolist(),
            'min': float(serie.min()),
            'q1': q1,
            'median': float(serie.median()),
            'mean': float(serie.mean()),
            'q3': q3,
            'max': float(serie.max()),
            'total': int(len(serie)),
        }

    def analizar_obstetrico_por_edad(self):
        """Histograma de variables obstétricas comparadas por grupo de edad."""
        variables = [
            ('N° gestaciones', 'Gestaciones'),
            ('Partos vaginales', 'Partos vaginales'),
            ('Cesáreas', 'Cesáreas'),
            ('Abortos', 'Abortos'),
        ]
        grupos_edad = [
            {'label': '<20', 'min': 0, 'max': 19},
            {'label': '20-29', 'min': 20, 'max': 29},
            {'label': '30-39', 'min': 30, 'max': 39},
            {'label': '≥40', 'min': 40, 'max': 120},
        ]
        tiene_edad = 'Edad' in self.df.columns
        resultado = {}

        for col, nombre in variables:
            if col not in self.df.columns:
                continue
            serie = pd.to_numeric(self.df[col], errors='coerce').dropna()
            if len(serie) < 2:
                continue
            max_val = min(int(serie.max()), 10)
            valores_eje = list(range(0, max_val + 1))
            conteos_total = [int((serie == v).sum()) for v in valores_eje]

            por_edad = {}
            if tiene_edad:
                edades = pd.to_numeric(self.df['Edad'], errors='coerce')
                for grupo in grupos_edad:
                    mask = (edades >= grupo['min']) & (edades <= grupo['max'])
                    subgrupo = pd.to_numeric(self.df.loc[mask, col], errors='coerce').dropna()
                    if len(subgrupo) > 0:
                        por_edad[grupo['label']] = [int((subgrupo == v).sum()) for v in valores_eje]

            resultado[col] = {
                'nombre': nombre,
                'valores_eje': valores_eje,
                'conteos_total': conteos_total,
                'por_edad': por_edad,
                'promedio': float(serie.mean()),
                'total': int(len(serie)),
            }
        return resultado

    def clustering_perfiles_morbilidad(self, n_clusters=3):
        """
        Clustering de perfiles de morbilidad materna.
        
        Args:
            n_clusters: Número de clusters
            
        Returns:
            dict con resultados del clustering
        """
        features_cols = [
            'N° gestaciones', 'Partos vaginales', 'Cesáreas',
            'N° controles prenatales', 'Edad gestacional ocurrencia (sem)',
            'Total criterios', 'Días estancia hospitalaria'
        ]
        
        available_cols = [col for col in features_cols if col in self.df.columns]
        
        if len(available_cols) < 2:
            return {'error': 'Datos insuficientes para clustering'}
        
        df_cluster = self.df[available_cols].dropna()
        
        if len(df_cluster) < n_clusters:
            return {'error': f'Se necesitan al menos {n_clusters} registros completos'}
        
        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_cluster)
        
        # K-means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        # PCA para visualización
        pca_2d = PCA(n_components=2)
        X_pca_2d = pca_2d.fit_transform(X_scaled)
        
        pca_3d = PCA(n_components=3)
        X_pca_3d = pca_3d.fit_transform(X_scaled)
        
        resultado = {
            'n_clusters': n_clusters,
            'n_samples': len(df_cluster),
            'features_used': available_cols,
            'clusters': clusters.tolist(),
            'pca_2d': {
                'x': X_pca_2d[:, 0].tolist(),
                'y': X_pca_2d[:, 1].tolist(),
                'variance_explained': float(pca_2d.explained_variance_ratio_.sum())
            },
            'pca_3d': {
                'x': X_pca_3d[:, 0].tolist(),
                'y': X_pca_3d[:, 1].tolist(),
                'z': X_pca_3d[:, 2].tolist(),
                'variance_explained': float(pca_3d.explained_variance_ratio_.sum())
            },
            'cluster_sizes': [int((clusters == i).sum()) for i in range(n_clusters)]
        }
        
        # Perfiles por cluster
        df_cluster['cluster'] = clusters
        cluster_profiles = []
        
        for i in range(n_clusters):
            cluster_data = df_cluster[df_cluster['cluster'] == i][available_cols]
            profile = {
                'cluster_id': i,
                'size': int((clusters == i).sum()),
                'features': {
                    col: float(cluster_data[col].mean())
                    for col in available_cols
                }
            }
            cluster_profiles.append(profile)
        
        resultado['cluster_profiles'] = cluster_profiles
        
        return resultado
    
    def heatmap_correlacion(self):
        """Genera matriz de correlación para heatmap."""
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return {'error': 'Datos numéricos insuficientes'}
        
        # Limitar a columnas relevantes
        relevant_cols = [
            col for col in numeric_cols
            if any(keyword in col for keyword in [
                'gestaciones', 'Partos', 'Cesáreas', 'controles',
                'gestacional', 'estancia', 'criterios'
            ])
        ]
        
        if not relevant_cols:
            relevant_cols = numeric_cols[:10]  # Tomar las primeras 10
        
        corr_matrix = self.df[relevant_cols].corr()
        
        return {
            'columns': relevant_cols,
            'correlation_matrix': corr_matrix.values.tolist(),
            'values': corr_matrix.values.tolist()
        }


def procesar_archivo_analisis(archivo_path, tipo):
    """
    Función principal para procesar un archivo y generar análisis completo.
    
    Args:
        archivo_path: Ruta al archivo Excel
        tipo: 'mortalidad' o 'morbilidad'
        
    Returns:
        dict con todos los análisis
    """
    try:
        df = pd.read_excel(archivo_path, engine='openpyxl')
        df, limpieza = preparar_dataframe_analisis(df)
        
        if tipo == 'mortalidad':
            processor = MortalidadProcessor(df)
            return {
                'limpieza_datos': limpieza,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'momento_muerte': processor.analizar_momento_muerte(),
                'demoras': processor.analizar_demoras(),
                'causas_cie10': processor.analizar_causas_cie10(),
                'clustering_factores': processor.clustering_factores_riesgo(n_clusters=3),
            }
        
        elif tipo == 'morbilidad':
            processor = MorbilidadProcessor(df)
            return {
                'limpieza_datos': limpieza,
                'estadisticas_basicas': processor.calcular_estadisticas_basicas(),
                'criterios_inclusion': processor.analizar_criterios_inclusion(),
                'momento_ocurrencia': processor.analizar_momento_ocurrencia(),
                'clustering_perfiles': processor.clustering_perfiles_morbilidad(n_clusters=3),
                'heatmap_correlacion': processor.heatmap_correlacion(),
            }
        
        else:
            return {'error': 'Tipo de análisis no válido'}
            
    except Exception as e:
        return {'error': str(e)}
