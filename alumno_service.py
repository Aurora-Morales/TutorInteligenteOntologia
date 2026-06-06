# Lógica de negocio (Búsquedas, historial, reglas)
import streamlit as st

def buscar_alumno_por_filtro(onto, criterio):
    """
    Busca un alumno por su matrícula o por su nombre de usuario en la ontología.
    """
    criterio_limpio = criterio.strip().lower()
    if not criterio_limpio:
        return None

    # Obtener todas las instancias de la clase Alumno de tu ontología
    alumnos = onto.Alumno.instances()
    
    for alumno in alumnos:
        # 1. Buscar por Nombre de Instancia (ej: aurora, alexa, juan)
        if alumno.name.lower() == criterio_limpio:
            return alumno
            
        # 2. Buscar por la Data Property 'matricula' definida en tu RDF
        if hasattr(alumno, "matricula") and alumno.matricula:
            # Si es funcional puede ser un string único
            if isinstance(alumno.matricula, list):
                if any(m.lower() == criterio_limpio for m in alumno.matricula):
                    return alumno
            elif alumno.matricula.lower() == criterio_limpio:
                return alumno
                
        # 3. Buscar por el apellido si existe
        if hasattr(alumno, "apellido") and alumno.apellido:
            if isinstance(alumno.apellido, list):
                if any(ap.lower() == criterio_limpio for ap in alumno.apellido):
                    return alumno
            elif alumno.apellido.lower() == criterio_limpio:
                return alumno

    return None


def obtener_historial_academico(alumno):
    """
    Extrae las materias que el alumno ya aprobó y las que está inscribiendo actualmente.
    """
    materias_aprobadas = []
    materias_inscritas = []

    # Extraer de la Object Property 'aprobo'
    if hasattr(alumno, "aprobo"):
        materias_aprobadas = [materia.name.replace("_", " ").title() for materia in alumno.aprobo]

    # Extraer de la Object Property 'inscribe'
    if hasattr(alumno, "inscribe"):
        materias_inscritas = [materia.name.replace("_", " ").title() for materia in alumno.inscribe]

    return {
        "aprobadas": materias_aprobadas,
        "inscritas": materias_inscritas
    }


def obtener_materias_disponibles(onto, alumno, semestre_tipo):
    """
    Filtra las materias basándose en las inferencias del razonador (regla puedeCursar)
    y el tipo de semestre elegido (Par o Impar).
    """
    materias_disponibles = []
    
    # 1. Consultar lo que el razonador dedujo mediante la propiedad 'puedeCursar'
    if hasattr(alumno, "puedeCursar"):
        materias_razonadas = alumno.puedeCursar
    else:
        materias_razonadas = []

    # Si el razonador no infirió nada por falta de datos, usamos todas las materias menos aprobadas como fallback
    if not materias_razonadas:
        todas_materias = onto.Materia.instances()
        aprobadas = alumno.aprobo if hasattr(alumno, "aprobo") else []
        materias_razonadas = [m for m in todas_materias if m not in aprobadas]

    # 2. Filtrar por clasificación del Semestre (Par / Impar) de acuerdo a tu ontología
    for materia in materias_razonadas:
        # Buscamos a qué semestre pertenece la materia en tu grafo ontológico
        es_valida_para_semestre = False
        
        # Revisamos qué semestres 'tienen' esta materia
        for sem in onto.Semestre.instances():
            if hasattr(sem, "tiene") and materia in sem.tiene:
                # Comprobar si el semestre cumple con el tipo seleccionado (Par o Impar)
                if semestre_tipo == "Par" and isinstance(sem, onto.Par):
                    es_valida_para_semestre = True
                elif semestre_tipo == "Impar" and isinstance(sem, onto.Impar):
                    es_valida_para_semestre = True
        
        # Si tu ontología no vincula materias con semestres específicos explícitamente,
        # la agregamos por defecto para no vaciar la lista
        if es_valida_para_semestre or not any(hasattr(s, "tiene") and materia in s.tiene for s in onto.Semestre.instances()):
            materias_disponibles.append(materia)

    return materias_disponibles


def registrar_interes_materia(onto, alumno, nombre_materia_instancia):
    """
    Vincula dinámicamente un interés del alumno usando la propiedad 'interesadoEn'.
    """
    try:
        materia_obj = onto[nombre_materia_instancia]
        if materia_obj:
            # Añadir a la lista de intereses de la Object Property
            if hasattr(alumno, "interesadoEn"):
                if materia_obj not in alumno.interesadoEn:
                    alumno.interesadoEn.append(materia_obj)
            else:
                alumno.interesadoEn = [materia_obj]
            return True, f"✨ Se ha registrado tu interés en la materia: {materia_obj.name.replace('_', ' ').title()}"
        return False, "No se encontró la materia seleccionada."
    except Exception as e:
        return False, f"Error al guardar el interés: {str(e)}"

