import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Customer Location Finder", page_icon="📍", layout="wide")

EXCEL_FILE = "NPL Report (1).xlsx Location Bandaragama.xlsx"
LOCATIONS_FILE = "customer_locations.csv"

def find_column(df, possible_names):
    """Excel එකේ Column හිස්තැන්/Case වෙනස් වුවත් හරියාකාරව සොයාගැනීමට"""
    for col in df.columns:
        clean_col = str(col).strip().lower()
        for name in possible_names:
            if clean_col == name.strip().lower():
                return col
    return None

def clean_str(val):
    """ඕනෑම Value එකක් (Float/Int/NaN) සුදුසු String එකක් බවට හැරවීමට"""
    if pd.isna(val) or val is None:
        return ""
    if isinstance(val, float):
        if val.is_integer():
            val = int(val)
    val_str = str(val).strip()
    return "" if val_str.lower() in ["nan", "none", "null"] else val_str

@st.cache_data(ttl=5)
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None
    
    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        st.error(f"Excel file එක කියවීමේ දෝෂයක්: {e}")
        return None

    # Column Mapping (හැකියාව ඇති සියලුම Header Names)
    nic_col = find_column(df, ['Customer NIC', 'NIC', 'NIC No', 'NIC Number'])
    code_col = find_column(df, ['Customer Code', 'Code', 'Cust Code'])
    facility_col = find_column(df, ['Facility Status', 'Facility Code', 'Facility No'])
    name_col = find_column(df, ['Customer Name', 'Name', 'Full Name'])

    # Search සඳහා අවශ්‍ය Cleaned Columns සැකසීම
    df['Search_NIC'] = df[nic_col].apply(clean_str) if nic_col else ""
    df['Search_CustomerCode'] = df[code_col].apply(clean_str) if code_col else ""
    df['Search_FacilityCode'] = df[facility_col].apply(clean_str) if facility_col else ""
    df['Search_Name'] = df[name_col].apply(clean_str) if name_col else ""

    # Real Columns Store කිරීම
    df['Display_NIC'] = df[nic_col] if nic_col else ""
    df['Display_Code'] = df[code_col] if code_col else ""
    df['Display_Facility'] = df[facility_col] if facility_col else ""
    df['Display_Name'] = df[name_col] if name_col else ""

    return df

def load_locations():
    if os.path.exists(LOCATIONS_FILE):
        return pd.read_csv(LOCATIONS_FILE, dtype=str)
    else:
        return pd.DataFrame(columns=[
            'Customer Code', 'Customer NIC', 'Facility Code', 
            'Address', 'Landmark', 'Latitude', 'Longitude', 'Updated By'
        ])

df_customers = load_data()
df_locations = load_locations()

st.title("📍 Customer Location Lookup & Entry App")

if df_customers is None:
    st.error(f"Excel File එක '{EXCEL_FILE}' නමින් සොයාගත නොහැක! GitHub එකට Upload කර ඇති File Name එක පරීක්ෂා කරන්න.")
