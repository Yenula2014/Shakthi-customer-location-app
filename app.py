import streamlit as st
import pandas as pd
import os
import glob

# Page Config
st.set_page_config(page_title="Customer Location Finder", page_icon="📍", layout="wide")

LOCATIONS_FILE = "customer_locations.csv"

# Cache එක ඉවත් කර සෑම විටම අලුතින් Read කිරීමට (ttl=0)
@st.cache_data(ttl=0)
def get_dataset():
    # Folder එකේ ඇති Excel File සොයා ගැනීම
    files = glob.glob("*.xlsx") + glob.glob("*.xls")
    if not files:
        return None, "No Excel file found in root directory!"
    
    file_path = files[0]
    
    try:
        # Sheet එක Read කිරීම
        df = pd.read_excel(file_path)
    except Exception as e:
        return None, f"Error reading excel: {e}"

    # Column names clean කිරීම
    df.columns = df.columns.astype(str).str.strip()

    # Data Clean කර ගැනීම (Search පහසු කිරීමට)
    def clean_val(v):
        if pd.isna(v) or v is None:
            return ""
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        return str(v).strip()

    df['NIC_Clean'] = df['Customer NIC'].apply(clean_val) if 'Customer NIC' in df.columns else ""
    df['Code_Clean'] = df['Customer Code'].apply(clean_val) if 'Customer Code' in df.columns else ""
    df['Facility_Clean'] = df['Facility Status'].apply(clean_val) if 'Facility Status' in df.columns else ""
    df['Name_Clean'] = df['Customer Name'].apply(clean_val) if 'Customer Name' in df.columns else ""

    return df, os.path.basename(file_path)

def load_locations():
    if os.path.exists(LOCATIONS_FILE):
        return pd.read_csv(LOCATIONS_FILE, dtype=str)
    return pd.DataFrame(columns=[
        'Customer Code', 'Customer NIC', 'Facility Code', 
        'Address', 'Landmark', 'Latitude', 'Longitude', 'Updated By'
    ])

# Streamlit App UI
st.title("📍 Customer Location Lookup & Entry")

df, filename = get_dataset()
df_locs = load_locations()

if df is None:
    st.error(filename)
else:
    st.success(f"📁 Loaded File: **{filename}** | 📊 Total Customers: **{len(df)}**")

    # Search Bar
    query = st.text_input("🔍 Search Customer (Type NIC / Customer Code / Name / Facility No):", "").strip()

    if query:
        q = query.lower()
        # Case-insensitive substring matching
        match_mask = (
            df['NIC_Clean'].str.lower().str.contains(q, na=False) |
            df['Code_Clean'].str.lower().str.contains(q, na=False) |
            df['Facility_Clean'].str.lower().str.contains(q, na=False) |
            df['Name_Clean'].str.lower().str.contains(q, na=False)
        )
        matched_df = df[match_mask]

        if matched_df.empty:
            st.warning(f"❌ '{query}' සඳහා කිසිදු පාරිභෝගිකයෙකු හමු නොවීය (No records found).")
        else:
            st.success(f"✅ පාරිභෝගිකයින් {len(matched_df)} දෙනෙකු හමු විය.")

            for idx, row in matched_df.iterrows():
                st.divider()
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader("📋 Customer Information")
                    st.write(f"**Name:** {row.get('Customer Name', 'N/A')}")
                    st.write(f"**NIC:** {row.get('Customer NIC', 'N/A')}")
                    st.write(f"**Customer Code:** {row.get('Customer Code', 'N/A')}")
                    st.write(f"**Facility Status/No:** {row.get('Facility Status', 'N/A')}")
                    st.write(f"**Center:** {row.get('Center', 'N/A')} ({row.get('Branch', 'N/A')})")
                    st.write(f"**Contact No:** {row.get('Customer Contact No', 'N/A')}")
                    st.write(f"**Total Arrears:** {row.get('Total Arrears', 'N/A')}")

                cust_code = str(row['Code_Clean'])
                saved_loc = df_locs[df_locs['Customer Code'] == cust_code]

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
                        st.markdown("**Enter / Update Location:**")
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
                                'Customer Code': cust_code,
                                'Customer NIC': str(row['NIC_Clean']),
                                'Facility Code': str(row['Facility_Clean']),
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
        st.info("💡 සෙවීම සඳහා උඩ Search Bar එකේ NIC / Name / Customer Code ටයිප් කරන්න.")