def obtener_materias_recomendadas(onto, alumno):
    """
    Consulta las asignaturas que el razonador dedujo y vinculó al alumno 
    mediante la Object Property 'seRecomienda' (activada por las reglas SWRL).
    """
    materias_recomendadas = []
    
    # Comprobar si el objeto alumno tiene la propiedad 'seRecomienda' inferida
    if hasattr(alumno, "seRecomienda") and alumno.seRecomienda:
        for materia in alumno.seRecomienda:
            # Obtener el tipo de asignatura (Obligatoria u Optativa)
            tipo_clase = "Materia"
            if hasattr(onto, "Obligatoria") and onto.Obligatoria in materia.is_a:
                tipo_clase = "Obligatoria"
            elif hasattr(onto, "Optativa") and onto.Optativa in materia.is_a:
                tipo_clase = "Optativa"
                
            materias_recomendadas.append({
                "Clave / Instancia": materia.name,
                "Nombre Completo": materia.name.replace("_", " ").title(),
                "Tipo de Asignatura": tipo_clase
            })
            
    return materias_recomendadas

def obtener_diagnostico_pedagogico(onto, alumno):
    """
    Analiza las clases inferidas o el promedio del alumno para determinar
    su nivel de desempeño y generar un perfil adaptativo.
    """
    # Valores por defecto
    nivel = "Regular"
    consejo = "Mantén un ritmo constante de estudio y asiste a tus asesorías programadas."
    color = "normal"
    
    # 1. Intentar evaluar por clases de la ontología (Avanzado, Regular, Deficiente)
    # Comprobamos las clases a las que pertenece el individuo (is_a)
    clases_alumno = [c.name for c in alumno.is_a]
    
    if "Avanzado" in clases_alumno:
        nivel = "Avanzado"
        consejo = "🚀 ¡Excelente rendimiento! Tienes un perfil sobresaliente. El tutor te sugiere considerar participar en proyectos de investigación, tutorías entre pares o registrar materias optativas de alta especialidad."
        color = "success"
    elif "Deficiente" in clases_alumno:
        nivel = "Deficiente"
        consejo = "⚠️ Alerta de Rezago: Tu historial muestra dificultades en ciertas asignaturas. El tutor te recomienda encarecidamente no saturar tu carga académica este semestre, priorizar materias seriadas pendientes y solicitar un asesor de inmediato."
        color = "danger"
    
    # 2. Fallback / Refuerzo por la propiedad 'promedio' si está disponible
    elif hasattr(alumno, "promedio") and alumno.promedio:
        try:
            # Si viene como lista o string, extraemos el valor numérico
            val_promedio = alumno.promedio[0] if isinstance(alumno.promedio, list) else alumno.promedio
            promedio_num = float(val_promedio)
            
            if promedio_num >= 9.0:
                nivel = "Avanzado"
                consejo = "¡Excelente rendimiento! Tu promedio actual es de {} puntos. El tutor te sugiere mantener este nivel y explorar opciones de movilidad estudiantil o proyectos de titulación temprana.".format(promedio_num)
                color = "success"
            elif promedio_num < 7.5:
                nivel = "Condicionado / Deficiente"
                consejo = "⚠️ Alerta Académica: Tu promedio actual es de {} puntos. Para evitar caer en rezago, te sugerimos inscribir un máximo de 3 asignaturas este periodo y calendarizar horas de estudio semanales en biblioteca.".format(promedio_num)
                color = "danger"
        except ValueError:
            pass # Si el promedio no es convertible a número, se queda con la clasificación previa

    return {
        "nivel": nivel,
        "consejo": consejo,
        "color": color
    }

