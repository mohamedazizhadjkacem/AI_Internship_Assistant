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

def get_required_template():
    """Get the required resume template structure."""
    return {
        "personal_information": {
            "name": "string",
            "phone": "string",
            "email": "string",
            "linkedin": "string",
            "github": "string"
        },
        "education": [
            {
                "degree": "string",
                "institution": "string",
                "years": "string"
            }
        ],
        "skills": ["string"],
        "languages": ["string"],
        "certifications": ["string"],
        "professional_experience": [
            {
                "role": "string",
                "organization": "string",
                "duration": "string",
                "achievements": ["string"]
            }
        ],
        "projects": [
            {
                "title": "string",
                "technologies": ["string"],
                "description": "string"
            }
        ],
        "extracurricular_activities": ["string"]
    }

def validate_resume_structure(data, template, path=""):
    """Recursively validate data structure against template."""
    errors = []
    
    if isinstance(template, dict):
        if not isinstance(data, dict):
            errors.append(f"❌ {path or 'Root'} should be an object/dictionary")
            return errors
        
        # Check for missing required fields
        for key, value in template.items():
            if key not in data:
                errors.append(f"❌ Missing required field: {path}.{key}" if path else f"❌ Missing required field: {key}")
            else:
                errors.extend(validate_resume_structure(data[key], value, f"{path}.{key}" if path else key))
        
        # Check for extra fields not in template
        for key in data:
            if key not in template:
                errors.append(f"⚠️ Extra field not in template: {path}.{key}" if path else f"⚠️ Extra field not in template: {key}")
    
    elif isinstance(template, list):
        if not isinstance(data, list):
            errors.append(f"❌ {path} should be a list/array")
            return errors
        
        if len(template) > 0 and len(data) > 0:
            # Validate each item in the list against the first template item
            template_item = template[0]
            for i, item in enumerate(data):
                errors.extend(validate_resume_structure(item, template_item, f"{path}[{i}]"))
        elif len(data) == 0:
            errors.append(f"⚠️ {path} is empty - consider adding at least one item")
    
    elif template == "string":
        if not isinstance(data, str):
            errors.append(f"❌ {path} should be a string")
        elif data.strip() == "":
            errors.append(f"⚠️ {path} is empty - please provide a value")
    
    return errors

def validate_json_format(json_text):
    """Validate JSON format and structure against template."""
    # First check if it's valid JSON
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return False, [f"❌ Invalid JSON format: {str(e)}"]
    
    # Then validate structure against template
    template = get_required_template()
    structure_errors = validate_resume_structure(data, template)
    
    if structure_errors:
        return False, structure_errors
    
    return True, None

def show_resume_page():
    """Show the simple JSON-based resume management view."""
    st.title("📄 Resume Manager")
    
    # Introduction
    st.info("""
    Welcome to the Resume Manager! This tool enforces a **strict template structure** for consistent 
    resume formatting across all internship applications.
    
    ✅ **What you can do:**
    - Enter resume information following the required JSON template
    - Validate your resume against the template structure
    - Store and automatically update your resume
    - Export validated data for applications
    
    ⚠️ **Important Rules:**
    - Your resume **MUST** follow the exact template structure
    - All required fields must be present
    - Extra fields not in the template will cause validation errors
    - Only valid resumes can be saved or downloaded
    
    📝 **Note**: Only one resume is stored at a time. Adding a new resume will replace the previous one.
    """)
    
    # Tabs for different input methods
    tab1, tab2 = st.tabs(["✏️ Manual Entry", "📊 My Resumes"])
    
    with tab1:
        st.header("Manual JSON Entry")
        
        st.write("Enter your resume information in JSON format:")
        
        # JSON template
        if st.button("📋 Load Complete Template"):
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
                if json_input.strip():
                    is_valid, errors = validate_json_format(json_input)
                    if is_valid:
                        st.success("🎉 Perfect! Your resume matches the required template!")
                        st.balloons()
                    else:
                        st.error("❌ **Validation Failed!** Your resume doesn't match the required template:")
                        for error in errors:
                            st.write(f"• {error}")
                else:
                    st.warning("⚠️ Please enter some JSON data to validate")
        
        with col2:
            if st.button("💾 Save Resume"):
                if json_input.strip():
                    is_valid, errors = validate_json_format(json_input)
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
                        st.error("❌ **Cannot save invalid resume!**")
                        st.write("**Validation errors:**")
                        for error in errors:
                            st.write(f"• {error}")
                        st.info("💡 Use the 'Validate JSON' button to see all issues and fix them first.")
                else:
                    st.warning("⚠️ Please enter resume data before saving")
        
        with col3:
            if json_input and json_input.strip():
                is_valid, _ = validate_json_format(json_input)
                if is_valid:
                    st.download_button(
                        "📥 Download JSON",
                        data=json_input,
                        file_name=f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                else:
                    st.button("📥 Download JSON", disabled=True, help="Fix validation errors first")
    
    with tab2:
        st.header("My Resume")
        
        if 'resume' not in st.session_state or not st.session_state.resume:
            st.info("No resume saved yet. Create a resume to get started!")
        else:
            resume = st.session_state.resume
            st.success("You have a resume saved!")
            
            with st.expander(f"📄 Resume - {resume.get('personal_information', {}).get('name', 'Unnamed')}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Created:** {resume.get('created_at', 'Unknown')}")
                    if resume.get('updated_at'):
                        st.write(f"**Last Updated:** {resume.get('updated_at')}")
                    if 'personal_information' in resume:
                        info = resume['personal_information']
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