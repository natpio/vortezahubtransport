# -*- coding: utf-8 -*-
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
    from vorteza_admin import run_admin
except ImportError as e:
    st.error(f"KRYTYCZNY BŁĄD IMPORTU: {e}")

# --- 2. KONFIGURACJA ---
st.set_page_config(page_title="VORTEZA TMS v25.0", layout="wide", initial_sidebar_state="expanded", page_icon="🕋")
SHEET_ID = "1Arq4WTFcvbvH7JkMEMWpWkGjaN44J4UpgJ2T9lKQLn8"

@st.cache_resource
def get_gspread_client():
    try:
        creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
        credentials = Credentials.from_service_account_info(
            creds_info, 
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Błąd konfiguracji Google Auth: {e}")
        return None

@st.cache_data
def get_base64_of_bin_file(bin_file):
    try:
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as f: return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

@st.cache_data(ttl=300)
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

def authenticate_user(username, password):
    if username.strip().upper() == "MASTER" and password == st.secrets.get("password", ""):
        return "ADMINISTRATOR / SZEF"
    client = get_gspread_client()
    if not client: return None
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet("Uzytkownicy")
        records = sheet.get_all_records()
        for row in records:
            if str(row.get('Login', '')).strip().lower() == username.strip().lower():
                if str(row.get('Haslo', '')).strip() == password.strip():
                    status = str(row.get('Status', '')).strip().upper()
                    if status == "AKTYWNY": return str(row.get('Rola', ''))
                    else: return "BLOCKED"
        return None
    except: return None

# --- 4. SILNIK WIZUALNY (FULL FIX + MIEDZIANY COLOR) ---
def inject_hub_theme():
    bg_b64 = get_base64_of_bin_file(os.path.join("assets", "tlo_hub_2.jpg"))
    bg_style = f".stApp {{ background: linear-gradient(rgba(6, 6, 6, 0.85), rgba(6, 6, 6, 0.85)), url('data:image/jpeg;base64,{bg_b64}') !important; background-size: cover !important; background-attachment: fixed !important; }}" if bg_b64 else ".stApp { background-color: #060606; }"

    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&family=JetBrains+Mono&display=swap');
            {bg_style}
            
            /* USUNIĘCIE BRANDINGU I BIAŁEGO PASKA */
            header {{ visibility: hidden !important; display: none !important; height: 0px !important; }}
            [data-testid="stHeader"] {{ visibility: hidden !important; display: none !important; height: 0px !important; }}
            footer {{ visibility: hidden !important; display: none !important; }}
            #MainMenu {{ visibility: hidden !important; display: none !important; }}
            .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; margin-top: 0 !important; }}
            div[data-testid="stAppViewBlockContainer"] {{ padding-top: 1rem !important; }}

            /* ANTY-LAG: BLOKADA SZARZENIA */
            *[data-stale="true"], div[data-stale="true"], button[data-stale="true"] {{
                opacity: 1 !important;
                filter: none !important;
                transition: none !important;
            }}

            /* MIEDZIANY KOLOR CZCIONKI (LABEL, SIDEBAR, P) */
            .stApp {{ color: #FFFFFF; font-family: 'Montserrat', sans-serif; }}
            label, p, span, [data-testid="stWidgetLabel"] p {{ color: #B58863 !important; font-weight: 700 !important; }}
            div[data-testid="stRadio"] label p {{ color: #B58863 !important; }}
            
            section[data-testid="stSidebar"] {{ 
                background-color: rgba(3, 3, 3, 0.95) !important; 
                border-right: 1px solid rgba(181, 136, 99, 0.3); 
                width: 350px !important; 
                backdrop-filter: blur(10px); 
            }}
            
            h1, h2, h3, h4 {{ color: #B58863 !important; text-transform: uppercase; letter-spacing: 6px !important; font-weight: 700 !important; }}
            
            .stButton>button {{ background-color: rgba(10,10,10,0.8) !important; color: #B58863 !important; border: 1px solid #B58863 !important; width: 100%; transition: 0.4s; font-weight: bold; }}
            .stButton>button:hover {{ background-color: #B58863 !important; color: black !important; }}
            
            .module-card {{ background: rgba(10, 10, 10, 0.75); border: 1px solid rgba(181, 136, 99, 0.4); border-top: 3px solid #B58863; padding: 20px; border-radius: 8px; text-align: center; backdrop-filter: blur(5px); margin-bottom: 15px; }}
            [data-testid="stMetricLabel"] p {{ color: #B58863 !important; font-weight: 700 !important; }}
            [data-testid="stMetricValue"] div {{ color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace !important; }}
        </style>
    """, unsafe_allow_html=True)

def navigate_to(page_name): st.session_state.active_module = page_name

@st.fragment(run_every="10s")
def live_notification_listener():
    path = os.path.join("data", "live_notif.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f: notifs = json.load(f)
            if "last_notif_count" not in st.session_state: st.session_state.last_notif_count = len(notifs)
            if len(notifs) > st.session_state.last_notif_count:
                for i in range(len(notifs) - st.session_state.last_notif_count):
                    n = notifs[st.session_state.last_notif_count + i]
                    st.toast(f"**ALARM FLOTY ({n['time']})**\n\n{n['msg']}", icon="🔔")
                st.session_state.last_notif_count = len(notifs)
        except: pass

# --- 5. GŁÓWNA LOGIKA HUB-A ---
def main_hub():
    inject_hub_theme()
    
    if "global_auth" not in st.session_state: st.session_state.global_auth = False
    if "username" not in st.session_state: st.session_state.username = "UNAUTHORIZED"
    if "role" not in st.session_state: st.session_state.role = "BRAK"
    if "active_module" not in st.session_state: st.session_state.active_module = "PULPIT (DASHBOARD)"

    if not st.session_state.global_auth:
        _, col, _ = st.columns([0.8, 2, 0.8])
        with col:
            video_path = os.path.join("assets", "video 1.mp4")
            if os.path.exists(video_path): st.video(video_path, autoplay=True, muted=True, loop=False)
            st.markdown("<h1 style='text-align:center;'>VORTEZA TMS LOGIN</h1>", unsafe_allow_html=True)
            with st.form("ApexAuth"):
                user_input = st.text_input("NAZWA UŻYTKOWNIKA (LOGIN)")
                pwd_input = st.text_input("HASŁO DOSTĘPU", type="password")
                if st.form_submit_button("ZALOGUJ DO SYSTEMU"):
                    if user_input and pwd_input:
                        role = authenticate_user(user_input, pwd_input)
                        if role == "BLOCKED": st.error("KONTO ZABLOKOWANE.")
                        elif role:
                            st.session_state.global_auth = True
                            st.session_state.username = user_input.upper()
                            st.session_state.role = role
                            st.session_state.active_module = "FLOTA (BASE)" if role == "KIEROWCA" else "PULPIT (DASHBOARD)"
                            st.rerun()
                        else: st.error("Nieprawidłowy login lub hasło!")
        return

    if st.session_state.active_module == "PULPIT (DASHBOARD)":
        st.markdown("""<style>[data-testid="collapsedControl"] { display: none !important; } section[data-testid="stSidebar"] { display: none !important; }</style>""", unsafe_allow_html=True)
    else:
        with st.sidebar:
            # PRZYWRÓCONY UKŁAD IKONEK W SIDEBARZE
            logo_path = os.path.join("assets", "logo_vorteza.png")
            if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
            else: st.markdown("<h2 style='text-align:center;'>VORTEZA</h2>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;'><span style='color: #00FF41; font-family: JetBrains Mono; font-size: 0.8rem;'>● SYSTEM STATUS: ONLINE</span></div>", unsafe_allow_html=True)
            st.divider()
            
            if st.session_state.role == "KIEROWCA":
                st.markdown("### PANEL KIEROWCY")
                st.button("TERMINAL MOBILNY (BASE)", key="sb_nav_base_driver", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)
            else:
                # PRZYWRÓCONE MAŁE IKONKI NAWIGACYJNE
                c1, c2 = st.columns([1, 4])
                with c1: st.image(os.path.join("assets", "home.jpg"))
                with c2: st.button("PULPIT", key="sb_nav_dash", on_click=navigate_to, args=("PULPIT (DASHBOARD)",), use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1: st.markdown("""<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 100%; filter: drop-shadow(0px 0px 3px #B58863);"><path d="M12 2L3 7L12 12L21 7L12 2Z" stroke="#B58863" stroke-width="2" stroke-linejoin="round"/><path d="M3 12L12 17L21 12" stroke="#B58863" stroke-width="2" stroke-linejoin="round"/><path d="M3 17L12 22L21 17" stroke="#B58863" stroke-width="2" stroke-linejoin="round"/></svg>""", unsafe_allow_html=True)
                with c2: st.button("ZLECENIA", key="sb_nav_core", on_click=navigate_to, args=("ZLECENIA (CORE)",), use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1: st.image(os.path.join("assets", "icon_stack.png"))
                with c2: st.button("PLANER 3D", key="sb_nav_stack", on_click=navigate_to, args=("PLANER 3D (STACK)",), use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1: st.image(os.path.join("assets", "icon_flow.png"))
                with c2: st.button("FINANSE", key="sb_nav_flow", on_click=navigate_to, args=("FINANSE (FLOW)",), use_container_width=True)
                
                c1, c2 = st.columns([1, 4])
                with c1: st.image(os.path.join("assets", "icon_base.png"))
                with c2: st.button("FLOTA", key="sb_nav_base", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)

                if st.session_state.role == "ADMINISTRATOR / SZEF":
                    st.divider()
                    st.button("📊 RAPORTY I KADRY", on_click=navigate_to, args=("RAPORTY (ADMIN)",), use_container_width=True)

            st.divider()
            st.markdown(f"**UŻYTKOWNIK:** {st.session_state.username}")
            if st.button("WYLOGUJ"): 
                st.session_state.global_auth = False
                st.rerun()

    if st.session_state.global_auth and st.session_state.role != "KIEROWCA":
        live_notification_listener()

    if st.session_state.active_module == "PULPIT (DASHBOARD)":
        st.markdown("<h1>DASHBOARD SPEDYTORA</h1>", unsafe_allow_html=True)
        banner_path = os.path.join("assets", "baner 1.jpg")
        if os.path.exists(banner_path): st.image(banner_path, use_container_width=True)
        
        st.markdown("---")
        s = get_dashboard_stats()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("KURS EURO", f"{s['euro']} PLN")
        c2.metric("BAZA JEDNOSTEK", s["skus"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        m0, m1, m2, m3 = st.columns(4)
        # Przywrócone Base64 dla kart na Dashboardzie
        with m0:
            st.markdown("""<div class='module-card'><svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 45%; display: block; margin: 0 auto; filter: drop-shadow(0px 0px 5px #B58863);"><path d="M12 2L3 7L12 12L21 7L12 2Z" stroke="#B58863" stroke-width="1.5" stroke-linejoin="round"/><path d="M3 12L12 17L21 12" stroke="#B58863" stroke-width="1.5" stroke-linejoin="round"/><path d="M3 17L12 22L21 17" stroke="#B58863" stroke-width="1.5" stroke-linejoin="round"/></svg><h4>ZLECENIA</h4></div>""", unsafe_allow_html=True)
            st.button("URUCHOM CORE", key="btn_go_core", on_click=navigate_to, args=("ZLECENIA (CORE)",), use_container_width=True)
        with m1:
            icon_b64 = get_base64_of_bin_file(os.path.join("assets", "icon_stack.png"))
            img_html = f"<img src='data:image/png;base64,{icon_b64}' style='width: 45%; display: block; margin: 0 auto;'/>" if icon_b64 else ""
            st.markdown(f"<div class='module-card'>{img_html}<h4>PLANER 3D</h4></div>", unsafe_allow_html=True)
            st.button("URUCHOM STACK", key="btn_go_stack", on_click=navigate_to, args=("PLANER 3D (STACK)",), use_container_width=True)
        with m2:
            icon_b64 = get_base64_of_bin_file(os.path.join("assets", "icon_flow.png"))
            img_html = f"<img src='data:image/png;base64,{icon_b64}' style='width: 45%; display: block; margin: 0 auto;'/>" if icon_b64 else ""
            st.markdown(f"<div class='module-card'>{img_html}<h4>FINANSE</h4></div>", unsafe_allow_html=True)
            st.button("URUCHOM FLOW", key="btn_go_flow", on_click=navigate_to, args=("FINANSE (FLOW)",), use_container_width=True)
        with m3:
            icon_b64 = get_base64_of_bin_file(os.path.join("assets", "icon_base.png"))
            img_html = f"<img src='data:image/png;base64,{icon_b64}' style='width: 45%; display: block; margin: 0 auto;'/>" if icon_b64 else ""
            st.markdown(f"<div class='module-card'>{img_html}<h4>FLOTA</h4></div>", unsafe_allow_html=True)
            st.button("URUCHOM BASE", key="btn_go_base", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)

    elif st.session_state.active_module == "ZLECENIA (CORE)": run_core()
    elif st.session_state.active_module == "PLANER 3D (STACK)": run_stack()
    elif st.session_state.active_module == "FINANSE (FLOW)": run_flow()
    elif st.session_state.active_module == "FLOTA (BASE)": run_base()
    elif st.session_state.active_module == "RAPORTY (ADMIN)": run_admin()

if __name__ == "__main__":
    main_hub()
