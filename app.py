import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
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
    url = str(st.secrets["SUPABASE_URL"]).strip().strip("()\"'")
    if "/rest/v1" in url:
        url = url.split("/rest/v1")
    url = url.rstrip("/")
    
    key = str(st.secrets["SUPABASE_KEY"]).strip().strip("()\"'")
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
                    st.error(f"Error al iniciar sesión: {e}")

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
                    
    st.stop()

# ----------------------------------------------------
# APLICACIÓN PRINCIPAL (USUARIO AUTENTICADO)
# ----------------------------------------------------
user_obj = st.session_state.user
user_id = getattr(user_obj, "id")
user_email = getattr(user_obj, "email")

# ----------------------------------------------------
# CONFIGURACIÓN DE HORA LOCAL
# ----------------------------------------------------
st.sidebar.title("Menú Principal")
st.sidebar.write(f"👤 **Usuario:** {user_email}")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Configuración de Hora")
offset_horas = st.sidebar.number_input(
    "Ajuste de hora local (UTC +/- horas):",
    value=2,
    step=1,
    help="Si el servidor está 2 horas retrasado respecto a tu hora local, déjalo en +2."
)

def obtener_hora_local():
    now_utc = datetime.now(timezone.utc)
    return now_utc + timedelta(hours=offset_horas)

hora_actual_str = obtener_hora_local().strftime("%H:%M:%S")
st.sidebar.markdown(f"🕒 **Hora local actual:** {hora_actual_str}")

