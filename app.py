import streamlit as st
import pandas as pd
import os
import glob

st.set_page_config(page_title="Customer Location Finder", page_icon="📍", layout="wide")

LOCATIONS_FILE = "customer_locations.csv"

@st.cache_data(ttl=0)
def load_excel_data():
    files = glob.glob("*.xlsx") + glob.glob("*.xls")
    if not files:
        return None, "No Excel file found in root directory!"
    
    file_path = files[0]
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.astype(str).str.strip()
        
        # සියලුම columns එකතු කර එකම Full_Search_Text column එකක් සෑදීම
        df['Full_Search_Text'] = df.astype(str).apply(lambda row: ' '.join(row.values).lower(), axis=1)
        
        return df, os.path.basename(file_path)
    except Exception as e:
        return None, f"Error reading excel file: {e}"

def load_locations():
    if os.path.exists(LOCATIONS_FILE):
        return pd.read_csv(LOCATIONS_FILE, dtype=str)
    return pd.DataFrame(columns=[
        'Customer Code', 'Customer NIC', 'Facility Code', 
        'Address', 'Landmark', 'Latitude', 'Longitude', 'Updated By'
    ])

st.title("📍 Customer Location Lookup & Entry")

df, file_status = load_excel_data()
df_locs = load_locations()

if df is None:
    st.error(f"❌ {file_status}")
    st.info("💡 කරුණාකර Excel ගොනුව GitHub Repository එකට හරියාකාරව Upload කර ඇත්දැයි බලන්න.")
else:
    st.success(f"📁 Loaded File: **{file_status}** | 📊 Total Records: **{len(df)}**")

    # Debug Section (Show Columns & Sample Data)
    with st.expander("🔍 View Detected Excel Columns & Data Preview"):
        st.write("**Detected Columns in Excel:**", list(df.columns))
        st.dataframe(df.head(5))

    st.divider()

    # Search Bar
    query = st.text_input("🔍 Enter Search Term (NIC / Customer Code / Name / Facility No):", "").strip().lower()

    if query:
        # Full Text Match across all fields
        matched_df = df[df['Full_Search_Text'].str.contains(query, regex=False, na=False)]

        if matched_df.empty:
            st.error(f"❌ No records found matching: **'{query}'**")
        else:
            st.success(f"✅ Found **{len(matched_df)}** matching record(s).")

            for idx, row in matched_df.iterrows():
                st.divider()
                col1, col2 = st.columns([1, 1])

                # Get Values safely using column fallback
                nic_val = row.get('Customer NIC', row.get('NIC', 'N/A'))
                code_val = row.get('Customer Code', row.get('Code', 'N/A'))
                name_val = row.get('Customer Name', row.get('Name', 'N/A'))
                fac_val = row.get('Facility Status', row.get('Facility Code', 'N/A'))
                center_val = row.get('Center', 'N/A')
                branch_val = row.get('Branch', 'N/A')
                contact_val = row.get('Customer Contact No', 'N/A')
                arrears_val = row.get('Total Arrears', 'N/A')

                with col1:
                    st.subheader("📋 Customer Details")
                    st.write(f"**Customer Name:** {name_val}")
                    st.write(f"**NIC Number:** {nic_val}")
                    st.write(f"**Customer Code:** {code_val}")
                    st.write(f"**Facility Status/No:** {fac_val}")
                    st.write(f"**Center / Branch:** {center_val} ({branch_val})")
                    st.write(f"**Contact No:** {contact_val}")
                    st.write(f"**Total Arrears:** {arrears_val}")

                cust_code_str = str(code_val).strip()
                saved_loc = df_locs[df_locs['Customer Code'] == cust_code_str]

                with col2:
                    st.subheader("🗺️ Location Details")

                    if not saved_loc.empty:
                        loc_data = saved_loc.iloc[-1]
                        st.info("📍 **Saved Location:**")
                        st.write(f"**Address:** {loc_data.get('Address', 'N/A')}")
                        st.write(f"**Landmark:** {loc_data.get('Landmark', 'N/A')}")
                        if loc_data.get('Latitude') and loc_data.get('Longitude'):
                            st.write(f"**GPS:** {loc_data['Latitude']}, {loc_data['Longitude']}")
                            st.markdown(f"[🔗 View in Google Maps](https://www.google.com/maps?q={loc_data['Latitude']},{loc_data['Longitude']})")
                    else:
                        st.warning("⚠️ නොදන්නා ස්ථානයකි (No location saved yet).")

                    with st.form(key=f"form_{idx}"):
                        st.markdown("**Enter / Update Location Information:**")
                        addr = st.text_area("Address / Directions", value=saved_loc.iloc[-1]['Address'] if not saved_loc.empty else "")
                        land = st.text_input("Landmark", value=saved_loc.iloc[-1]['Landmark'] if not saved_loc.empty else "")
                        
                        clat, clon = st.columns(2)
                        with clat:
                            lat = st.text_input("Latitude", value=saved_loc.iloc[-1]['Latitude'] if not saved_loc.empty else "")
                        with clon:
                            lon = st.text_input("Longitude", value=saved_loc.iloc[-1]['Longitude'] if not saved_loc.empty else "")
                        
                        officer = st.text_input("Officer Name/ID", value="")
                        
                        if st.form_submit_button("Save Location"):
                            new_row = pd.DataFrame([{
                                'Customer Code': cust_code_str,
                                'Customer NIC': str(nic_val),
                                'Facility Code': str(fac_val),
                                'Address': addr,
                                'Landmark': land,
                                'Latitude': lat,
                                'Longitude': lon,
                                'Updated By': officer
                            }])
                            df_locs = pd.concat([df_locs, new_row], ignore_index=True)
                            df_locs.to_csv(LOCATIONS_FILE, index=False)
                            st.success("Location saved successfully!")
                            st.rerun()

    else:
        st.info("💡 සෙවීම සඳහා උඩ Search Bar එකේ NIC / Name / Customer Code හි කොටසක් ටයිප් කරන්න.")
