import streamlit as st
import pandas as pd
import os

# App Title & Layout Configuration
st.set_page_config(page_title="Customer Location Finder", page_icon="📍", layout="wide")

EXCEL_FILE = "NPL Report (1).xlsx Location Bandaragama.xlsx"
LOCATIONS_FILE = "customer_locations.csv"

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None
    
    # Excel file එක කියවීම
    df = pd.read_excel(EXCEL_FILE)
    
    # Column names වල අගට/මුලට ඇති Spaces ඉවත් කිරීම (Strip spaces from headers)
    df.columns = df.columns.astype(str).str.strip()
    
    # Search fields string බවට හැරවීම (Safe Column Matching)
    nic_col = [c for c in df.columns if 'NIC' in c.upper()]
    cust_code_col = [c for c in df.columns if 'CUSTOMER CODE' in c.upper()]
    facility_col = [c for c in df.columns if 'FACILITY STATUS' in c.upper() or 'FACILITY CODE' in c.upper()]

    # Standard names සාදා ගැනීම
    if nic_col:
        df['Search_NIC'] = df[nic_col[0]].astype(str).str.strip().str.upper()
    else:
        df['Search_NIC'] = ""

    if cust_code_col:
        df['Search_CustCode'] = df[cust_code_col[0]].astype(str).str.strip().str.upper()
    else:
        df['Search_CustCode'] = ""

    if facility_col:
        df['Search_Facility'] = df[facility_col[0]].astype(str).str.strip().str.upper()
    else:
        df['Search_Facility'] = ""

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
st.markdown("Search by **NIC**, **Customer Code**, or **Facility Number** to view details and save location.")

if df_customers is None:
    st.error(f"Excel file '{EXCEL_FILE}' not found! Please make sure it is uploaded and named correctly in your GitHub repository.")
else:
    # Search Input Bar
    search_query = st.text_input("Enter NIC / Customer Code / Facility Number:", "").strip().upper()

    if search_query:
        # Search Query Matching
        matched = df_customers[
            (df_customers['Search_NIC'] == search_query) |
            (df_customers['Search_CustCode'] == search_query) |
            (df_customers['Search_Facility'] == search_query) |
            (df_customers['Search_NIC'].str.contains(search_query, na=False)) |
            (df_customers['Search_CustCode'].str.contains(search_query, na=False)) |
            (df_customers['Search_Facility'].str.contains(search_query, na=False))
        ]

        if matched.empty:
            st.warning(f"No records found matching: **{search_query}**")
        else:
            st.success(f"Found {len(matched)} matching record(s).")
            
            for idx, row in matched.iterrows():
                st.divider()
                col1, col2 = st.columns([1, 1])

                # Get Values safely
                cust_name = row.get('Customer Name', 'N/A')
                cust_nic = row.get('Customer NIC', 'N/A')
                cust_code = row.get('Customer Code', 'N/A')
                fac_code = row.get('Facility Status', row.get('Facility Code', 'N/A'))
                center = row.get('Center', 'N/A')
                branch = row.get('Branch', 'N/A')
                contact = row.get('Customer Contact No', 'N/A')
                arrears = row.get('Total Arrears', 0)

                with col1:
                    st.subheader("📋 Customer Details")
                    st.write(f"**Customer Name:** {cust_name}")
                    st.write(f"**NIC Number:** {cust_nic}")
                    st.write(f"**Customer Code:** {cust_code}")
                    st.write(f"**Facility Code:** {fac_code}")
                    st.write(f"**Center / Branch:** {center} ({branch})")
                    st.write(f"**Contact No:** {contact}")
                    try:
                        st.write(f"**Total Arrears:** LKR {float(arrears):,.2f}")
                    except:
                        st.write(f"**Total Arrears:** LKR {arrears}")

                # Saved Location Data Check
                existing_loc = df_locations[df_locations['Customer Code'] == str(cust_code)]

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
                                'Customer Code': str(cust_code),
                                'Customer NIC': str(cust_nic),
                                'Facility Code': str(fac_code),
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
