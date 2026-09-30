import streamlit as st
import pandas as pd
import os

# App Title & Layout Configuration
st.set_page_config(page_title="Customer Location Finder", page_icon="📍", layout="wide")

# Excel File name updated
EXCEL_FILE = "NPL Report (1).xlsx Location Bandaragama.xlsx"
LOCATIONS_FILE = "customer_locations.csv"

@st.cache_data
def load_data():
    if not os.path.exists(EXCEL_FILE):
        return None
    df = pd.read_excel(EXCEL_FILE)
    # Search fields string බවට හැරවීම
    df['Customer NIC'] = df['Customer NIC'].astype(str).str.strip().str.upper()
    df['Customer Code'] = df['Customer Code'].astype(str).str.strip().str.upper()
    df['Facility Code Real'] = df['Facility Status'].astype(str).str.strip().str.upper()
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
    st.error(f"Excel file '{EXCEL_FILE}' not found! Please make sure it is uploaded and named correctly.")
else:
    # Search Input Bar
    search_query = st.text_input("Enter NIC / Customer Code / Facility Number:", "").strip().upper()

    if search_query:
        # Search Query Matching
        matched = df_customers[
            (df_customers['Customer NIC'] == search_query) |
            (df_customers['Customer Code'] == search_query) |
            (df_customers['Facility Code Real'] == search_query) |
            (df_customers['Customer NIC'].str.contains(search_query, na=False)) |
            (df_customers['Customer Code'].str.contains(search_query, na=False)) |
            (df_customers['Facility Code Real'].str.contains(search_query, na=False))
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
                    st.write(f"**Customer Name:** {row['Customer Name']}")
                    st.write(f"**NIC Number:** {row['Customer NIC']}")
                    st.write(f"**Customer Code:** {row['Customer Code']}")
                    st.write(f"**Facility Code:** {row['Facility Status']}")
                    st.write(f"**Center / Branch:** {row['Center']} ({row['Branch']})")
                    st.write(f"**Contact No:** {row['Customer Contact No']}")
                    st.write(f"**Total Arrears:** LKR {row['Total Arrears']:,.2f}")

                # Saved Location Data Check
                existing_loc = df_locations[df_locations['Customer Code'] == str(row['Customer Code'])]

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
                                'Customer Code': str(row['Customer Code']),
                                'Customer NIC': str(row['Customer NIC']),
                                'Facility Code': str(row['Facility Status']),
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