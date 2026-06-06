# Carga y ejecución del razonador (Pallet)
import streamlit as st
from owlready2 import get_ontology, sync_reasoner_pellet

# Nombre de tu archivo ontológico
ARCHIVO_ONTOLOGIA = "PracticaOntologia.rdf"

@st.cache_resource
def obtener_instancia_ontologia():
    """
    Carga de forma segura el archivo RDF y ejecuta el razonador Pellet.
    Mantiene la ontología en caché global dentro de la sesión de Streamlit.
    """
    try:
        # Cargar Ontología usando la ruta local
        onto = get_ontology(f"file://{ARCHIVO_ONTOLOGIA}").load()
        
        # Ejecutar Razonador Pellet para procesar las reglas SWRL y restricciones
        with onto:
            sync_reasoner_pellet(infer_property_values=True)
            
        return onto, "✅ Ontología y Reglas SWRL cargadas y razonadas exitosamente con Pellet."
    except Exception as e:
        return None, f"❌ Error crítico al procesar la ontología: {str(e)}"