# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import json
import math
import base64
import re

# ==============================================================================
# 0. ZASOBY I KONFIGURACJA
# ==============================================================================
PATH_CONFIG = os.path.join("data", "config.json")
PATH_BG = os.path.join("assets", "tlo_hub_2.jpg")

@st.cache_data # <--- Buforowanie tła w pamięci RAM
def load_vorteza_asset_b64(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return ""
    except: return ""

def load_config():
    try:
        if os.path.exists(PATH_CONFIG):
            with open(PATH_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.error(f"BŁĄD KRYTYCZNY CONFIGA: {e}")
        return {}

def save_config(config_data):
    try:
        with open(PATH_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"BŁĄD ZAPISU: {e}")
        return False

VEH_MAP = {
    "TIR FTL Mega 13.6m": "FTL", 
    "TIR FTL Standard 13.6m": "FTL",
    "Solo 9m Heavy Duty": "Solo", 
    "Solo 7m Medium": "Solo", 
    "Solo 6m Light": "Solo",
    "BUS Opel Movano": "Bus"
}

# ==============================================================================
# 1. UI ENGINE: APEX FLOW CONTRAST FIX
# ==============================================================================
def inject_vorteza_flow_ui():
    bg_data = load_vorteza_asset_b64(PATH_BG)
    
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;700&family=JetBrains+Mono&display=swap');
            
            .stApp {{ 
                background: linear-gradient(rgba(6, 6, 6, 0.85), rgba(6, 6, 6, 0.85)), 
                            url("data:image/jpeg;base64,{bg_data}") !important;
                background-size: cover !important; 
                background-attachment: fixed !important; 
            }}

            .v-flow-card {{
                background: rgba(10, 10, 10, 0.9);
                border: 1px solid rgba(181, 136, 99, 0.3);
                border-top: 4px solid #B58863;
                padding: 20px;
                text-align: center;
                backdrop-filter: blur(10px);
                margin-bottom: 15px;
                border-radius: 4px;
            }}
            .v-flow-label {{ color: #B58863; font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; }}
            .v-flow-value-main {{ color: #FFFFFF; font-size: 1.7rem; font-family: 'JetBrains Mono', monospace; font-weight: 500; }}
            .v-flow-value-sub {{ color: #B58863; font-size: 1.1rem; font-family: 'JetBrains Mono', monospace; margin-top: 5px; border-top: 1px solid rgba(181,136,99,0.2); padding-top: 5px; }}
            
            div[data-testid="stTable"] {{ background-color: rgba(0, 0, 0, 0.8) !important; border-radius: 4px; padding: 10px; }}
            div[data-testid="stTable"] td {{ color: #FFFFFF !important; font-family: 'JetBrains Mono', monospace !important; border-bottom: 1px solid rgba(181, 136, 99, 0.2) !important; }}
            div[data-testid="stTable"] th {{ color: #B58863 !important; text-transform: uppercase !important; background-color: rgba(15, 15, 15, 0.95) !important; }}
            
            .v-positive {{ color: #00FF41 !important; }}
            .v-negative {{ color: #FF3131 !important; }}
            
            div[data-testid="stWidgetLabel"] p {{ color: #B58863 !important; font-weight: 700 !important; letter-spacing: 1px; }}
            .v-badge-unit {{ background: rgba(181,136,99,0.15); border: 1px solid #B58863; padding: 12px; color: #B58863; font-size: 0.85rem; text-align: center; margin-bottom: 15px; font-weight: 700; }}
        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. MODUŁ ANALIZY FINANSOWEJ (TMS)
# ==============================================================================
@st.fragment # <--- Fragment! Zmiany suwaków nie przeładowują całej apki
def show_financial_analysis(CONF):
    with st.sidebar:
        st.markdown("### 🛠️ KONFIGURACJA")
        tryb_biznesowy = st.radio("MODEL ROZLICZEŃ", ["🚛 WŁASNY TABOR", "🤝 SPEDYCJA (PODWYKONAWCA)"])
        st.divider()
        
        eur_rate = st.number_input("KURS EUR/PLN", value=float(CONF.get("EURO_RATE", 4.30)), step=0.01)
        view_curr = st.radio("POKAZUJ WYNIKI W:", ["PLN", "EUR"], horizontal=True)
        st.divider()

        # Zaciąganie danych z modułu CORE (jeśli weszliśmy stamtąd)
        core_orig = st.session_state.get("flow_origin", "")
        core_dest = st.session_state.get("flow_dest", "")
        
        origins_list = list(CONF.get("DISTANCES_AND_MYTO", {}).keys())
        idx_orig = origins_list.index(core_orig) if core_orig in origins_list else 0
        origin = st.selectbox("PUNKT STARTU", origins_list if origins_list else ["Brak"], index=idx_orig)
        
        dests_list = list(CONF.get("DISTANCES_AND_MYTO", {}).get(origin, {}).keys())
        idx_dest = dests_list.index(core_dest) if dests_list and core_dest in dests_list else 0
        dest = st.selectbox("PUNKT DOCELOWY", dests_list if dests_list else ["Brak"], index=idx_dest)

        st.divider()
        st.markdown("### 💰 DANE FINANSOWE")
        
        core_rate_raw = str(st.session_state.get("flow_rate", "0"))
        core_rate_val = 0.0
        try:
            match = re.search(r'\d+([.,]\d+)?', core_rate_raw.replace(' ', ''))
            if match: core_rate_val = float(match.group(0).replace(',', '.'))
        except: pass
        
        rate_curr = st.selectbox("WALUTA FRACHTU", ["PLN", "EUR"], index=0 if "PLN" in core_rate_raw.upper() or core_rate_val == 0 else 1)
        fracht_sprzedaz = st.number_input(f"FRACHT SPRZEDAŻ ({rate_curr})", value=float(core_rate_val))
        
        if tryb_biznesowy == "🤝 SPEDYCJA (PODWYKONAWCA)":
            fracht_kupno = st.number_input(f"FRACHT KUPNO ({rate_curr})", value=float(core_rate_val * 0.85) if core_rate_val > 0 else 0.0)
        else:
            veh_list = list(VEH_MAP.keys())
            stack_veh = st.session_state.get("stack_selected_veh", "")
            idx_veh = veh_list.index(stack_veh) if stack_veh in veh_list else 0
            active_veh_name = st.selectbox("TYP POJAZDU", veh_list, index=idx_veh)

    mult = 1.0 if view_curr == "PLN" else (1.0 / eur_rate)

    # ---------------------------------------------
    # LOGIKA KALKULATORA
    # ---------------------------------------------
    revenue_pln = fracht_sprzedaz if rate_curr == "PLN" else fracht_sprzedaz * eur_rate

    if tryb_biznesowy == "🤝 SPEDYCJA (PODWYKONAWCA)":
        cost_pln = fracht_kupno if rate_curr == "PLN" else fracht_kupno * eur_rate
        margin_pln = revenue_pln - cost_pln
        margin_pct = (margin_pln / revenue_pln * 100) if revenue_pln > 0 else 0
        
        st.markdown(f"#### 📍 RELACJA SPEDYCYJNA: {origin.upper()} ➔ {dest.upper()}")
        st.markdown("<div class='v-badge-unit'>MODEL: SPEDYCJA / FORWARDING | WYZNACZANIE MARŻY</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="v-flow-card"><div class="v-flow-label">FRACHT SPRZEDAŻ (DLA KLIENTA)</div><div class="v-flow-value-main">{revenue_pln*mult:,.2f} {view_curr}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="v-flow-card"><div class="v-flow-label">FRACHT KUPNO (KOSZT PRZEWOŹNIKA)</div><div class="v-flow-value-main">{cost_pln*mult:,.2f} {view_curr}</div></div>', unsafe_allow_html=True)
        
        m_clr = "v-positive" if margin_pln > 0 else "v-negative"
        c3.markdown(f'<div class="v-flow-card"><div class="v-flow-label">MARŻA SPEDYCYJNA (ZYSK)</div><div class="v-flow-value-main {m_clr}">{margin_pln*mult:,.2f} {view_curr}</div><div class="v-flow-value-sub {m_clr}">{margin_pct:.1f}% RENTOWNOŚCI</div></div>', unsafe_allow_html=True)

    else:
        # LOGIKA DLA WŁASNEGO TABORU
        route = CONF.get("DISTANCES_AND_MYTO", {}).get(origin, {}).get(dest, {"distPL":0, "distEU":0, "mytoFTL":0, "mytoSolo":0, "mytoBus":0})
        dPL, dEU = route.get("distPL", 0), route.get("distEU", 0)
        total_dist = dPL + dEU
        
        cat = VEH_MAP[active_veh_name]
        v_spec = CONF["VEHICLE_DATA"][cat]
        prices = CONF["PRICE"]

        total_fuel_needed = total_dist * v_spec["fuelUsage"]
        fuel_from_pl = min(total_fuel_needed, v_spec["tankCapacity"])
        fuel_from_eu = max(0, total_fuel_needed - fuel_from_pl)
        cost_fuel_pln = (fuel_from_pl * prices["fuelPLN"]) + (fuel_from_eu * prices["fuelEUR"] * eur_rate)
        
        cost_adblue_pln = (total_dist * v_spec["adBlueUsage"] * prices["adBluePLN"])
        cost_service_pln = (total_dist * v_spec["serviceCostPLN"])
        
        myto_key = f"myto{cat}"
        cost_tolls_eur = route.get(myto_key, 0)
        cost_tolls_pln = cost_tolls_eur * eur_rate
        
        cost_driver_pln = 500 + (total_dist * 0.15) 
        total_cost_pln = cost_fuel_pln + cost_adblue_pln + cost_service_pln + cost_tolls_pln + cost_driver_pln
        
        margin_pln = revenue_pln - total_cost_pln
        margin_pct = (margin_pln / revenue_pln * 100) if revenue_pln > 0 else 0

        st.markdown(f"#### 📍 RELACJA KRAJ/ZAGRANICA: {origin.upper()} ➔ {dest.upper()}")
        st.markdown(f"<div class='v-badge-unit'>DYSTANS: {total_dist} KM (PL: {dPL} KM | EU: {dEU} KM) | POJAZD: {active_veh_name}</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="v-flow-card"><div class="v-flow-label">PRZYCHÓD Z FRACHTU</div><div class="v-flow-value-main">{revenue_pln*mult:,.2f} {view_curr}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="v-flow-card"><div class="v-flow-label">KOSZTY OPERACYJNE TRASY</div><div class="v-flow-value-main">{total_cost_pln*mult:,.2f} {view_curr}</div></div>', unsafe_allow_html=True)
        
        m_clr = "v-positive" if margin_pln > 0 else "v-negative"
        c3.markdown(f'<div class="v-flow-card"><div class="v-flow-label">WYNIK FINANSOWY (ZYSK)</div><div class="v-flow-value-main {m_clr}">{margin_pln*mult:,.2f} {view_curr}</div><div class="v-flow-value-sub {m_clr}">{margin_pct:.1f}% RENTOWNOŚCI</div></div>', unsafe_allow_html=True)

        st.divider()
        ca, cb = st.columns(2)
        with ca:
            st.markdown(f"### 📊 STRUKTURA KOSZTÓW ({view_curr})")
            cost_df = pd.DataFrame({
                "SKŁADNIK": ["Paliwo (Smart)", "AdBlue", "Myto (EUR->PLN)", "Serwis/Amort.", "Kierowca"],
                "WARTOŚĆ": [round(x * mult, 2) for x in [cost_fuel_pln, cost_adblue_pln, cost_tolls_pln, cost_service_pln, cost_driver_pln]]
            })
            st.table(cost_df.set_index("SKŁADNIK"))
        with cb:
            st.markdown(f"### ⛽ ANALIZA OPERACYJNA ({view_curr})")
            st.info(f"**PRÓG RENTOWNOŚCI (BEP):** {round((total_cost_pln/max(1,total_dist))*mult, 2)} {view_curr}/KM")
            st.write(f"**Stawka za KM:** {round((revenue_pln/max(1,total_dist))*mult, 2)} {view_curr}/KM")
            st.write(f"**Szacowane spalanie:** {round(total_fuel_needed, 1)} L")

# ==============================================================================
# 3. MODUŁ EDYTORA TRAS (ROUTE MASTER)
# ==============================================================================
@st.fragment # <--- Fragment! Zmiany w tabeli nie resetują widoku
def show_route_editor(CONF):
    st.markdown("### 🗺️ ZARZĄDZANIE BAZĄ TRAS")
    st.write("Edytuj kilometry i opłaty drogowe bezpośrednio w tabeli. Kliknij 'Zapisz', aby zaktualizować config.json.")
    
    flat_data = []
    for origin, destinations in CONF.get("DISTANCES_AND_MYTO", {}).items():
        for d_name, d_val in destinations.items():
            flat_data.append({
                "SKĄD": origin, "DOKĄD": d_name,
                "KM POLSKA": d_val.get("distPL", 0), "KM ZAGRANICA": d_val.get("distEU", 0),
                "MYTO FTL (EUR)": d_val.get("mytoFTL", 0), "MYTO SOLO (EUR)": d_val.get("mytoSolo", 0), "MYTO BUS (EUR)": d_val.get("mytoBus", 0)
            })
    
    df_routes = pd.DataFrame(flat_data)
    edited_df = st.data_editor(df_routes, num_rows="dynamic", use_container_width=True, key="route_master_editor")
    
    if st.button("💾 ZAPISZ ZMIANY W BAZIE"):
        new_dist = {}
        for _, row in edited_df.iterrows():
            o, d = row["SKĄD"], row["DOKĄD"]
            if o not in new_dist: new_dist[o] = {}
            new_dist[o][d] = {
                "distPL": int(row["KM POLSKA"]), "distEU": int(row["KM ZAGRANICA"]),
                "mytoFTL": float(row["MYTO FTL (EUR)"]), "mytoSolo": float(row["MYTO SOLO (EUR)"]), "mytoBus": float(row["MYTO BUS (EUR)"])
            }
        
        CONF["DISTANCES_AND_MYTO"] = new_dist
        if save_config(CONF):
            st.success("Baza danych tras została pomyślnie zaktualizowana!"); st.rerun()

# ==============================================================================
# 4. RUN FLOW
# ==============================================================================
def run_flow():
    inject_vorteza_flow_ui()
    st.markdown(f"<h2 style='color:#B58863; letter-spacing:10px;'>VORTEZA FLOW | FINANSE</h2>", unsafe_allow_html=True)
    
    CONF = load_config()
    if not CONF:
        st.error("Błąd: Plik konfiguracyjny config.json nie został załadowany.")
        return

    with st.sidebar:
        st.markdown("### 🕹️ TRYB OPERACYJNY")
        app_mode = st.radio("WYBIERZ ZADANIE:", ["🛰️ ANALIZA RENTOWNOŚCI", "🗺️ EDYTOR TRAS"], label_visibility="collapsed")
        st.divider()

    if app_mode == "🛰️ ANALIZA RENTOWNOŚCI":
        show_financial_analysis(CONF)
    else:
        show_route_editor(CONF)

if __name__ == "__main__":
    run_flow()
