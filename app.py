import streamlit as st
import pandas as pd
import os
import glob

# Page Setup
st.set_page_config(page_title="Customer Location Tracker", page_icon="📍", layout="centered")

LOCATIONS_FILE = "customer_locations.csv"

@st.cache_data(ttl=0)
def load_data():
    files = glob.glob("*.xlsx") + glob.glob("*.xls")
    if not files:
        return None
    file_path = files[0]
    try:
        df = pd.read_excel(file_path)
        # Check header row
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
        return pd.read_csv(LOCATIONS_FILE, dtype=str)
    return pd.DataFrame(columns=['Customer Code', 'Customer NIC', 'Facility Code', 'Address', 'Landmark', 'Latitude', 'Longitude', 'Updated By'])

def get_col_val(row, targets):
    for col in row.index:
        if str(col).strip().lower() in [t.lower() for t in targets]:
            val = row[col]
            if pd.isna(val) or str(val).lower() in ['nan', 'none']:
                return "N/A"
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            return str(val).strip()
    return "N/A"

df = load_data()
df_locs = load_locations()

st.title("📍 Location Tracker")

if df is None:
    st.error("Excel File එක සොයාගත නොහැක!")
else:
    # Search Box
    search_query = st.text_input("🔍 Search Customer (NIC / Code / Facility No / Name):", "").strip().lower()

    if search_query:
        matched_df = df[df['Full_Search'].str.contains(search_query, regex=False, na=False)]

        if matched_df.empty:
            st.warning("Customer හමු නොවීය.")
        else:
            for idx, row in matched_df.iterrows():
                name_val = get_col_val(row, ['Customer Name'])
                nic_val = get_col_val(row, ['Customer NIC'])
                code_val = get_col_val(row, ['Customer Code'])
                fac_val = get_col_val(row, ['Facility Status', 'Facility Code'])

                cust_code_str = str(code_val).strip()
                saved_loc = df_locs[df_locs['Customer Code'] == cust_code_str]

                st.markdown("---")
                # Basic Customer Details
                st.subheader(f"👤 {name_val}")
                st.write(f"**NIC:** `{nic_val}` | **Code:** `{code_val}` | **Facility:** `{fac_val}`")

                # Saved Location Details & Map Link
                if not saved_loc.empty:
                    loc_data = saved_loc.iloc[-1]
                    st.success("📍 **ස්ථානය Save කර ඇත**")
                    if loc_data.get('Address'):
                        st.write(f"**Address:** {loc_data['Address']}")
                    if loc_data.get('Landmark'):
                        st.write(f"**Landmark:** {loc_data['Landmark']}")
                    
                    lat = loc_data.get('Latitude', '').strip()
                    lon = loc_data.get('Longitude', '').strip()
                    
                    if lat and lon:
                        st.write(f"**GPS Coordinates:** `{lat}, {lon}`")
                        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
                        st.markdown(f"[🚗 Open Google Maps Navigation]({maps_url})", unsafe_allow_html=True)
                else:
                    st.info("ℹ️ ස්ථානය තවම Save කර නොමැත.")

                # Location Form
                with st.form(key=f"form_{idx}"):
                    st.markdown("**Update / Save Location Details:**")
                    address = st.text_area("ලිපිනය / පාර (Address / Directions)", value=saved_loc.iloc[-1]['Address'] if not saved_loc.empty else "", height=70)
                    landmark = st.text_input("ආසන්නතම සලකුණ (Landmark)", value=saved_loc.iloc[-1]['Landmark'] if not saved_loc.empty else "")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        latitude = st.text_input("අක්ෂාංශ (Latitude)", value=saved_loc.iloc[-1]['Latitude'] if not saved_loc.empty else "")
                    with c2:
                        longitude = st.text_input("දේශාංශ (Longitude)", value=saved_loc.iloc[-1]['Longitude'] if not saved_loc.empty else "")

                    officer = st.text_input("Officer ID / Name", value="")

                    if st.form_submit_button("💾 Save Location"):
                        new_record = pd.DataFrame([{
                            'Customer Code': cust_code_str,
                            'Customer NIC': str(nic_val),
                            'Facility Code': str(fac_val),
                            'Address': address,
                            'Landmark': landmark,
                            'Latitude': latitude,
                            'Longitude': longitude,
                            'Updated By': officer
                        }])
                        df_locs = pd.concat([df_locs, new_record], ignore_index=True)
                        df_locs.to_csv(LOCATIONS_FILE, index=False)
                        st.success("ස්ථානය සාර්ථකව Save විය!")
                        st.rerun()

    else:
        st.info("💡 සෙවීම සඳහා උඩ Search Bar එකේ Customer ගේ NIC, Code, Facility No හෝ Name එක ටයිප් කරන්න.")
