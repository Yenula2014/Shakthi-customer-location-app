import streamlit as st
import pandas as pd
import os

# App Title & Layout Configuration
st.set_page_config(page_title="Customer Location Finder", page_icon="📍", layout="wide")

EXCEL_FILE = "NPL Report (1).xlsx Location Bandaragama.xlsx"
LOCATIONS_FILE = "customer_locations.csv"

def clean_val(val):
    """Numbers සහ Text හරියාකාරව Clean කිරීමට Helper Function එකක්"""
    if pd.isna(val):
        return ""
    if isinstance(val, float):
        if val.is_integer():
            val = int(val)
    return str(val).strip().upper()

@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None
    
    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        st.error(f"Excel file එක කියවීමේ දෝෂයක්: {e}")
        return None
    
    # Column Names වල දෙපස අමතර spaces ඉවත් කිරීම
    df.columns = df.columns.astype(str).str.strip()
    
    # Cleaning columns for smooth searching
    if 'Customer NIC' in df.columns:
        df['Search_NIC'] = df['Customer NIC'].apply(clean_val)
    else:
        df['Search_NIC'] = ""

    if 'Customer Code' in df.columns:
        df['Search_CustomerCode'] = df['Customer Code'].apply(clean_val)
    else:
        df['Search_CustomerCode'] = ""

    if 'Facility Status' in df.columns:
        df['Search_FacilityCode'] = df['Facility Status'].apply(clean_val)
    elif 'Facility Code' in df.columns:
        df['Search_FacilityCode'] = df['Facility Code'].apply(clean_val)
    else:
        df['Search_FacilityCode'] = ""

    if 'Customer Name' in df.columns:
        df['Search_Name'] = df['Customer Name'].apply(clean_val)
    else:
        df['Search_Name'] = ""

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
st.markdown("Search by **NIC**, **Customer Code**, **Facility Number**, or **Customer Name**.")

if df_customers is None:
    st.error(f"Excel File එක '{EXCEL_FILE}' නමින් සොයාගත නොහැක! කාරුණිකව GitHub එකට Upload කර ඇති File Name එක පරීක්ෂා කරන්න.")
else:
    # Debug / Status view
    st.caption(f"📊 Total Loaded Records in Database: {len(df_customers)}")

    # Search Input Bar
    search_input = st.text_input("Enter Search Key (NIC / Customer Code / Facility No / Name):", "")
    search_query = search_input.strip().upper()

    if search_query:
        # Flexible Partial Matching (Contains)
        matched = df_customers[
            (df_customers['Search_NIC'].str.contains(search_query, regex=False, na=False)) |
            (df_customers['Search_CustomerCode'].str.contains(search_query, regex=False, na=False)) |
            (df_customers['Search_FacilityCode'].str.contains(search_query, regex=False, na=False)) |
            (df_customers['Search_Name'].str.contains(search_query, regex=False, na=False))
        ]

        if matched.empty:
            st.warning(f"No records found matching: **{search_query}**")
        else:
            st.success(f"Found {len(matched)} matching record(s).")
            
            for idx, row in matched.iterrows():
                st.divider()
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader("📋 Customer Details")
                    st.write(f"**Customer Name:** {row.get('Customer Name', 'N/A')}")
                    st.write(f"**NIC Number:** {row.get('Customer NIC', 'N/A')}")
                    st.write(f"**Customer Code:** {row.get('Customer Code', 'N/A')}")
                    st.write(f"**Facility Code:** {row.get('Facility Status', 'N/A')}")
                    st.write(f"**Center / Branch:** {row.get('Center', 'N/A')} ({row.get('Branch', 'N/A')})")
                    st.write(f"**Contact No:** {row.get('Customer Contact No', 'N/A')}")
                    
                    arrears = row.get('Total Arrears', 0)
                    try:
                        st.write(f"**Total Arrears:** LKR {float(arrears):,.2f}")
                    except:
                        st.write(f"**Total Arrears:** {arrears}")

                # Saved Location Check
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
