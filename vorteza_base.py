# -*- coding: utf-8 -*-
import streamlit as st
import json
import base64
import gspread
import pandas as pd
import os
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================================================
# 1. KONFIGURACJA ŚCIEŻEK I ZASOBÓW
# =========================================================
PATH_CHECKLIST = os.path.join("data", "lista_kontrolna.json")
PATH_BG = os.path.join("assets", "tlo_hub_2.jpg")
SHEET_ID = "1Arq4WTFcvbvH7JkMEMWpWkGjaN44J4UpgJ2T9lKQLn8"
UPLOAD_DIR = os.path.join("data", "uploads")

# Upewniamy się, że folder na skany CMR istnieje
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_vorteza_asset_b64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

def load_checklist_local():
    if os.path.exists(PATH_CHECKLIST):
        with open(PATH_CHECKLIST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# =========================================================
# 2. SILNIK GOOGLE SHEETS
# =========================================================
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(credentials)

def load_sheet_data(worksheet_name):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(worksheet_name)
        return pd.DataFrame(sheet.get_all_records())
    except Exception as e:
        return pd.DataFrame()

def save_to_sheet(worksheet_name, row_data):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(worksheet_name)
        sheet.append_row(row_data)
        return True
    except: return False

def update_carrier_status(nip, new_status):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Przewoznicy")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('NIP')) == str(nip):
                sheet.update_cell(i + 2, 8, new_status)
                return True
        return False
    except: return False

def update_driver_order(order_id, new_status, file_name=""):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                row_idx = i + 2
                sheet.update_cell(row_idx, 2, new_status) 
                if file_name:
                    sheet.update_cell(row_idx, 20, str(file_name)) 
                return True
        return False
    except Exception as e:
        st.error(f"Błąd aktualizacji bazy: {e}")
        return False

# =========================================================
# 3. INTERFEJS I STYLIZACJA
# =========================================================
def apply_base_theme():
    bg_data = load_vorteza_asset_b64(PATH_BG)
    bg_style = f"""
        .stApp {{
            background: linear-gradient(rgba(6, 6, 6, 0.90), rgba(6, 6, 6, 0.90)), 
                        url("data:image/jpeg;base64,{bg_data}") !important;
            background-size: cover !important; background-attachment: fixed !important;
        }}
    """ if bg_data else ".stApp { background-color: #060606 !important; }"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;700&family=JetBrains+Mono&display=swap');
        {bg_style}
        h2, h3, h4 {{ color: #B58863 !important; text-transform: uppercase; letter-spacing: 4px !important; font-weight: 700 !important; }}
        .log-entry {{ background-color: rgba(15, 15, 15, 0.85) !important; border: 1px solid rgba(181, 136, 99, 0.3); border-left: 5px solid #B58863 !important; padding: 15px; margin-bottom: 15px; border-radius: 4px; }}
        .log-entry-alert {{ border-left: 5px solid #FF4B4B !important; }}
        .carrier-card {{ background: rgba(20, 20, 20, 0.9); border: 1px solid #333; border-left: 4px solid #2980B9; padding: 15px; margin-bottom: 15px; border-radius: 6px; }}
        .carrier-active {{ border-left-color: #27AE60 !important; }}
        .carrier-blocked {{ border-left-color: #FF4B4B !important; opacity: 0.7; }}
        div[data-testid="stButton"] button {{ border-color: #B58863 !important; color: #B58863 !important; background: transparent !important; }}
        div[data-testid="stButton"] button:hover {{ background: #B58863 !important; color: #000 !important; }}
        .btn-action div[data-testid="stButton"] button {{ background: rgba(181, 136, 99, 0.2) !important; border: 1px solid #B58863 !important; }}
        
        /* STYLIZACJA KIEROWCY */
        div[data-testid="stRadio"] label p {{ color: #B58863 !important; font-weight: bold !important; font-size: 0.95rem !important; letter-spacing: 0.5px; }}
        div[data-testid="stCheckbox"] label p {{ color: #B58863 !important; font-size: 0.95rem !important; font-weight: bold !important; }}
        div[data-testid="stWidgetLabel"] p {{ color: #B58863 !important; font-weight: bold !important; letter-spacing: 1px; }}
        div[data-testid="stExpander"] details summary p {{ color: #B58863 !important; font-weight: bold !important; letter-spacing: 1px; text-transform: uppercase; }}
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# 4. GŁÓWNA FUNKCJA MODUŁU
# =========================================================
def run_base():
    apply_base_theme()
    current_user = st.session_state.get("username", "OPERATOR")
    current_role = st.session_state.get("role", "BRAK")
    
    st.markdown("<h2>VORTEZA BASE | KONSOLA FLOTY</h2>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🎛️ PANEL STEROWANIA")
        
        if current_role == "KIEROWCA":
            mode = st.radio("WYBIERZ MODUŁ:", [
                "📋 KARTA DROGOWA (INSPEKCJA)",
                "🚚 MOJE TRASY (ZADANIA)"
            ], label_visibility="collapsed")
        else:
            mode = st.radio("WYBIERZ MODUŁ:", [
                "🤝 BAZA PRZEWOŹNIKÓW", 
                "🚛 RAPORTY FLOTY (WŁASNEJ)"
            ], label_visibility="collapsed")
        st.divider()

    # =========================================================
    # WIDOKI DLA LOGISTYKA / SPEDYTORA
    # =========================================================
    if mode == "🤝 BAZA PRZEWOŹNIKÓW":
        c1, c2 = st.columns([2, 1])
        with c1: st.markdown("### 📇 REJESTR PODWYKONAWCÓW")
        with c2:
            with st.expander("➕ DODAJ NOWEGO PRZEWOŹNIKA"):
                with st.form("new_carrier_form", clear_on_submit=True):
                    nip = st.text_input("NIP")
                    nazwa = st.text_input("NAZWA FIRMY")
                    kontakt = st.text_input("OSOBA KONTAKTOWA (DYSPOZYTOR)")
                    tel = st.text_input("TELEFON")
                    email = st.text_input("E-MAIL")
                    ocp = st.date_input("OCP WAŻNE DO")
                    uwagi = st.text_area("UWAGI (np. kierunki, tabor)")
                    if st.form_submit_button("ZAPISZ W BAZIE"):
                        if nip and nazwa:
                            if save_to_sheet("Przewoznicy", [nip, nazwa, kontakt, tel, email, str(ocp), uwagi, "AKTYWNY"]):
                                st.success("Przewoźnik dodany do bazy!"); st.rerun()
                            else: st.error("Błąd zapisu!")
                        else: st.error("Wypełnij przynajmniej NIP i Nazwę!")

        df_c = load_sheet_data("Przewoznicy")
        if df_c.empty: st.info("Baza przewoźników jest pusta.")
        else:
            search_query = st.text_input("🔍 Wyszukaj przewoźnika (Nazwa lub NIP)...")
            if search_query: df_c = df_c[df_c['Nazwa'].astype(str).str.contains(search_query, case=False) | df_c['NIP'].astype(str).str.contains(search_query, case=False)]
            
            for _, row in df_c.iterrows():
                nip_val = str(row.get('NIP', ''))
                status = str(row.get('Status', 'AKTYWNY'))
                ocp_str = str(row.get('OCP_Wazne_Do', ''))
                ocp_alert = ""
                try:
                    if ocp_str:
                        ocp_date = datetime.strptime(ocp_str, "%Y-%m-%d").date()
                        if ocp_date < datetime.now().date():
                            ocp_alert = "<span style='color:#FF4B4B; font-weight:bold;'> ⚠️ OCP NIEWAŻNE!</span>"
                            status = "ZABLOKOWANY" 
                except: pass

                card_class = "carrier-card carrier-active" if status == "AKTYWNY" else "carrier-card carrier-blocked"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#FFFFFF; font-size:1.1rem; font-weight:bold;">{row.get('Nazwa', '-')} (NIP: {nip_val})</span>
                        <span style="font-family:'JetBrains Mono'; font-size:0.9rem;">STATUS: {status}</span>
                    </div>
                    <div style="color:#AAAAAA; font-size:0.9rem; margin-top:8px; line-height:1.4;">
                        <b>Dyspozytor:</b> {row.get('Kontakt', '-')} | <b>Tel:</b> {row.get('Telefon', '-')} | <b>E-mail:</b> {row.get('Email', '-')}<br>
                        <b>Ważność OCP:</b> {ocp_str} {ocp_alert}<br>
                        <b>Uwagi:</b> {row.get('Uwagi', '-')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if status == "AKTYWNY":
                    if st.button("🚫 ZABLOKUJ (BRAK OCP)", key=f"blk_{nip_val}"): update_carrier_status(nip_val, "ZABLOKOWANY"); st.rerun()
                else:
                    if st.button("✅ ODBLOKUJ", key=f"unb_{nip_val}"): update_carrier_status(nip_val, "AKTYWNY"); st.rerun()

    elif mode == "🚛 RAPORTY FLOTY (WŁASNEJ)":
        st.markdown("### 📋 DZIENNIK KONTROLI TABORU")
        df_f = load_sheet_data("Flota")
        if df_f.empty: st.info("Brak aktywnych logów dla własnej floty.")
        else:
            for idx, row in df_f.iloc[::-1].iterrows(): 
                is_alert = "ALERT" in str(row.get('Status', ''))
                entry_class = "log-entry log-entry-alert" if is_alert else "log-entry"
                st.markdown(f"""
                <div class="{entry_class}">
                    <b style="color:#B58863; font-size:1.1rem;">POJAZD: {row.get('Pojazd', 'N/A')}</b> | Data: {row.get('Data', 'N/A')} | OP: {row.get('Operator', 'N/A')}<br>
                    <span style="color:{'#FF4B4B' if is_alert else '#00FF41'}">STATUS INSPEKCJI: {row.get('Status', 'NOMINAL')}</span><br>
                    <span style="color:#AAA; font-size:0.85rem;">Przebieg: {row.get('Przebieg', 0)} km | Uwagi: {row.get('Uwagi', '-')}</span>
                </div>
                """, unsafe_allow_html=True)

    # =========================================================
    # WIDOKI DLA KIEROWCY
    # =========================================================
    elif mode == "📋 KARTA DROGOWA (INSPEKCJA)":
        st.markdown("### 🛠️ KARTA KONTROLNA POJAZDU")
        data_gh = load_checklist_local()
        
        with st.form("driver_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1: r_plate = st.text_input("NUMER REJESTRACYJNY POJAZDU (np. PO12345)").upper()
            with col2: k_odo = st.number_input("AKTUALNY PRZEBIEG (KM)", min_value=0, step=1)
            
            st.info("Zaznacz stan każdego elementu poniżej. System nie pozwoli na wysłanie raportu, jeśli pominiesz jakikolwiek punkt.")
            
            check_results = {}
            if data_gh and "lista_kontrolna" in data_gh:
                st.markdown("---")
                for kat, punkty in data_gh["lista_kontrolna"].items():
                    # --- POWRÓT ZWIJANYCH LIST (EXPANDERÓW) ---
                    with st.expander(kat.upper(), expanded=False):
                        for pt in punkty:
                            check_results[pt] = st.radio(
                                pt, 
                                ["✅ OK", "⚠️ UWAGA (Drobna usterka)", "🛑 KRYTYCZNE (Uziemienie)"], 
                                index=None, 
                                horizontal=True, 
                                key=f"f_{pt}"
                            )
            
            st.markdown("---")
            st.markdown("#### 📸 DOKUMENTACJA USTEREK")
            u_notes = st.text_area("Jeśli w którymś punkcie zaznaczyłeś 'UWAGA' lub 'KRYTYCZNE', krótko opisz problem poniżej:")
            uploaded_files = st.file_uploader("Wgraj zdjęcia usterek (Aparat w telefonie / Galeria)", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
            
            st.markdown("---")
            deklaracja = st.checkbox("Oświadczam, że dokonałem fizycznych oględzin pojazdu. Mam świadomość odpowiedzialności za przekazanie nieprawdziwych danych.")
            
            submitted = st.form_submit_button("🚀 ZATWIERDŹ I WYŚLIJ RAPORT", use_container_width=True)
            
            if submitted:
                brakujace_punkty = [pt for pt, val in check_results.items() if val is None]
                
                if not r_plate:
                    st.error("Wpisz numer rejestracyjny pojazdu!")
                elif k_odo <= 0:
                    st.error("Podaj prawidłowy, aktualny przebieg w kilometrach!")
                elif len(brakujace_punkty) > 0:
                    st.error(f"Nie sprawdziłeś {len(brakujace_punkty)} punktów! Rozwiń listy wyżej i zaznacz brakujące opcje (podświetlone na czerwono).")
                elif not deklaracja:
                    st.error("Musisz zaznaczyć oświadczenie o dokonaniu oględzin na samym dole formularza!")
                else:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    saved_files = []
                    if uploaded_files:
                        for uf in uploaded_files:
                            fname = f"INSP_{r_plate}_{datetime.now().strftime('%H%M%S')}_{uf.name}"
                            with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
                                f.write(uf.getbuffer())
                            saved_files.append(fname)

                    krytyczne = [pt for pt, val in check_results.items() if "KRYTYCZNE" in val]
                    uwagi = [pt for pt, val in check_results.items() if "UWAGA" in val]

                    if krytyczne:
                        status = "ALERT: KRYTYCZNY"
                    elif uwagi:
                        status = "UWAGA: WYMAGA PRZEGLĄDU"
                    else:
                        status = "NOMINAL (OK)"

                    final_notes = u_notes
                    if saved_files:
                        final_notes += f" | ZDJĘCIA: {', '.join(saved_files)}"

                    if krytyczne or uwagi:
                        final_notes = f"Zgłoszono: {len(krytyczne)} kryt., {len(uwagi)} uwag. " + final_notes

                    if save_to_sheet("Flota", [ts, current_user, r_plate, k_odo, status, final_notes]):
                        st.success(f"Raport wysłany pomyślnie! Wykryty status pojazdu: {status}")
                        st.balloons()
                    else:
                        st.error("Błąd zapisu w Google Sheets.")

    elif mode == "🚚 MOJE TRASY (ZADANIA)":
        st.markdown("### 🚚 LISTA ZADAŃ I TRAS KIEROWCY")
        st.info("Podaj numer rejestracyjny swojego pojazdu, aby pobrać przypisane zlecenia z centrali.")
        
        pojazd_kierowcy = st.text_input("TWÓJ POJAZD (REJESTRACJA)", value=st.session_state.get("last_plate", "")).upper()
        
        if pojazd_kierowcy:
            st.session_state.last_plate = pojazd_kierowcy
            st.markdown("---")
            
            with st.spinner("Synchronizacja z serwerem logistycznym..."):
                df_zlecenia = load_sheet_data("Zlecenia")
            
            if df_zlecenia.empty:
                st.error("Błąd połączenia z bazą zleceń.")
            else:
                df_kierowcy = df_zlecenia[
                    (df_zlecenia['Pojazd_Kierowca'].astype(str).str.upper() == pojazd_kierowcy) & 
                    (df_zlecenia['Status'].isin(['ZAPLANOWANE', 'W TRASIE']))
                ]
                
                if df_kierowcy.empty:
                    st.success(f"Brak aktywnych zleceń w systemie dla pojazdu: {pojazd_kierowcy}. Odpoczywaj!")
                else:
                    st.markdown(f"**Odnaleziono zlecenia dla {pojazd_kierowcy}:**")
                    for _, row in df_kierowcy.iterrows():
                        o_id = row.get('ID', 'N/A')
                        status = row.get('Status')
                        
                        ladunek_str = ""
                        try:
                            lad_list = json.loads(str(row.get('Ladunek', '[]')))
                            ladunek_str = " | ".join([f"{item['ILOSC']}x {item['SKU']}" for item in lad_list])
                        except: ladunek_str = "Brak szczegółów ładunku."
                        
                        card_border = "#F1C40F" if status == 'ZAPLANOWANE' else "#E67E22"
                        
                        st.markdown(f"""
                            <div style="background: rgba(20, 20, 20, 0.9); border: 1px solid #333; border-left: 5px solid {card_border}; padding: 15px; margin-bottom: 10px; border-radius: 6px;">
                                <div style="display:flex; justify-content:space-between; margin-bottom: 10px;">
                                    <span style="color:#B58863; font-weight:bold; font-size:1.1rem;">ZLECENIE: {o_id}</span>
                                    <span style="color:{card_border}; font-weight:bold; font-family:'JetBrains Mono';">STATUS: {status}</span>
                                </div>
                                <div style="color:#FFFFFF; font-size:1.2rem; font-weight:bold; margin-bottom: 10px;">
                                    📍 {row.get('Start', '-')} ➔ 🏁 {row.get('Koniec', '-')}
                                </div>
                                <div style="color:#AAAAAA; font-size:0.9rem; line-height:1.6;">
                                    <b>Klient (Rozładunek):</b> {row.get('Klient', '-')}<br>
                                    <b>Daty:</b> {row.get('DataZal', '-')} do {row.get('DataRozl', '-')}<br>
                                    <b>Ładunek:</b> <span style="color:#FFF;">{ladunek_str}</span><br>
                                    <b>Uwagi:</b> <span style="color:#FF4B4B;">{row.get('Uwagi', 'Brak')}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div class='btn-action'>", unsafe_allow_html=True)
                        
                        if status == 'ZAPLANOWANE':
                            if st.button(f"▶️ ROZPOCZNIJ TRASĘ (START)", key=f"start_{o_id}", use_container_width=True):
                                if update_driver_order(o_id, "W TRASIE"):
                                    st.success("Status zaktualizowany! Trasa rozpoczęta."); st.rerun()
                                else: st.error("Błąd połączenia.")
                                
                        elif status == 'W TRASIE':
                            with st.form(f"end_form_{o_id}"):
                                st.info("Gdy dotrzesz na miejsce i rozładujesz towar, wgraj zdjęcie dokumentu i zakończ trasę.")
                                cmr_file = st.file_uploader("Wgraj zdjęcie CMR (Opcjonalnie)", type=["pdf", "jpg", "png", "jpeg"], key=f"cmr_{o_id}")
                                
                                if st.form_submit_button("🏁 ZGŁOŚ ROZŁADUNEK (KONIEC)", use_container_width=True):
                                    saved_filename = ""
                                    if cmr_file is not None:
                                        saved_filename = f"CMR_{o_id}_{cmr_file.name}"
                                        with open(os.path.join(UPLOAD_DIR, saved_filename), "wb") as f:
                                            f.write(cmr_file.getbuffer())
                                            
                                    if update_driver_order(o_id, "ZAKOŃCZONE", saved_filename):
                                        st.success("Rozładunek zgłoszony! Zlecenie zakończone."); st.rerun()
                                    else: st.error("Błąd połączenia.")
                                    
                        st.markdown("</div><br>", unsafe_allow_html=True)

if __name__ == "__main__":
    run_base()
