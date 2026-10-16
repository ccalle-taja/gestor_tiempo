import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página web
st.set_page_config(
    page_title="Mi Gestor de Tiempo",
    page_icon="⏱️",
    layout="wide"
)

# Inicializar memoria temporal en Streamlit
if "registros" not in st.session_state:
    st.session_state.registros = []

if "actividad_en_curso" not in st.session_state:
    st.session_state.actividad_en_curso = None

if "proyectos" not in st.session_state:
    st.session_state.proyectos = [
        {"nombre": "Construir App Web de Gestión de Tiempo", "estado": "En Progreso", "foco": "Estudio / Trabajo"},
        {"nombre": "Rutina Diaria de Ejercicio (Kaizen)", "estado": "En Progreso", "foco": "Personal / Salud"}
    ]

# Título principal
st.title("⏱️ Registro y Gestión del Tiempo")

# Barra lateral para el menú
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una sección:",
    ["⏱️ Cronómetro", "📊 Dashboard y Análisis", "🎯 Proyectos (Máx 3)"]
)

# ----------------------------------------------------
# SECCIÓN 1: CRONÓMETRO DE ACTIVIDADES
# ----------------------------------------------------
if opcion == "⏱️ Cronómetro":
    st.header("⏱️ Cronómetro de Actividades")
    
    st.subheader("1. Configura tu actividad")
    col1, col2 = st.columns(2)
    
    with col1:
        nombre_tarea = st.text_input(
            "Nombre de la tarea o actividad:",
            placeholder="Ej: Redactar informe, Leer, Ejercicio..."
        )
        categoria = st.selectbox(
            "Categoría (5 Áreas Clave):",
            [
                "A - Vida Personal (Hobbies, descanso, relax)",
                "B - Familia Directa y Pareja",
                "C - Vida Social (Amigos, reuniones)",
                "D - Trabajo y Tareas Domésticas",
                "E - Estudio y Formación"
            ]
        )
    
    with col2:
        tipo_valor = st.selectbox(
            "Clasificación de Valor (Regla 80/20):",
            [
                "Alto Valor (20% bisagra)",
                "Bajo Valor / Rutina",
                "🚨 Fuga de Tiempo / Distracción"
            ]
        )
    
    st.markdown("---")
    st.subheader("2. Control de Tiempo")
    
    # Si no hay actividad en curso
    if st.session_state.actividad_en_curso is None:
        if st.button("▶️ Iniciar Actividad", type="primary"):
            if nombre_tarea.strip() == "":
                st.warning("Por favor, escribe un nombre para la tarea antes de iniciar.")
            else:
                st.session_state.actividad_en_curso = {
                    "tarea": nombre_tarea,
                    "categoria": categoria,
                    "categoria_nombre": categoria,
                    "tipo_valor": tipo_valor,
                    "hora_inicio": datetime.now()
                }
                st.rerun()
    else:
        # Si hay una actividad corriendo
        act = st.session_state.actividad_en_curso
        inicio_str = act["hora_inicio"].strftime("%H:%M:%S")
        
        st.success(f"🟢 **En curso:** {act['tarea']} | **Categoría:** {act['categoria_nombre']} | **Inicio:** {inicio_str}")
        
        col_stop, col_cancel = st.columns(2)
        
        with col_stop:
            if st.button("⏹️ Detener y Guardar Registro"):
                hora_fin = datetime.now()
                duracion_segundos = (hora_fin - act["hora_inicio"]).total_seconds()
                duracion_minutos = round(duracion_segundos / 60, 2)
                duracion_horas = round(duracion_minutos / 60, 2)
                
                nuevo_registro = {
                    "Fecha": act["hora_inicio"].strftime("%Y-%m-%d"),
                    "Tarea": act["tarea"],
                    "Código": act["categoria"],
                    "Categoría": act["categoria_nombre"],
                    "Valor": act["tipo_valor"],
                    "Inicio": act["hora_inicio"].strftime("%H:%M:%S"),
                    "Fin": hora_fin.strftime("%H:%M:%S"),
                    "Minutos": duracion_minutos,
                    "Horas": duracion_horas
                }
                
                st.session_state.registros.append(nuevo_registro)
                st.session_state.actividad_en_curso = None
                st.toast("✅ ¡Registro guardado con éxito!")
                st.rerun()
                
        with col_cancel:
            if st.button("❌ Cancelar sin Guardar"):
                st.session_state.actividad_en_curso = None
                st.rerun()

    # Tabla de registros guardados hoy
    st.markdown("---")
    st.subheader("📋 Registros de Hoy")
    
    if len(st.session_state.registros) > 0:
        df_registros = pd.DataFrame(st.session_state.registros)
        st.dataframe(df_registros, use_container_width=True)
        
        total_minutos = df_registros["Minutos"].sum()
        total_horas = round(total_minutos / 60, 2)
        st.metric("Total Acumulado Hoy", f"{total_horas} horas ({round(total_minutos, 1)} min)")
    else:
        st.info("Aún no has registrado ninguna actividad. ¡Inicia una arriba!")