def simular_aprobacion_materia(onto, alumno, nombre_materia_simulada):
    """
    Simula temporalmente en memoria la aprobación de una materia, re-ejecuta
    el razonador y devuelve las nuevas asignaturas que el alumno podría cursar.
    """
    nuevas_disponibles = []
    
    try:
        materia_obj = onto[nombre_materia_simulada]
        if not materia_obj:
            return []
            
        # 1. Guardar una copia del estado original de materias aprobadas del alumno
        estado_original_aprobadas = list(alumno.aprobo) if hasattr(alumno, "aprobo") else []
        estado_original_puede_cursar = list(alumno.puedeCursar) if hasattr(alumno, "puedeCursar") else []
        
        # 2. Modificar temporalmente el grafo en memoria: añadir la materia simulada a 'aprobo'
        if hasattr(alumno, "aprobo"):
            if materia_obj not in alumno.aprobo:
                alumno.aprobo.append(materia_obj)
        else:
            alumno.aprobo = [materia_obj]
            
        # 3. Forzar al razonador Pellet a re-evaluar las reglas SWRL con este nuevo dato simulado
        from owlready2 import sync_reasoner_pellet
        with onto:
            sync_reasoner_pellet(infer_property_values=True)
            
        # 4. Capturar el nuevo resultado inferido por la regla 'puedeCursar'
        estado_simulado_puede_cursar = list(alumno.puedeCursar) if hasattr(alumno, "puedeCursar") else []
        
        # 5. Comparar: ¿Qué materias puede cursar AHORA que NO podía cursar ANTES?
        # También excluimos la propia materia que estamos simulando como aprobada
        for mat in estado_simulado_puede_cursar:
            if mat not in estado_original_puede_cursar and mat != materia_obj:
                tipo_clase = "Materia"
                if hasattr(onto, "Obligatoria") and onto.Obligatoria in mat.is_a:
                    tipo_clase = "Obligatoria"
                elif hasattr(onto, "Optativa") and onto.Optativa in mat.is_a:
                    tipo_clase = "Optativa"
                    
                nuevas_disponibles.append({
                    "Clave / Instancia": mat.name,
                    "Nombre Completo": mat.name.replace("_", " ").title(),
                    "Tipo de Asignatura": tipo_clase
                })
                
        # 6. RESTAURAR LA ONTOLOGÍA A SU ESTADO REAL
        # Esto es vital para no dejar datos ficticios grabados en la sesión
        alumno.aprobo = estado_original_aprobadas
        with onto:
            sync_reasoner_pellet(infer_property_values=True)
            
    except Exception as e:
        print(f"Error durante la simulación semántica: {str(e)}")
        
    return nuevas_disponibles

def calcular_semaforo_rezago(onto, alumno):
    """
    Calcula estadísticamente el avance del alumno y genera un indicador
    de semáforo (Verde, Amarillo, Rojo) basado en su nivel de rezago.
    """
    # 1. Obtener total de materias registradas en la ontología para tener una base
    total_materias_plan = len(onto.Materia.instances())
    if total_materias_plan == 0:
        total_materias_plan = 40  # Valor por defecto en caso de un grafo vacío
        
    # 2. Contar cuántas ha aprobado el alumno realmente
    materias_aprobadas = len(alumno.aprobo) if hasattr(alumno, "aprobo") else 0
    
    # 3. Calcular porcentaje de avance
    porcentaje_avance = (materias_aprobadas / total_materias_plan) * 100
    
    # 4. Determinar el estado del semáforo y las recomendaciones de carga
    # Mapeamos también si pertenece a la clase "Deficiente" inferida por la ontología
    clases_alumno = [c.name for c in alumno.is_a]
    
    if "Deficiente" in clases_alumno or (porcentaje_avance < 30 and materias_aprobadas <= 2):
        estado = "🔴 AVANCE CRÍTICO"
        color_web = "red"
        nota = "Riesgo extremx<o de deserción. Se sugiere inscripción mínima obligatoria y asignación de un tutor docente uno a uno."
    elif materias_aprobadas < (total_materias_plan * 0.5) and "Avanzado" not in clases_alumno:
        estado = "🟡 AVANCE MODERADO"
        color_web = "orange"
        nota = "El alumno muestra un avance lento o intermitente. Se recomienda regularizar materias seriadas antes de avanzar a optativas."
    else:
        estado = "🟢 EXCELENTE AVANCE"
        color_web = "green"
        nota = "Trayectoria ideal. El alumno se encuentra dentro de los parámetros de tiempo y créditos estipulados en el plan."

    return {
        "porcentaje": round(porcentaje_avance, 1),
        "aprobadas": materias_aprobadas,
        "totales": total_materias_plan,
        "estado": estado,
        "color": color_web,
        "nota": nota
    }

def explicar_bloqueo_materia(onto, alumno, nombre_materia):
    """
    Analiza la ontología para descubrir qué prerrequisitos de una materia
    específica le hacen falta aprobar al alumno actual.
    """
    faltantes = []
    try:
        materia_obj = onto[nombre_materia]
        if not materia_obj:
            return ["Materia no encontrada en el catálogo."]
            
        # 1. Obtener los prerrequisitos definidos en la propiedad 'tienePrerequisito'
        prerrequisitos = []
        if hasattr(materia_obj, "tienePrerequisito"):
            prerrequisitos = materia_obj.tienePrerequisito
            
        # 2. Si la ontología usa la propiedad de forma inversa (la materia ES prerrequisito de otra)
        # o si está vacía, buscamos en todas las materias si tienen vinculación
        if not prerrequisitos:
            for mat in onto.Materia.instances():
                if hasattr(mat, "tienePrerequisito") and materia_obj in mat.tienePrerequisito:
                    # En algunas estructuras el mapeo es inverso, se valida la existencia
                    pass

        # 3. Cruzar los prerrequisitos contra lo que el alumno YA aprobó
        materias_aprobadas = alumno.aprobo if hasattr(alumno, "aprobo") else []
        
        for pre in prerrequisitos:
            if pre not in materias_aprobadas:
                faltantes.append(pre.name.replace("_", " ").title())
                
    except Exception as e:
        return [f"Error al analizar la estructura semántica: {str(e)}"]
        
    return faltantes