else:
    st.info(f"📊 දත්ත පද්ධතියේ මුළු පාරිභෝගිකයින් ගණන: **{len(df_customers)}**")

    search_type = st.radio("Search Method:", ["Type Query (NIC / Code / Name)", "Select Customer from List"], horizontal=True)

    matched = pd.DataFrame()

    if search_type == "Type Query (NIC / Code / Name)":
        search_input = st.text_input("Enter Search Key (e.g. 647180663V or C/MF/5/000077):", "")
        query = search_input.strip().upper()

        if query:
            matched = df_customers[
                (df_customers['Search_NIC'].str.upper().str.contains(query, regex=False, na=False)) |
                (df_customers['Search_CustomerCode'].str.upper().str.contains(query, regex=False, na=False)) |
                (df_customers['Search_FacilityCode'].str.upper().str.contains(query, regex=False, na=False)) |
                (df_customers['Search_Name'].str.upper().str.contains(query, regex=False, na=False))
            ]

    else:
        # Construct Label Options Correctly
        options = ["-- Select Customer --"] + [
            f"{row['Search_NIC']} | {row['Search_CustomerCode']} | {row['Search_Name']}" 
            for _, row in df_customers.iterrows()
        ]
        selected_option = st.selectbox("Choose a customer:", options)
        
        if selected_option != "-- Select Customer --":
            selected_nic = selected_option.split(" | ")[0].strip()
            selected_code = selected_option.split(" | ")[1].strip()
            
            matched = df_customers[
                (df_customers['Search_NIC'] == selected_nic) & 
                (df_customers['Search_CustomerCode'] == selected_code)
            ]

    # Display Results
    if not matched.empty:
        st.success(f"Found {len(matched)} matching record(s).")
        
        for idx, row in matched.iterrows():
            st.divider()
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📋 Customer Details")
                st.write(f"**Customer Name:** {row.get('Display_Name', 'N/A')}")
                st.write(f"**NIC Number:** {row.get('Display_NIC', 'N/A')}")
                st.write(f"**Customer Code:** {row.get('Display_Code', 'N/A')}")
                st.write(f"**Facility Code:** {row.get('Display_Facility', 'N/A')}")
                st.write(f"**Center / Branch:** {row.get('Center', 'N/A')} ({row.get('Branch', 'N/A')})")
                st.write(f"**Contact No:** {row.get('Customer Contact No', 'N/A')}")
                
                arrears = row.get('Total Arrears', 0)
                try:
                    st.write(f"**Total Arrears:** LKR {float(arrears):,.2f}")
                except:
                    st.write(f"**Total Arrears:** {arrears}")

            cust_code_str = str(row.get('Search_CustomerCode', ''))
            existing_loc = df_locations[df_locations['Customer Code'] == cust_code_str]

            with col2:
                st.subheader("🗺️ Location Entry")
                
                if not existing_loc.empty:
                    current_loc = existing_loc.iloc[-1]
                    st.info("📍 **Current Saved Location:**")
                    st.write(f"**Address:** {current_loc.get('Address', 'N/A')}")
                    st.write(f"**Landmark:** {current_loc.get('Landmark', 'N/A')}")
                    if current_loc.get('Latitude') and current_loc.get('Longitude'):
                        st.write(f"**GPS:** {current_loc['Latitude']}, {current_loc['Longitude']}")
                        maps_url = f"https://www.google.com/maps?q={current_loc['Latitude']},{current_loc['Longitude']}"
                        st.markdown(f"[🔗 View in Google Maps]({maps_url})", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ නොදන්නා ස්ථානයකි (No location saved yet). පහත Form එකෙන් එකතු කරන්න.")

                with st.form(key=f"loc_form_{idx}"):
                    st.markdown("**Enter / Update Location Information**")
                    address = st.text_area("Address / Directions", value=existing_loc.iloc[-1]['Address'] if not existing_loc.empty else "")
                    landmark = st.text_input("Nearest Landmark", value=existing_loc.iloc[-1]['Landmark'] if not existing_loc.empty else "")
                    
                    c_lat, c_long = st.columns(2)
                    with c_lat:
                        lat = st.text_input("Latitude (Optional)", value=existing_loc.iloc[-1]['Latitude'] if not existing_loc.empty else "")
                    with c_long:
                        lon = st.text_input("Longitude (Optional)", value=existing_loc.iloc[-1]['Longitude'] if not existing_loc.empty else "")

                    updated_by = st.text_input("Officer Name / ID", value="")
                    
                    submit = st.form_submit_button("Save Location")

                    if submit:
                        new_record = pd.DataFrame([{
                            'Customer Code': cust_code_str,
                            'Customer NIC': str(row.get('Search_NIC', '')),
                            'Facility Code': str(row.get('Search_FacilityCode', '')),
                            'Address': address,
                            'Landmark': landmark,
                            'Latitude': lat,
                            'Longitude': lon,
                            'Updated By': updated_by
                        }])

                        df_locations = pd.concat([df_locations, new_record], ignore_index=True)
                        df_locations.to_csv(LOCATIONS_FILE, index=False)
                        st.success("Location successfully saved!")
                        st.rerun()

    elif 'search_input' in locals() and search_input:
        st.error(f"No records found matching: **{search_input}**")
