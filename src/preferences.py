"""Gerenciamento de preferências do usuário com persistência em JSON."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

PREFERENCES_FILE = Path(__file__).parent.parent / "user_preferences.json"


def load_preferences() -> dict[str, Any]:
    """Carrega preferências salvas do arquivo JSON."""
    if not PREFERENCES_FILE.exists():
        return get_default_preferences()
    
    try:
        with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return get_default_preferences()


def get_default_preferences() -> dict[str, Any]:
    """Retorna estrutura padrão de preferências."""
    return {
        "portfolio": [],
        "selected_category": "Todas",
        "selected_sources": [],
        "sentiment_filter": [],
        "search_term": "",
        "period": "Últimos 7 dias",
        "last_update": datetime.now().isoformat()
    }


def save_preferences(prefs: dict[str, Any]) -> None:
    """Salva preferências no arquivo JSON."""
    prefs["last_update"] = datetime.now().isoformat()
    try:
        PREFERENCES_FILE.write_text(json.dumps(prefs, indent=2, ensure_ascii=False), encoding="utf-8")
    except IOError as e:
        st.warning(f"⚠️ Não foi possível salvar preferências: {e}")


def init_session_state() -> None:
    """Inicializa session_state com preferências persistidas."""
    if "preferences" not in st.session_state:
        st.session_state.preferences = load_preferences()
    
    # Garante que todas as chaves estão presentes
    defaults = get_default_preferences()
    for key, value in defaults.items():
        if key not in st.session_state.preferences:
            st.session_state.preferences[key] = value


def update_preference(key: str, value: Any) -> None:
    """Atualiza uma preferência e salva automaticamente."""
    st.session_state.preferences[key] = value
    save_preferences(st.session_state.preferences)


def reset_preferences() -> None:
    """Reseta todas as preferências para os valores padrão."""
    st.session_state.preferences = get_default_preferences()
    save_preferences(st.session_state.preferences)
