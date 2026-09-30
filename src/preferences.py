"""Gerenciamento de preferências do usuário, identificadas por e-mail e persistidas em cookie.

Não é autenticação real (sem senha) — é apenas uma conveniência para o usuário
recuperar suas preferências ao voltar, usando o mesmo e-mail informado antes.
"""
import base64
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
_PREFS_COOKIE = "nih_prefs"  # backup das preferências no navegador — sobrevive a reinícios do disco efêmero do servidor


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


def _get_all_cookies() -> dict[str, str]:
    """Lê todos os cookies uma única vez por execução (evita key duplicada no componente)."""
    if "_cookies_cache" not in st.session_state:
        st.session_state["_cookies_cache"] = _get_cookie_manager().get_all() or {}
    return st.session_state["_cookies_cache"]


def get_saved_email() -> str | None:
    """Lê o e-mail salvo no cookie do navegador, se houver."""
    cookies = _get_all_cookies()
    email = cookies.get(_EMAIL_COOKIE) if cookies else None
    return email if email and is_valid_email(email) else None


def _encode_prefs_cookie(prefs: dict[str, Any]) -> str:
    """Serializa as preferências para um valor seguro de guardar em cookie."""
    raw = json.dumps(prefs, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_prefs_cookie(value: str) -> dict[str, Any] | None:
    """Desserializa preferências gravadas em cookie; retorna None se estiver ausente/corrompido."""
    if not value:
        return None
    try:
        raw = base64.urlsafe_b64decode(value.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None


def _get_saved_preferences_from_cookie() -> dict[str, Any] | None:
    """Lê as preferências salvas em cookie, se houver."""
    cookies = _get_all_cookies()
    return _decode_prefs_cookie(cookies.get(_PREFS_COOKIE)) if cookies else None


def login_with_email(email: str) -> bool:
    """Vincula a sessão atual a um e-mail: salva o cookie e carrega/cria as preferências dele.

    As preferências são recuperadas tanto do arquivo no servidor quanto do cookie do
    navegador, prevalecendo a versão com `last_update` mais recente. Isso evita perda de
    dados quando o disco do servidor é efêmero (ex.: Streamlit Community Cloud, que apaga
    `data/user_prefs/` a cada reinício/hibernação do app).
    """
    email = (email or "").strip().lower()
    if not is_valid_email(email):
        return False

    cookie_manager = _get_cookie_manager()
    cookie_manager.set(_EMAIL_COOKIE, email, expires_at=datetime.now() + timedelta(days=365),
                        key=f"set_email_{_email_to_id(email)}")

    user_id = _email_to_id(email)
    from_file = load_preferences(user_id)
    from_cookie = _get_saved_preferences_from_cookie()
    if from_cookie and from_cookie.get("last_update", "") > from_file.get("last_update", ""):
        prefs = from_cookie
    else:
        prefs = from_file

    st.session_state["email"] = email
    st.session_state["_user_id"] = user_id
    st.session_state.preferences = prefs
    save_preferences(prefs)  # ressincroniza arquivo e cookie com a versão mais recente escolhida
    return True


def logout() -> None:
    """Desvincula a sessão do e-mail atual e volta ao modo convidado (sem persistência)."""
    cookie_manager = _get_cookie_manager()
    cookie_manager.delete(_EMAIL_COOKIE, key="delete_email_cookie")
    cookie_manager.delete(_PREFS_COOKIE, key="delete_prefs_cookie")
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
    """Salva as preferências no arquivo do usuário atual e num cookie de backup no navegador.

    O cookie garante que as preferências sobrevivam mesmo que o disco do servidor seja
    apagado (ex.: hibernação/redeploy no Streamlit Community Cloud).
    """
    user_id = st.session_state.get("_user_id")
    if not user_id:
        return
    prefs["last_update"] = datetime.now().isoformat()
    try:
        PREFERENCES_DIR.mkdir(parents=True, exist_ok=True)
        _preferences_file(user_id).write_text(json.dumps(prefs, indent=2, ensure_ascii=False), encoding="utf-8")
    except IOError as e:
        st.warning(f"⚠️ Não foi possível salvar preferências: {e}")

    _get_cookie_manager().set(_PREFS_COOKIE, _encode_prefs_cookie(prefs),
                               expires_at=datetime.now() + timedelta(days=365), key="set_prefs_cookie")


@st.fragment
def _autologin_from_cookie() -> None:
    """Tenta logar com o e-mail do cookie assim que o navegador o entregar.

    O componente de cookies só retorna o valor real numa atualização posterior à
    primeira renderização; isolar essa leitura num fragmento evita que a página
    inteira grave `email=None` na sessão antes desse valor chegar.
    """
    if st.session_state.get("email"):
        return
    email = get_saved_email()
    if email:
        login_with_email(email)
        st.rerun()


def init_session_state() -> None:
    """Inicializa session_state com preferências do usuário atual (se houver e-mail salvo em cookie)."""
    st.session_state.pop("_cookies_cache", None)  # relê cookies a cada execução do script

    if "email" not in st.session_state:
        st.session_state["email"] = None
        st.session_state["_user_id"] = None

    if "preferences" not in st.session_state:
        st.session_state.preferences = get_default_preferences()

    _autologin_from_cookie()

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

