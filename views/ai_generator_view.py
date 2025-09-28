"""
AI Content Generator View
Allows users to generate emails and cover letters from LinkedIn job descriptions
"""

import streamlit as st
from ai_content_generator import generate_email_content, generate_cover_letter_content, create_fallback_email, create_fallback_cover_letter
from pdf_generator import create_cover_letter_pdf, generate_pdf_filename
import re
from datetime import datetime

def show_ai_generator_page():
    """Main AI Content Generator page"""
    
    st.title("🤖 AI Content Generator")
    st.markdown("""
    **Generate personalized emails and cover letters from LinkedIn job descriptions.**
    
    Simply paste a LinkedIn job description below, and our AI will create tailored application content based on your resume.
    """)
    
    # Check if user has resume
    if 'resume' not in st.session_state or not st.session_state.resume:
        st.warning("⚠️ **Resume Required**: Please add your resume in the Resume Manager first for personalized content generation.")
        st.info("💡 **Tip**: Go to the Resume Manager tab in the sidebar to upload and manage your resume information.")
        return
    
    st.markdown("---")
    
    # Input section
    st.markdown("## 📋 Job Information Input")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Job description input
        job_description = st.text_area(
            "LinkedIn Job Description:",
            placeholder="Paste the complete LinkedIn job description here...\\n\\nExample:\\n\\nSoftware Engineer Intern\\nTechCorp Inc.\\n\\nWe are looking for a passionate Software Engineer Intern to join our team...\\n\\nResponsibilities:\\n- Develop web applications using React.js\\n- Collaborate with cross-functional teams\\n- Write clean, maintainable code\\n\\nRequirements:\\n- Currently pursuing a degree in Computer Science\\n- Knowledge of JavaScript, HTML, CSS\\n- Experience with Git version control",
            height=300,
            key="job_description_input"
        )
    
    with col2:
        st.markdown("### 💡 Tips for Best Results")
        st.info("""
        **Include these details:**
        - Company name
        - Job title
        - Job responsibilities  
        - Required skills
        - Preferred qualifications
        - Company culture info
        
        **The more details, the better the AI can tailor your content!**
        """)
    
    # Parse job information and generate content
    if job_description.strip():
        parsed_info = parse_job_description(job_description)
        
        # Generation buttons
        st.markdown("---")
        st.markdown("## 🚀 Generate Content")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📧 Generate Email", type="primary", use_container_width=True):
                generate_content("email", parsed_info, "")
        
        with col2:
            if st.button("📄 Generate Cover Letter", type="primary", use_container_width=True):
                generate_content("cover_letter", parsed_info, "")
        
        # Display generated content
        display_generated_content(parsed_info)
    
    else:
        st.info("📝 **Paste a LinkedIn job description above to get started!**")

def parse_job_description(job_description: str) -> dict:
    """
    Parse job description to extract key information
    
    Args:
        job_description: Raw job description text
        
    Returns:
        Dictionary with extracted information
    """
    
    lines = job_description.strip().split('\\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    parsed = {
        'job_title': '',
        'company_name': '',
        'location': '',
        'employment_type': '',
        'job_description': job_description
    }
    
    # Try to extract job title and company (usually in first few lines)
    if len(lines) >= 1:
        # First line is often the job title
        potential_title = lines[0]
        # Common job title patterns
        if any(term in potential_title.lower() for term in ['intern', 'developer', 'engineer', 'analyst', 'manager', 'specialist', 'coordinator', 'assistant']):
            parsed['job_title'] = potential_title
    
    if len(lines) >= 2:
        # Second line is often the company name
        potential_company = lines[1]
        # Avoid lines that look like job descriptions
        if not any(word in potential_company.lower() for word in ['we are', 'looking for', 'seeking', 'responsibilities', 'requirements']):
            parsed['company_name'] = potential_company
    
    # Look for location indicators
    for line in lines[:5]:  # Check first 5 lines
        if any(indicator in line.lower() for indicator in ['location:', 'remote', 'hybrid', 'on-site', 'city', 'state']):
            parsed['location'] = line
            break
    
    # Look for employment type
    text_lower = job_description.lower()
    if 'intern' in text_lower or 'internship' in text_lower:
        parsed['employment_type'] = 'Internship'
    elif 'full-time' in text_lower or 'full time' in text_lower:
        parsed['employment_type'] = 'Full-time'
    elif 'part-time' in text_lower or 'part time' in text_lower:
        parsed['employment_type'] = 'Part-time'
    elif 'contract' in text_lower:
        parsed['employment_type'] = 'Contract'
    
    # Fallback: if no job title detected, try to find it in the text
    if not parsed['job_title']:
        for line in lines[:3]:
            if any(term in line.lower() for term in ['position', 'role', 'job', 'opportunity']):
                parsed['job_title'] = line
                break
    
    # Fallback: if no company detected, look for "at [Company]" pattern
    if not parsed['company_name']:
        for line in lines:
            if ' at ' in line.lower():
                parts = line.split(' at ')
                if len(parts) >= 2:
                    parsed['company_name'] = parts[-1]
                    break
    
    return parsed

