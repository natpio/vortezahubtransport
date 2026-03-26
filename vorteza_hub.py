import streamlit as st
import json
import os
import pandas as pd
import base64
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

# --- 1. IMPORTY MODUŁÓW VORTEZA ---
try:
    from vorteza_stack import run_stack
    from vorteza_flow import run_flow
    from vorteza_base import run_base
    from vorteza_core import run_core
except ImportError as e:
    st.error(f"KRYTYCZNY BŁĄD IMPORTU: Upewnij się, że pliki vorteza_stack.py, vorteza_flow.py, vorteza_base.py i vorteza_core.py znajdują się w folderze. Szczegóły: {e}")

# --- 2. KONFIGURACJA APEX ULTIMATE PLUS ---
st.set_page_config(
    page_title="VORTEZA TMS v25.0",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🕋"
)

def get_base64_of_bin_file(bin_file):
    try:
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

# --- 3. DYNAMICZNY SILNIK STATYSTYK (LIVE DATA) ---
def get_dashboard_stats():
    stats = {"vehicles": 0, "alerts": 0, "euro": 0.0, "skus": 0}
    try:
        if os.path.exists(os.path.join("data", "config.json")):
            with open(os.path.join("data", "config.json"), "r", encoding="utf-8") as f:
                stats["euro"] = json.load(f).get("EURO_RATE", 0.0)
        if os.path.exists(os.path.join("data", "products.json")):
            with open(os.path.join("data", "products.json"), "r", encoding="utf-8") as f:
                stats["skus"] = len(json.load(f))
    except: pass
    return stats

