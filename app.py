import streamlit as st
import pandas as pd
import os
import glob

# Page Setup
st.set_page_config(page_title="Customer Location Tracker", page_icon="📍", layout="centered")

LOCATIONS_FILE = "customer_locations.csv"

def clean_text(val):
    """NaN, None හෝ Float අගයන් ආරක්ෂිතව Clean Text බවට හැරවීමට"""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    return "" if val_str.lower() in ["nan", "none", "null"] else val_str

@st.cache_data(ttl=0)
def load_data():
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
        return pd.read_csv(LOCATIONS_FILE, dtype=str)
    return pd.DataFrame(columns=['Customer Code', 'Customer NIC', 'Facility Code', 'Address', 'Landmark', 'Latitude', 'Longitude', 'Updated By'])

def get_col_val(row, targets):
    for col in row.index:
        if str(col).strip().lower() in [t.lower() for t in targets]:
            val = row[col]
            return clean_text(val) if clean_text(val) else "N/A"
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

                # Existing Location Check
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

                # Location Form
                with st.form(key=f"form_{idx}"):
                    st.markdown("**Update / Save Location Details:**")
                    address = st.text_area("ලිපිනය / පාර (Address / Directions)", value=existing_addr, height=70)
                    landmark = st.text_input("ආසන්නතම සලකුණ (Landmark)", value=existing_land)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        latitude = st.text_input("අක්ෂාංශ (Latitude)", value=existing_lat)
                    with c2:
                        longitude = st.text_input("දේශාංශ (Longitude)", value=existing_lon)

                    officer = st.text_input("Officer ID / Name", value="")

                    if st.form_submit_button("💾 Save Location"):
                        new_record = pd.DataFrame([{
                            'Customer Code': cust_code_str,
                            'Customer NIC': str(nic_val),
                            'Facility Code': str(fac_val),
                            'Address': address.strip(),
                            'Landmark': landmark.strip(),
                            'Latitude': latitude.strip(),
                            'Longitude': longitude.strip(),
                            'Updated By': officer.strip()
                        }])
                        df_locs = pd.concat([df_locs, new_record], ignore_index=True)
                        df_locs.to_csv(LOCATIONS_FILE, index=False)
                        st.success("ස්ථානය සාර්ථකව Save විය!")
                        st.rerun()

    else:
        st.info("💡 සෙවීම සඳහා උඩ Search Bar එකේ Customer ගේ NIC, Code, Facility No හෝ Name එක ටයිප් කරන්න.")
