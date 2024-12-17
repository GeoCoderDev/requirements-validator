import unicodedata
import spacy
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

class AdvancedRequirementValidator:
    def __init__(self):
        try:
            # Cargar modelo de lenguaje para español
            self.nlp = spacy.load("es_core_news_sm")
        except:
            self.nlp = None

        # Palabras ambiguas y débiles
        self.weak_words = [
            'algo', 'algún', 'algunos', 'tal vez', 'quizás', 'podría',
            'aproximadamente', 'más o menos', 'creo que', 'parece'
        ]

        # Palabras clave para tipos de requerimientos
        self.functional_keywords = [
            'debe', 'debería', 'tiene que', 'permitir', 'gestionar',
            'calcular', 'mostrar', 'registrar', 'generar'
        ]

        self.non_functional_keywords = [
            'rendimiento', 'seguridad', 'escalabilidad', 'disponibilidad',
            'usabilidad', 'tiempo de respuesta', 'número de usuarios'
        ]

    def normalize_text(self, text: str) -> str:
        """Normaliza texto removiendo acentos y convirtiendo a minúsculas"""
        return ''.join(
            c for c in unicodedata.normalize('NFD', text.lower())
            if unicodedata.category(c) != 'Mn'
        )

    def validate_requirement(self, requirement: str, is_functional: bool) -> Dict:
        """Validación comprehensiva de requerimientos"""
        # Preprocesamiento
        requirement = requirement.strip()
        normalized_req = self.normalize_text(requirement)

        # Resultado de validación
        validation_result = {
            'original_text': requirement,
            'is_valid': True,
            'errors': [],
            'suggestions': []
        }

        # Validación de longitud
        if len(requirement.split()) < 5:
            validation_result['is_valid'] = False
            validation_result['errors'].append({
                'type': 'Longitud Insuficiente',
                'description': 'El requerimiento es demasiado corto para ser significativo.',
                'suggestion': 'Expanda su requerimiento para incluir más detalles específicos.'
            })

        # Detección de palabras ambiguas
        ambiguous_words_found = [
            word for word in self.weak_words
            if word in normalized_req
        ]
        if ambiguous_words_found:
            validation_result['is_valid'] = False
            validation_result['errors'].append({
                'type': 'Ambigüedad',
                'description': f'Se encontraron palabras ambiguas: {", ".join(ambiguous_words_found)}',
                'suggestion': 'Reemplace palabras vagas con términos precisos y concretos.'
            })

        # Verificación de palabras clave
        keywords = (self.functional_keywords if is_functional
                    else self.non_functional_keywords)
        has_keywords = any(
            keyword in normalized_req
            for keyword in keywords
        )
        if not has_keywords:
            validation_result['is_valid'] = False
            validation_result['errors'].append({
                'type': 'Ausencia de Palabras Clave',
                'description': 'No se encontraron palabras características del tipo de requerimiento.',
                'suggestion': f'Incluya palabras como: {", ".join(keywords[:3])}'
            })

        # Verificación sin spaCy por si falla la carga
        if self.nlp is not None:
            # Análisis gramatical
            doc = self.nlp(requirement)
            verbs = [token for token in doc if token.pos_ == 'VERB']
            nouns = [token for token in doc if token.pos_ == 'NOUN']

            # Verificación de especificidad
            if len(verbs) == 0 or len(nouns) < 2:
                validation_result['is_valid'] = False
                validation_result['errors'].append({
                    'type': 'Falta de Especificidad',
                    'description': 'El requerimiento carece de verbos o sustantivos específicos.',
                    'suggestion': 'Defina claramente la acción (verbo) y el objeto (sustantivo) del requerimiento.'
                })

        # Detección de métricas
        metrics_indicators = ['máximo', 'mínimo', 'al menos', 'no más de', '%']
        has_metrics = any(
            metric in requirement.lower()
            for metric in metrics_indicators
        )
        if not has_metrics and is_functional:
            validation_result['suggestions'].append({
                'type': 'Medibilidad',
                'description': 'No se detectaron métricas específicas.',
                'recommendation': 'Considere agregar métricas o criterios de aceptación medibles.'
            })

        return validation_result

# Crear instancia de FastAPI
app = FastAPI(
    title="Requirement Validator API",
    description="API para validar requerimientos de software",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequirementRequest(BaseModel):
    requirement: str
    is_functional: bool

# Inicializar validador
validator = AdvancedRequirementValidator()

@app.post("/validate-requirement")
async def validate_requirement(request: RequirementRequest):
    try:
        result = validator.validate_requirement(
            request.requirement, 
            request.is_functional
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Requirement Validator API",
        "status": "✅ Online",
        "version": "1.0.0"
    }
