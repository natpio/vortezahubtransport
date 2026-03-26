# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
import os
import base64
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

# ==============================================================================
# 1. KONFIGURACJA I ZASOBY
# ==============================================================================
PATH_CONFIG = os.path.join("data", "config.json")
PATH_PRODUCTS = os.path.join("data", "products.json")
PATH_BG = os.path.join("assets", "tlo_hub_2.jpg")

# NOWE ID ARKUSZA
SHEET_ID = "1Arq4WTFcvbvH7JkMEMWpWkGjaN44J4UpgJ2T9lKQLn8"

def load_vorteza_asset_b64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

def load_local_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return {}

# ==============================================================================
# 2. GOOGLE SHEETS ENGINE (SPEDYCJA)
# ==============================================================================
def get_gspread_client():
    creds_info = st.secrets["GCP_SERVICE_ACCOUNT"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(credentials)

def load_orders():
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        return pd.DataFrame(sheet.get_all_records())
    except gspread.exceptions.WorksheetNotFound:
        st.error("KRYTYCZNY BŁĄD: Utwórz w Google Sheets zakładkę o nazwie 'Zlecenia'!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Błąd bazy danych: {e}")
        return pd.DataFrame()

def save_new_order(row_data):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        sheet.append_row(row_data)
        return True
    except Exception as e: 
        st.error(f"Błąd zapisu: {e}")
        return False

def update_order_status(order_id, new_status):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                sheet.update_cell(i + 2, 2, new_status) # Kolumna B to Status
                return True
        return False
    except: return False

def update_order_billing(order_id, inv_num, inv_date, term_days, is_paid):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                row_idx = i + 2
                sheet.update_cell(row_idx, 16, str(inv_num))   # P: Faktura
                sheet.update_cell(row_idx, 17, str(inv_date))  # Q: DataFaktury
                sheet.update_cell(row_idx, 18, int(term_days)) # R: TerminDni
                sheet.update_cell(row_idx, 19, str(is_paid))   # S: StatusPlatnosci
                return True
        return False
    except: return False

def update_full_order(order_id, klient, spedytor, start, koniec, data_z, data_r, trakcja, przewoznik, auto_kierowca, f_sprzedaz, f_kupno, ladunek_json, uwagi):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).worksheet("Zlecenia")
        records = sheet.get_all_records()
        for i, row in enumerate(records):
            if str(row.get('ID')) == str(order_id):
                row_idx = i + 2
                cell_list = sheet.range(f'C{row_idx}:O{row_idx}')
                values = [
                    str(klient), str(spedytor), str(start), str(koniec), 
                    str(data_z), str(data_r), str(trakcja), str(przewoznik), 
                    str(auto_kierowca), str(f_sprzedaz), str(f_kupno), 
                    str(ladunek_json), str(uwagi)
                ]
                for j, val in enumerate(values):
                    cell_list[j].value = val
                sheet.update_cells(cell_list)
                return True
        return False
    except Exception as e: 
        st.error(f"Błąd zapisu bazy: {e}")
        return False

