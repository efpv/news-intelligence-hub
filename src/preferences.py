"""Gerenciamento de preferências do usuário, identificadas por e-mail e persistidas em cookie.

Não é autenticação real (sem senha) — é apenas uma conveniência para o usuário
recuperar suas preferências ao voltar, usando o mesmo e-mail informado antes.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import extra_streamlit_components as stx
import streamlit as st

PREFERENCES_DIR = Path(__file__).parent.parent / "data" / "user_prefs"
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_EMAIL_COOKIE = "nih_email"


def _email_to_id(email: str) -> str:
    """Deriva um id de arquivo estável a partir do e-mail (não guarda o e-mail em texto puro no nome do arquivo)."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _preferences_file(user_id: str) -> Path:
    return PREFERENCES_DIR / f"{user_id}.json"


def _get_cookie_manager() -> stx.CookieManager:
    """Reaproveita uma única instância do gerenciador de cookies por sessão."""
    if "_cookie_manager" not in st.session_state:
        st.session_state["_cookie_manager"] = stx.CookieManager(key="nih_cookie_manager")
    return st.session_state["_cookie_manager"]


def is_valid_email(email: str) -> bool:
    """Validação simples de formato de e-mail."""
    return bool(email) and _EMAIL_PATTERN.match(email.strip()) is not None


def get_saved_email() -> str | None:
    """Lê o e-mail salvo no cookie do navegador, se houver."""
    cookies = _get_cookie_manager().get_all()
    email = cookies.get(_EMAIL_COOKIE) if cookies else None
    return email if email and is_valid_email(email) else None


def login_with_email(email: str) -> bool:
    """Vincula a sessão atual a um e-mail: salva o cookie e carrega/cria as preferências dele."""
    email = (email or "").strip().lower()
    if not is_valid_email(email):
        return False

    cookie_manager = _get_cookie_manager()
    cookie_manager.set(_EMAIL_COOKIE, email, expires_at=datetime.now() + timedelta(days=365),
                        key=f"set_email_{_email_to_id(email)}")

    user_id = _email_to_id(email)
    st.session_state["email"] = email
    st.session_state["_user_id"] = user_id
    st.session_state.preferences = load_preferences(user_id)
    return True


def logout() -> None:
    """Desvincula a sessão do e-mail atual e volta ao modo convidado (sem persistência)."""
    cookie_manager = _get_cookie_manager()
    cookie_manager.delete(_EMAIL_COOKIE, key="delete_email_cookie")
    st.session_state["email"] = None
    st.session_state["_user_id"] = None
    st.session_state.preferences = get_default_preferences()


def load_preferences(user_id: str) -> dict[str, Any]:
    """Carrega preferências salvas do usuário identificado por `user_id`."""
    path = _preferences_file(user_id)
    if not path.exists():
        return get_default_preferences()

    try:
        with open(path, "r", encoding="utf-8") as f:
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
    """Salva as preferências no arquivo do usuário atual (identificado em session_state)."""
    user_id = st.session_state.get("_user_id")
    if not user_id:
        return
    prefs["last_update"] = datetime.now().isoformat()
    try:
        PREFERENCES_DIR.mkdir(parents=True, exist_ok=True)
        _preferences_file(user_id).write_text(json.dumps(prefs, indent=2, ensure_ascii=False), encoding="utf-8")
    except IOError as e:
        st.warning(f"⚠️ Não foi possível salvar preferências: {e}")


def init_session_state() -> None:
    """Inicializa session_state com preferências do usuário atual (se houver e-mail salvo em cookie)."""
    if "email" not in st.session_state:
        st.session_state["email"] = get_saved_email()
        st.session_state["_user_id"] = _email_to_id(st.session_state["email"]) if st.session_state["email"] else None

    if "preferences" not in st.session_state:
        user_id = st.session_state.get("_user_id")
        st.session_state.preferences = load_preferences(user_id) if user_id else get_default_preferences()

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

