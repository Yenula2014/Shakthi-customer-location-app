import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import urllib.request
import os
import glob

# Page Setup
st.set_page_config(page_title="Customer Location Tracker", page_icon="📍", layout="centered")

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzyBmF1brakYllsKQOD3o55SOS1loZ76jlhfjPJbIdKzowPGbDPBQ5bSJVOCF0WTc9w-A/exec"
LOCATIONS_FILE = "customer_locations.csv"

def clean_text(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    return "" if val_str.lower() in ["nan", "none", "null"] else val_str

@st.cache_data(ttl=0)
def load_excel_data():
    files = glob.glob("*.xlsx") + glob.glob("*.xls")
    if not files:
        return None
    file_path = files[0]
    try:
        df = pd.read_excel(file_path)
        cols_str = " ".join([str(c) for c in df.columns]).lower()
        if "unnamed" in cols_str or "customer nic" not in cols_str:
            for r in range(1, 5):
                temp_df = pd.read_excel(file_path, header=r)
                temp_cols = " ".join([str(c) for c in temp_df.columns]).lower()
                if "customer nic" in temp_cols or "customer code" in temp_cols:
                    df = temp_df
                    break
        df.columns = df.columns.astype(str).str.strip()
        df['Full_Search'] = df.astype(str).apply(lambda row: ' '.join(row.values).lower(), axis=1)
        return df
    except Exception:
        return None

def load_locations():
    if os.path.exists(LOCATIONS_FILE):
        try:
            return pd.read_csv(LOCATIONS_FILE, dtype=str)
        except Exception:
            pass
    return pd.DataFrame(columns=['Customer Code', 'Customer NIC', 'Facility Code', 'Address', 'Landmark', 'Latitude', 'Longitude', 'Updated By'])

def save_data_webhook(record_dict):
    df_locs = load_locations()
    new_df = pd.DataFrame([record_dict])
    df_locs = pd.concat([df_locs, new_df], ignore_index=True)
    try:
        df_locs.to_csv(LOCATIONS_FILE, index=False)
    except Exception:
        pass

    if "script.google.com" in WEB_APP_URL:
        try:
            payload = {
                "code": record_dict.get('Customer Code', ''),
                "nic": record_dict.get('Customer NIC', ''),
                "facility": record_dict.get('Facility Code', ''),
                "address": record_dict.get('Address', ''),
                "landmark": record_dict.get('Landmark', ''),
                "lat": record_dict.get('Latitude', ''),
                "lon": record_dict.get('Longitude', ''),
                "officer": record_dict.get('Updated By', '')
            }
            req = urllib.request.Request(
                WEB_APP_URL, 
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
    return True

def get_col_val(row, targets):
    for col in row.index:
        if str(col).strip().lower() in [t.lower() for t in targets]:
            val = row[col]
            return clean_text(val) if clean_text(val) else "N/A"
    return "N/A"

def multi_word_match(row_text, search_query):
    words = search_query.strip().lower().split()
    return all(word in row_text for word in words)

# URL Parameters හරහා GPS ලබාගැනීම
query_params = st.query_params
captured_lat = query_params.get("lat", "")
captured_lon = query_params.get("lon", "")
get_gps = query_params.get("get_gps", "")

# 🎯 Standalone HTML Page for Direct Browser Geolocation
if get_gps == "1":
    gps_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; text-align: center; padding: 40px 20px; background: #f8fafc; color: #1e293b; }
            .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }
            .btn { background: #16a34a; color: white; border: none; padding: 14px 24px; font-size: 16px; font-weight: bold; border-radius: 8px; width: 100%; cursor: pointer; }
            .status { margin-top: 15px; font-size: 14px; color: #2563eb; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🎯 GPS Location Fetch</h2>
            <p>කරුණාකර පහත Button එක ක්ලික් කර Browser එකෙන් <b>Allow Location</b> ලබාදෙන්න.</p>
            <button class="btn" onclick="fetchGPS()">📍 Get Current Location</button>
            <div id="status" class="status"></div>
        </div>

        <script>
        function fetchGPS() {
            var status = document.getElementById("status");
            status.innerHTML = "⌛ GPS ස්ථානය ලබාගනිමින් පවතී...";

            if (!navigator.geolocation) {
                status.innerHTML = "❌ ඔබගේ Browser එක Geolocation සපයන්නේ නැත.";
                return;
            }

            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    var lat = pos.coords.latitude.toFixed(6);
                    var lon = pos.coords.longitude.toFixed(6);
                    status.innerHTML = "✅ GPS හමුවිය! App එක වෙත මාරු වෙමින් පවතී...";
                    
                    var url = new URL(window.location.href);
                    url.searchParams.delete('get_gps');
                    url.searchParams.set('lat', lat);
                    url.searchParams.set('lon', lon);
                    window.location.href = url.href;
                },
                function(err) {
                    status.innerHTML = "❌ GPS ලබාගත නොහැකි විය: " + err.message + "<br><small>කරුණාකර Phone එකේ GPS / Location Access On කර ඇත්දැයි බලන්න.</small>";
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
        }
        // Auto trigger on load
        window.onload = fetchGPS;
        </script>
    </body>
    </html>
    """
    components.html(gps_html, height=450, scrolling=True)
    st.stop()

df = load_excel_data()
df_locs = load_locations()

st.title("📍 Field Location Capture App")

if df is None:
    st.error("Excel File එක සොයාගත නොහැක!")
else:
    search_query = st.text_input("🔍 Customer සොයන්න (නම, NIC, Code, Facility):", "").strip()

    if search_query:
        matched_mask = df['Full_Search'].apply(lambda x: multi_word_match(x, search_query))
        matched_df = df[matched_mask]

        if matched_df.empty:
            st.warning(f"'{search_query}' සඳහා කිසිදු පාරිභෝගිකයෙකු හමු නොවීය.")
        else:
            st.success(f"පාරිභෝගිකයින් {len(matched_df)} දෙනෙකු හමු විය.")

            for idx, row in matched_df.iterrows():
                name_val = get_col_val(row, ['Customer Name'])
                nic_val = get_col_val(row, ['Customer NIC'])
                code_val = get_col_val(row, ['Customer Code'])
                fac_val = get_col_val(row, ['Facility Status', 'Facility Code'])

                cust_code_str = str(code_val).strip()
                saved_loc = df_locs[df_locs['Customer Code'] == cust_code_str] if not df_locs.empty else pd.DataFrame()

                st.markdown("---")
                st.subheader(f"👤 {name_val}")
                st.write(f"**NIC:** `{nic_val}` | **Code:** `{code_val}` | **Facility:** `{fac_val}`")

                has_loc = False
                existing_addr, existing_land, existing_lat, existing_lon = "", "", "", ""

                if not saved_loc.empty:
                    loc_data = saved_loc.iloc[-1]
                    existing_addr = clean_text(loc_data.get('Address'))
                    existing_land = clean_text(loc_data.get('Landmark'))
                    existing_lat = clean_text(loc_data.get('Latitude'))
                    existing_lon = clean_text(loc_data.get('Longitude'))

                    if existing_addr or existing_land or (existing_lat and existing_lon):
                        has_loc = True
                        st.success("📍 **ස්ථානය Save කර ඇත**")
                        if existing_addr:
                            st.write(f"**Address:** {existing_addr}")
                        if existing_land:
                            st.write(f"**Landmark:** {existing_land}")
                        
                        if existing_lat and existing_lon:
                            st.write(f"**GPS Coordinates:** `{existing_lat}, {existing_lon}`")
                            maps_url = f"https://www.google.com/maps/dir/?api=1&destination={existing_lat},{existing_lon}"
                            st.markdown(f"[🚗 Open Google Maps Navigation]({maps_url})", unsafe_allow_html=True)

                if not has_loc:
                    st.info("ℹ️ ස්ථානය තවම Save කර නොමැත.")

                # Direct Safe GPS Capture Button
                st.markdown(
                    f"""
                    <a href="?get_gps=1&search={search_query}" target="_self" style="text-decoration:none;">
                        <div style="background-color:#16A34A; color:white; text-align:center; padding:12px; border-radius:8px; font-weight:bold; font-size:15px; margin-bottom:15px;">
                            🎯 Capture Current GPS Location
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True
                )

                final_lat = captured_lat if captured_lat else existing_lat
                final_lon = captured_lon if captured_lon else existing_lon

                # Form for Location Saving
                with st.form(key=f"form_{idx}"):
                    st.markdown("**📌 Location Details:**")
                    address = st.text_area("ලිපිනය / පාර (Address / Directions)", value=existing_addr, height=70)
                    landmark = st.text_input("ආසන්නතම සලකුණ (Landmark)", value=existing_land)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        latitude = st.text_input("අක්ෂාංශ (Latitude)", value=final_lat, key=f"lat_{idx}")
                    with c2:
                        longitude = st.text_input("දේශාංශ (Longitude)", value=final_lon, key=f"lon_{idx}")

                    officer = st.text_input("Officer ID / Name", value="")

                    save_btn = st.form_submit_button("💾 Save Location")

                    if save_btn:
                        record = {
                            'Customer Code': cust_code_str,
                            'Customer NIC': str(nic_val),
                            'Facility Code': str(fac_val),
                            'Address': address.strip(),
                            'Landmark': landmark.strip(),
                            'Latitude': latitude.strip(),
                            'Longitude': longitude.strip(),
                            'Updated By': officer.strip()
                        }
                        save_data_webhook(record)
                        st.success("ස්ථානය සාර්ථකව Save විය!")
                        st.query_params.clear()
                        st.rerun()

    else:
        st.info("💡 සෙවීම සඳහා උඩ Search Bar එකේ Customer ගේ නම, NIC, Code හෝ Facility No හි කොටසක් ටයිප් කරන්න.")
