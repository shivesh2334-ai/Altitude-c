import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import math

# Page configuration
st.set_page_config(
    page_title="Mountain Altitude Sickness Analyzer",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .low-risk {
        background-color: #D1FAE5;
        border-left: 5px solid #10B981;
    }
    .moderate-risk {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
    }
    .high-risk {
        background-color: #FEE2E2;
        border-left: 5px solid #EF4444;
    }
    .info-box {
        background-color: #EFF6FF;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3B82F6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def calculate_altitude_from_location(location):
    """Approximate altitudes for common mountain locations"""
    locations = {
        "Sea Level": 0,
        "Denver, CO": 1600,
        "Cusco, Peru": 3400,
        "La Paz, Bolivia": 3640,
        "Lhasa, Tibet": 3650,
        "Mount Kilimanjaro Base": 1800,
        "Kilimanjaro Summit": 5895,
        "Everest Base Camp": 5364,
        "Mount Everest Summit": 8849,
        "Aconcagua Base Camp": 4200,
        "Mont Blanc": 4808,
        "Matterhorn": 4478,
        "Pikes Peak": 4302
    }
    return locations.get(location, 0)

def assess_ams_risk(history, sleeping_elevation, ascent_rate, age, medical_conditions):
    """Assess AMS risk based on WMS 2024 guidelines"""
    risk_score = 0
    risk_factors = []
    
    # History of altitude illness
    if history == "HAPE or HACE":
        risk_score += 3
        risk_factors.append("Previous HAPE/HACE (High Risk)")
    elif history == "Moderate-Severe AMS":
        risk_score += 2
        risk_factors.append("Previous Moderate-Severe AMS")
    elif history == "Mild AMS":
        risk_score += 1
        risk_factors.append("Previous Mild AMS")
    
    # Sleeping elevation on Day 1
    if sleeping_elevation > 3500:
        risk_score += 3
        risk_factors.append(f"High sleeping elevation: {sleeping_elevation}m")
    elif sleeping_elevation >= 2800:
        risk_score += 2
        risk_factors.append(f"Moderate sleeping elevation: {sleeping_elevation}m")
    elif sleeping_elevation >= 2500:
        risk_score += 1
        risk_factors.append(f"Elevated sleeping elevation: {sleeping_elevation}m")
    
    # Ascent rate
    if ascent_rate > 500:
        risk_score += 2
        risk_factors.append(f"Rapid ascent rate: {ascent_rate}m/day")
    
    # Age factor (children and elderly may be at higher risk)
    if age < 18 or age > 65:
        risk_score += 1
        risk_factors.append(f"Age factor: {age} years")
    
    # Medical conditions
    if "Cardiac disease" in medical_conditions:
        risk_score += 1
        risk_factors.append("Cardiac disease")
    if "Pulmonary disease" in medical_conditions:
        risk_score += 1
        risk_factors.append("Pulmonary disease")
    
    # Determine risk category
    if risk_score >= 6:
        return "High", risk_factors, risk_score
    elif risk_score >= 3:
        return "Moderate", risk_factors, risk_score
    else:
        return "Low", risk_factors, risk_score

def recommend_prophylaxis(risk_level, has_contraindications):
    """Recommend prophylactic medications based on WMS 2024 guidelines"""
    recommendations = []
    
    if risk_level == "Low":
        recommendations.append({
            "action": "Gradual Ascent",
            "details": "No medication needed. Follow gradual ascent guidelines.",
            "strength": "Strong Recommendation"
        })
    elif risk_level == "Moderate":
        if not has_contraindications["acetazolamide"]:
            recommendations.append({
                "medication": "Acetazolamide",
                "dose": "125 mg every 12 hours",
                "start": "Night before ascent",
                "duration": "2-4 days at target altitude",
                "strength": "Strong Recommendation",
                "notes": "First-line prophylaxis. Start 125mg at bedtime before ascent."
            })
        else:
            recommendations.append({
                "medication": "Dexamethasone",
                "dose": "2 mg every 6 hours or 4 mg every 12 hours",
                "start": "Day before ascent",
                "duration": "2-4 days at target altitude",
                "strength": "Strong Recommendation (Alternative)",
                "notes": "Use if acetazolamide contraindicated"
            })
    elif risk_level == "High":
        if not has_contraindications["acetazolamide"]:
            recommendations.append({
                "medication": "Acetazolamide",
                "dose": "250 mg every 12 hours",
                "start": "Night before ascent",
                "duration": "2-4 days at target altitude",
                "strength": "Strong Recommendation",
                "notes": "Higher dose for high-risk profiles"
            })
        
        recommendations.append({
            "action": "Consider Staged Ascent",
            "details": "Spend 6-7 days at 2200-3000m before proceeding higher",
            "strength": "Strong Recommendation"
        })
    
    # Add alternative option
    if risk_level in ["Moderate", "High"]:
        recommendations.append({
            "medication": "Ibuprofen (Alternative)",
            "dose": "600 mg every 8 hours",
            "start": "Before ascent",
            "duration": "Short-term use only",
            "strength": "Weak Recommendation",
            "notes": "For those who cannot take acetazolamide or dexamethasone"
        })
    
    return recommendations

def recommend_hape_prophylaxis(history_hape, contraindications):
    """Recommend HAPE prophylaxis based on WMS 2024 guidelines"""
    if not history_hape:
        return []
    
    recommendations = []
    
    if not contraindications["nifedipine"]:
        recommendations.append({
            "medication": "Nifedipine (Extended Release)",
            "dose": "30 mg every 12 hours",
            "start": "Day before ascent",
            "duration": "4-7 days at target altitude",
            "strength": "Strong Recommendation",
            "notes": "First-line for HAPE prevention in susceptible individuals"
        })
    
    if contraindications["nifedipine"]:
        recommendations.append({
            "medication": "Tadalafil",
            "dose": "10 mg every 12 hours",
            "start": "Day before ascent",
            "duration": "4-7 days at target altitude",
            "strength": "Strong Recommendation (Alternative)",
            "notes": "Use if nifedipine contraindicated"
        })
        
        recommendations.append({
            "medication": "Dexamethasone",
            "dose": "8 mg every 12 hours",
            "start": "Day before ascent",
            "duration": "4-7 days at target altitude",
            "strength": "Strong Recommendation (Alternative)",
            "notes": "Use if nifedipine and tadalafil contraindicated"
        })
    
    return recommendations

def generate_ascent_plan(starting_altitude, target_altitude):
    """Generate safe ascent plan based on WMS 2024 guidelines"""
    plan = []
    current_altitude = starting_altitude
    day = 0
    
    # If starting below 3000m, suggest intermediate stop
    if starting_altitude < 1500 and target_altitude > 2800:
        plan.append({
            "day": day,
            "action": "Intermediate Stop",
            "altitude": 1600,
            "notes": "Spend 1 night at intermediate altitude (e.g., Denver)"
        })
        current_altitude = 1600
        day += 1
    
    # Initial ascent to starting point
    if current_altitude < 3000:
        plan.append({
            "day": day,
            "action": "Ascent to Base",
            "altitude": min(3000, target_altitude),
            "notes": "Initial ascent to starting elevation"
        })
        current_altitude = min(3000, target_altitude)
        day += 1
    
    # Gradual ascent above 3000m
    rest_day_counter = 0
    while current_altitude < target_altitude:
        next_altitude = min(current_altitude + 500, target_altitude)
        
        plan.append({
            "day": day,
            "action": "Ascent",
            "altitude": next_altitude,
            "notes": f"Gain {next_altitude - current_altitude}m (sleep at {next_altitude}m)"
        })
        
        current_altitude = next_altitude
        day += 1
        rest_day_counter += 1
        
        # Add rest day every 3-4 days
        if rest_day_counter >= 3 and current_altitude < target_altitude:
            plan.append({
                "day": day,
                "action": "Rest Day",
                "altitude": current_altitude,
                "notes": "Acclimatization day - no gain in sleeping elevation"
            })
            day += 1
            rest_day_counter = 0
    
    return plan

def diagnose_symptoms(symptoms, altitude, time_since_ascent):
    """Diagnose altitude illness based on symptoms"""
    diagnosis = []
    severity = "None"
    
    # Check for AMS
    if "Headache" in symptoms:
        ams_symptoms = [s for s in symptoms if s in ["Nausea/Vomiting", "Fatigue", "Dizziness"]]
        if len(ams_symptoms) >= 1:
            # Calculate Lake Louise Score approximation
            lake_louise_score = len(symptoms)
            
            if lake_louise_score >= 6 or "Severe headache" in symptoms:
                diagnosis.append("Moderate-Severe AMS")
                severity = "Moderate-Severe"
            else:
                diagnosis.append("Mild AMS")
                severity = "Mild"
    
    # Check for HACE
    if any(s in symptoms for s in ["Ataxia", "Altered mental status", "Confusion"]):
        diagnosis.append("HIGH ALTITUDE CEREBRAL EDEMA (HACE) - EMERGENCY")
        severity = "Severe - Emergency"
    
    # Check for HAPE
    if "Dyspnea at rest" in symptoms or "Severe dyspnea on exertion" in symptoms:
        hape_symptoms = [s for s in symptoms if s in ["Cough", "Chest tightness", "Fatigue"]]
        if len(hape_symptoms) >= 1:
            diagnosis.append("HIGH ALTITUDE PULMONARY EDEMA (HAPE) - EMERGENCY")
            severity = "Severe - Emergency"
    
    return diagnosis, severity

def recommend_treatment(diagnosis, severity, current_altitude):
    """Recommend treatment based on WMS 2024 guidelines"""
    treatments = []
    
    if "Mild AMS" in diagnosis:
        treatments.append({
            "priority": "High",
            "action": "Stop Ascent",
            "details": "Do not ascend higher until symptoms resolve"
        })
        treatments.append({
            "priority": "High",
            "action": "Symptom Management",
            "details": "Ibuprofen 600mg every 8h or Acetaminophen 1000mg every 8h for headache"
        })
        treatments.append({
            "priority": "Medium",
            "action": "Consider Medication",
            "details": "Acetazolamide 250mg every 12h may help (not required for mild AMS)"
        })
        treatments.append({
            "priority": "Medium",
            "action": "Hydration & Rest",
            "details": "Maintain adequate hydration, rest, avoid alcohol"
        })
    
    if "Moderate-Severe AMS" in diagnosis:
        treatments.append({
            "priority": "Critical",
            "action": "Stop Ascent & Consider Descent",
            "details": "Descend 300-1000m if symptoms worsen or don't improve in 24h"
        })
        treatments.append({
            "priority": "High",
            "action": "Dexamethasone",
            "details": "4mg every 6 hours (oral, IM, or IV). Strong Recommendation"
        })
        treatments.append({
            "priority": "High",
            "action": "Acetazolamide",
            "details": "250mg every 12 hours (adjunct therapy)"
        })
        treatments.append({
            "priority": "High",
            "action": "Supplemental Oxygen",
            "details": "If available, titrate to SpO2 >90%"
        })
    
    if "HACE" in " ".join(diagnosis):
        treatments.append({
            "priority": "EMERGENCY",
            "action": "IMMEDIATE DESCENT",
            "details": "Descend immediately! This is a life-threatening emergency. Do not descend alone."
        })
        treatments.append({
            "priority": "EMERGENCY",
            "action": "Dexamethasone",
            "details": "8mg immediately, then 4mg every 6 hours (Strong Recommendation)"
        })
        treatments.append({
            "priority": "EMERGENCY",
            "action": "Supplemental Oxygen",
            "details": "Administer oxygen to achieve SpO2 >90% during descent"
        })
        treatments.append({
            "priority": "EMERGENCY",
            "action": "Portable Hyperbaric Chamber",
            "details": "Use if descent impossible and oxygen unavailable"
        })
    
    if "HAPE" in " ".join(diagnosis):
        treatments.append({
            "priority": "EMERGENCY",
            "action": "IMMEDIATE DESCENT",
            "details": "Descend at least 1000m or until symptoms resolve. Minimize exertion."
        })
        treatments.append({
            "priority": "EMERGENCY",
            "action": "Supplemental Oxygen",
            "details": "Titrate to SpO2 >90%. First-line treatment if descent delayed."
        })
        treatments.append({
            "priority": "High",
            "action": "Nifedipine (if oxygen unavailable)",
            "details": "30mg extended release every 12h (only if descent impossible and no oxygen)"
        })
        treatments.append({
            "priority": "High",
            "action": "Portable Hyperbaric Chamber",
            "details": "Use if descent delayed and oxygen unavailable"
        })
        treatments.append({
            "priority": "Medium",
            "action": "Consider CPAP/EPAP",
            "details": "If available and patient can tolerate, as adjunct to oxygen"
        })
    
    return treatments

# Main Application
def main():
    st.markdown("<h1 class='main-header'>🏔️ Mountain Altitude Sickness Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #6B7280;'>Based on Wilderness Medical Society 2024 Guidelines</p>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Risk Assessment", 
        "📊 Symptom Checker", 
        "💊 Prevention Plan", 
        "🗺️ Ascent Planner",
        "❓ Ask Questions"
    ])
    
    # TAB 1: RISK ASSESSMENT
    with tab1:
        st.header("Altitude Illness Risk Assessment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Personal Information")
            age = st.number_input("Age (years)", min_value=1, max_value=100, value=30)
            
            history = st.selectbox(
                "Previous altitude illness history",
                ["None or Mild AMS", "Moderate-Severe AMS", "HAPE or HACE"]
            )
            
            medical_conditions = st.multiselect(
                "Existing medical conditions",
                ["None", "Cardiac disease", "Pulmonary disease", "Migraine", "Sleep apnea"]
            )
            
            medications = st.multiselect(
                "Current medications that may affect altitude response",
                ["None", "Diuretics", "Beta blockers", "Calcium channel blockers", "Sleeping pills"]
            )
        
        with col2:
            st.subheader("Trip Details")
            
            altitude_input_method = st.radio(
                "How do you want to specify altitude?",
                ["Enter altitude directly", "Select from locations"]
            )
            
            if altitude_input_method == "Enter altitude directly":
                starting_altitude = st.number_input(
                    "Starting altitude (meters from sea level)", 
                    min_value=0, 
                    max_value=9000, 
                    value=0,
                    help="Your current elevation or where you'll begin your ascent"
                )
                sleeping_elevation = st.number_input(
                    "Sleeping elevation Day 1 (meters)", 
                    min_value=0, 
                    max_value=9000, 
                    value=2800,
                    help="Where you'll sleep on your first night at altitude"
                )
                target_altitude = st.number_input(
                    "Target/maximum altitude (meters)", 
                    min_value=0, 
                    max_value=9000, 
                    value=4000,
                    help="Highest elevation you plan to reach"
                )
            else:
                start_location = st.selectbox(
                    "Starting location",
                    ["Sea Level", "Denver, CO", "Cusco, Peru"]
                )
                starting_altitude = calculate_altitude_from_location(start_location)
                st.info(f"Starting altitude: {starting_altitude}m")
                
                sleep_location = st.selectbox(
                    "Where will you sleep on Day 1?",
                    ["Denver, CO", "Cusco, Peru", "La Paz, Bolivia", "Lhasa, Tibet", 
                     "Mount Kilimanjaro Base", "Everest Base Camp"]
                )
                sleeping_elevation = calculate_altitude_from_location(sleep_location)
                st.info(f"Sleeping elevation: {sleeping_elevation}m")
                
                target_location = st.selectbox(
                    "Target destination",
                    ["Pikes Peak", "Mont Blanc", "Mount Kilimanjaro Base", 
                     "Kilimanjaro Summit", "Everest Base Camp", "Aconcagua Base Camp"]
                )
                target_altitude = calculate_altitude_from_location(target_location)
                st.info(f"Target altitude: {target_altitude}m")
            
            days_to_target = st.number_input(
                "Number of days to reach target altitude", 
                min_value=1, 
                max_value=30, 
                value=5
            )
            
            if days_to_target > 0:
                ascent_rate = (target_altitude - sleeping_elevation) / days_to_target
            else:
                ascent_rate = 0
        
        st.markdown("---")
        
        if st.button("🔍 Assess My Risk", type="primary", use_container_width=True):
            # Risk assessment
            risk_level, risk_factors, risk_score = assess_ams_risk(
                history, sleeping_elevation, ascent_rate, age, medical_conditions
            )
            
            # Display results
            st.subheader("📊 Risk Assessment Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if risk_level == "Low":
                    st.success(f"### {risk_level} Risk")
                    risk_class = "low-risk"
                elif risk_level == "Moderate":
                    st.warning(f"### {risk_level} Risk")
                    risk_class = "moderate-risk"
                else:
                    st.error(f"### {risk_level} Risk")
                    risk_class = "high-risk"
            
            with col2:
                st.metric("Risk Score", f"{risk_score}/10")
            
            with col3:
                st.metric("Ascent Rate", f"{ascent_rate:.0f} m/day")
            
            # Risk factors
            st.markdown(f"<div class='risk-card {risk_class}'>", unsafe_allow_html=True)
            st.write("**Identified Risk Factors:**")
            if risk_factors:
                for factor in risk_factors:
                    st.write(f"• {factor}")
            else:
                st.write("• No significant risk factors identified")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Altitude thresholds
            st.markdown("<div class='info-box'>", unsafe_allow_html=True)
            st.write("**Altitude Classifications:**")
            st.write(f"• Starting altitude: {starting_altitude}m")
            st.write(f"• Day 1 sleeping elevation: {sleeping_elevation}m")
            st.write(f"• Target altitude: {target_altitude}m")
            
            if sleeping_elevation < 2500:
                st.success("✓ Below altitude illness risk threshold (<2500m)")
            elif sleeping_elevation < 3500:
                st.warning("⚠️ Moderate altitude (2500-3500m) - Risk present")
            else:
                st.error("⚠️ High altitude (>3500m) - Significant risk")
            
            if ascent_rate > 500:
                st.error(f"❌ Ascent rate ({ascent_rate:.0f}m/day) exceeds recommended 500m/day")
            else:
                st.success(f"✓ Ascent rate ({ascent_rate:.0f}m/day) within recommendations")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # HAPE risk assessment
            if history == "HAPE or HACE":
                st.warning("⚠️ **HAPE Risk**: You have a history of HAPE/HACE. Special prophylaxis recommended.")
            
            # Visualizations
            st.subheader("📈 Altitude Profile Visualization")
            
            # Create altitude profile chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=[0, days_to_target],
                y=[sleeping_elevation, target_altitude],
                mode='lines+markers',
                name='Your Planned Ascent',
                line=dict(color='red', width=3)
            ))
            
            # Add recommended ascent line
            recommended_days = max(days_to_target, (target_altitude - sleeping_elevation) / 500)
            fig.add_trace(go.Scatter(
                x=[0, recommended_days],
                y=[sleeping_elevation, target_altitude],
                mode='lines+markers',
                name='Recommended Ascent (500m/day)',
                line=dict(color='green', width=2, dash='dash')
            ))
            
            # Add altitude zones
            fig.add_hrect(y0=0, y1=2500, fillcolor="lightgreen", opacity=0.2, 
                         annotation_text="Low Altitude", annotation_position="left")
            fig.add_hrect(y0=2500, y1=3500, fillcolor="yellow", opacity=0.2,
                         annotation_text="Moderate Altitude", annotation_position="left")
            fig.add_hrect(y0=3500, y1=5500, fillcolor="orange", opacity=0.2,
                         annotation_text="High Altitude", annotation_position="left")
            fig.add_hrect(y0=5500, y1=9000, fillcolor="red", opacity=0.2,
                         annotation_text="Extreme Altitude", annotation_position="left")
            
            fig.update_layout(
                title="Altitude Ascent Profile",
                xaxis_title="Days",
                yaxis_title="Altitude (meters)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: SYMPTOM CHECKER
    with tab2:
        st.header("Symptom Checker & Diagnosis")
        st.write("Select your current symptoms for evaluation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current Situation")
            current_altitude = st.number_input(
                "Current altitude (meters)", 
                min_value=0, 
                max_value=9000, 
                value=3000,
                key="symptom_altitude"
            )
            
            hours_since_ascent = st.number_input(
                "Hours since arriving at this altitude", 
                min_value=0, 
                max_value=168, 
                value=12
            )
            
            oxygen_saturation = st.number_input(
                "Oxygen saturation (SpO2) if known", 
                min_value=50, 
                max_value=100, 
                value=95,
                help="Normal at sea level: 95-100%. At altitude: depends on elevation."
            )
        
        with col2:
            st.subheader("Select Your Symptoms")
            symptoms = st.multiselect(
                "What symptoms are you experiencing?",
                [
                    "Headache",
                    "Severe headache",
                    "Nausea/Vomiting",
                    "Fatigue",
                    "Dizziness",
                    "Shortness of breath on exertion",
                    "Severe dyspnea on exertion",
                    "Dyspnea at rest",
                    "Cough",
                    "Chest tightness",
                    "Ataxia (loss of coordination)",
                    "Altered mental status",
                    "Confusion",
                    "Difficulty sleeping"
                ]
            )
            
            functional_status = st.select_slider(
                "Functional status",
                options=[
                    "Normal activities",
                    "Slightly reduced",
                    "Moderately limited",
                    "Severely limited",
                    "Unable to function"
                ]
            )
        
        st.markdown("---")
        
        if st.button("🔬 Analyze Symptoms", type="primary", use_container_width=True):
            if not symptoms:
                st.warning("Please select at least one symptom for analysis.")
            else:
                # Diagnosis
                diagnosis, severity = diagnose_symptoms(symptoms, current_altitude, hours_since_ascent)
                
                # Display diagnosis
                st.subheader("🏥 Diagnostic Assessment")
                
                if not diagnosis:
                    st.success("✓ No altitude illness detected based on symptoms")
                    st.info("Continue monitoring. If symptoms worsen, reassess immediately.")
                else:
                    for dx in diagnosis:
                        if "EMERGENCY" in dx:
                            st.error(f"🚨 **{dx}**")
                        elif "Moderate-Severe" in dx:
                            st.warning(f"⚠️ **{dx}**")
                        else:
                            st.info(f"ℹ️ **{dx}**")
                
                # Lake Louise Score approximation
                if "Headache" in symptoms:
                    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                    st.write("**Lake Louise AMS Score (Approximate):**")
                    score = len([s for s in symptoms if s in ["Headache", "Nausea/Vomiting", "Fatigue", "Dizziness"]])
                    if functional_status == "Severely limited" or functional_status == "Unable to function":
                        score += 2
                    elif functional_status == "Moderately limited":
                        score += 1
                    
                    st.write(f"Estimated score: **{score}**/12")
                    if score >= 6:
                        st.write("Interpretation: **Moderate-Severe AMS**")
                    elif score >= 3:
                        st.write("Interpretation: **Mild AMS**")
                    else:
                        st.write("Interpretation: **Unlikely AMS**")
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Oxygen saturation interpretation
                st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                st.write("**Oxygen Saturation Interpretation:**")
                expected_spo2 = 100 - (current_altitude / 300)  # Rough approximation
                st.write(f"Your SpO2: **{oxygen_saturation}%**")
                st.write(f"Expected at {current_altitude}m: **~{expected_spo2:.0f}%**")
                
                if oxygen_saturation < expected_spo2 - 5:
                    st.error("⚠️ SpO2 lower than expected for this altitude - concerning for HAPE")
                elif oxygen_saturation < 90:
                    st.error("⚠️ SpO2 <90% - Significant hypoxemia")
                else:
                    st.success("✓ SpO2 appropriate for altitude")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Treatment recommendations
                if diagnosis:
                    st.subheader("💊 Treatment Recommendations")
                    treatments = recommend_treatment(diagnosis, severity, current_altitude)
                    
                    for treatment in treatments:
                        priority = treatment["priority"]
                        if priority == "EMERGENCY":
                            color = "red"
                            icon = "🚨"
                        elif priority == "Critical":
                            color = "orange"
                            icon = "⚠️"
                        elif priority == "High":
                            color = "yellow"
                            icon = "❗"
                        else:
                            color = "lightblue"
                            icon = "ℹ️"
                        
                        st.markdown(f"""
                        <div style='background-color: {color}; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: black;'>
                            <strong>{icon} {priority}: {treatment['action']}</strong><br>
                            {treatment['details']}
                        </div>
                        """, unsafe_allow_html=True)
                
                # When to seek immediate medical help
                st.markdown("---")
                st.error("""
                **⚠️ SEEK IMMEDIATE MEDICAL HELP IF:**
                - Ataxia (loss of coordination/balance)
                - Altered mental status or confusion
                - Severe shortness of breath at rest
                - Pink, frothy sputum when coughing
                - Symptoms rapidly worsening
                - Unable to eat or drink
                - Oxygen saturation <75% at rest
                """)
    
    # TAB 3: PREVENTION PLAN
    with tab3:
        st.header("Personalized Prevention Plan")
        st.write("Get customized recommendations for preventing altitude illness")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Trip Parameters")
            prev_risk_level = st.selectbox(
                "Your risk level (from Risk Assessment)",
                ["Low", "Moderate", "High"]
            )
            
            prev_target_altitude = st.number_input(
                "Target altitude (meters)", 
                min_value=2000, 
                max_value=9000, 
                value=4000,
                key="prev_altitude"
            )
            
            has_hape_history = st.checkbox("I have a history of HAPE")
            
        with col2:
            st.subheader("Medical Considerations")
            contraindications = {
                "acetazolamide": st.checkbox("Contraindication to Acetazolamide (sulfa allergy, etc.)"),
                "dexamethasone": st.checkbox("Contraindication to Dexamethasone"),
                "nifedipine": st.checkbox("Contraindication to Nifedipine (hypotension, etc.)"),
                "ibuprofen": st.checkbox("Contraindication to Ibuprofen (GI issues, etc.)")
            }
            
            pregnant = st.checkbox("Currently pregnant")
            
        st.markdown("---")
        
        if st.button("📋 Generate Prevention Plan", type="primary", use_container_width=True):
            st.subheader("🎯 Your Personalized Prevention Plan")
            
            # General recommendations
            st.markdown("### 🏔️ General Prevention Strategies")
            st.markdown("""
            <div class='info-box'>
            <strong>1. Gradual Ascent (MOST IMPORTANT)</strong><br>
            • Above 3000m: Increase sleeping elevation by no more than 500m per day<br>
            • Include rest days (no elevation gain) every 3-4 days<br>
            • "Climb high, sleep low" when possible<br>
            • Remember: sleeping elevation matters more than daytime altitude<br><br>
            
            <strong>2. Hydration & Nutrition</strong><br>
            • Maintain adequate hydration (clear to pale yellow urine)<br>
            • Eat regular meals even if appetite is reduced<br>
            • Avoid excessive alcohol and sedatives<br><br>
            
            <strong>3. Recognize Symptoms Early</strong><br>
            • Monitor for headache, nausea, fatigue, dizziness<br>
            • Never ascend with symptoms of altitude illness<br>
            • Descend if symptoms worsen despite treatment<br>
            </div>
            """, unsafe_allow_html=True)
            
            # AMS prophylaxis
            st.markdown("### 💊 Medication Prophylaxis for AMS/HACE")
            ams_recommendations = recommend_prophylaxis(prev_risk_level, contraindications)
            
            for idx, rec in enumerate(ams_recommendations):
                with st.expander(f"Option {idx+1}: {rec.get('medication', rec.get('action', 'Recommendation'))}", expanded=(idx==0)):
                    if 'medication' in rec:
                        st.write(f"**Medication:** {rec['medication']}")
                        st.write(f"**Dose:** {rec['dose']}")
                        st.write(f"**When to start:** {rec['start']}")
                        st.write(f"**Duration:** {rec['duration']}")
                        st.write(f"**Evidence strength:** {rec['strength']}")
                        if 'notes' in rec:
                            st.info(f"📝 {rec['notes']}")
                    else:
                        st.write(f"**Action:** {rec['action']}")
                        st.write(f"**Details:** {rec['details']}")
                        st.write(f"**Evidence strength:** {rec['strength']}")
            
            # HAPE prophylaxis
            if has_hape_history:
                st.markdown("### 🫁 HAPE Prophylaxis (High Priority for You)")
                hape_recommendations = recommend_hape_prophylaxis(has_hape_history, contraindications)
                
                for idx, rec in enumerate(hape_recommendations):
                    with st.expander(f"HAPE Prevention Option {idx+1}: {rec['medication']}", expanded=(idx==0)):
                        st.write(f"**Medication:** {rec['medication']}")
                        st.write(f"**Dose:** {rec['dose']}")
                        st.write(f"**When to start:** {rec['start']}")
                        st.write(f"**Duration:** {rec['duration']}")
                        st.write(f"**Evidence strength:** {rec['strength']}")
                        if 'notes' in rec:
                            st.info(f"📝 {rec['notes']}")
                
                st.error("""
                ⚠️ **Important for HAPE-susceptible individuals:**
                - Use prophylactic medication for ALL ascents above 3000m
                - Continue medication for full duration (4-7 days at target altitude)
                - Consider staged ascent or preacclimatization
                - Minimize exertion, especially on ascent days
                """)
            
            # Staging/preacclimatization
            st.markdown("### 🏕️ Staging & Preacclimatization")
            if prev_risk_level in ["Moderate", "High"]:
                st.markdown("""
                <div class='info-box'>
                <strong>Recommended: Staged Ascent</strong><br>
                • Spend 6-7 days at 2200-3000m before going higher<br>
                • Even 2 days at moderate altitude provides benefit<br>
                • Example: Spend time in Denver (1600m) before going to higher Colorado destinations<br><br>
                
                <strong>Optional: Preacclimatization (if time permits)</strong><br>
                • Use hyperbaric chamber or travel to moderate altitude 1-2 weeks before trip<br>
                • Multiple 8+ hour exposures over 7+ days most effective<br>
                • Hypobaric (actual altitude) superior to normobaric (chamber)<br>
                </div>
                """, unsafe_allow_html=True)
            
            # Special populations
            if pregnant:
                st.warning("""
                ⚠️ **Pregnancy Considerations:**
                - Travel above 2500m carries unknown risks to fetus
                - Acetazolamide generally avoided in pregnancy
                - Ginkgo biloba should be avoided
                - Consult with your obstetrician before high-altitude travel
                - Consider postponing trip or limiting altitude exposure
                """)
            
            # Download prevention plan
            st.markdown("---")
            prevention_summary = f"""
            ALTITUDE ILLNESS PREVENTION PLAN
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            
            RISK LEVEL: {prev_risk_level}
            TARGET ALTITUDE: {prev_target_altitude}m
            
            KEY RECOMMENDATIONS:
            1. Gradual ascent: Max 500m/day above 3000m
            2. Rest days every 3-4 days
            
            MEDICATIONS:
            """
            
            for rec in ams_recommendations:
                if 'medication' in rec:
                    prevention_summary += f"\n- {rec['medication']}: {rec['dose']}\n  Start: {rec['start']}, Duration: {rec['duration']}\n"
            
            if has_hape_history:
                prevention_summary += "\nHAPE PROPHYLAXIS:\n"
                for rec in hape_recommendations:
                    prevention_summary += f"- {rec['medication']}: {rec['dose']}\n  Start: {rec['start']}, Duration: {rec['duration']}\n"
            
            st.download_button(
                label="📥 Download Prevention Plan",
                data=prevention_summary,
                file_name="altitude_prevention_plan.txt",
                mime="text/plain"
            )
    
    # TAB 4: ASCENT PLANNER
    with tab4:
        st.header("Safe Ascent Planner")
        st.write("Generate a day-by-day ascent plan based on WMS guidelines")
        
        col1, col2 = st.columns(2)
        
        with col1:
            plan_start_altitude = st.number_input(
                "Starting altitude (meters)", 
                min_value=0, 
                max_value=5000, 
                value=0,
                key="plan_start"
            )
        
        with col2:
            plan_target_altitude = st.number_input(
                "Target altitude (meters)", 
                min_value=1000, 
                max_value=9000, 
                value=5000,
                key="plan_target"
            )
        
        if st.button("🗓️ Generate Ascent Plan", type="primary", use_container_width=True):
            ascent_plan = generate_ascent_plan(plan_start_altitude, plan_target_altitude)
            
            st.subheader("📅 Your Recommended Ascent Schedule")
            
            # Display plan as table
            plan_df = pd.DataFrame(ascent_plan)
            st.dataframe(plan_df, use_container_width=True)
            
            # Visualize ascent plan
            fig = go.Figure()
            
            altitudes = [step['altitude'] for step in ascent_plan]
            days = [step['day'] for step in ascent_plan]
            actions = [step['action'] for step in ascent_plan]
            
            # Color code by action type
            colors = ['green' if 'Rest' in action else 'blue' if 'Ascent' in action else 'orange' 
                     for action in actions]
            
            fig.add_trace(go.Scatter(
                x=days,
                y=altitudes,
                mode='lines+markers',
                name='Ascent Profile',
                line=dict(color='blue', width=3),
                marker=dict(size=10, color=colors),
                text=actions,
                hovertemplate='<b>Day %{x}</b><br>' +
                             'Altitude: %{y}m<br>' +
                             '%{text}<br>' +
                             '<extra></extra>'
            ))
            
            # Add altitude zones
            fig.add_hrect(y0=0, y1=2500, fillcolor="lightgreen", opacity=0.1)
            fig.add_hrect(y0=2500, y1=3500, fillcolor="yellow", opacity=0.1)
            fig.add_hrect(y0=3500, y1=5500, fillcolor="orange", opacity=0.1)
            fig.add_hrect(y0=5500, y1=9000, fillcolor="red", opacity=0.1)
            
            fig.update_layout(
                title="Recommended Ascent Profile",
                xaxis_title="Day",
                yaxis_title="Altitude (meters)",
                hovermode='closest',
                height=500,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key insights
            st.markdown("### 🔑 Key Plan Features")
            
            total_days = len(ascent_plan)
            rest_days = len([step for step in ascent_plan if 'Rest' in step['action']])
            average_gain = (plan_target_altitude - plan_start_altitude) / (total_days - rest_days) if total_days > rest_days else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Days", total_days)
            col2.metric("Rest/Acclimatization Days", rest_days)
            col3.metric("Average Daily Gain", f"{average_gain:.0f}m")
            
            st.info("""
            **✓ This plan follows WMS 2024 guidelines:**
            - Maximum 500m gain in sleeping elevation per day above 3000m
            - Rest days included every 3-4 days
            - Staged ascent if starting from low elevation
            - Gradual acclimatization prioritized over speed
            """)
            
            # Download ascent plan
            plan_text = f"""
            SAFE ASCENT PLAN
            Generated: {datetime.now().strftime('%Y-%m-%d')}
            
            Start: {plan_start_altitude}m → Target: {plan_target_altitude}m
            Total Days: {total_days} | Rest Days: {rest_days}
            
            DAY-BY-DAY SCHEDULE:
            """
            
            for step in ascent_plan:
                plan_text += f"\nDay {step['day']}: {step['action']} - {step['altitude']}m"
                plan_text += f"\n  {step['notes']}\n"
            
            st.download_button(
                label="📥 Download Ascent Plan",
                data=plan_text,
                file_name="ascent_plan.txt",
                mime="text/plain"
            )
    
    # TAB 5: ASK QUESTIONS
    with tab5:
        st.header("❓ Altitude Medicine Q&A")
        st.write("Common questions about altitude illness based on WMS 2024 Guidelines")
        
        questions = {
            "What is acute mountain sickness (AMS)?": """
            **Acute Mountain Sickness (AMS)** is the most common form of altitude illness. It typically occurs within 
            6-12 hours of ascending to altitudes above 2500m.
            
            **Symptoms include:**
            - Headache (required for diagnosis)
            - Plus one or more of: nausea/vomiting, fatigue, dizziness, difficulty sleeping
            
            **Severity levels:**
            - **Mild AMS**: Lake Louise Score 3-5, symptoms don't limit activities
            - **Moderate-Severe AMS**: Lake Louise Score 6-12, symptoms significantly limit activities
            
            **Key point:** AMS is uncomfortable but not immediately life-threatening if recognized and treated appropriately.
            """,
            
            "What is HACE?": """
            **High Altitude Cerebral Edema (HACE)** is a severe, life-threatening form of altitude illness representing 
            progression from severe AMS.
            
            **Signs and symptoms:**
            - All symptoms of AMS, plus:
            - **Ataxia** (loss of coordination/balance) - often earliest sign
            - Altered mental status, confusion
            - Severe lassitude
            - Progression can lead to coma if untreated
            
            **Critical actions:**
            - IMMEDIATE descent required
            - Administer dexamethasone 8mg immediately
            - Provide supplemental oxygen if available
            - Do not descend alone
            
            **This is a medical emergency!**
            """,
            
            "What is HAPE?": """
            **High Altitude Pulmonary Edema (HAPE)** is a life-threatening accumulation of fluid in the lungs 
            caused by excessive hypoxic pulmonary vasoconstriction.
            
            **Symptoms:**
            - Severe dyspnea (shortness of breath), initially with exertion, progressing to rest
            - Cough (may be dry or productive)
            - Chest tightness
            - Extreme fatigue
            - Pink, frothy sputum (late sign)
            
            **Signs:**
            - Low oxygen saturation (much lower than expected for altitude)
            - Crackles in lungs on examination
            
            **Treatment:**
            - IMMEDIATE descent (minimize exertion)
            - Supplemental oxygen to SpO2 >90%
            - Nifedipine if descent impossible and oxygen unavailable
            
            **This is a medical emergency!**
            """,
            
            "Who is at risk for altitude illness?": """
            **Risk factors for AMS/HACE:**
            - Previous history of altitude illness (especially severe AMS or HACE)
            - Rapid ascent rate (>500m/day above 3000m)
            - High sleeping elevation on Day 1 (>2800m)
            - Younger age (children may be at higher risk)
            - Lack of previous altitude exposure
            - Physical exertion at altitude
            - Individual susceptibility (varies greatly)
            
            **Risk factors for HAPE:**
            - Previous history of HAPE (STRONGEST predictor)
            - Rapid ascent
            - Heavy exertion on ascent
            - Cold exposure
            - Respiratory infections
            - Living at high altitude, descending, then rapidly re-ascending ("re-entry HAPE")
            
            **Factors that do NOT predict risk:**
            - Physical fitness level
            - Gender
            - Training status
            """,
            
            "How can I prevent altitude illness?": """
            **PRIMARY PREVENTION STRATEGY: Gradual Ascent**
            
            **Above 3000m:**
            - Increase sleeping elevation by no more than 500m per day
            - Include rest days (no elevation gain) every 3-4 days
            - "Climb high, sleep low" when possible
            
            **Medication options:**
            
            **For AMS/HACE prevention:**
            - **Acetazolamide 125mg twice daily** (first-line)
              - Start night before ascent
              - Continue 2-4 days at target altitude
            - **Dexamethasone 2-4mg twice daily** (alternative)
            
            **For HAPE prevention (if susceptible):**
            - **Nifedipine 30mg ER twice daily** (first-line)
              - Start day before ascent
              - Continue 4-7 days at target altitude
            
            **Additional strategies:**
            - Staged ascent (6-7 days at 2200-3000m)
            - Adequate hydration
            - Avoid alcohol and sleeping pills
            - Avoid overexertion on ascent
            """,
            
            "When should I take acetazolamide?": """
            **Acetazolamide for AMS/HACE Prevention:**
            
            **Who should consider it:**
            - Moderate to high risk individuals (see Risk Assessment)
            - Anyone with history of altitude illness
            - Those unable to follow gradual ascent guidelines
            
            **Dosing:**
            - **Standard:** 125mg every 12 hours
            - **High-risk situations:** Consider 250mg every 12 hours
            - **Pediatric:** 1.25 mg/kg every 12 hours (max 125mg/dose)
            
            **When to start:**
            - **Optimal:** Night before ascent
            - **Still effective:** Day of ascent
            
            **Duration:**
            - Continue for 2 days at target altitude if following recommended ascent rate
            - Continue 2-4 days if ascending faster than recommended
            
            **Side effects:**
            - Tingling in fingers/toes (common, harmless)
            - Frequent urination
            - Carbonated beverages taste flat
            - Rare: sulfa allergy reactions
            
            **Contraindications:**
            - Sulfa allergy (though risk is very low)
            - Severe kidney or liver disease
            """,
            
            "What should I do if I develop symptoms?": """
            **Step-by-step approach:**
            
            **Mild AMS:**
            1. **STOP ASCENDING** - do not go higher
            2. Rest at current altitude
            3. Treat headache: Ibuprofen 600mg every 8h OR Acetaminophen 1000mg every 8h
            4. Hydrate well
            5. Consider acetazolamide 250mg twice daily
            6. Monitor symptoms closely
            7. **Descend if symptoms worsen or don't improve in 24 hours**
            
            **Moderate-Severe AMS:**
            1. **STOP ASCENDING**
            2. **Consider descent** (especially if symptoms worsening)
            3. **Dexamethasone 4mg every 6 hours** (strong recommendation)
            4. Acetazolamide 250mg twice daily (adjunct)
            5. Oxygen if available (target SpO2 >90%)
            6. **Descend if no improvement in 24 hours**
            
            **HACE (EMERGENCY):**
            1. **IMMEDIATE DESCENT** (life-threatening emergency)
            2. **Dexamethasone 8mg immediately, then 4mg every 6 hours**
            3. Oxygen (keep SpO2 >90%)
            4. Portable hyperbaric chamber if descent impossible
            5. **Do not descend alone**
            6. Evacuate to medical facility
            
            **HAPE (EMERGENCY):**
            1. **IMMEDIATE DESCENT** (at least 1000m or until symptoms resolve)
            2. **Minimize exertion** during descent
            3. Oxygen (target SpO2 >90%)
            4. Nifedipine 30mg ER every 12h IF descent impossible and no oxygen
            5. Portable hyperbaric chamber if available
            6. Evacuate to medical facility
            
            **When to seek immediate medical help:**
            - Ataxia (loss of coordination)
            - Altered mental status
            - Severe dyspnea at rest
            - Rapidly worsening symptoms
            - Unable to eat or drink
            """,
            
            "Can I use oxygen from oxygen bars or portable canisters?": """
            **Short answer: No, not effective for prevention or treatment.**
            
            **Why:**
            - Canisters contain only 2-10 liters of oxygen
            - Brief use (few minutes) provides no lasting benefit
            - Altitude illness requires sustained oxygenation (hours, not minutes)
            
            **What IS effective:**
            - **For prevention:** Gradual ascent, acetazolamide, dexamethasone
            - **For treatment:** 
              - Supplemental oxygen for HOURS (1-2 L/min for >2 hours), titrated to SpO2 >90%
              - DESCENT
              - Appropriate medications
              - Portable hyperbaric chamber
            
            **Bottom line:** Oxygen bars and portable canisters are marketing gimmicks with no proven benefit 
            for altitude illness.
            """,
            
            "Is it safe to exercise at altitude?": """
            **General principles:**
            
            **During acclimatization (first 3-4 days):**
            - Light activity is fine and may aid acclimatization
            - Avoid strenuous exercise
            - Heavy exertion increases AMS risk
            - For HAPE-susceptible individuals, minimize ALL exertion on ascent
            
            **After acclimatization:**
            - Exercise is generally safe
            - Performance will be reduced compared to sea level
            - Monitor for symptoms
            - Stay well hydrated
            
            **Warning signs to stop exercise:**
            - Severe headache
            - Excessive dyspnea (beyond what's expected)
            - Dizziness or confusion
            - Nausea
            
            **Special consideration:**
            - "Climb high, sleep low" is better than "sleep high, rest" for acclimatization
            - Daytime ascents to higher elevation, returning to lower altitude to sleep, are beneficial
            """,
            
            "How do children respond to altitude?": """
            **Key points about children at altitude:**
            
            **Risk of altitude illness:**
            - Children can develop altitude illness, including severe forms
            - Diagnosis can be challenging (difficulty describing symptoms)
            - Same altitude thresholds apply (>2500m)
            
            **Prevention:**
            - **Gradual ascent** (same guidelines as adults)
            - **Acetazolamide** can be used: 1.25 mg/kg every 12h (max 125mg/dose)
            - **Dexamethasone NOT recommended** for prophylaxis in children
            
            **Symptoms to watch for:**
            - Fussiness, crying
            - Poor appetite
            - Vomiting
            - Lethargy
            - Changes in play behavior
            - Difficulty sleeping (more than expected)
            
            **Treatment:**
            - Same principles as adults (descent, oxygen, medications)
            - Acetazolamide: 2.5 mg/kg every 12h (max 250mg/dose) for treatment
            - Dexamethasone: 0.15 mg/kg every 6h (max 4mg/dose) for HACE treatment
            
            **When in doubt:**
            - Assume altitude illness and treat/descend
            - Better to be overcautious with children
            """,
            
            "Can I travel to altitude after having COVID-19?": """
            **Based on WMS 2024 recommendations:**
            
            **Most people (no persistent symptoms):**
            - Can travel to altitude after full recovery
            - No special precautions needed
            - Follow standard altitude illness prevention guidelines
            
            **Evaluation needed if:**
            - Persistent symptoms >2 weeks after positive test
            - Required intensive care for COVID-19
            - Experienced myocarditis (heart inflammation)
            - Had thromboembolic complications (blood clots)
            
            **Recommended testing before travel:**
            - Pulse oximetry at rest and with activity
            - Pulmonary function testing
            - Chest X-ray
            - ECG
            - BNP and high-sensitivity troponin
            - Echocardiography
            - Consider cardiopulmonary exercise testing if significantly limited
            
            **Depending on results:**
            - May need to modify plans (lower altitude, slower ascent)
            - May need to postpone travel
            - May require supplemental oxygen
            
            **Timing:**
            - Wait at least 2 weeks after symptom resolution before strenuous activity at altitude
            - For severe COVID-19, wait longer (4-6 weeks minimum)
            """,
            
            "What medications should I pack for a high-altitude trip?": """
            **Essential medications to consider:**
            
            **FOR PREVENTION:**
            - **Acetazolamide 125mg tablets** (if moderate/high risk)
              - Typical amount: 30-40 tablets for 2-week trip
            - **Nifedipine 30mg ER tablets** (if history of HAPE)
              - Typical amount: 20-30 tablets
            
            **FOR TREATMENT:**
            - **Acetazolamide 250mg tablets** (AMS treatment)
              - 10-20 tablets
            - **Dexamethasone 4mg tablets** (severe AMS/HACE)
              - 20-30 tablets
            - **Ibuprofen 600mg or 800mg** (headache, pain)
              - 20-30 tablets
            - **Acetaminophen 500mg** (alternative pain relief)
              - 20-30 tablets
            
            **SYMPTOMATIC RELIEF:**
            - Anti-nausea medication (ondansetron 4-8mg)
            - Loperamide (for diarrhea)
            - Antibiotic (ciprofloxacin or azithromycin for traveler's diarrhea)
            
            **EQUIPMENT (if possible):**
            - Pulse oximeter
            - Thermometer
            - First aid kit
            
            **IMPORTANT:**
            - Carry prescriptions for controlled medications
            - Know generic names (especially when traveling internationally)
            - Store in original containers with labels
            - Check expiration dates
            - Carry in readily accessible location
            - Consider packing half in separate bag (in case of loss)
            
            **Consult your doctor to obtain prescriptions and ensure medications are appropriate for your situation.**
            """
        }
        
        # Display questions
        for question, answer in questions.items():
            with st.expander(question):
                st.markdown(answer)
        
        # Custom question input
        st.markdown("---")
        st.subheader("📝 Ask Your Own Question")
        user_question = st.text_area(
            "Enter your question about altitude illness:",
            placeholder="Example: Can I drink alcohol at high altitude?"
        )
        
        if st.button("Submit Question"):
            if user_question:
                st.info("""
                **Thank you for your question!**
                
                This is an automated tool based on the Wilderness Medical Society 2024 Guidelines. 
                For personalized medical advice, please consult with:
                
                - Your primary care physician
                - A travel medicine specialist
                - A high-altitude medicine expert
                
                You can find more information at:
                - Wilderness Medical Society: www.wms.org
                - Travel medicine clinics
                - High-altitude research centers (e.g., University of Colorado Altitude Research Center)
                """)
            else:
                st.warning("Please enter a question.")
        
        # Emergency contacts and resources
        st.markdown("---")
        st.markdown("### 🚨 Emergency Resources")
        st.error("""
        **In case of emergency at altitude:**
        
        **Immediate actions:**
        1. Assess for HACE or HAPE (life-threatening emergencies)
        2. If HACE or HAPE suspected: DESCEND IMMEDIATELY
        3. Administer appropriate medications
        4. Seek emergency medical help
        
        **International emergency numbers:**
        - **Nepal (Everest region):** Himalayan Rescue Association clinics at Pheriche and Manang
        - **Peru:** Tourist Police 105, Emergency 116
        - **Bolivia:** Emergency 118
        - **Tibet:** Check with your tour operator for emergency contacts
        
        **Helicopter evacuation:**
        - Ensure you have travel insurance with emergency evacuation coverage
        - Have emergency contact numbers readily available
        - GPS coordinates of your location are helpful
        
        **Telemedicine:**
        - Some expedition companies offer telemedicine consultation
        - International SOS provides medical support for members
        """)
        
        st.info("""
        **Useful Resources:**
        
        - **Wilderness Medical Society:** www.wms.org
        - **International Society for Mountain Medicine (ISMM):** www.ismmed.org
        - **Himalayan Rescue Association:** www.himalayanrescue.org
        - **Institute for Altitude Medicine:** www.altitudemedicine.org
        - **CDC Travel Health:** wwwnc.cdc.gov/travel
        """)

# Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6B7280; padding: 2rem 0;'>
        <p><strong>Altitude Sickness Analyzer v2.0</strong></p>
        <p>Based on Wilderness Medical Society Clinical Practice Guidelines 2024</p>
        <p style='font-size: 0.9rem;'>⚠️ This tool provides general guidance based on published guidelines. 
        It is not a substitute for professional medical advice, diagnosis, or treatment.</p>
        <p style='font-size: 0.9rem;'>Always consult with a qualified healthcare provider about your specific situation.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