if st.sidebar.button("Cerrar Sesión"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

st.sidebar.markdown("---")
opcion = st.sidebar.radio(
    "Selecciona una sección:",
    ["⏱️ Cronómetro y Registros", "📊 Dashboard y Análisis", "🎯 Proyectos (Máx 3)"]
)

st.title("⏱️ Registro y Gestión del Tiempo")

CATEGORIAS_LISTA = [
    "A - Vida Personal (Hobbies, descanso, relax)",
    "B - Familia Directa y Pareja",
    "C - Vida Social (Amigos, reuniones)",
    "D - Trabajo y Tareas Domésticas",
    "E - Estudio y Formación"
]

VALORES_LISTA = [
    "Alto Valor (20% bisagra)",
    "Bajo Valor / Rutina",
    "🚨 Fuga de Tiempo / Distracción"
]

if "actividad_en_curso" not in st.session_state:
    st.session_state.actividad_en_curso = None

# ----------------------------------------------------
# SECCIÓN 1: CRONÓMETRO Y REGISTROS
# ----------------------------------------------------
if opcion == "⏱️ Cronómetro y Registros":
    st.header("⏱️ Control de Actividades")
    
    sub_tab_vivo, sub_tab_manual = st.tabs(["▶️ Cronómetro en Vivo", "✍️ Entrada Manual"])
    
    # 1. CRONÓMETRO EN VIVO
    with sub_tab_vivo:
        st.subheader("1. Configura tu actividad")
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_tarea = st.text_input(
                "Nombre de la tarea o actividad:",
                placeholder="Ej: Redactar informe, Leer, Ejercicio..."
            )
            categoria = st.selectbox("Categoría (5 Áreas Clave):", CATEGORIAS_LISTA, key="cat_vivo")
        
        with col2:
            tipo_valor = st.selectbox("Clasificación de Valor (Regla 80/20):", VALORES_LISTA, key="val_vivo")
        
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
                        "hora_inicio": obtener_hora_local()
                    }
                    st.rerun()
        else:
            act = st.session_state.actividad_en_curso
            inicio_str = act["hora_inicio"].strftime("%H:%M:%S")
            st.success(f"🟢 **En curso:** {act['tarea']} | **Inicio:** {inicio_str}")
            
            col_stop, col_cancel = st.columns(2)
            with col_stop:
                if st.button("⏹️ Detener y Guardar Registro"):
                    hora_fin = obtener_hora_local()
                    duracion_segundos = (hora_fin - act["hora_inicio"]).total_seconds()
                    duracion_minutos = round(duracion_segundos / 60, 2)
                    duracion_horas = round(duracion_minutos / 60, 2)
                    
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

    # 2. REGISTRO MANUAL DE ACTIVIDADES
    with sub_tab_manual:
        st.subheader("✍️ Añadir Actividad Pasada o Manual")
        with st.form("form_manual"):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                fecha_manual = st.date_input("Fecha de la actividad:", value=obtener_hora_local().date())
                tarea_manual = st.text_input("Nombre de la tarea:", placeholder="Ej: Lectura matutina")
                cat_manual = st.selectbox("Categoría:", CATEGORIAS_LISTA, key="cat_man")
            with col_m2:
                val_manual = st.selectbox("Clasificación de Valor:", VALORES_LISTA, key="val_man")
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    hora_inicio_manual = st.time_input("Hora de inicio:", value=datetime.strptime("09:00", "%H:%M").time())
                with col_h2:
                    hora_fin_manual = st.time_input("Hora de fin:", value=datetime.strptime("10:00", "%H:%M").time())
            
            btn_guardar_manual = st.form_submit_button("💾 Guardar Registro Manual", type="primary")
            
            if btn_guardar_manual:
                if tarea_manual.strip() == "":
                    st.warning("Escribe el nombre de la tarea.")
                else:
                    dt_inicio = datetime.combine(fecha_manual, hora_inicio_manual)
                    dt_fin = datetime.combine(fecha_manual, hora_fin_manual)
                    if dt_fin < dt_inicio:
                        dt_fin += timedelta(days=1)
                    
                    dur_seg = (dt_fin - dt_inicio).total_seconds()
                    dur_min = round(dur_seg / 60, 2)
                    dur_hrs = round(dur_min / 60, 2)
                    
                    reg_manual_data = {
                        "user_id": user_id,
                        "fecha": fecha_manual.strftime("%Y-%m-%d"),
                        "tarea": tarea_manual,
                        "codigo": cat_manual,
                        "categoria": cat_manual,
                        "valor": val_manual,
                        "inicio": hora_inicio_manual.strftime("%H:%M:%S"),
                        "fin": hora_fin_manual.strftime("%H:%M:%S"),
                        "minutos": dur_min,
                        "horas": dur_hrs
                    }
                    supabase.table("registros").insert(reg_manual_data).execute()
                    st.toast("✅ Registro manual añadido con éxito")
                    st.rerun()

    # 3. MOSTRAR, MODIFICAR Y ELIMINAR REGISTROS
    st.markdown("---")
    st.subheader("📋 Tus Registros Guardados")
    res_regs = supabase.table("registros").select("*").eq("user_id", user_id).order("id", desc=True).execute()
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
        
        # MÓDULO DE EDICIÓN Y BORRADO DE REGISTROS
        with st.expander("✏️ Modificar o Eliminar un Registro Existente"):
            opciones_reg = {f"ID #{r['id']} | {r['fecha']} | {r['tarea']} ({r['inicio']} - {r['fin']})": r for r in datos_regs}
            seleccion_str = st.selectbox("Selecciona el registro a modificar:", list(opciones_reg.keys()))
            
            if seleccion_str:
                reg_sel = opciones_reg[seleccion_str]
                
                with st.form(f"form_edit_reg_{reg_sel['id']}"):
                    st.write(f"**Modificando Registro ID #{reg_sel['id']}**")
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        edit_fecha = st.text_input("Fecha (AAAA-MM-DD):", value=str(reg_sel.get("fecha", "")))
                        edit_tarea = st.text_input("Tarea:", value=str(reg_sel.get("tarea", "")))
                        idx_cat = next((i for i, c in enumerate(CATEGORIAS_LISTA) if c.startswith(reg_sel.get("codigo", "A"))), 0)
                        edit_cat = st.selectbox("Categoría:", CATEGORIAS_LISTA, index=idx_cat)
                    
                    with col_e2:
                        idx_val = next((i for i, v in enumerate(VALORES_LISTA) if v == reg_sel.get("valor")), 0)
                        edit_val = st.selectbox("Valor:", VALORES_LISTA, index=idx_val)
                        edit_inicio = st.text_input("Hora Inicio (HH:MM:SS):", value=str(reg_sel.get("inicio", "09:00:00")))
                        edit_fin = st.text_input("Hora Fin (HH:MM:SS):", value=str(reg_sel.get("fin", "10:00:00")))
                        edit_minutos = st.number_input("Minutos de duración:", value=float(reg_sel.get("minutos", 0.0)), step=5.0)
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        btn_actualizar_reg = st.form_submit_button("💾 Guardar Cambios")
                    with col_b2:
                        btn_eliminar_reg = st.form_submit_button("🗑️ Eliminar Registro", type="secondary")
                    
                    if btn_actualizar_reg:
                        dur_h = round(edit_minutos / 60, 2)
                        update_payload = {
                            "fecha": edit_fecha,
                            "tarea": edit_tarea,
                            "codigo": edit_cat,
                            "categoria": edit_cat,
                            "valor": edit_val,
                            "inicio": edit_inicio,
                            "fin": edit_fin,
                            "minutos": edit_minutos,
                            "horas": dur_h
                        }
                        supabase.table("registros").update(update_payload).eq("id", reg_sel['id']).execute()
                        st.toast("✅ Registro actualizado correctamente")
                        st.rerun()
                        
                    if btn_eliminar_reg:
                        supabase.table("registros").delete().eq("id", reg_sel['id']).execute()
                        st.toast("🗑️ Registro eliminado")
                        st.rerun()
    else:
        st.info("Aún no tienes registros guardados en tu cuenta. ¡Inicia uno o agrégalo manualmente arriba!")

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
# SECCIÓN 3: PROYECTOS FINITOS CON FECHAS LÍMITE
# ----------------------------------------------------
elif opcion == "🎯 Proyectos (Máx 3)":
    st.header("🎯 Gestión de Proyectos Activos (Límite Finito y Fechas Límite)")
    
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
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nuevo_foco = st.selectbox("Área / Enfoque:", ["Trabajo", "Estudio / Formación", "Personal / Salud", "Familia / Hogar"])
            estado_deseado = st.selectbox("Estado inicial:", ["En Progreso (Lista Cerrada)", "En Espera / Backlog (Lista Abierta)"])
        with col_f2:
            fecha_limite_input = st.date_input("📅 Fecha Límite (Opcional):", value=obtener_hora_local().date() + timedelta(days=30))
        
        btn_guardar_proj = st.form_submit_button("➕ Guardar Proyecto", type="primary")
        
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
                
                payload_proyecto = {
                    "user_id": user_id,
                    "nombre": nuevo_nombre,
                    "foco": nuevo_foco,
                    "estado": estado_final,
                    "fecha_limite": fecha_limite_input.strftime("%Y-%m-%d")
                }
                
                try:
                    supabase.table("proyectos").insert(payload_proyecto).execute()
                except Exception:
                    payload_proyecto.pop("fecha_limite", None)
                    supabase.table("proyectos").insert(payload_proyecto).execute()
                    
                st.toast(f"✅ Proyecto guardado en {estado_final}")
                st.rerun()

    def formato_fecha_limite(fecha_str):
        if not fecha_str:
            return "Sin fecha límite"
        try:
            flim = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            hoy = obtener_hora_local().date()
            dias = (flim - hoy).days
            if dias < 0:
                return f"📅 {fecha_str} (🚨 Vencido hace {abs(dias)} días)"
            elif dias == 0:
                return f"📅 {fecha_str} (⚠️ Vence HOY)"
            else:
                return f"📅 {fecha_str} (⏳ Quedan {dias} días)"
        except Exception:
            return f"📅 {fecha_str}"

    st.markdown("---")
    st.subheader("2. Proyectos Activos en Ejecución (Máximo 3)")
    if num_activos == 0:
        st.info("No tienes proyectos activos en tu cuenta.")
    else:
        for p in activos:
            c1, c2, c3 = st.columns(3)
            info_flim = formato_fecha_limite(p.get("fecha_limite"))
            with c1:
                st.markdown(f"🔥 **{p['nombre']}** `[{p['foco']}]` — {info_flim}")
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
            info_flim = formato_fecha_limite(p.get("fecha_limite"))
            with c1:
                st.markdown(f"💤 **{p['nombre']}** `[{p['foco']}]` — {info_flim}")
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
            st.write(f"🎉 **{p['nombre']}** `[{p['foco']}]` — Fecha límite: {p.get('fecha_limite', 'Sin fecha')}")