# ----------------------------------------------------
# SECCIÓN 2: DASHBOARD Y ANÁLISIS
# ----------------------------------------------------
elif opcion == "📊 Dashboard y Análisis":
    st.header("📊 Cuadro de Mandos y Diagnóstico de Tiempo")
    
    if len(st.session_state.registros) == 0:
        st.warning("⚠️ Todavía no hay actividades registradas. Ve a la pestaña '⏱️ Cronómetro' y guarda al menos una tarea para ver tu análisis.")
    else:
        df = pd.DataFrame(st.session_state.registros)
        total_minutos_totales = df["Minutos"].sum()
        total_horas_totales = round(total_minutos_totales / 60, 2)
        
        # 1. Métricas Clave Superiores
        col_m1, col_m2, col_m3 = st.columns(3)
        
        minutos_alto_valor = df[df["Valor"] == "Alto Valor (20% bisagra)"]["Minutos"].sum()
        pct_alto_valor = round((minutos_alto_valor / total_minutos_totales) * 100, 1) if total_minutos_totales > 0 else 0
        
        minutos_fugas = df[df["Valor"] == "🚨 Fuga de Tiempo / Distracción"]["Minutos"].sum()
        horas_fugas = round(minutos_fugas / 60, 2)
        
        with col_m1:
            st.metric("⏱️ Tiempo Total Registrado", f"{total_horas_totales} h")
        with col_m2:
            st.metric("🎯 % Tiempo de Alto Valor (80/20)", f"{pct_alto_valor} %")
        with col_m3:
            st.metric("🚨 Tiempo en Fugas / Distracciones", f"{horas_fugas} h ({round(minutos_fugas, 1)} min)")
        
        st.markdown("---")
        
        # 2. Análisis por 5 Áreas Clave vs Ideal
        st.subheader("1. Distribución de Tiempo por Categorías (5 Áreas)")
        
        resumen_cat = df.groupby("Código")["Minutos"].sum().reset_index()
        
        categorias_base = pd.DataFrame({
            "Código": ["A", "B", "C", "D", "E"],
            "Nombre Categoría": [
                "A - Vida Personal",
                "B - Familia y Pareja",
                "C - Vida Social",
                "D - Trabajo y Hogar",
                "E - Estudio y Formación"
            ],
            "% Ideal": [20.0, 15.0, 10.0, 35.0, 20.0]
        })
        
        df_analisis = pd.merge(categorias_base, resumen_cat, on="Código", how="left").fillna(0)
        df_analisis["Horas Reales"] = round(df_analisis["Minutos"] / 60, 2)
        df_analisis["% Real"] = round((df_analisis["Minutos"] / total_minutos_totales) * 100, 1) if total_minutos_totales > 0 else 0
        df_analisis["Diferencia (% Real - Ideal)"] = round(df_analisis["% Real"] - df_analisis["% Ideal"], 1)
        
        col_graf, col_tabla = st.columns(2)
        
        with col_graf:
            st.write("**Comparativa: % Real vs % Ideal**")
            chart_data = df_analisis.set_index("Código")[["% Real", "% Ideal"]]
            st.bar_chart(chart_data)
            
        with col_tabla:
            st.write("**Tabla Detallada por Categorías**")
            st.dataframe(
                df_analisis[["Nombre Categoría", "Horas Reales", "% Real", "% Ideal", "Diferencia (% Real - Ideal)"]],
                use_container_width=True
            )
        
        st.markdown("---")
        
        # 3. Diagnóstico de Valor (Regla 80/20)
        st.subheader("2. Desglose por Calidad de Tiempo (80/20)")
        resumen_valor = df.groupby("Valor")["Minutos"].sum().reset_index()
        resumen_valor["Horas"] = round(resumen_valor["Minutos"] / 60, 2)
        resumen_valor["% del Total"] = round((resumen_valor["Minutos"] / total_minutos_totales) * 100, 1)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.dataframe(resumen_valor[["Valor", "Horas", "% del Total"]], use_container_width=True)
        with col_v2:
            if minutos_fugas > 0:
                st.error(f"⚠️ **Alerta de Fuga:** Has acumulado {horas_fugas} horas en actividades clasificadas como distracción. Revisa estas tareas para definir estrategias de eliminación.")
            else:
                st.success("🎉 ¡Excelente! No has registrado fugas de tiempo ni distracciones en tus sesiones.")

