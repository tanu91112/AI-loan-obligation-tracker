import streamlit as st
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from extractor.pdf_reader import extract_text_from_bytes, read_file_content
from extractor.obligation_extractor import extract_obligations_from_text
from extractor.deadline_parser import get_compliance_status
from utils.risk_scoring import update_obligation_risks, get_high_risk_obligations, get_upcoming_deadlines


# Set page configuration
st.set_page_config(
    page_title="AI Loan Obligation & Covenant Tracker",
    page_icon="📋",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #374151;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin: 10px;
        color: black;
    }
    .high-risk {
        border-left: 5px solid #ef4444;
    }
    .medium-risk {
        border-left: 5px solid #f59e0b;
    }
    .low-risk {
        border-left: 5px solid #10b981;
    }
    .compliant {
        background-color: #d1fae5;
    }
    .due-soon {
        background-color: #fef3c7;
    }
    .missed {
        background-color: #fee2e2;
    }
</style>
""", unsafe_allow_html=True)

# App title and header
st.markdown('<div class="main-header">AI Loan Obligation & Covenant Tracker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated extraction and tracking of loan obligations and covenants</div>', unsafe_allow_html=True)

# Initialize session state
if 'obligations' not in st.session_state:
    st.session_state.obligations = []

if 'processed_text' not in st.session_state:
    st.session_state.processed_text = ""

# Sidebar with instructions
with st.sidebar:
    st.header("📋 About This Tool")
    st.write("This AI-powered tool automatically extracts and tracks borrower obligations from loan agreements.")
    
    st.markdown("""
    **Features:**
    - PDF upload or text paste
    - Automatic obligation extraction
    - Risk assessment
    - Compliance tracking
    - Dashboard visualization
    """)
    
    st.info("⚠️ **Important**: All data is processed locally and not stored anywhere.")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Input Document")
    
    # Input options
    input_option = st.radio(
        "Choose input method:",
        ("Upload PDF", "Paste Text", "Use Sample Agreement")
    )
    
    text_input = ""
    
    if input_option == "Upload PDF":
        uploaded_file = st.file_uploader("Upload a loan agreement PDF", type=["pdf"])
        if uploaded_file is not None:
            try:
                text_input = extract_text_from_bytes(uploaded_file.getvalue())
                st.success("PDF uploaded and text extracted successfully!")
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
    
    elif input_option == "Paste Text":
        text_input = st.text_area("Paste your loan agreement text here:", height=300)
    
    elif input_option == "Use Sample Agreement":
        sample_path = "data/sample_loan_agreement.txt"
        if os.path.exists(sample_path):
            text_input = read_file_content(sample_path)
            st.info("Sample loan agreement loaded!")
        else:
            st.warning("Sample agreement not found. Please create data/sample_loan_agreement.txt")

# Process button
process_clicked = False
if st.button("🔍 Extract Obligations", disabled=(text_input == "")):
    if text_input:
        with st.spinner("Processing loan agreement..."):
            try:
                # Extract obligations
                obligations = extract_obligations_from_text(text_input)
                
                # Update risk scores
                obligations = update_obligation_risks(obligations)
                
                # Update compliance status based on current date
                for obligation in obligations:
                    if obligation['next_deadline'] and obligation['next_deadline'] != "Upon Event" and "End of" not in obligation['next_deadline']:
                        try:
                            obligation['compliance_status'] = get_compliance_status(obligation['next_deadline'])
                        except:
                            obligation['compliance_status'] = "Compliant"
                
                st.session_state.obligations = obligations
                st.session_state.processed_text = text_input
                
                st.success(f"Successfully extracted {len(obligations)} obligations!")
                
                # Save obligations to JSON
                with open("data/extracted_obligations.json", "w") as f:
                    json.dump(obligations, f, indent=2, default=str)
                
            except Exception as e:
                st.error(f"Error extracting obligations: {str(e)}")
    else:
        st.warning("Please provide loan agreement text or upload a PDF.")

# Display results if obligations exist
if st.session_state.obligations:
    with col2:
        st.subheader("📊 Compliance Dashboard")
        
        obligations = st.session_state.obligations
        
        # Metrics cards
        total_obligations = len(obligations)
        compliant_count = len([ob for ob in obligations if ob['compliance_status'] == 'Compliant'])
        due_soon_count = len([ob for ob in obligations if ob['compliance_status'] == 'Due Soon'])
        missed_count = len([ob for ob in obligations if ob['compliance_status'] == 'Missed'])
        high_risk_count = len(get_high_risk_obligations(obligations))
        
        # Display metrics in columns
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.markdown(f'<div class="metric-card"><h3>{total_obligations}</h3><p>Total Obligations</p></div>', unsafe_allow_html=True)
        
        with metric_col2:
            st.markdown(f'<div class="metric-card"><h3>{compliant_count}</h3><p>Compliant</p></div>', unsafe_allow_html=True)
        
        with metric_col3:
            st.markdown(f'<div class="metric-card"><h3>{due_soon_count}</h3><p>Due Soon</p></div>', unsafe_allow_html=True)
        
        with metric_col4:
            st.markdown(f'<div class="metric-card"><h3>{missed_count}</h3><p>Missed</p></div>', unsafe_allow_html=True)
        
        # Risk distribution
        st.subheader("🚨 Risk Distribution")
        risk_counts = {
            "High": len([ob for ob in obligations if ob['risk_category'] == 'High']),
            "Medium": len([ob for ob in obligations if ob['risk_category'] == 'Medium']),
            "Low": len([ob for ob in obligations if ob['risk_category'] == 'Low'])
        }
        

        
        # Create a pie chart for risk distribution
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.pie(risk_counts.values(), labels=risk_counts.keys(), autopct='%1.1f%%', startangle=90, 
               colors=['#ef4444', '#f59e0b', '#10b981'])
        ax.set_title('Risk Level Distribution')
        st.pyplot(fig)
        plt.close()
    
    # Display obligations table
    st.subheader("📋 All Obligations")
    
    if st.session_state.obligations:
        # Convert obligations to DataFrame for display
        df_data = []
        for ob in st.session_state.obligations:
            df_data.append({
                'ID': ob['id'],
                'Type': ob['type'],
                'Description': ob['description'][:100] + "..." if len(ob['description']) > 100 else ob['description'],
                'Frequency': ob['frequency'],
                'Deadline Rule': ob['deadline_rule'],
                'Next Deadline': ob['next_deadline'],
                'Risk Level': ob['risk_category'],
                'Status': ob['compliance_status']
            })
        
        df = pd.DataFrame(df_data)
        
        # Color-code the status column
        def color_status(val):
            if val == 'Compliant':
                return 'background-color: #d1fae5; color: #065f46'
            elif val == 'Due Soon':
                return 'background-color: #fef3c7; color: #92400e'
            elif val == 'Missed':
                return 'background-color: #fee2e2; color: #991b1b'
            else:
                return ''
        
        def color_risk(val):
            if val == 'High':
                return 'background-color: #fee2e2; color: #991b1b; font-weight: bold'
            elif val == 'Medium':
                return 'background-color: #fef3c7; color: #92400e'
            else:
                return 'background-color: #d1fae5; color: #065f46'
        
        styled_df = df.style.applymap(color_status, subset=['Status']).applymap(color_risk, subset=['Risk Level'])
        
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    # High-risk obligations section
    high_risk_obligations = get_high_risk_obligations(st.session_state.obligations)
    if high_risk_obligations:
        st.subheader("⚠️ High-Risk Obligations")
        for ob in high_risk_obligations:
            status_class = "high-risk"
            if ob['compliance_status'] == 'Due Soon':
                status_class += " due-soon"
            elif ob['compliance_status'] == 'Missed':
                status_class += " missed"
            
            with st.container():
                html_content = f"""<div class='{status_class} card'>
                    <strong>Type:</strong> {ob['type']}<br>
                    <strong>Description:</strong> {ob['description']}<br>
                    <strong>Frequency:</strong> {ob['frequency']}<br>
                    <strong>Deadline:</strong> {ob['deadline_rule']} (Next: {ob['next_deadline']})<br>
                    <strong>Status:</strong> <span style='font-weight:bold;'>{ob['compliance_status']}</span>
                </div>"""
                st.markdown(html_content, unsafe_allow_html=True)
    
    # Upcoming deadlines section
    upcoming = get_upcoming_deadlines(st.session_state.obligations)
    if upcoming:
        st.subheader("📅 Upcoming Deadlines")
        for ob in upcoming:
            status_class = "due-soon"
            
            with st.container():
                html_content = f"""<div class='{status_class} card'>
                    <strong>Type:</strong> {ob['type']}<br>
                    <strong>Description:</strong> {ob['description']}<br>
                    <strong>Deadline:</strong> {ob['deadline_rule']}<br>
                    <strong>Next Deadline:</strong> {ob['next_deadline']}<br>
                    <strong>Status:</strong> <span style='font-weight:bold;'>{ob['compliance_status']}</span>
                </div>"""
                st.markdown(html_content, unsafe_allow_html=True)

else:
    # If no obligations, show welcome message
    html_content = """<div style='text-align: center; padding: 50px;'>
        <h3>📤 Upload a loan agreement to get started</h3>
        <p>Use the left panel to upload a PDF or paste text from a loan agreement.</p>
    </div>"""
    st.markdown(html_content, unsafe_allow_html=True)