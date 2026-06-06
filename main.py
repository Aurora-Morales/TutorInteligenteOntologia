# Interfaz gráfica con Streamlite y navegación
import streamlit as st
import pandas as pd
from ontologia_manager import obtener_instancia_ontologia
from alumno_service import *

# Configuración estética de la app de Streamlit
st.set_page_config(
    page_title="Tutor Inteligente Semántico - UACM",
    page_icon="🎓",
    layout="wide"
)

st.title("🤖 Tutor Inteligente Basado en Ontologías (UACM)")
st.caption("Sistema de asesoramiento académico mediante razonamiento lógico y reglas SWRL")

# 1. Cargar e inicializar la Ontología
onto, mensaje = obtener_instancia_ontologia()

if onto is None:
    st.error(mensaje)
    st.stop()
else:
    st.sidebar.success("Ondología Conectada")

# 2. Buscador Global en Barra Lateral
st.sidebar.header("🔍 Selector de Alumno")
busqueda = st.sidebar.text_input("Ingresa Nombre o Matrícula:", placeholder="Ej. aurora o 20-003-1553")

alumno_activo = None
if busqueda:
    alumno_activo = buscar_alumno_por_filtro(onto, busqueda)
    if alumno_activo:
        st.sidebar.success(f"👤 Alumno: **{alumno_activo.name.upper()}**")
        if hasattr(alumno_activo, "promedio"):
            st.sidebar.metric("Promedio General", f"{alumno_activo.promedio}")
    else:
        st.sidebar.error("❌ Alumno no encontrado.")

# 3. Control del flujo de la interfaz principal
if not alumno_activo:
    st.info("👋 Bienvenido al Tutor Inteligente. Por favor, introduce la matrícula o el nombre de un alumno en la barra lateral para comenzar la tutoría.")
    st.write("💡 *Prueba escribiendo `aurora`, `alexa`, `mariana`, `roma` o `juan` para ver los perfiles precargados en tu archivo RDF.*")