# ----------------------------------------------------
# SECCIÓN 3: PROYECTOS FINITOS
# ----------------------------------------------------
elif opcion == "🎯 Proyectos (Máx 3)":
    st.header("🎯 Gestión de Proyectos Activos (Límite Finito)")
    st.write("Según *Cuatro mil semanas* (Oliver Burkeman), para lograr progresos reales debemos **cerrar nuestra lista de compromisos y limitar el trabajo activo a un máximo de 3 proyectos simultáneos**.")
    
    proyectos_activos = [p for p in st.session_state.proyectos if p["estado"] == "En Progreso"]
    num_activos = len(proyectos_activos)
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.metric("Proyectos Activos Actuales", f"{num_activos} / 3", delta="Límite Finito Alcanzado" if num_activos >= 3 else f"Quedan {3 - num_activos} huecos")
    with col_p2:
        if num_activos >= 3:
            st.error("🚨 **Lista Cerrada (Capacidad Llena):** Para activar un proyecto nuevo, primero debes completar o pausar uno de los actuales.")
        else:
            st.success(f"🟢 Tienes margen para trabajar de forma enfocada en {3 - num_activos} proyecto(s) más.")
            
    st.markdown("---")
    st.subheader("1. Añadir Nuevo Proyecto")
    
    with st.form("form_nuevo_proyecto"):
        nuevo_nombre = st.text_input("Nombre del proyecto:")
        nuevo_foco = st.selectbox("Área / Enfoque:", ["Trabajo", "Estudio / Formación", "Personal / Salud", "Familia / Hogar"])
        estado_deseado = st.selectbox("Estado inicial:", ["En Progreso (Lista Cerrada)", "En Espera / Backlog (Lista Abierta)"])
        btn_guardar_proj = st.form_submit_button("➕ Guardar Proyecto")
        
        if btn_guardar_proj:
            if nuevo_nombre.strip() == "":
                st.warning("Escribe un nombre para el proyecto.")
            else:
                quiere_activo = "En Progreso" in estado_deseado
                if quiere_activo and num_activos >= 3:
                    st.error("❌ No puedes crearlo 'En Progreso'. Ya tienes 3 proyectos activos. Se guardará en 'En Espera'.")
                    st.session_state.proyectos.append({"nombre": nuevo_nombre, "estado": "En Espera", "foco": nuevo_foco})
                    st.rerun()
                else:
                    estado_final = "En Progreso" if quiere_activo else "En Espera"
                    st.session_state.proyectos.append({"nombre": nuevo_nombre, "estado": estado_final, "foco": nuevo_foco})
                    st.toast(f"✅ Proyecto '{nuevo_nombre}' creado en {estado_final}")
                    st.rerun()

    st.markdown("---")
    st.subheader("2. Proyectos Activos en Ejecución (Máximo 3)")
    
    if num_activos == 0:
        st.info("No tienes ningún proyecto activo. Activa alguno de tu lista en espera abajo.")
    else:
        for idx, p in enumerate(st.session_state.proyectos):
            if p["estado"] == "En Progreso":
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"🔥 **{p['nombre']}** `[{p['foco']}]`")
                with c2:
                    if st.button("✅ Completar", key=f"comp_{idx}"):
                        st.session_state.proyectos[idx]["estado"] = "Completado"
                        st.rerun()
                with c3:
                    if st.button("⏸️ Pausar", key=f"pause_{idx}"):
                        st.session_state.proyectos[idx]["estado"] = "En Espera"
                        st.rerun()

    st.markdown("---")
    st.subheader("3. Lista Abierta (En Espera / Ideas Pendientes)")
    
    proyectos_espera = [(i, p) for i, p in enumerate(st.session_state.proyectos) if p["estado"] == "En Espera"]
    if len(proyectos_espera) == 0:
        st.caption("No tienes proyectos pendientes en la lista de espera.")
    else:
        for idx, p in proyectos_espera:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"💤 **{p['nombre']}** `[{p['foco']}]`")
            with c2:
                if st.button("▶️ Activar", key=f"act_{idx}"):
                    if num_activos >= 3:
                        st.error("❌ Capacidad llena (3/3). Completa o pausa uno activo primero.")
                    else:
                        st.session_state.proyectos[idx]["estado"] = "En Progreso"
                        st.rerun()

    st.markdown("---")
    st.subheader("4. Histórico de Proyectos Completados")
    completados = [p for p in st.session_state.proyectos if p["estado"] == "Completado"]
    if len(completados) == 0:
        st.caption("Aún no has completado proyectos.")
    else:
        for p in completados:
            st.write(f"🎉 **{p['nombre']}** `[{p['foco']}]`")
