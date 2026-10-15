"""Tu perfil y preferencias de búsqueda. Edita este archivo para ajustar el filtro."""

# Texto que ve el modelo de IA para puntuar cada oferta contra tu perfil
PROFILE_TEXT = """
Recién graduado en Ingeniería en Computación (título obtenido en julio de 2026).
También se considera ingeniero de software. Interesado en puestos de Full Stack Developer
o Software Engineer (frontend, backend o full stack). Cualquier stack tecnológico vale
(JavaScript/TypeScript, Python, Java, PHP...), no está atado a ninguna tecnología.
Busca: Zaragoza (presencial o híbrido) o 100% remoto (España o Europa).
Nivel: junior / entrada / recién graduado. Sin experiencia profesional laboral larga
pero con práctica de 6 meses en NTT Data.
"""

# Frases que indican puesto de desarrollo de software (título o descripción)
INCLUDE_ROLE_PATTERNS = [
    r"desarrollador",
    r"desarrolladora",
    r"developer",
    r"software engineer",
    r"ingenier[íi]a de software",
    r"full[\s\-]?stack",
    r"fullstack",
    r"backend",
    r"front[\s\-]?end",
    r"web developer",
    r"programador",
    r"engineer",
    r"ingenier[óo]",
    r"devops",
    r"data (engineer|developer)",
]

# Si el TÍTULO coincide con esto, se descarta (puestos demasiado senior o no técnicos)
EXCLUDE_TITLE_PATTERNS = [
    r"\bsenior\b",
    r"\bsr\.?\b",
    r"\blead\b",
    r"\bprincipal\b",
    r"\barchitect\b",
    r"\barquitect[oa]\b",
    r"\bmanager\b",
    r"\bhead of\b",
    r"\bdirector\b",
    r"\bjefe\b",
    r"\bstaff\b",
    r"\bcto\b",
    r"\bvp of\b",
    r"m[áa]nster",
    r"\bformador\b",
    r"\bprofesor\b",
    r"\bcommercial\b",
    r"\bcomercial\b",
    r"becar[íi]a|becario",
]

# Si la DESCRIPCIÓN contiene años de experiencia exigidos (demasiados para junior),
# se descarta. Excluimos de 4 años en adelante; 1-3 años lo decide la IA.
EXCLUDE_DESC_PATTERNS = [
    r"\b[4-9]\s*\+?\s*a[ñn]os de experiencia",
    r"\bm[íi]nimo (de )?[4-9] a[ñn]os",
    r"\bminimum of [4-9] years",
    r"\bat least [4-9] years",
    r"\b[4-9]\+?\s*years of experience",
    r"\bmore than [3-9] years",
    r"\bm[áa]s de [3-9] a[ñn]os de experiencia",
]

# Palabras clave que indican remoto/híbrido en localizaciones ambiguas
REMOTE_HINT_PATTERNS = [r"\bremote\b", r"\bteletrabajo\b", r"\bremoto\b", r"\bhibrid[oa]\b", r"\bh[íi]brid"]
ZARAGOZA_HINT = r"zaragoza|utebo|la muela|alag[óo]n|villanueva|ejea|monz[óo]n|huesca"

# IA
MIN_SCORE = 6          # oferta mínima (1-10) para notificar
MAX_DIGEST_ITEMS = 8   # máximo de ofertas por mensaje de Telegram
MAX_DESC_CHARS = 3000  # descripción truncada antes de mandarla a la IA
MAX_SCORE_JOBS = 24    # máx. ofertas que se puntúan con IA por ejecución (limita tiempo/cuota)
LINKEDIN_DETAIL_LIMIT = 15  # máx. descripciones completas a descargar de LinkedIn por ejecución

# Consultas LinkedIn: (keywords, location, remote_only)
LINKEDIN_QUERIES = [
    ("desarrollador software", "Zaragoza, Aragón, Spain", False),
    ("software engineer", "Zaragoza, Aragón, Spain", False),
    ("software engineer", "Spain", True),
    ("full stack developer", "Spain", True),
]

# Consultas InfoJobs: diccionario de parámetros
INFOJOBS_QUERIES = [
    {"keyword": "desarrollador", "provinceIds": "53"},          # Zaragoza (id interno 53)
    {"keyword": "desarrollador", "teleworkingIds": "2"},        # Solo teletrabajo en España
    {"keyword": "software engineer", "teleworkingIds": "2"},
]

INFOJOBS_REQUEST_DELAY = 5  # segundos entre peticiones (evita captcha)
