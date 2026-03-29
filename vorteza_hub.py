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
    st.error(f"KRYTYCZNY BŁĄD IMPORTU: Upewnij się, że wszystkie pliki modułów są w folderze. Szczegóły: {e}")

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

# --- 3. SILNIK AUTORYZACJI Z GOOGLE SHEETS ---
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
    except Exception as e:
        st.error(f"Błąd autoryzacji bazy: {e}")
        return None

# --- 4. SILNIK WIZUALNY (FULL FIX) ---
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

            /* KOLOR CZCIONKI: MIEDZIANY DLA ETYKIET I SIDEBARA */
            label, [data-testid="stWidgetLabel"] p, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{ 
                color: #B58863 !important; 
                font-weight: 700 !important; 
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            /* Tekst w Radio Buttonach */
            div[data-testid="stRadio"] label p {{ color: #B58863 !important; }}

            .stApp {{ color: #FFFFFF; font-family: 'Montserrat', sans-serif; }}
            section[data-testid="stSidebar"] {{ background-color: rgba(3, 3, 3, 0.95) !important; border-right: 1px solid rgba(181, 136, 99, 0.3); width: 350px !important; backdrop-filter: blur(10px); }}
            h1, h2, h3, h4 {{ color: #B58863 !important; text-transform: uppercase; letter-spacing: 6px !important; font-weight: 700 !important; }}
            
            .stButton>button {{ background-color: rgba(10,10,10,0.8) !important; color: #B58863 !important; border: 1px solid #B58863 !important; width: 100%; transition: 0.4s; }}
            .stButton>button:hover {{ background-color: #B58863 !important; color: black !important; }}
            
            .module-card {{ background: rgba(10, 10, 10, 0.75); border: 1px solid rgba(181, 136, 99, 0.4); border-top: 3px solid #B58863; padding: 20px; border-radius: 8px; text-align: center; backdrop-filter: blur(5px); margin-bottom: 15px; }}
            [data-testid="stMetricLabel"] p {{ color: #B58863 !important; font-weight: 700 !important; letter-spacing: 1px !important; }}
            [data-testid="stMetricValue"] div {{ color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace !important; }}
        </style>
    """, unsafe_allow_html=True)

def navigate_to(page_name): st.session_state.active_module = page_name

# --- NASŁUCHIWACZ POWIADOMIEŃ ---
@st.fragment(run_every="10s")
def live_notification_listener():
    path = os.path.join("data", "live_notif.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                notifs = json.load(f)
            if "last_notif_count" not in st.session_state:
                st.session_state.last_notif_count = len(notifs)
            current_count = len(notifs)
            if current_count > st.session_state.last_notif_count:
                new_notifs_count = current_count - st.session_state.last_notif_count
                for i in range(new_notifs_count):
                    n = notifs[st.session_state.last_notif_count + i]
                    st.toast(f"**ALARM FLOTY ({n['time']})**\n\n{n['msg']}", icon="🔔")
                st.session_state.last_notif_count = current_count
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
            else: st.markdown("<br><br>", unsafe_allow_html=True)
            
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
                            if role == "KIEROWCA": st.session_state.active_module = "FLOTA (BASE)"
                            elif role == "ADMINISTRATOR / SZEF": st.session_state.active_module = "RAPORTY (ADMIN)"
                            else: st.session_state.active_module = "PULPIT (DASHBOARD)"
                            st.rerun()
                        else: st.error("Nieprawidłowy login lub hasło!")
        return

    # Ukrywanie paska bocznego na Dashboardzie
    if st.session_state.active_module == "PULPIT (DASHBOARD)":
        st.markdown("""<style>[data-testid="collapsedControl"] { display: none !important; } section[data-testid="stSidebar"] { display: none !important; }</style>""", unsafe_allow_html=True)
    else:
        with st.sidebar:
            logo_path = os.path.join("assets", "logo_vorteza.png")
            if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
            else: st.markdown("<h2 style='text-align:center;'>VORTEZA</h2>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;'><span style='color: #00FF41; font-family: JetBrains Mono; font-size: 0.8rem;'>● SYSTEM STATUS: ONLINE</span></div>", unsafe_allow_html=True)
            st.divider()
            
            if st.session_state.role == "KIEROWCA":
                st.button("TERMINAL MOBILNY (BASE)", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)
            else:
                st.button("PULPIT (DASHBOARD)", on_click=navigate_to, args=("PULPIT (DASHBOARD)",), use_container_width=True)
                st.button("ZLECENIA I SPEDYCJA", on_click=navigate_to, args=("ZLECENIA (CORE)",), use_container_width=True)
                st.button("PLANER 3D (STACK)", on_click=navigate_to, args=("PLANER 3D (STACK)",), use_container_width=True)
                st.button("FINANSE (FLOW)", on_click=navigate_to, args=("FINANSE (FLOW)",), use_container_width=True)
                st.button("FLOTA (BASE)", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)
                if st.session_state.role == "ADMINISTRATOR / SZEF":
                    st.button("📊 RAPORTY I KADRY", on_click=navigate_to, args=("RAPORTY (ADMIN)",), use_container_width=True)

            st.divider()
            st.markdown(f"**UŻYTKOWNIK:** {st.session_state.username}")
            if st.button("WYLOGUJ"):
                st.session_state.global_auth = False
                st.rerun()

    if st.session_state.global_auth and st.session_state.role != "KIEROWCA":
        live_notification_listener()

    # Renderowanie modułów
    if st.session_state.active_module == "PULPIT (DASHBOARD)":
        st.markdown("<h1>DASHBOARD SPEDYTORA</h1>", unsafe_allow_html=True)
        banner_path = os.path.join("assets", "baner 1.jpg")
        if os.path.exists(banner_path): st.image(banner_path, use_container_width=True)
        s = get_dashboard_stats()
        c1, c2 = st.columns(2)
        c1.metric("KURS EURO (V)", f"{s['euro']} PLN")
        c2.metric("BAZA JEDNOSTEK", s["skus"])
        
        # Przyciski szybkiego startu na dashboardzie
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.button("URUCHOM CORE", on_click=navigate_to, args=("ZLECENIA (CORE)",), use_container_width=True)
        with m2: st.button("URUCHOM STACK", on_click=navigate_to, args=("PLANER 3D (STACK)",), use_container_width=True)
        with m3: st.button("URUCHOM FLOW", on_click=navigate_to, args=("FINANSE (FLOW)",), use_container_width=True)
        with m4: st.button("URUCHOM BASE", on_click=navigate_to, args=("FLOTA (BASE)",), use_container_width=True)

    elif st.session_state.active_module == "ZLECENIA (CORE)": run_core()
    elif st.session_state.active_module == "PLANER 3D (STACK)": run_stack()
    elif st.session_state.active_module == "FINANSE (FLOW)": run_flow()
    elif st.session_state.active_module == "FLOTA (BASE)": run_base()
    elif st.session_state.active_module == "RAPORTY (ADMIN)": run_admin()

if __name__ == "__main__":
    main_hub()