# --- 4. SILNIK WIZUALNY VORTEZA ---
def inject_hub_theme():
    bg_path = os.path.join("assets", "tlo_hub_2.jpg")
    bg_b64 = get_base64_of_bin_file(bg_path)
    
    bg_style = f"""
    .stApp {{
        background: linear-gradient(rgba(6, 6, 6, 0.85), rgba(6, 6, 6, 0.85)), 
                    url("data:image/jpeg;base64,{bg_b64}") !important;
        background-size: cover !important; background-attachment: fixed !important;
    }}
    """ if bg_b64 else ".stApp { background-color: var(--v-dark); }"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&family=JetBrains+Mono&display=swap');
            :root {{ --v-copper: #B58863; --v-dark: #060606; }}
            {bg_style}
            .stApp {{ color: #FFFFFF; font-family: 'Montserrat', sans-serif; }}
            section[data-testid="stSidebar"] {{ background-color: rgba(3, 3, 3, 0.95) !important; border-right: 1px solid rgba(181, 136, 99, 0.3); width: 350px !important; backdrop-filter: blur(10px); }}
            .v-status-glow {{ color: #00FF41; text-shadow: 0 0 10px #00FF41; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; }}
            h1, h2, h3, h4 {{ color: var(--v-copper) !important; text-transform: uppercase; letter-spacing: 6px !important; font-weight: 700 !important; }}
            .stButton>button {{ background-color: rgba(10,10,10,0.8) !important; color: var(--v-copper) !important; border: 1px solid var(--v-copper) !important; width: 100%; transition: 0.4s; }}
            .stButton>button:hover {{ background-color: var(--v-copper) !important; color: black !important; }}
            .module-card {{ background: rgba(10, 10, 10, 0.75); border: 1px solid rgba(181, 136, 99, 0.4); border-top: 3px solid #B58863; padding: 20px; border-radius: 8px; text-align: center; backdrop-filter: blur(5px); margin-bottom: 15px; }}
            [data-testid="stMetricLabel"] p {{ color: var(--v-copper) !important; font-weight: 700 !important; letter-spacing: 1px !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.9); }}
            [data-testid="stMetricValue"] div {{ color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace !important; text-shadow: 2px 2px 5px rgba(0,0,0,0.9); }}
        </style>
    """, unsafe_allow_html=True)

def navigate_to(page_name):
    st.session_state.active_module = page_name

# --- 5. GŁÓWNA LOGIKA HUB-A ---
def main_hub():
    inject_hub_theme()
    
    if "global_auth" not in st.session_state: st.session_state.global_auth = False
    if "username" not in st.session_state: st.session_state.username = "UNAUTHORIZED"
    if "role" not in st.session_state: st.session_state.role = "BRAK"
    if "active_module" not in st.session_state: st.session_state.active_module = "PULPIT (DASHBOARD)"

    # --- EKRAN LOGOWANIA ---
    if not st.session_state.global_auth:
        _, col, _ = st.columns([0.8, 2, 0.8])
        with col:
            video_path = os.path.join("assets", "video 1.mp4")
            if os.path.exists(video_path): st.video(video_path, autoplay=True, muted=True, loop=False)
            else: st.markdown("<br><br>", unsafe_allow_html=True)
            
            st.markdown("<h1 style='text-align:center;'>VORTEZA TMS LOGIN</h1>", unsafe_allow_html=True)
            with st.form("ApexAuth"):
                user_input = st.text_input("NAZWA UŻYTKOWNIKA (IMIĘ)")
                pwd_input = st.text_input("HASŁO DOSTĘPU", type="password")
                role_input = st.selectbox("STANOWISKO", ["SPEDYTOR / LOGISTYKA", "KIEROWCA"])
                
                if st.form_submit_button("VALIDATE ACCESS"):
                    # W docelowej wersji możesz tu podpiąć logikę weryfikacji po użytkownikach
                    if pwd_input == st.secrets["password"]:
                        st.session_state.global_auth = True
                        st.session_state.username = user_input.upper() if user_input else "OPERATOR"
                        st.session_state.role = role_input
                        
                        # Przekierowanie zależne od roli
                        if role_input == "KIEROWCA":
                            st.session_state.active_module = "FLOTA (BASE)"
                        else:
                            st.session_state.active_module = "PULPIT (DASHBOARD)"
                        st.rerun()
                    else: st.error("ACCESS DENIED: INVALID KEY")
        return

    # --- UKRYCIE SIDEBARU NA PULPICIE GŁÓWNYM ---
    if st.session_state.active_module == "PULPIT (DASHBOARD)":
        st.markdown("""<style>[data-testid="collapsedControl"] { display: none !important; } section[data-testid="stSidebar"] { display: none !important; }</style>""", unsafe_allow_html=True)
    else:
        with st.sidebar:
            logo_path = os.path.join("assets", "logo_vorteza.png")
            if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
            else: st.markdown("<h2 style='letter-spacing:10px; text-align:center;'>VORTEZA</h2>", unsafe_allow_html=True)
                
            st.markdown("<div style='text-align:center;'><span class='v-status-glow'>● SYSTEM STATUS: ONLINE</span></div>", unsafe_allow_html=True)
            st.divider()
            
            # --- NAWIGACJA ZALEŻNA OD ROLI ---
            if st.session_state.role == "KIEROWCA":
                st.markdown("### PANEL KIEROWCY")
                st.button("TERMINAL MOBILNY (BASE)", key="sb_nav_base_driver", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)
            else:
                c1, c2 = st.columns([1, 4])
                with c1:
                    icon_path_home = os.path.join("assets", "home.jpg")
                    if os.path.exists(icon_path_home): st.image(icon_path_home)
                with c2: st.button("PULPIT (DASHBOARD)", key="sb_nav_dash", on_click=navigate_to, args=("PULPIT (DASHBOARD)",), use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                c1, c2 = st.columns([1, 4])
                with c1: st.markdown("""<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 100%; filter: drop-shadow(0px 0px 3px #B58863);"><path d="M12 2L3 7L12 12L21 7L12 2Z" stroke="#B58863" stroke-width="2" stroke-linejoin="round"/><path d="M3 12L12 17L21 12" stroke="#B58863" stroke-width="2" stroke-linejoin="round"/><path d="M3 17L12 22L21 17" stroke="#B58863" stroke-width="2" stroke-linejoin="round"/></svg>""", unsafe_allow_html=True)
                with c2: st.button("ZLECENIA I SPEDYCJA", key="sb_nav_core", on_click=navigate_to, args=("ZLECENIA (CORE)",), use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1:
                    icon_path_stack = os.path.join("assets", "icon_stack.png")
                    if os.path.exists(icon_path_stack): st.image(icon_path_stack)
                with c2: st.button("PLANER 3D (STACK)", key="sb_nav_stack", on_click=navigate_to, args=("PLANER 3D (STACK)",), use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1:
                    icon_path_flow = os.path.join("assets", "icon_flow.png")
                    if os.path.exists(icon_path_flow): st.image(icon_path_flow)
                with c2: st.button("FINANSE (FLOW)", key="sb_nav_flow", on_click=navigate_to, args=("FINANSE (FLOW)",), use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1:
                    icon_path_base = os.path.join("assets", "icon_base.png")
                    if os.path.exists(icon_path_base): st.image(icon_path_base)
                with c2: st.button("FLOTA (BASE)", key="sb_nav_base", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)

            st.divider()
            st.markdown(f"**UŻYTKOWNIK:** {st.session_state.username}")
            st.markdown(f"**ROLA:** {st.session_state.role}")
            if st.button("WYLOGUJ Z SYSTEMU", key="sb_logout"):
                st.session_state.global_auth = False
                st.session_state.username = "UNAUTHORIZED"
                st.session_state.role = "BRAK"
                st.rerun()

    # --- RENDEROWANIE MODUŁÓW ---
    if st.session_state.active_module == "PULPIT (DASHBOARD)" and st.session_state.role != "KIEROWCA":
        st.markdown("<h1>DASHBOARD SPEDYTORA</h1>", unsafe_allow_html=True)
        banner_path = os.path.join("assets", "baner 1.jpg")
        if os.path.exists(banner_path):
            _, b_col, _ = st.columns([1, 2, 1])
            with b_col: st.image(banner_path, use_container_width=True)
                
        st.markdown("---")
        s = get_dashboard_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("KURS EURO (V)", f"{s['euro']} PLN")
        c2.metric("BAZA JEDNOSTEK", s["skus"])
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        m0, m1, m2, m3 = st.columns(4)
        with m0:
            st.markdown("""<div class='module-card'><svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 45%; max-width: 150px; display: block; margin: 0 auto; filter: drop-shadow(0px 0px 10px rgba(181,136,99,0.5));"><path d="M12 2L3 7L12 12L21 7L12 2Z" stroke="#B58863" stroke-width="1.5" stroke-linejoin="round"/><path d="M3 12L12 17L21 12" stroke="#B58863" stroke-width="1.5" stroke-linejoin="round"/><path d="M3 17L12 22L21 17" stroke="#B58863" stroke-width="1.5" stroke-linejoin="round"/></svg><h4 style='text-align:center; font-size: 1.1rem; margin-top: 15px;'>ZLECENIA</h4></div>""", unsafe_allow_html=True)
            st.button("URUCHOM CORE", key="btn_go_core", on_click=navigate_to, args=("ZLECENIA (CORE)",), use_container_width=True)
        with m1:
            icon_b64 = get_base64_of_bin_file(os.path.join("assets", "icon_stack.png"))
            img_html = f"<img src='data:image/png;base64,{icon_b64}' style='width: 45%; max-width: 150px; display: block; margin: 0 auto;'/>" if icon_b64 else ""
            st.markdown(f"<div class='module-card'>{img_html}<h4 style='text-align:center; font-size: 1.1rem; margin-top: 15px;'>PLANER 3D</h4></div>", unsafe_allow_html=True)
            st.button("URUCHOM STACK", key="btn_go_stack", on_click=navigate_to, args=("PLANER 3D (STACK)",), use_container_width=True)
        with m2:
            icon_b64 = get_base64_of_bin_file(os.path.join("assets", "icon_flow.png"))
            img_html = f"<img src='data:image/png;base64,{icon_b64}' style='width: 45%; max-width: 150px; display: block; margin: 0 auto;'/>" if icon_b64 else ""
            st.markdown(f"<div class='module-card'>{img_html}<h4 style='text-align:center; font-size: 1.1rem; margin-top: 15px;'>FINANSE</h4></div>", unsafe_allow_html=True)
            st.button("URUCHOM FLOW", key="btn_go_flow", on_click=navigate_to, args=("FINANSE (FLOW)",), use_container_width=True)
        with m3:
            icon_b64 = get_base64_of_bin_file(os.path.join("assets", "icon_base.png"))
            img_html = f"<img src='data:image/png;base64,{icon_b64}' style='width: 45%; max-width: 150px; display: block; margin: 0 auto;'/>" if icon_b64 else ""
            st.markdown(f"<div class='module-card'>{img_html}<h4 style='text-align:center; font-size: 1.1rem; margin-top: 15px;'>FLOTA</h4></div>", unsafe_allow_html=True)
            st.button("URUCHOM BASE", key="btn_go_base", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)

    elif st.session_state.active_module == "ZLECENIA (CORE)" and st.session_state.role != "KIEROWCA": run_core()
    elif st.session_state.active_module == "PLANER 3D (STACK)" and st.session_state.role != "KIEROWCA": run_stack()
    elif st.session_state.active_module == "FINANSE (FLOW)" and st.session_state.role != "KIEROWCA": run_flow()
    elif st.session_state.active_module == "FLOTA (BASE)": run_base()

if __name__ == "__main__":
    main_hub()
