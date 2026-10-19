import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Configuración de la página web
st.set_page_config(
    page_title="Mi Gestor de Tiempo",
    page_icon="⏱️",
    layout="wide"
)

# ----------------------------------------------------
# CONEXIÓN CON SUPABASE
# ----------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Manejo de la sesión de usuario
if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------------------------------------
# PANTALLA DE AUTENTICACIÓN (LOGIN / REGISTRO)
# ----------------------------------------------------
if st.session_state.user is None:
    st.title("⏱️ Gestor de Tiempo y Productividad")
    st.write("Inicia sesión o crea tu cuenta para guardar y sincronizar tu tiempo en cualquier dispositivo.")
    
    tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta"])
    
    with tab_login:
        with st.form("form_login"):
            email_login = st.text_input("Correo electrónico:")
            pass_login = st.text_input("Contraseña:", type="password")
            btn_login = st.form_submit_button("Entrar", type="primary")
            
            if btn_login:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                    st.session_state.user = res.user
                    st.success("¡Bienvenido!")
                    st.rerun()
                except Exception as e:
                    st.error("Error al iniciar sesión. Revisa tu correo y contraseña.")

    with tab_registro:
        with st.form("form_registro"):
            email_reg = st.text_input("Correo electrónico:")
            pass_reg = st.text_input("Crea una contraseña (mínimo 6 caracteres):", type="password")
            btn_reg = st.form_submit_button("Crear mi cuenta")
            
            if btn_reg:
                try:
                    res = supabase.auth.sign_up({"email": email_reg, "password": pass_reg})
                    st.success("✅ Cuenta creada con éxito. Ya puedes iniciar sesión.")
                except Exception as e:
                    st.error(f"Error al registrarse: {e}")
                    
    st.stop()  # Detiene la ejecución aquí hasta que el usuario se autentique

# ----------------------------------------------------
# APLICACIÓN PRINCIPAL (USUARIO AUTENTICADO)
# ----------------------------------------------------
user_obj = st.session_state.user
user_id = getattr(user_obj, "id")
user_email = getattr(user_obj, "email")

# Inicializar estado temporal si no existe
if "actividad_en_curso" not in st.session_state:
    st.session_state.actividad_en_curso = None

# Barra lateral
st.sidebar.title("Menú Principal")
st.sidebar.write(f"👤 **Usuario:** {user_email}")