# ==============================================================================
# 3. INTERFEJS I MOTYW VORTEZA
# ==============================================================================
def inject_core_theme():
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
            h1, h2, h3 {{ color: #B58863 !important; text-transform: uppercase; letter-spacing: 4px !important; font-weight: 700 !important; }}
            .order-card {{
                background: rgba(15, 15, 15, 0.85); border: 1px solid rgba(181, 136, 99, 0.3);
                border-left: 4px solid #B58863; padding: 15px; margin-bottom: 15px; border-radius: 4px;
            }}
            .order-card-title {{ color: #FFFFFF; font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; }}
            .order-card-route {{ color: #B58863; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; margin-bottom: 10px; }}
            .order-card-details {{ color: #AAAAAA; font-size: 0.8rem; line-height: 1.4; }}
            .status-draft {{ border-left-color: #AAAAAA !important; }}
            .status-akcept {{ border-left-color: #2980B9 !important; }}
            .status-trasa {{ border-left-color: #E67E22 !important; }}
            .status-koniec {{ border-left-color: #27AE60 !important; opacity: 0.6; }}
            
            .billing-card {{
                background: rgba(20, 20, 20, 0.9); border: 1px solid #333;
                border-left: 4px solid #E67E22; padding: 15px; margin-bottom: 15px; border-radius: 6px;
            }}
            
            div[data-testid="stButton"] button {{ width: 100%; border-color: #B58863 !important; color: #B58863 !important; background: transparent !important; margin-bottom: 5px; }}
            div[data-testid="stButton"] button:hover {{ background: #B58863 !important; color: #000 !important; }}
            .billing-btn div[data-testid="stButton"] button {{ background: rgba(181, 136, 99, 0.2) !important; }}
            .btn-danger div[data-testid="stButton"] button {{ color: #FF4B4B !important; border-color: #FF4B4B !important; padding: 0px !important; margin: 0px !important; }}
            .btn-danger div[data-testid="stButton"] button:hover {{ background: #FF4B4B !important; color: white !important; }}
        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 4. GŁÓWNA LOGIKA MODUŁU CORE
# ==============================================================================
def run_core():
    inject_core_theme()
    st.markdown("<h2>VORTEZA TMS | ZARZĄDZANIE SPEDYCJĄ</h2>", unsafe_allow_html=True)
    
    current_user = st.session_state.get("username", "OPERATOR")
    config_data = load_local_json(PATH_CONFIG)
    products_data = load_local_json(PATH_PRODUCTS)
    
    if "core_cart" not in st.session_state: st.session_state.core_cart = []
    if "edit_cart" not in st.session_state: st.session_state.edit_cart = []
    if "current_edit_id" not in st.session_state: st.session_state.current_edit_id = ""

    with st.sidebar:
        st.markdown("### 🎛️ PANEL STEROWANIA")
        mode = st.radio("TRYB PRACY:", [
            "📊 TABLICA ZLECEŃ (KANBAN)", 
            "➕ NOWE ZLECENIE", 
            "✏️ EDYCJA ZLECENIA",
            "💰 ROZLICZENIA (BILLING)",
            "🗄️ BAZA / ARCHIWUM"
        ], label_visibility="collapsed")
        st.divider()

    df = load_orders()

    # --------------------------------------------------------------------------
    # WIDOK 1: KANBAN
    # --------------------------------------------------------------------------
    if mode == "📊 TABLICA ZLECEŃ (KANBAN)":
        if df.empty:
            st.info("Brak zleceń w systemie. Przejdź do zakładki 'NOWE ZLECENIE'.")
            return
            
        c1, c2, c3, c4 = st.columns(4)
        columns = {"DRAFT (NOWE)": c1, "ZAAKCEPTOWANE": c2, "W TRASIE": c3, "ZAKOŃCZONE": c4}
        
        for title, col in columns.items():
            with col:
                st.markdown(f"<h4 style='text-align:center; font-size:1rem; border-bottom:1px solid #B58863; padding-bottom:10px;'>{title}</h4>", unsafe_allow_html=True)
                df_filtered = df[df['Status'].astype(str) == title]
                
                for _, row in df_filtered.iterrows():
                    o_id = row.get('ID', 'N/A')
                    css_class = "order-card status-draft" if title == "DRAFT (NOWE)" else "order-card status-akcept" if title == "ZAAKCEPTOWANE" else "order-card status-trasa" if title == "W TRASIE" else "order-card status-koniec"
                    
                    st_sprz = row.get('Fracht_Sprzedaz', 0)
                    st_kup = row.get('Fracht_Kupno', 0)
                    try:
                        marza = float(st_sprz) - float(st_kup)
                    except:
                        marza = 0

                    st.markdown(f"""
                        <div class="{css_class}">
                            <div class="order-card-title">{o_id} | {row.get('Klient', '-')}</div>
                            <div class="order-card-route">📍 {row.get('Start', '-')} ➔ {row.get('Koniec', '-')}</div>
                            <div class="order-card-details">
                                <b>Przewoźnik:</b> {row.get('Przewoznik', 'WŁASNY')}<br>
                                <b>Załadunek:</b> {row.get('DataZal', '-')}<br>
                                <b>Marża (Zysk):</b> <span style="color:#00FF41;">{marza}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if title == "DRAFT (NOWE)":
                        a1, a2 = st.columns(2)
                        if a1.button("✅ AKCEPT", key=f"akc_{o_id}"):
                            update_order_status(o_id, "ZAAKCEPTOWANE"); st.rerun()
                        if a2.button("📦 STACK", key=f"stk_{o_id}"):
                            try:
                                order_items = json.loads(row.get('Ladunek', '[]'))
                                new_manifest = []
                                for item in order_items:
                                    for p in products_data:
                                        if p['name'] == item['SKU']:
                                            p_copy = p.copy(); p_copy['p_act'] = int(item['ILOSC']); new_manifest.append(p_copy); break
                                st.session_state.v_manifest = new_manifest
                                st.session_state.active_module = "PLANER 3D (STACK)"; st.rerun()
                            except Exception as e: st.error(f"Błąd ładunku: {e}")
                            
                        if st.button("❌ ANULUJ", key=f"anl_{o_id}"):
                            update_order_status(o_id, "ANULOWANE"); st.rerun()
                                    
                    elif title == "ZAAKCEPTOWANE":
                        a1, a2 = st.columns(2)
                        if a1.button("🚚 W DROGĘ", key=f"drg_{o_id}"):
                            update_order_status(o_id, "W TRASIE"); st.rerun()
                        if a2.button("💸 FLOW", key=f"flw_{o_id}"):
                            try:
                                order_items = json.loads(row.get('Ladunek', '[]'))
                                new_manifest = []
                                for item in order_items:
                                    for p in products_data:
                                        if p['name'] == item['SKU']:
                                            p_copy = p.copy(); p_copy['p_act'] = int(item['ILOSC']); new_manifest.append(p_copy); break
                                st.session_state.v_manifest = new_manifest
                                st.session_state.flow_origin = row.get('Start', '')
                                st.session_state.flow_dest = row.get('Koniec', '')
                                st.session_state.flow_rate = str(row.get('Fracht_Sprzedaz', ''))
                                st.session_state.active_module = "FINANSE (FLOW)"; st.rerun()
                            except Exception as e: st.error(f"Błąd ładunku: {e}")
                            
                        b1, b2 = st.columns(2)
                        if b1.button("↩️ COFNIJ", key=f"cof_{o_id}"):
                            update_order_status(o_id, "DRAFT (NOWE)"); st.rerun()
                        if b2.button("❌ ANULUJ", key=f"anl2_{o_id}"):
                            update_order_status(o_id, "ANULOWANE"); st.rerun()
                            
                    elif title == "W TRASIE":
                        a1, a2 = st.columns(2)
                        if a1.button("🏁 KONIEC", key=f"kon_{o_id}"):
                            update_order_status(o_id, "ZAKOŃCZONE"); st.rerun()
                        if a2.button("↩️ COFNIJ", key=f"cof_{o_id}"):
                            update_order_status(o_id, "ZAAKCEPTOWANE"); st.rerun()
                            
                    elif title == "ZAKOŃCZONE":
                        a1, a2 = st.columns(2)
                        if a1.button("↩️ COFNIJ", key=f"cof_{o_id}"):
                            update_order_status(o_id, "W TRASIE"); st.rerun()
                        if a2.button("🗄️ ARCHIWIZUJ", key=f"arc_{o_id}"):
                            update_order_status(o_id, "ZAMKNIĘTE"); st.rerun()

    # --------------------------------------------------------------------------
    # WIDOK 2: KREATOR ZLECENIA SPEDYCYJNEGO
    # --------------------------------------------------------------------------
    elif mode == "➕ NOWE ZLECENIE":
        st.markdown("### 📝 KREATOR ZLECENIA SPEDYCYJNEGO")
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            with st.container(border=True):
                st.markdown("#### 1. DANE OPERACYJNE")
                col1, col2 = st.columns(2)
                klient = col1.text_input("KLIENT / ZLECENIODAWCA (Kto płaci nam)")
                
                trakcja = col2.radio("TYP TRAKCJI", ["WŁASNY TABOR", "PODWYKONAWCA (PRZEWOŹNIK)"], horizontal=True)
                
                col_p1, col_p2 = st.columns(2)
                if trakcja == "PODWYKONAWCA (PRZEWOŹNIK)":
                    przewoznik = col_p1.text_input("NAZWA PRZEWOŹNIKA")
                else:
                    przewoznik = "VORTEZA FLEET"
                    
                auto_kierowca = col_p2.text_input("POJAZD (REJ.) I TEL. KIEROWCY")

                st.divider()
                st.markdown("#### 2. FINANSE (WALUTA DOMYŚLNA: PLN/EUR wpisz ręcznie)")
                col_f1, col_f2 = st.columns(2)
                fracht_sprzedaz = col_f1.text_input("FRACHT SPRZEDAŻ (Dla Klienta)", "0")
                if trakcja == "PODWYKONAWCA (PRZEWOŹNIK)":
                    fracht_kupno = col_f2.text_input("FRACHT KUPNO (Koszty Przewoźnika)", "0")
                else:
                    fracht_kupno = col_f2.text_input("SZACOWANY KOSZT WŁASNY", "0")

                st.divider()
                st.markdown("#### 3. LOGISTYKA TRASY")
                miasta_start = list(config_data.get("DISTANCES_AND_MYTO", {}).keys()) if config_data else ["Poznań", "Warszawa"]
                
                col3, col4 = st.columns(2)
                start = col3.selectbox("MIEJSCE ZAŁADUNKU", miasta_start)
                
                miasta_cel = list(config_data.get("DISTANCES_AND_MYTO", {}).get(start, {}).keys()) if config_data else []
                koniec = col4.selectbox("MIEJSCE ROZŁADUNKU", miasta_cel)
                
                col5, col6 = st.columns(2)
                data_z = col5.date_input("DATA ZAŁADUNKU")
                data_r = col6.date_input("DATA ROZŁADUNKU")
                
                uwagi = st.text_area("UWAGI (Awizacja, warunki załadunku, nr referencyjny)")

        with c_right:
            with st.container(border=True):
                st.markdown("#### 4. ŁADUNEK / PALETY")
                lista_sku = [p['name'] for p in products_data] if products_data else []
                wybrane_sku = st.selectbox("WYBIERZ JEDNOSTKĘ LOGISTYCZNĄ", lista_sku)
                ilosc_sku = st.number_input("ILOŚĆ (SZTUKI)", min_value=1, value=1)
                
                if st.button("➕ DODAJ DO LISTY ZLECENIA"):
                    st.session_state.core_cart.append({"SKU": wybrane_sku, "ILOSC": ilosc_sku})
                
                st.markdown("---")
                if st.session_state.core_cart:
                    for i, item in enumerate(st.session_state.core_cart):
                        st.markdown(f"- **{item['ILOSC']}x** {item['SKU']}")
                    if st.button("🗑️ WYCZYŚĆ ŁADUNEK"):
                        st.session_state.core_cart = []
                        st.rerun()
                else:
                    st.info("Brak zadeklarowanego ładunku.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 ZAPISZ I UTWÓRZ ZLECENIE", use_container_width=True):
            if not klient:
                st.error("Podaj nazwę klienta!")
            else:
                now = datetime.now()
                order_id = f"TMS-{now.strftime('%y')}-{now.strftime('%H%M%S')}"
                ladunek_json = json.dumps(st.session_state.core_cart, ensure_ascii=False)
                
                row = [
                    order_id, "DRAFT (NOWE)", klient, current_user, start, koniec, 
                    str(data_z), str(data_r), trakcja, przewoznik, auto_kierowca,
                    fracht_sprzedaz, fracht_kupno, ladunek_json, uwagi,
                    "", "", 30, "NIE" # domyślnie 30 dni terminu w spedycji
                ]
                
                if save_new_order(row):
                    st.session_state.core_cart = [] 
                    st.success(f"Zlecenie {order_id} zostało pomyślnie utworzone!")
                    st.balloons()
                else:
                    st.error("Błąd zapisu w Google Sheets.")

    # --------------------------------------------------------------------------
    # WIDOK 3: EDYCJA ZLECENIA
    # --------------------------------------------------------------------------
    elif mode == "✏️ EDYCJA ZLECENIA":
        st.markdown("### ✏️ EDYTOR ZLECENIA")
        if df.empty:
            st.info("Brak zleceń w systemie.")
        else:
            aktywne_df = df[df['Status'].isin(['DRAFT (NOWE)', 'ZAAKCEPTOWANE', 'W TRASIE'])]
            if aktywne_df.empty:
                st.success("Brak aktywnych zleceń do edycji.")
            else:
                lista_zlecen = aktywne_df['ID'].astype(str) + " | " + aktywne_df['Klient'].astype(str)
                wybrane_zlecenie_str = st.selectbox("WYBIERZ ZLECENIE DO EDYCJI", lista_zlecen.tolist())
                
                wybrane_id = wybrane_zlecenie_str.split(" | ")[0]
                row_data = aktywne_df[aktywne_df['ID'].astype(str) == wybrane_id].iloc[0]
                
                if st.session_state.get('current_edit_id') != wybrane_id:
                    st.session_state.current_edit_id = wybrane_id
                    try: st.session_state.edit_cart = json.loads(row_data.get('Ladunek', '[]'))
                    except: st.session_state.edit_cart = []
                
                c_left, c_right = st.columns([2, 1])
                
                with c_left:
                    with st.container(border=True):
                        st.markdown("#### 1. DANE OPERACYJNE")
                        col1, col2 = st.columns(2)
                        klient = col1.text_input("KLIENT / ZLECENIODAWCA", value=str(row_data.get('Klient', '')))
                        
                        tr_idx = 1 if row_data.get('Trakcja', '') == "PODWYKONAWCA (PRZEWOŹNIK)" else 0
                        trakcja = col2.radio("TYP TRAKCJI", ["WŁASNY TABOR", "PODWYKONAWCA (PRZEWOŹNIK)"], index=tr_idx, horizontal=True, key="ed_tr")
                        
                        col_p1, col_p2 = st.columns(2)
                        przewoznik = col_p1.text_input("NAZWA PRZEWOŹNIKA", value=str(row_data.get('Przewoznik', '')))
                        auto_kierowca = col_p2.text_input("POJAZD I KIEROWCA", value=str(row_data.get('Pojazd_Kierowca', '')))

                        st.divider()
                        col_f1, col_f2 = st.columns(2)
                        fracht_sprzedaz = col_f1.text_input("FRACHT SPRZEDAŻ", value=str(row_data.get('Fracht_Sprzedaz', '0')))
                        fracht_kupno = col_f2.text_input("FRACHT KUPNO", value=str(row_data.get('Fracht_Kupno', '0')))

                        st.divider()
                        st.markdown("#### 2. LOGISTYKA")
                        miasta_start = list(config_data.get("DISTANCES_AND_MYTO", {}).keys()) if config_data else ["Poznań", "Warszawa"]
                        start_val = str(row_data.get('Start', ''))
                        idx_start = miasta_start.index(start_val) if start_val in miasta_start else 0
                        
                        col3, col4 = st.columns(2)
                        start = col3.selectbox("MIEJSCE ZAŁADUNKU", miasta_start, index=idx_start, key="ed_start")
                        
                        miasta_cel = list(config_data.get("DISTANCES_AND_MYTO", {}).get(start, {}).keys()) if config_data else []
                        koniec_val = str(row_data.get('Koniec', ''))
                        idx_koniec = miasta_cel.index(koniec_val) if koniec_val in miasta_cel else 0
                        koniec = col4.selectbox("MIEJSCE ROZŁADUNKU", miasta_cel, index=idx_koniec, key="ed_koniec")
                        
                        col5, col6 = st.columns(2)
                        try: dz_obj = datetime.strptime(str(row_data.get('DataZal', '')), "%Y-%m-%d").date()
                        except: dz_obj = datetime.now().date()
                        try: dr_obj = datetime.strptime(str(row_data.get('DataRozl', '')), "%Y-%m-%d").date()
                        except: dr_obj = datetime.now().date()
                        
                        data_z = col5.date_input("DATA ZAŁADUNKU", value=dz_obj, key="ed_dz")
                        data_r = col6.date_input("DATA ROZŁADUNKU", value=dr_obj, key="ed_dr")
                        
                        uwagi = st.text_area("UWAGI", value=str(row_data.get('Uwagi', '')), key="ed_uwagi")

                with c_right:
                    with st.container(border=True):
                        st.markdown("#### 3. ŁADUNEK / PALETY")
                        lista_sku = [p['name'] for p in products_data] if products_data else []
                        wybrane_sku = st.selectbox("WYBIERZ", lista_sku, key="ed_sku")
                        ilosc_sku = st.number_input("ILOŚĆ", min_value=1, value=1, key="ed_ilosc")
                        
                        if st.button("➕ DODAJ DO ŁADUNKU", key="ed_dodaj"):
                            st.session_state.edit_cart.append({"SKU": wybrane_sku, "ILOSC": ilosc_sku})
                            st.rerun()
                        
                        st.markdown("---")
                        if st.session_state.edit_cart:
                            for i, item in enumerate(st.session_state.edit_cart):
                                col_a, col_b = st.columns([4, 1])
                                col_a.markdown(f"- **{item['ILOSC']}x** {item['SKU']}")
                                st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                                if col_b.button("❌", key=f"del_ed_{i}"):
                                    st.session_state.edit_cart.pop(i)
                                    st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                            if st.button("🗑️ WYCZYŚĆ WSZYSTKO", key="ed_clear"):
                                st.session_state.edit_cart = []
                                st.rerun()
                        else:
                            st.info("Brak ładunku.")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 NADPISZ I ZAPISZ ZMIANY", use_container_width=True, key="ed_save"):
                    if not klient:
                        st.error("Podaj nazwę klienta!")
                    else:
                        ladunek_json = json.dumps(st.session_state.edit_cart, ensure_ascii=False)
                        spedytor = current_user
                        if update_full_order(wybrane_id, klient, spedytor, start, koniec, data_z, data_r, trakcja, przewoznik, auto_kierowca, fracht_sprzedaz, fracht_kupno, ladunek_json, uwagi):
                            st.success(f"Zlecenie {wybrane_id} zaktualizowane!")
                            st.balloons()
                        else:
                            st.error("Błąd zapisu danych.")

    # --------------------------------------------------------------------------
    # WIDOK 4: ROZLICZENIA (BILLING)
    # --------------------------------------------------------------------------
    elif mode == "💰 ROZLICZENIA (BILLING)":
        st.markdown("### 💰 PANEL ROZLICZEŃ I WINDYKACJI")
        st.markdown("---")
        
        if df.empty:
            st.info("Brak zleceń w systemie.")
        else:
            df_billing = df[df['Status'].isin(['ZAKOŃCZONE', 'ZAMKNIĘTE'])]
            if df_billing.empty:
                st.success("Brak zakończonych zleceń do rozliczenia.")
            else:
                for _, row in df_billing.iterrows():
                    o_id = row.get('ID', 'N/A')
                    inv_no = str(row.get('Faktura', '')).strip()
                    inv_date_str = str(row.get('DataFaktury', '')).strip()
                    try: term_days = int(row.get('TerminDni', 30))
                    except: term_days = 30
                    is_paid_str = str(row.get('StatusPlatnosci', 'NIE')).strip().upper()
                    is_paid = (is_paid_str == 'TAK')
                    
                    badge_html = ""
                    if inv_no and inv_date_str:
                        try:
                            inv_date_obj = datetime.strptime(inv_date_str, "%Y-%m-%d").date()
                            due_date = inv_date_obj + timedelta(days=term_days)
                            today = datetime.now().date()
                            delta = (due_date - today).days
                            
                            if is_paid:
                                badge_html = f"<span style='color:#27AE60; font-size: 1.1rem;'>✅ OPŁACONA ({inv_no})</span>"
                            elif delta < 0:
                                badge_html = f"<span style='color:#FF3131; font-size: 1.1rem;'>⚠️ PO TERMINIE {abs(delta)} DNI! (Termin: {due_date.strftime('%d.%m.%Y')})</span>"
                            elif delta == 0:
                                badge_html = f"<span style='color:#E67E22; font-size: 1.1rem;'>⏳ TERMIN MIJA DZIŚ!</span>"
                            else:
                                badge_html = f"<span style='color:#F1C40F; font-size: 1.1rem;'>⏳ POZOSTAŁO {delta} DNI (Termin: {due_date.strftime('%d.%m.%Y')})</span>"
                        except:
                            badge_html = "<span style='color:#AAAAAA;'>BŁĄD DATY FAKTURY</span>"
                    else:
                        badge_html = "<span style='color:#AAAAAA; font-size: 1.1rem;'>⏳ BRAK FAKTURY</span>"
                    
                    st.markdown(f"""
                        <div class="billing-card">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                                <div>
                                    <span style="color:#B58863; font-weight:bold; font-size:1.2rem;">{o_id}</span> | {row.get('Klient', '-')}
                                    <br><span style="color:#888; font-size:0.8rem;">Fracht: {row.get('Fracht_Sprzedaz', '-')} | Przewoźnik: {row.get('Przewoznik', '-')}</span>
                                </div>
                                <div style="text-align: right; font-weight: bold;">
                                    {badge_html}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with st.form(f"bill_form_{o_id}"):
                        c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1.5])
                        new_inv_no = c1.text_input("NUMER FAKTURY", value=inv_no, key=f"inv_{o_id}")
                        try: default_date = datetime.strptime(inv_date_str, "%Y-%m-%d").date() if inv_date_str else datetime.now().date()
                        except: default_date = datetime.now().date()
                        new_inv_date = c2.date_input("DATA WYSTAWIENIA", value=default_date, key=f"date_{o_id}")
                        new_term = c3.number_input("TERMIN (DNI)", value=term_days, step=1, key=f"term_{o_id}")
                        new_is_paid = c4.checkbox("✅ OPŁACONA", value=is_paid, key=f"paid_{o_id}")
                        
                        st.markdown("<div class='billing-btn'>", unsafe_allow_html=True)
                        submitted = c5.form_submit_button("💾 ZAPISZ / AKTUALIZUJ")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        if submitted:
                            status_val = "TAK" if new_is_paid else "NIE"
                            if update_order_billing(o_id, new_inv_no, new_inv_date.strftime("%Y-%m-%d"), new_term, status_val):
                                st.success("Dane faktury zaktualizowane!"); st.rerun()
                            else:
                                st.error("Błąd zapisu w Google Sheets.")

    # --------------------------------------------------------------------------
    # WIDOK 5: BAZA / ARCHIWUM
    # --------------------------------------------------------------------------
    elif mode == "🗄️ BAZA / ARCHIWUM":
        st.markdown("### 🗄️ REJESTR WSZYSTKICH ZLECEŃ")
        if df.empty:
            st.info("Baza zleceń jest pusta.")
        else:
            display_df = df.copy()
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Wszystkich Zleceń", len(display_df))
            col2.metric("W Trasie", len(display_df[display_df['Status'] == 'W TRASIE']))
            col3.metric("Zakończone (Oczekujące)", len(display_df[display_df['Status'] == 'ZAKOŃCZONE']))
            col4.metric("Zarchiwizowane", len(display_df[display_df['Status'] == 'ZAMKNIĘTE']))
            col5.metric("Anulowane", len(display_df[display_df['Status'] == 'ANULOWANE']))
            st.dataframe(display_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    run_core()
