import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Mountain Sickness Analysis",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-low {
        background-color: #4CAF50;
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .risk-moderate {
        background-color: #FF9800;
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .risk-high {
        background-color: #F44336;
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .recommendation-box {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1E88E5;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
        margin: 1rem 0;
    }
    .danger-box {
        background-color: #FFEBEE;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #F44336;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessment_complete' not in st.session_state:
    st.session_state.assessment_complete = False

def calculate_ams_score(symptoms):
    """Calculate Lake Louise AMS Score"""
    score_map = {
        'None': 0,
        'Mild': 1,
        'Moderate': 2,
        'Severe': 3
    }
    total_score = sum(score_map.get(symptoms[key], 0) for key in symptoms)
    return total_score

def assess_ams_severity(score):
    """Assess AMS severity based on Lake Louise Score"""
    if score == 0:
        return "No AMS"
    elif 3 <= score <= 5:
        return "Mild AMS"
    elif 6 <= score <= 12:
        return "Moderate-Severe AMS"
    else:
        return "No AMS"

def calculate_risk_category(history, altitude, ascent_rate, age):
    """Calculate overall risk category"""
    risk_score = 0
    
    # History factor
    if history == "HAPE or HACE":
        risk_score += 3
    elif history == "Moderate-Severe AMS":
        risk_score += 2
    elif history == "Mild AMS":
        risk_score += 1
    
    # Altitude factor
    if altitude > 3500:
        risk_score += 2
    elif altitude >= 2800:
        risk_score += 1
    
    # Ascent rate factor
    if ascent_rate == ">500 m/d without extra acclimatization days":
        risk_score += 2
    elif ascent_rate == "≥500 m/d with extra acclimatization days":
        risk_score += 1
    
    # Age factor (children and elderly at slightly higher risk)
    if age < 12 or age > 65:
        risk_score += 1
    
    if risk_score >= 5:
        return "High"
    elif risk_score >= 3:
        return "Moderate"
    else:
        return "Low"

def get_prevention_recommendations(risk_category, altitude, has_history):
    """Get personalized prevention recommendations"""
    recommendations = []
    
    # Gradual ascent
    recommendations.append({
        "title": "⛰️ Gradual Ascent (Primary Prevention)",
        "details": [
            "Sleep no more than 500m higher each night above 3000m",
            "Include a rest day every 3-4 days",
            "Consider spending a night at intermediate altitude (1500-2000m) before going higher",
            f"Target sleeping elevation: {altitude}m"
        ]
    })
    
    # Medication recommendations based on risk
    if risk_category in ["Moderate", "High"]:
        medications = {
            "title": "💊 Pharmacological Prevention",
            "details": [
                "**Acetazolamide (Recommended)**:",
                "  • Dose: 125mg every 12 hours",
                "  • Start: Night before ascent",
                "  • Duration: Continue for 2 days at highest altitude",
                "  • High-risk situations: Consider 250mg every 12 hours",
                "",
                "**Alternative: Dexamethasone**:",
                "  • Dose: 2mg every 6 hours or 4mg every 12 hours",
                "  • Use only if acetazolamide contraindicated",
                "  • NOT recommended for children",
                "",
                "**Ibuprofen (Second-line)**:",
                "  • Dose: 600mg every 8 hours",
                "  • Less effective than acetazolamide",
                "  • Can be used if allergic to acetazolamide"
            ]
        }
        recommendations.append(medications)
    
    if has_history:
        hape_prevention = {
            "title": "🫁 HAPE Prevention (For Susceptible Individuals)",
            "details": [
                "**Nifedipine (Extended Release)**:",
                "  • Dose: 30mg every 12 hours",
                "  • Start: Day before ascent",
                "  • Duration: Continue for 4 days at highest altitude",
                "",
                "**Alternative: Tadalafil**:",
                "  • Dose: 10mg every 12 hours",
                "  • Use if nifedipine not available",
                "",
                "Monitor for hypotension with these medications"
            ]
        }
        recommendations.append(hape_prevention)
    
    # General recommendations
    general = {
        "title": "🎯 General Recommendations",
        "details": [
            "Stay well hydrated (but avoid overhydration)",
            "Avoid alcohol and sedatives",
            "Eat high-carbohydrate diet",
            "Avoid strenuous exercise on first day",
            "Listen to your body and communicate symptoms",
            "Know the symptoms of altitude illness"
        ]
    }
    recommendations.append(general)
    
    return recommendations

def get_treatment_recommendations(ams_severity, has_hace_symptoms, has_hape_symptoms):
    """Get treatment recommendations based on symptoms"""
    treatments = []
    
    if ams_severity == "Mild AMS":
        treatments.append({
            "urgency": "moderate",
            "title": "Treatment for Mild AMS",
            "actions": [
                "✅ STOP ascending - stay at current altitude",
                "✅ Rest and allow acclimatization (1-3 days)",
                "✅ Treat symptoms:",
                "   • Headache: Ibuprofen 600mg every 8h or Acetaminophen 1000mg every 8h",
                "   • Nausea: Antiemetics as needed",
                "✅ Ensure adequate hydration",
                "✅ Consider acetazolamide 250mg every 12h",
                "⚠️ Monitor for worsening symptoms",
                "⚠️ Descend if symptoms worsen or don't improve in 24-48 hours"
            ]
        })
    
    elif ams_severity == "Moderate-Severe AMS":
        treatments.append({
            "urgency": "high",
            "title": "Treatment for Moderate-Severe AMS",
            "actions": [
                "🚨 DESCEND immediately (at least 300-1000m or until symptoms resolve)",
                "🚨 Do NOT ascend further",
                "💊 Dexamethasone: 4mg every 6 hours (oral/IV/IM)",
                "💊 Consider adding Acetazolamide: 250mg every 12 hours",
                "💊 Treat symptoms (pain, nausea)",
                "🫁 Supplemental oxygen if available (target SpO2 >90%)",
                "⚠️ Do not descend alone",
                "⚠️ Seek medical attention",
                "⚠️ Watch for signs of HACE (ataxia, confusion)"
            ]
        })
    
    if has_hace_symptoms:
        treatments.append({
            "urgency": "emergency",
            "title": "⚠️ MEDICAL EMERGENCY - HACE Treatment",
            "actions": [
                "🚨 IMMEDIATE DESCENT - This is life-threatening!",
                "🚨 Call for emergency evacuation",
                "💊 Dexamethasone: 8mg immediately, then 4mg every 6 hours",
                "🫁 Supplemental oxygen: Target SpO2 >90%",
                "🎒 Portable hyperbaric chamber if descent delayed",
                "👥 Patient should NOT descend alone",
                "🏥 Transfer to medical facility urgently",
                "⚠️ Do not give oral medications if altered mental status"
            ]
        })
    
    if has_hape_symptoms:
        treatments.append({
            "urgency": "emergency",
            "title": "⚠️ MEDICAL EMERGENCY - HAPE Treatment",
            "actions": [
                "🚨 IMMEDIATE DESCENT (300-1000m minimum)",
                "🚨 Minimize exertion during descent",
                "🫁 Supplemental oxygen: Target SpO2 >90%",
                "💊 Nifedipine ER: 30mg every 12 hours (if descent delayed/impossible)",
                "🎒 Portable hyperbaric chamber if oxygen unavailable",
                "⚠️ Keep patient warm",
                "🏥 Evacuate to medical facility",
                "⚠️ May need ICU-level care"
            ]
        })
    
    if not treatments:
        treatments.append({
            "urgency": "low",
            "title": "No Current Altitude Illness",
            "actions": [
                "✅ Continue monitoring for symptoms",
                "✅ Follow prevention guidelines",
                "✅ Ascend gradually if going higher",
                "✅ Stay hydrated and well-nourished"
            ]
        })
    
    return treatments

def symptom_checker():
    """Interactive symptom checker for current illness"""
    st.subheader("🏥 Symptom Checker - Do you have any of these symptoms now?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### AMS Symptoms (Lake Louise Score)")
        symptoms = {}
        symptoms['headache'] = st.selectbox(
            "Headache",
            ['None', 'Mild', 'Moderate', 'Severe'],
            help="Headache is the cardinal symptom of AMS"
        )
        symptoms['nausea'] = st.selectbox(
            "Gastrointestinal symptoms (nausea/vomiting/loss of appetite)",
            ['None', 'Mild', 'Moderate', 'Severe']
        )
        symptoms['fatigue'] = st.selectbox(
            "Fatigue/weakness",
            ['None', 'Mild', 'Moderate', 'Severe']
        )
        symptoms['dizziness'] = st.selectbox(
            "Dizziness/lightheadedness",
            ['None', 'Mild', 'Moderate', 'Severe']
        )
    
    with col2:
        st.markdown("### HACE Warning Signs")
        hace_symptoms = {
            'ataxia': st.checkbox("Difficulty walking/balance problems (ataxia)", help="CRITICAL: Cannot walk heel-to-toe in straight line"),
            'confusion': st.checkbox("Confusion/altered mental status", help="CRITICAL: Disorientation, bizarre behavior"),
            'severe_lassitude': st.checkbox("Severe tiredness/inability to care for self", help="CRITICAL: Cannot perform basic tasks")
        }
        
        st.markdown("### HAPE Warning Signs")
        hape_symptoms = {
            'dyspnea_rest': st.checkbox("Shortness of breath at rest", help="CRITICAL: Breathless without exertion"),
            'dyspnea_exertion': st.checkbox("Shortness of breath with minimal exertion", help="Worse than others at same altitude"),
            'cough': st.checkbox("Persistent cough", help="May be dry or productive"),
            'chest_tightness': st.checkbox("Chest tightness/congestion", help="Gurgling sensation in chest"),
            'cyanosis': st.checkbox("Blue lips or fingernails (cyanosis)", help="CRITICAL: Sign of severe hypoxemia")
        }
    
    # Calculate AMS score
    ams_score = calculate_ams_score(symptoms)
    ams_severity = assess_ams_severity(ams_score)
    
    # Check for HACE
    has_hace = any(hace_symptoms.values())
    
    # Check for HAPE
    has_hape = any([hape_symptoms['dyspnea_rest'], 
                    hape_symptoms['cyanosis']]) or \
               (hape_symptoms['dyspnea_exertion'] and 
                sum([hape_symptoms['cough'], hape_symptoms['chest_tightness']]) >= 1)
    
    return {
        'ams_score': ams_score,
        'ams_severity': ams_severity,
        'has_hace': has_hace,
        'has_hape': has_hape,
        'symptoms': symptoms,
        'hace_symptoms': hace_symptoms,
        'hape_symptoms': hape_symptoms
    }

def main():
    st.markdown('<h1 class="main-header">⛰️ Mountain Sickness Analysis & Prevention</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div class="recommendation-box">
    <h3>📋 About This Tool</h3>
    <p>This application provides evidence-based risk assessment and recommendations for altitude illness 
    based on the <strong>Wilderness Medical Society Clinical Practice Guidelines 2024</strong>.</p>
    <p><strong>⚠️ Medical Disclaimer:</strong> This tool is for educational purposes only. 
    Always consult healthcare professionals for medical advice.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for navigation
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/mountain.png", width=100)
        st.title("Navigation")
        page = st.radio("Select Assessment Type:", 
                       ["🎯 Risk Assessment", 
                        "🏥 Symptom Checker & Diagnosis",
                        "📚 Educational Resources",
                        "💬 Ask Questions"])
    
    if page == "🎯 Risk Assessment":
        show_risk_assessment()
    elif page == "🏥 Symptom Checker & Diagnosis":
        show_symptom_checker()
    elif page == "📚 Educational Resources":
        show_educational_resources()
    elif page == "💬 Ask Questions":
        show_qa_section()

def show_risk_assessment():
    st.header("🎯 Pre-Trip Risk Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        age = st.number_input("Age", min_value=1, max_value=120, value=30)
        
        history = st.selectbox(
            "History of altitude illness",
            ["None or mild AMS", "Moderate-Severe AMS", "HAPE or HACE"],
            help="Select your worst experience at altitude"
        )
        
        current_altitude = st.number_input(
            "Current/home altitude (meters)",
            min_value=0,
            max_value=3000,
            value=0,
            help="Altitude where you currently live"
        )
        
        medical_conditions = st.multiselect(
            "Pre-existing conditions (select all that apply)",
            ["None", "Heart disease", "Lung disease", "Pregnancy", 
             "Recent COVID-19", "Sleep apnea", "Sickle cell disease"],
            default=["None"]
        )
    
    with col2:
        st.subheader("Trip Details")
        destination_altitude = st.number_input(
            "Highest sleeping altitude (meters)",
            min_value=0,
            max_value=9000,
            value=3500,
            help="The highest elevation where you will sleep"
        )
        
        ascent_rate = st.selectbox(
            "Planned ascent rate above 3000m",
            ["<500 m/d with extra acclimatization days every 1000m",
             "≥500 m/d with extra acclimatization days",
             ">500 m/d without extra acclimatization days"],
            help="How fast will you gain elevation?"
        )
        
        days_at_altitude = st.number_input(
            "Days planned at altitude",
            min_value=1,
            max_value=90,
            value=7
        )
        
        activity_level = st.select_slider(
            "Planned physical activity level",
            options=["Light", "Moderate", "Strenuous", "Very Strenuous"],
            value="Moderate"
        )
        
        staging = st.checkbox(
            "Will you stage at intermediate altitude (2000-3000m) for 1+ nights?",
            help="Staging helps with acclimatization"
        )
    
    if st.button("Calculate Risk", type="primary", use_container_width=True):
        # Calculate risk
        risk_category = calculate_risk_category(
            history, 
            destination_altitude, 
            ascent_rate,
            age
        )
        
        # Adjust risk based on medical conditions
        high_risk_conditions = ["Heart disease", "Lung disease", "Pregnancy", 
                               "Recent COVID-19", "Sickle cell disease"]
        if any(cond in medical_conditions for cond in high_risk_conditions):
            if risk_category == "Low":
                risk_category = "Moderate"
            elif risk_category == "Moderate":
                risk_category = "High"
        
        # Display risk