if st.sidebar.button("Cerrar Sesión"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

opcion = st.sidebar.radio(
    "Selecciona una sección:",
    ["⏱️ Cronómetro", "📊 Dashboard y Análisis", "🎯 Proyectos (Máx 3)"]
)

st.title("⏱️ Registro y Gestión del Tiempo")

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
    
    if st.session_state.actividad_en_curso is None:
        if st.button("▶️ Iniciar Actividad", type="primary"):
            if nombre_tarea.strip() == "":
                st.warning("Por favor, escribe un nombre para la tarea.")
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
                
                # Guardar directamente en Supabase
                nuevo_reg = {
                    "user_id": user_id,
                    "fecha": act["hora_inicio"].strftime("%Y-%m-%d"),
                    "tarea": act["tarea"],
                    "codigo": act["categoria"],
                    "categoria": act["categoria_nombre"],
                    "valor": act["tipo_valor"],
                    "inicio": act["hora_inicio"].strftime("%H:%M:%S"),
                    "fin": hora_fin.strftime("%H:%M:%S"),
                    "minutos": duracion_minutos,
                    "horas": duracion_horas
                }
                
                supabase.table("registros").insert(nuevo_reg).execute()
                st.session_state.actividad_en_curso = None
                st.toast("✅ ¡Guardado en tu base de datos!")
                st.rerun()
                
        with col_cancel:
            if st.button("❌ Cancelar sin Guardar"):
                st.session_state.actividad_en_curso = None
                st.rerun()

    # Cargar registros desde Supabase
    st.markdown("---")
    st.subheader("📋 Tus Registros Guardados")
    res_regs = supabase.table("registros").select("*").eq("user_id", user_id).execute()
    datos_regs = getattr(res_regs, "data", [])
    
    if len(datos_regs) > 0:
        df_registros = pd.DataFrame(datos_regs)
        st.dataframe(
            df_registros[["fecha", "tarea", "codigo", "categoria", "valor", "inicio", "fin", "minutos", "horas"]],
            use_container_width=True
        )
        total_minutos = df_registros["minutos"].sum()
        total_horas = round(total_minutos / 60, 2)
        st.metric("Total Acumulado", f"{total_horas} horas ({round(total_minutos, 1)} min)")
    else:
        st.info("Aún no tienes registros guardados en tu cuenta. ¡Inicia uno arriba!")

# ----------------------------------------------------
# SECCIÓN 2: DASHBOARD Y ANÁLISIS
# ----------------------------------------------------
elif opcion == "📊 Dashboard y Análisis":
    st.header("📊 Cuadro de Mandos y Diagnóstico de Tiempo")
    
    res_regs = supabase.table("registros").select("*").eq("user_id", user_id).execute()
    datos_regs = getattr(res_regs, "data", [])
    
    if len(datos_regs) == 0:
        st.warning("⚠️ No hay actividades registradas en tu cuenta para mostrar el diagnóstico.")
    else:
        df = pd.DataFrame(datos_regs)
        total_minutos_totales = df["minutos"].sum()
        total_horas_totales = round(total_minutos_totales / 60, 2)
        
        col_m1, col_m2, col_m3 = st.columns(3)
        minutos_alto_valor = df[df["valor"] == "Alto Valor (20% bisagra)"]["minutos"].sum()
        pct_alto_valor = round((minutos_alto_valor / total_minutos_totales) * 100, 1) if total_minutos_totales > 0 else 0
        minutos_fugas = df[df["valor"] == "🚨 Fuga de Tiempo / Distracción"]["minutos"].sum()
        horas_fugas = round(minutos_fugas / 60, 2)
        
        with col_m1:
            st.metric("⏱️ Tiempo Total Registrado", f"{total_horas_totales} h")
        with col_m2:
            st.metric("🎯 % Tiempo de Alto Valor (80/20)", f"{pct_alto_valor} %")
        with col_m3:
            st.metric("🚨 Tiempo en Fugas / Distracciones", f"{horas_fugas} h ({round(minutos_fugas, 1)} min)")
        
        st.markdown("---")
        st.subheader("1. Distribución de Tiempo por Categorías (5 Áreas)")
        
        resumen_cat = df.groupby("codigo")["minutos"].sum().reset_index()
        categorias_base = pd.DataFrame({
            "codigo": ["A", "B", "C", "D", "E"],
            "Nombre Categoría": ["A - Vida Personal", "B - Familia y Pareja", "C - Vida Social", "D - Trabajo y Hogar", "E - Estudio y Formación"],
            "% Ideal": [20.0, 15.0, 10.0, 35.0, 20.0]
        })
        
        df_analisis = pd.merge(categorias_base, resumen_cat, on="codigo", how="left").fillna(0)
        df_analisis["Horas Reales"] = round(df_analisis["minutos"] / 60, 2)
        df_analisis["% Real"] = round((df_analisis["minutos"] / total_minutos_totales) * 100, 1) if total_minutos_totales > 0 else 0
        df_analisis["Diferencia (% Real - Ideal)"] = round(df_analisis["% Real"] - df_analisis["% Ideal"], 1)
        
        col_graf, col_tabla = st.columns(2)
        with col_graf:
            st.write("**Comparativa: % Real vs % Ideal**")
            chart_data = df_analisis.set_index("codigo")[["% Real", "% Ideal"]]
            st.bar_chart(chart_data)
            
        with col_tabla:
            st.write("**Tabla Detallada por Categorías**")
            st.dataframe(df_analisis[["Nombre Categoría", "Horas Reales", "% Real", "% Ideal", "Diferencia (% Real - Ideal)"]], use_container_width=True)

# ----------------------------------------------------
# SECCIÓN 3: PROYECTOS FINITOS (SUPABASE)
# ----------------------------------------------------
elif opcion == "🎯 Proyectos (Máx 3)":
    st.header("🎯 Gestión de Proyectos Activos (Límite Finito)")
    
    res_proj = supabase.table("proyectos").select("*").eq("user_id", user_id).execute()
    proyectos_usuario = getattr(res_proj, "data", [])
    
    activos = [p for p in proyectos_usuario if p["estado"] == "En Progreso"]
    num_activos = len(activos)
    
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
                    st.error("❌ Capacidad llena. Se guardará en 'En Espera'.")
                    estado_final = "En Espera"
                else:
                    estado_final = "En Progreso" if quiere_activo else "En Espera"
                
                supabase.table("proyectos").insert({
                    "user_id": user_id,
                    "nombre": nuevo_nombre,
                    "foco": nuevo_foco,
                    "estado": estado_final
                }).execute()
                st.toast(f"✅ Proyecto guardado en {estado_final}")
                st.rerun()

    st.markdown("---")
    st.subheader("2. Proyectos Activos en Ejecución (Máximo 3)")
    if num_activos == 0:
        st.info("No tienes proyectos activos en tu cuenta.")
    else:
        for p in activos:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"🔥 **{p['nombre']}** `[{p['foco']}]`")
            with c2:
                if st.button("✅ Completar", key=f"comp_{p['id']}"):
                    supabase.table("proyectos").update({"estado": "Completado"}).eq("id", p['id']).execute()
                    st.rerun()
            with c3:
                if st.button("⏸️ Pausar", key=f"pause_{p['id']}"):
                    supabase.table("proyectos").update({"estado": "En Espera"}).eq("id", p['id']).execute()
                    st.rerun()

    st.markdown("---")
    st.subheader("3. Lista Abierta (En Espera / Ideas Pendientes)")
    espera = [p for p in proyectos_usuario if p["estado"] == "En Espera"]
    if len(espera) == 0:
        st.caption("No tienes proyectos pendientes.")
    else:
        for p in espera:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"💤 **{p['nombre']}** `[{p['foco']}]`")
            with c2:
                if st.button("▶️ Activar", key=f"act_{p['id']}"):
                    if num_activos >= 3:
                        st.error("❌ Capacidad llena (3/3). Completa o pausa uno activo primero.")
                    else:
                        supabase.table("proyectos").update({"estado": "En Progreso"}).eq("id", p['id']).execute()
                        st.rerun()

    st.markdown("---")
    st.subheader("4. Histórico de Proyectos Completados")
    completados = [p for p in proyectos_usuario if p["estado"] == "Completado"]
    if len(completados) == 0:
        st.caption("Aún no has completado proyectos.")
    else:
        for p in completados:
            st.write(f"🎉 **{p['nombre']}** `[{p['foco']}]`")
