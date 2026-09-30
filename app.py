import streamlit as st
import pandas as pd
import os
import glob

# Page Configuration
st.set_page_config(
    page_title="Customer Location Finder",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Modern UI
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748B;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        width: 100%;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

LOCATIONS_FILE = "customer_locations.csv"

@st.cache_data(ttl=0)
def load_smart_excel():
    files = glob.glob("*.xlsx") + glob.glob("*.xls")
    if not files:
        return None, "No Excel file found in root folder!"
    
    file_path = files[0]
    try:
        df = pd.read_excel(file_path)
        
        # Header check for merged or offset titles
        cols_str = " ".join([str(c) for c in df.columns]).lower()
        if "unnamed" in cols_str or "nic" not in cols_str:
            for r in range(1, 5):
                temp_df = pd.read_excel(file_path, header=r)
                temp_cols = " ".join([str(c) for c in temp_df.columns]).lower()
                if "nic" in temp_cols or "customer" in temp_cols:
                    df = temp_df
                    break
        
        df.columns = df.columns.astype(str).str.strip()
        df['Full_Search_Text'] = df.astype(str).apply(lambda row: ' '.join(row.values).lower(), axis=1)
        return df, os.path.basename(file_path)
    except Exception as e:
        return None, f"Error reading file: {e}"

def load_locations():
    if os.path.exists(LOCATIONS_FILE):
        return pd.read_csv(LOCATIONS_FILE, dtype=str)
    return pd.DataFrame(columns=[
        'Customer Code', 'Customer NIC', 'Facility Code', 
        'Address', 'Landmark', 'Latitude', 'Longitude', 'Updated By'
    ])

# Load Data
df, file_status = load_smart_excel()
df_locs = load_locations()

# Header Section
st.markdown('<div class="main-title">📍 Customer Location Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Search customer records and manage field locations effortlessly.</div>', unsafe_allow_html=True)

if df is None:
    st.error(f"❌ {file_status}")
else:
    # Stats row
    stat_col1, stat_col2 = st.columns(2)
    with stat_col1:
        st.info(f"📄 **Active File:** `{file_status}`")
    with stat_col2:
        st.success(f"📊 **Total Database Records:** `{len(df):,}`")

    # Search Bar
    search_query = st.text_input("🔍 Search Customer", placeholder="Type NIC, Customer Code, Name, or Facility No...").strip().lower()

    if search_query:
        matched_df = df[df['Full_Search_Text'].str.contains(search_query, regex=False, na=False)]

        if matched_df.empty:
            st.warning(f"No records found for **'{search_query}'**.")
        else:
            st.caption(f"Showing **{len(matched_df)}** result(s)")

            for idx, row in matched_df.iterrows():
                # Helper function for getting field values safely
                def get_val(possible_keys):
                    for k in row.index:
                        for pk in possible_keys:
                            if pk.lower() in str(k).lower():
                                return row[k]
                    return "N/A"

                nic_val = get_val(['Customer NIC', 'NIC'])
                code_val = get_val(['Customer Code', 'Code'])
                name_val = get_val(['Customer Name', 'Name'])
                fac_val = get_val(['Facility Status', 'Facility Code'])
                center_val = get_val(['Center'])
                branch_val = get_val(['Branch'])
                contact_val = get_val(['Customer Contact No', 'Contact'])
                arrears_val = get_val(['Total Arrears', 'Arrears'])

                cust_code_str = str(code_val).strip()
                saved_loc = df_locs[df_locs['Customer Code'] == cust_code_str]

                # Main Display Columns
                col1, col2 = st.columns([1, 1], gap="medium")

                with col1:
                    st.markdown("### 📋 Customer Profile")
                    st.markdown(f"""
                    **Customer Name:** {name_val}  
                    **NIC Number:** `{nic_val}`  
                    **Customer Code:** `{code_val}`  
                    **Facility No:** `{fac_val}`  
                    **Center & Branch:** {center_val} ({branch_val})  
                    **Contact No:** {contact_val}  
                    **Total Arrears:** `LKR {arrears_val}`
                    """)

                with col2:
                    st.markdown("### 🗺️ Location Details")
                    
                    if not saved_loc.empty:
                        loc_data = saved_loc.iloc[-1]
                        st.success("📍 **Saved Location Found**")
                        st.write(f"**Address:** {loc_data.get('Address', 'N/A')}")
                        st.write(f"**Landmark:** {loc_data.get('Landmark', 'N/A')}")
                        
                        lat_val = loc_data.get('Latitude', '')
                        lon_val = loc_data.get('Longitude', '')
                        if lat_val and lon_val:
                            maps_url = f"https://www.google.com/maps?q={lat_val},{lon_val}"
                            st.markdown(f"[🗺️ Open in Google Maps]({maps_url})", unsafe_allow_html=True)
                    else:
                        st.info("ℹ️ No location recorded yet. Add details below:")

                    # Compact Form inside expander or direct form
                    with st.form(key=f"form_{idx}"):
                        addr = st.text_area("Address / Directions", value=saved_loc.iloc[-1]['Address'] if not saved_loc.empty else "", height=80)
                        land = st.text_input("Nearest Landmark", value=saved_loc.iloc[-1]['Landmark'] if not saved_loc.empty else "")
                        
                        clat, clon = st.columns(2)
                        with clat:
                            lat = st.text_input("Latitude", value=saved_loc.iloc[-1]['Latitude'] if not saved_loc.empty else "")
                        with clon:
                            lon = st.text_input("Longitude", value=saved_loc.iloc[-1]['Longitude'] if not saved_loc.empty else "")
                        
                        officer = st.text_input("Officer Name / ID", value="")
                        
                        if st.form_submit_button("💾 Save Location"):
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

                st.divider()

    else:
        st.info("💡 **Getting Started:** Type any customer detail (NIC, Code, Name) in the search box above to view or update locations.")