def generate_content(content_type: str, job_info: dict, additional_info: str):
    """Generate email or cover letter content"""
    
    try:
        resume = st.session_state.resume
        
        with st.spinner(f"🤖 Generating {content_type.replace('_', ' ')}..."):
            if content_type == "email":
                success, content = generate_email_content(resume, job_info, additional_info)
                
                if not success:
                    st.warning(f"AI generation failed: {content}")
                    content = create_fallback_email(resume, job_info, additional_info)
                
                st.session_state['generated_email'] = content
                st.success("✅ Email generated successfully!")
                
            elif content_type == "cover_letter":
                success, content = generate_cover_letter_content(resume, job_info, additional_info)
                
                if not success:
                    st.warning(f"AI generation failed: {content}")
                    content = create_fallback_cover_letter(resume, job_info, additional_info)
                
                st.session_state['generated_cover_letter'] = content
                st.success("✅ Cover letter generated successfully!")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating content: {str(e)}")

def display_generated_content(job_info: dict):
    """Display generated email and cover letter content"""
    
    # Display generated email
    if 'generated_email' in st.session_state:
        st.markdown("---")
        st.markdown("## 📧 Generated Email")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.text_area(
                "Email Content:",
                value=st.session_state['generated_email'],
                height=300,
                key="email_display"
            )
        
        with col2:
            st.markdown("### Actions")
            
            if st.button("📋 Copy Email", use_container_width=True):
                st.info("📋 Email content is ready to copy from the text area!")
            
            if st.button("🗑️ Clear Email", use_container_width=True):
                del st.session_state['generated_email']
                st.rerun()
    
    # Display generated cover letter
    if 'generated_cover_letter' in st.session_state:
        st.markdown("---")
        st.markdown("## 📄 Generated Cover Letter")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.text_area(
                "Cover Letter Content:",
                value=st.session_state['generated_cover_letter'],
                height=400,
                key="cover_letter_display"
            )
        
        with col2:
            st.markdown("### Actions")
            
            if st.button("📋 Copy Cover Letter", use_container_width=True):
                st.info("📋 Cover letter content is ready to copy from the text area!")
            
            # PDF download
            try:
                cover_content = st.session_state['generated_cover_letter']
                
                # Get user info for PDF
                resume_data = st.session_state.get('resume', {})
                personal_info = resume_data.get('personal_information', {})
                user_name = personal_info.get('name', 'Applicant')
                
                pdf_data = create_cover_letter_pdf(
                    content=cover_content,
                    applicant_name=user_name,
                    job_title=job_info.get('job_title', 'Position'),
                    company_name=job_info.get('company_name', 'Company')
                )
                
                filename = generate_pdf_filename(
                    applicant_name=user_name,
                    job_title=job_info.get('job_title', 'Position'),
                    company_name=job_info.get('company_name', 'Company')
                )
                
                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
            
            if st.button("🗑️ Clear Cover Letter", use_container_width=True):
                del st.session_state['generated_cover_letter']
                st.rerun()
    
    # Show example if no content generated yet
    if 'generated_email' not in st.session_state and 'generated_cover_letter' not in st.session_state:
        show_example_content()

def show_example_content():
    """Show example of what the generated content looks like"""
    
    with st.expander("📖 **See Example Output**", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📧 Email Example")
            st.code("""Subject: Application for Software Engineer Intern at TechCorp

Dear Hiring Manager,

I am writing to express my strong interest in the Software Engineer Intern position at TechCorp. As a Computer Science student with hands-on experience in React.js and JavaScript, I am excited about the opportunity to contribute to your innovative team.

Your job posting particularly caught my attention because it aligns perfectly with my technical background in web development and my passion for creating user-friendly applications. My experience with React.js, HTML, and CSS through various academic projects has prepared me well for the responsibilities outlined in your posting.

I would welcome the opportunity to discuss how my enthusiasm for technology and eagerness to learn can benefit TechCorp. Thank you for considering my application.

Best regards,
[Your Name]
[Contact Information]""", language="text")
        
        with col2:
            st.markdown("### 📄 Cover Letter Example")
            st.code("""[Your Name]
[Your Address]
[Email] | [Phone]

[Date]

Hiring Manager
TechCorp Inc.
[Company Address]

Dear Hiring Manager,

I am writing to express my sincere interest in the Software Engineer Intern position at TechCorp Inc. As a dedicated Computer Science student with expertise in modern web technologies, I am excited about the opportunity to contribute to your team's continued success.

RELEVANT EXPERIENCE:
In my academic projects, I have successfully:
• Developed responsive web applications using React.js
• Collaborated with cross-functional teams on software projects
• Implemented clean, maintainable code following best practices

TECHNICAL SKILLS & PROJECTS:
My technical expertise includes JavaScript, React.js, HTML, CSS, and Git version control. Through my coursework and personal projects, I have demonstrated the ability to learn new technologies quickly and apply them effectively in real-world scenarios.

I am particularly drawn to TechCorp because of your reputation for innovation and excellence. This internship represents an ideal opportunity for me to apply my skills while contributing to meaningful projects.

I would welcome the opportunity to discuss how my background, skills, and enthusiasm align with your team's needs. Thank you for your time and consideration.

Sincerely,
[Your Name]""", language="text")