else:
    # === NUEVA SECCIÓN: PANELES ADAPTATIVOS Y SEMÁFORO DE ALERTA ===
    col_diag, col_semaforo = st.columns(2)
    
    with col_diag:
        st.markdown("##### 👩‍🏫 Diagnóstico de Rendimiento")
        diagnostico = obtener_diagnostico_pedagogico(onto, alumno_activo)
        
        # Adaptar el contenedor visual de acuerdo al perfil
        if diagnostico["color"] == "success":
            st.success(f"**Perfil:** {diagnostico['nivel']}\n\n{diagnostico['consejo']}")
        elif diagnostico["color"] == "danger":
            st.error(f"**Perfil:** {diagnostico['nivel']}\n\n{diagnostico['consejo']}")
        else:
            st.info(f"**Perfil:** {diagnostico['nivel']}\n\n{diagnostico['consejo']}")
            
    with col_semaforo:
        st.markdown("##### 🚦 Semáforo de Alerta de Avance")
        # Invocar la nueva función estadística del servicio
        alerta = calcular_semaforo_rezago(onto, alumno_activo)
        
        # Crear una tarjeta estilizada para el semáforo usando markdown
        st.markdown(
            f"""
            <div style="background-color: #ffffff; padding: 16px; border-radius: 8px; border-left: 6px solid {alerta['color']}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h4 style="margin: 0; color: {alerta['color']};">{alerta['estado']}</h4>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #555555;">
                    <b>Avance Curricular:</b> {alerta['aprobadas']} de {alerta['totales']} materias aprobadas ({alerta['porcentaje']}%).
                </p>
                <p style="margin: 8px 0 0 0; font-size: 13px; font-style: italic; color: #333333;">
                    💡 {alerta['nota']}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.write("") # Espacio estético de separación
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Historial Académico", 
        "📋 Inscripción por Semestre (Reglas Lógicas)", 
        "🎯 Registro de Intereses",
        "📋 Mapa Curricular"
    ])

    # ---------------------------------------------------------
    # TAB 1: HISTORIAL ACADÉMICO
    # ---------------------------------------------------------
    with tab1:
        st.header(f"Historial Académico de {alumno_activo.name.replace('_', ' ').title()}")
        historial = obtener_historial_academico(alumno_activo)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Materias Aprobadas")
            if historial["aprobadas"]:
                df_aprobadas = pd.DataFrame(historial["aprobadas"], columns=["Nombre de la Materia"])
                st.dataframe(df_aprobadas, use_container_width=True)
            else:
                st.warning("El alumno no registra materias aprobadas en la ontología.")
                
        with col2:
            st.subheader("📝 Cursando Actuales / Inscritas")
            if historial["inscritas"]:
                df_inscritas = pd.DataFrame(historial["inscritas"], columns=["Nombre de la Materia"])
                st.dataframe(df_inscritas, use_container_width=True)
            else:
                st.info("No se encuentra inscrito en ninguna asignatura en este ciclo.")

    # ---------------------------------------------------------
    # TAB 2: MATERIAS DISPONIBLES SEGÚN EL SEMESTRE
    # ---------------------------------------------------------
    with tab2:
        st.header("🔮 Planificación de Inscripción Inteligente")
        st.write("Esta sección ejecuta las reglas de la ontología para evaluar prerrequisitos válidos.")
        
        # === NUEVA SECCIÓN: RECOMENDACIONES SWRL ===
        st.subheader("🎯 Recomendaciones del Tutor Inteligente (Reglas SWRL)")
        recomendaciones = obtener_materias_recomendadas(onto, alumno_activo)
        
        if recomendaciones:
            st.info("💡 **El Tutor ha calculado recomendaciones personalizadas para ti basándose en las reglas del sistema:**")
            df_recom = pd.DataFrame(recomendaciones)
            st.dataframe(df_recom, use_container_width=True, hide_index=True)
        else:
            st.markdown("*No se generaron recomendaciones especiales mediante SWRL para este perfil en el estado actual.*")
        
        st.divider() # Línea divisoria para separar de las materias comunes por semestre
        
        # === SECCIÓN ANTERIOR: MATERIAS POR SEMESTRE (PAR/IMPAR) ===
        st.subheader("📋 Asignaturas Recomendadas por Tipo de Periodo")
        tipo_semestre = st.selectbox(
            "Selecciona el ciclo al que se va a inscribir el alumno:",
            ["Impar", "Par"],
            help="Filtrará las asignaturas correspondientes a semestres Pares o Impares."
        )
        
        materias_permitidas = obtener_materias_disponibles(onto, alumno_activo, tipo_semestre)
        
        if materias_permitidas:
            datos_materias = []
            for mat in materias_permitidas:
                tipo_clase = "Materia"
                if onto.Obligatoria in mat.is_a:
                    tipo_clase = "Obligatoria"
                elif onto.Optativa in mat.is_a:
                    tipo_clase = "Optativa"
                    
                datos_materias.append({
                    "Clave / Instancia": mat.name,
                    "Nombre Completo": mat.name.replace("_", " ").title(),
                    "Tipo de Asignatura": tipo_clase
                })
                
            df_permitidas = pd.DataFrame(datos_materias)
            st.dataframe(df_permitidas, use_container_width=True, hide_index=True)
            # === NUEVA SECCIÓN: EXPLICADOR SEMÁNTICO ===
            st.divider()
            st.subheader("❓ Explicador Semántico de Bloqueos")
            st.write("¿Hay alguna asignatura que te interese cursar pero no aparece en tu lista de disponibles? El tutor analiza las dependencias lógicas de la ontología para explicarte qué prerrequisitos te hacen falta.")
        
            # 1. Obtener todas las materias de la ontología
            todas_las_materias_exp = sorted([m.name for m in onto.Materia.instances()])
        
            # 2. Filtrar para mostrar solo las materias que el alumno NO puede cursar actualmente
            # (Es decir, quitamos las aprobadas, las que ya está cursando e inscribiendo, y las recomendadas/disponibles)
            materias_no_disponibles = []
            for m_name in todas_las_materias_exp:
                m_obj = onto[m_name]
            
                # Verificar si ya la aprobó
                ya_aprobada = m_obj in alumno_activo.aprobo if hasattr(alumno_activo, "aprobo") else False
                # Verificar si la inscribe actualmente
                ya_inscrita = m_obj in alumno_activo.inscribe if hasattr(alumno_activo, "inscribe") else False
                # Verificar si está en su lista actual de "puedeCursar"
                esta_permitida = m_obj in materias_permitidas
            
                if not ya_aprobada and not ya_inscrita and not esta_permitida:
                    materias_no_disponibles.append(m_name)
                
            if materias_no_disponibles:
                # Diccionario amigable para el usuario
                opciones_explicador = {m: m.replace("_", " ").title() for m in materias_no_disponibles}
            
                materia_a_explicar = st.selectbox(
                    "Selecciona una asignatura bloqueada para auditar sus prerrequisitos:",
                    options=list(opciones_explicador.keys()),
                    format_func=lambda x: opciones_explicador[x],
                    key="sb_explicador"
                )
            
                if st.button("🔍 Auditar Dependencias Lógicas"):
                    # Llamar al servicio que analiza las propiedades ontológicas
                    prerrequisitos_faltantes = explicar_bloqueo_materia(onto, alumno_activo, materia_a_explicar)
                
                    if prerrequisitos_faltantes:
                        st.warning(f"🔒 **Acceso Restringido:** No es posible inscribirse a *{opciones_explicador[materia_a_explicar]}* debido a que no has cubierto su cadena de seriación académica.")
                        st.markdown("**Asignaturas prerrequisito pendientes por aprobar:**")
                        for falta in prerrequisitos_faltantes:
                            st.markdown(f"- 🟥 *{falta}*")
                    else:
                        st.info(f"ℹ️ *{opciones_explicador[materia_a_explicar]}* no tiene prerrequisitos obligatorios directos registrados en la ontología. Su exclusión puede deberse a que corresponde a un ciclo escolar diferente al tipo seleccionado arriba (Par / Impar).")
            else:
                st.success("🎉 Todas las asignaturas de la carrera están desbloqueadas o aprobadas para este perfil.")
        else:
            st.warning("No se encontraron materias disponibles para este periodo.")

    # ---------------------------------------------------------
    # TAB 3: REGISTRO DE INTERESES DEL ALUMNO 
    # ---------------------------------------------------------
    with tab3:
        st.header("🎯 Registro de Intereses Académicos")
        st.write("Selecciona una asignatura que te llame la atención. El tutor auditará los grafos de la ontología para indicarte si cumples con las condiciones lógicas para cursarla hoy mismo.")
        
        # Obtener todas las materias existentes en el archivo RDF
        todas_las_materias = sorted([m.name for m in onto.Materia.instances()])
        opciones_combo = {m: m.replace("_", " ").title() for m in todas_las_materias}
        
        materia_seleccionada_id = st.selectbox(
            "Selecciona la materia de tu interés:",
            options=list(opciones_combo.keys()),
            format_func=lambda x: opciones_combo[x],
            key="sb_interes_nuevo"
        )
        
        # === AUDITORÍA EN TIEMPO REAL ===
        analisis = analizar_materia_interes(onto, alumno_activo, materia_seleccionada_id)
        
        if analisis["viable"]:
            st.success(analisis["motivo"])
        else:
            st.warning(analisis["motivo"])
            
        # Botón para registrar formalmente el interés
        if st.button("Registrar Interés en mi Expediente"):
            exito, mensaje_interes = registrar_interes_materia(onto, alumno_activo, materia_seleccionada_id)
            if exito:
                st.success(mensaje_interes)
                st.rerun() # Recargar la app para refrescar el listado de abajo
            else:
                st.error(mensaje_interes)
                
        # Mostrar los intereses actuales guardados
        st.subheader("Tus Intereses Registrados Actuales")
        if hasattr(alumno_activo, "interesadoEn") and alumno_activo.interesadoEn:
            intereses_actuales = [m.name.replace("_", " ").title() for m in alumno_activo.interesadoEn]
            for i in intereses_actuales:
                st.markdown(f"- **{i}**")
        else:
            st.info("Aún no has guardado intereses en tu expediente.")
    # ---------------------------------------------------------
    # TAB 4: MAPA CURRICULAR Y PRERREQUISITOS
    # ---------------------------------------------------------
    with tab4:
        st.header("📋 Catálogo General de Asignaturas y Seriación")
        st.write("Consulta el plan de estudios completo almacenado en la Ontología junto con sus reglas de prerrequisito asociadas.")
        
        # Invocar la función del servicio
        mapa_datos = obtener_mapa_curricular_completo(onto)
        
        if mapa_datos:
            df_mapa = pd.DataFrame(mapa_datos)
            
            # Buscador interno para el mapa curricular
            buscar_mat_mapa = st.text_input("Filtrar materias por nombre:", placeholder="Ej. Calculo")
            if buscar_mat_mapa:
                df_mapa = df_mapa[df_mapa["Materia"].str.contains(buscar_mat_mapa, case=False, na=False)]
                
            st.dataframe(df_mapa, use_container_width=True, hide_index=True)
        else:
            st.error("No se encontraron registros de materias en la ontología.")