def analizar_materia_interes(onto, alumno, nombre_materia_instancia):
    """
    Analiza una materia de interés. Evalúa la viabilidad académica (prerrequisitos)
    de forma independiente al ciclo escolar (Par/Impar), permitiendo planificar a futuro.
    """
    try:
        materia_obj = onto[nombre_materia_instancia]
        if not materia_obj:
            return {"viable": False, "motivo": "Materia no encontrada."}
            
        # 1. Verificar si ya la aprobó
        if hasattr(alumno, "aprobo") and materia_obj in alumno.aprobo:
            return {
                "viable": False,
                "motivo": "✨ Ya has aprobado esta asignatura previamente, ¡ya no necesitas cursarla!"
            }
            
        # 2. Verificar si la está cursando actualmente
        if hasattr(alumno, "inscribe") and materia_obj in alumno.inscribe:
            return {
                "viable": False,
                "motivo": "📝 Actualmente te encuentras inscrito y cursando esta asignatura."
            }
            
        # 3. AUDITORÍA DE PRERREQUISITOS (Viabilidad Académica Real)
        prereqs = materia_obj.tienePrerequisito if hasattr(materia_obj, "tienePrerequisito") else []
        aprobadas = alumno.aprobo if hasattr(alumno, "aprobo") else []
        faltantes = [p.name.replace("_", " ").title() for p in prereqs if p not in aprobadas]
        
        if faltantes:
            return {
                "viable": False,
                "motivo": f"❌ No cumples con los aspectos académicos aún. Te hace falta aprobar de forma obligatoria: {', '.join(faltantes)}."
            }
            
        # 4. SI PASÓ LOS PRERREQUISITOS, EVALUAMOS SI ES DE ESTE SEMESTRE O DEL SIGUIENTE
        # Revisamos si el razonador la incluyó en 'puedeCursar' actualmente
        puede_cursar_lista = alumno.puedeCursar if hasattr(alumno, "puedeCursar") else []
        
        if materia_obj in puede_cursar_lista:
            return {
                "viable": True,
                "motivo": "✅ ¡Es perfectamente viable! Cumples con los prerrequisitos y está disponible para inscribirse en este ciclo académico actual."
            }
        else:
            # Caso en que cumple prerrequisitos pero es del otro ciclo (Par/Impar)
            return {
                "viable": True,  # Es viable registrar interés porque académicamente está listo
                "motivo": "📅 ¡Viable para tu Plan de Vida! Académicamente cumples con todos los prerrequisitos. Nota: Esta materia pertenece al ciclo opuesto (Par/Impar), por lo que podrás inscribirla formalmente en el próximo periodo."
            }
            
    except Exception as e:
        return {"viable": False, "motivo": f"Error en el análisis semántico: {str(e)}"}

def obtener_mapa_curricular_completo(onto):
    """
    Extrae la lista completa de todas las materias del catálogo de la ontología
    junto con sus respectivos prerrequisitos definidos.
    """
    mapa = []
    try:
        for materia in onto.Materia.instances():
            # Determinar tipo
            tipo_clase = "Materia"
            if hasattr(onto, "Obligatoria") and onto.Obligatoria in materia.is_a:
                tipo_clase = "Obligatoria"
            elif hasattr(onto, "Optativa") and onto.Optativa in materia.is_a:
                tipo_clase = "Optativa"
                
            # Extraer prerrequisitos
            prereqs = materia.tienePrerequisito if hasattr(materia, "tienePrerequisito") else []
            nombres_prereq = ", ".join([p.name.replace("_", " ").title() for p in prereqs]) if prereqs else "Ninguno"
            
            mapa.append({
                "Materia": materia.name.replace("_", " ").title(),
                "Tipo": tipo_clase,
                "Prerrequisitos Requeridos": nombres_prereq
            })
            
        # Ordenar alfabéticamente por nombre de materia
        mapa = sorted(mapa, key=lambda x: x["Materia"])
    except Exception as e:
        print(f"Error al extraer mapa curricular: {str(e)}")
        
    return mapa
