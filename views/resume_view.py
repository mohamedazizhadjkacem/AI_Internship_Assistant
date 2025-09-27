import streamlit as st
import json
from datetime import datetime
from supabase_db import SupabaseDB

def save_resume_json(user_id, resume_data):
    """Save resume JSON data to the database."""
    try:
        db = SupabaseDB()
        # You can extend the database schema to include a resume table
        # For now, we'll store it in session state and provide download
        return True
    except Exception as e:
        st.error(f"Error saving resume: {str(e)}")
        return False

def validate_json_format(json_text):
    """Validate if the provided text is valid JSON."""
    try:
        json.loads(json_text)
        return True, None
    except json.JSONDecodeError as e:
        return False, str(e)

def show_resume_page():
    """Show the simple JSON-based resume management view."""
    st.title("📄 Resume Manager")
    
    # Introduction
    st.info("""
    Welcome to the Resume Manager! This tool helps you store and manage your resume information 
    for better internship applications. You can:
    
    - Enter resume information in JSON format
    - Store and automatically update your resume
    - Export your data for use in applications
    
    📝 **Note**: Only one resume is stored at a time. Adding a new resume will replace the previous one.
    """)
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["✏️ Manual Entry", "📊 My Resumes"])
    
    with tab1:
        st.header("Manual JSON Entry")
        st.write("Enter your resume information in JSON format:")
        
        # JSON template
        if st.button("📋 Load Template"):
            template = {
                "personal_information": {
                    "name": "Your Full Name",
                    "phone": "+1-234-567-8900",
                    "email": "your.email@example.com",
                    "linkedin": "https://linkedin.com/in/yourprofile",
                    "github": "https://github.com/yourusername"
                },
                "education": [
                    {
                        "degree": "Engineering Degree in Computer Science (Software Engineering & Information Systems)",
                        "institution": "Your University Name",
                        "years": "2023 – 2026 (Currently)"
                    },
                    {
                        "degree": "Preparatory Mathematics, Physics and Computer Science",
                        "institution": "Your Preparatory Institute",
                        "years": "2021 – 2023"
                    },
                    {
                        "degree": "Baccalaureate in Mathematics",
                        "institution": "Your High School",
                        "years": "2021"
                    }
                ],
                "skills": [
                    "Python",
                    "JavaScript", 
                    "React",
                    "Node.js",
                    "SQL",
                    "Git / Github",
                    "Machine Learning",
                    "Deep Learning (PyTorch/TensorFlow, CNN)",
                    "Database Systems (SQL, NoSQL)",
                    "Data Visualization (Matplotlib, Seaborn)",
                    "Object-Oriented Design"
                ],
                "languages": [
                    "English",
                    "French", 
                    "Arabic"
                ],
                "certifications": [
                    "Deep Learning with TensorFlow 2.0 – 365 Careers",
                    "ChatGPT Prompt Engineering for Developers – DeepLearning.AI",
                    "Python 101 for Data Science - Cognitive Class"
                ],
                "professional_experience": [
                    {
                        "role": "Summer Internship – Project Title",
                        "organization": "Company Name",
                        "duration": "2025/07 – 2025/08",
                        "achievements": [
                            "Developed end-to-end system using relevant technologies",
                            "Built and implemented specific features",
                            "Achieved measurable results and improvements"
                        ]
                    }
                ],
                "projects": [
                    {
                        "title": "Project Name",
                        "technologies": [
                            "Technology 1",
                            "Technology 2"
                        ],
                        "description": "Brief description of the project and your achievements"
                    }
                ],
                "extracurricular_activities": [
                    "Active member of relevant clubs or organizations",
                    "Leadership positions or responsibilities",
                    "Event organization or volunteer work"
                ]
            }
            st.session_state.json_template = json.dumps(template, indent=2)
        
        # JSON input area
        json_input = st.text_area(
            "Resume JSON Data:",
            value=st.session_state.get('json_template', ''),
            height=500,
            help="Enter your resume data in valid JSON format. Use the template above as a guide."
        )
        
        # Validation and save
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Validate JSON"):
                is_valid, error = validate_json_format(json_input)
                if is_valid:
                    st.success("Valid JSON format!")
                    
                else:
                    st.error(f"Invalid JSON: {error}")
        
        with col2:
            if st.button("💾 Save Resume"):
                is_valid, error = validate_json_format(json_input)
                if is_valid:
                    resume_data = json.loads(json_input)
                    resume_data['created_at'] = datetime.now().isoformat()
                    resume_data['updated_at'] = datetime.now().isoformat()
                    
                    # Check if updating existing resume
                    if 'resume' in st.session_state and st.session_state.resume:
                        st.session_state.resume = resume_data
                        st.success("🔄 Resume updated successfully!")
                        st.info("Your previous resume has been replaced with the new data.")
                    else:
                        st.session_state.resume = resume_data
                        st.success("💾 Resume saved successfully!")
                else:
                    st.error(f"Cannot save invalid JSON: {error}")
        
        with col3:
            if json_input and validate_json_format(json_input)[0]:
                st.download_button(
                    "📥 Download JSON",
                    data=json_input,
                    file_name=f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with tab2:
        st.header("My Resume")
        
        if 'resume' not in st.session_state or not st.session_state.resume:
            st.info("No resume saved yet. Create a resume to get started!")
        else:
            resume = st.session_state.resume
            st.success("You have a resume saved!")
            
            with st.expander(f"📄 Resume - {resume.get('personal_info', {}).get('name', 'Unnamed')}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Created:** {resume.get('created_at', 'Unknown')}")
                    if resume.get('updated_at'):
                        st.write(f"**Last Updated:** {resume.get('updated_at')}")
                    if 'personal_info' in resume:
                        info = resume['personal_info']
                        st.write(f"**Name:** {info.get('name', 'N/A')}")
                        st.write(f"**Email:** {info.get('email', 'N/A')}")
                        st.write(f"**Phone:** {info.get('phone', 'N/A')}")
                
                with col2:
                    st.download_button(
                        "📥 Download JSON",
                        data=json.dumps(resume, indent=2),
                        file_name=f"my_resume_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                    
                    if st.button("🗑️ Delete Resume", type="secondary", use_container_width=True):
                        st.session_state.resume = None
                        st.success("Resume deleted!")
                        st.rerun()
                
                # Show JSON data
                st.markdown("### JSON Data:")
                st.json(resume)