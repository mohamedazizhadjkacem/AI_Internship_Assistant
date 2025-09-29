"""
AI Content Generation Module
Handles prompt engineering and API calls for generating emails and cover letters
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

def has_sufficient_resume_data(resume_data: dict) -> bool:
    """
    Check if resume has sufficient data to generate quality content
    
    Args:
        resume_data: Dictionary containing resume information
        
    Returns:
        Boolean indicating if there's enough data for AI generation
    """
    if not resume_data:
        return False
    
    # Check for basic information
    has_education = bool(resume_data.get('education'))
    has_experience = bool(resume_data.get('experience'))
    has_skills = bool(resume_data.get('skills'))
    has_projects = bool(resume_data.get('projects'))
    
    # Need at least 2 of these categories to have meaningful content
    categories_count = sum([has_education, has_experience, has_skills, has_projects])
    
    return categories_count >= 2
import streamlit as st

# Configuration - Uses Streamlit secrets (preferred) or environment variable as fallback
def get_api_key():
    """Get API key from Streamlit secrets or environment variable"""
    try:
        return st.secrets.get("GROQ_API_KEY", "")
    except:
        return os.getenv("GROQ_API_KEY", "")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Groq API endpoint

def format_education_for_prompt(education: List[dict]) -> str:
    """Format education data for prompt inclusion"""
    if not education or education is None:
        return "No formal education listed"
    
    formatted = []
    for edu in education[:2]:  # Limit to 2 most recent/relevant
        if edu is None:
            continue
        degree = edu.get('degree', 'Degree') if edu else 'Degree'
        institution = edu.get('institution', 'Institution') if edu else 'Institution'
        graduation_date = edu.get('graduation_date', 'N/A') if edu else 'N/A'
        gpa = edu.get('gpa', '') if edu else ''
        
        edu_str = f"- {degree} from {institution}"
        if graduation_date and graduation_date != 'N/A':
            edu_str += f" ({graduation_date})"
        if gpa:
            edu_str += f" - GPA: {gpa}"
        formatted.append(edu_str)
    
    return '\n'.join(formatted)

def format_experience_for_prompt(experience: List[dict]) -> str:
    """Format work experience data for prompt inclusion (privacy-focused)"""
    if not experience or experience is None:
        return "No formal work experience listed"
    
    formatted = []
    for exp in experience[:3]:  # Limit to 3 most recent
        if exp is None:
            continue
        
        # Use correct field names from JSON structure and exclude organization for privacy
        role = exp.get('role', exp.get('job_title', 'Position')) if exp else 'Position'
        duration = exp.get('duration', 'Duration') if exp else 'Duration'
        achievements = exp.get('achievements', exp.get('description', [])) if exp else []
        
        # Format without organization name for privacy
        exp_str = f"- {role} ({duration})"
        if achievements:
            key_achievements = achievements[:2]  # Top 2 achievements
            exp_str += f"\n  Key achievements: {'; '.join(key_achievements)}"
        formatted.append(exp_str)
    
    return '\n'.join(formatted)

def format_skills_for_prompt(skills: List[str]) -> str:
    """Format skills data for prompt inclusion"""
    if not skills or skills is None:
        return "Not specified"
    
    # Group skills by category if possible
    return ', '.join(skills[:12])  # Limit to top 12 skills

def format_projects_for_prompt(projects: List[dict]) -> str:
    """Format projects data for prompt inclusion"""
    if not projects or projects is None:
        return "No projects listed"
    
    formatted = []
    for i, project in enumerate(projects[:3]):  # Limit to 3 most relevant
        if project is None:
            continue
        name = project.get('name', '') if project else ''
        description = project.get('description', []) if project else []
        technologies = project.get('technologies', []) if project else []
        
        # Use actual project name if available, otherwise use descriptive language
        if name and name.strip() and name != 'Project':
            proj_str = f"- {name} Project"
        else:
            # Use more natural descriptions instead of generic naming
            project_descriptors = ["Academic project", "Personal project", "Development project"]
            proj_str = f"- {project_descriptors[i % len(project_descriptors)]}"
        
        if description:
            proj_str += f": {description[0]}"
        if technologies:
            proj_str += f" (Technologies: {', '.join(technologies[:3])})"
        formatted.append(proj_str)
    
    return '\n'.join(formatted)

def get_email_prompt(resume_data: dict, internship_data: dict, additional_info: str = "") -> str:
    """
    Generate a detailed prompt for creating a professional job application email
    
    Args:
        resume_data: Dictionary containing user's resume information
        internship_data: Dictionary containing job/internship details
        additional_info: Additional job requirements or info provided by user
        
    Returns:
        Formatted prompt string for AI generation
    """
    
    # Handle None or missing resume data
    if not resume_data:
        resume_data = {}
    
    # Handle None or missing internship data
    if not internship_data:
        internship_data = {}
    
    personal_info = resume_data.get('personal_information', {}) if resume_data else {}
    experience = resume_data.get('experience', []) if resume_data else []
    education = resume_data.get('education', []) if resume_data else []
    skills = resume_data.get('skills', []) if resume_data else []
    
    # Ensure all data types are correct
    if personal_info is None:
        personal_info = {}
    if experience is None:
        experience = []
    if education is None:
        education = []
    if skills is None:
        skills = []
    
    try:
        education_str = format_education_for_prompt(education)
        experience_str = format_experience_for_prompt(experience)
        skills_str = ', '.join(skills[:10]) if skills else 'Not specified'
    except Exception as e:
        education_str = "No education data available"
        experience_str = "No experience data available"
        skills_str = "No skills data available"
    
    prompt = f"""
You are a professional career counselor helping a job candidate write a compelling application email. 

IMPORTANT: You must ONLY use factual information provided below. DO NOT invent or fabricate any experiences, projects, achievements, or statistics.

CANDIDATE INFORMATION:
- Professional background and qualifications as listed below
- Contact information will be added automatically after generation

EDUCATION:
{education_str}

WORK EXPERIENCE:
{experience_str}

TECHNICAL SKILLS:
{skills_str}

JOB DETAILS:
- Position: {internship_data.get('job_title', 'Position')}
- Company: {internship_data.get('company_name', 'Company')}
- Job Description: {(internship_data.get('job_description') or '')[:800]}

ADDITIONAL JOB INFO/REQUIREMENTS:
{additional_info.strip() if additional_info and additional_info.strip() else 'None provided - generate based on job description only'}

TASK:
Create a professional, concise job application email (subject line + body) that:

1. **Subject Line**: Clear, specific, and professional
2. **Opening**: Shows genuine enthusiasm for the specific role and company
3. **Body Paragraph 1**: Highlight 2-3 most relevant skills/experiences that match the job requirements
4. **Body Paragraph 2**: Demonstrate knowledge of the company/role and explain why you're a good fit
5. **Closing**: Professional call-to-action requesting an interview
6. **Signature**: End with "Best regards," - contact information will be added automatically

CRITICAL REQUIREMENTS:
- ONLY use information explicitly provided in the candidate's resume above
- DO NOT invent, fabricate, or assume any experiences, projects, or achievements
- DO NOT create fictional work examples or statistics
- If the candidate lacks specific experience, focus on transferable skills and enthusiasm to learn
- Keep email concise (under 200 words for body)
- Use professional tone but stay truthful to the candidate's actual background
- Match candidate's ACTUAL skills to job requirements
- DO NOT include personal contact information - this will be added automatically
- End the email with "Best regards," only
- When in doubt, be more generic rather than inventing false details
- NEVER use generic project names like "Project A", "Project B", "Project C", etc.
- If referring to projects, use natural language like "in one of my projects", "during a recent project", or mention the actual project name if provided
- Avoid alphabetical or numerical project labeling completely

Generate the email now:
"""
    return prompt

def get_cover_letter_prompt(resume_data: dict, internship_data: dict, additional_info: str = "") -> str:
    """
    Generate a detailed prompt for creating a professional cover letter
    
    Args:
        resume_data: Dictionary containing user's resume information
        internship_data: Dictionary containing job/internship details
        additional_info: Additional job requirements or info provided by user
        
    Returns:
        Formatted prompt string for AI generation
    """
    
    # Handle None or missing resume data
    if not resume_data:
        resume_data = {}
    
    # Handle None or missing internship data
    if not internship_data:
        internship_data = {}
    
    personal_info = resume_data.get('personal_information', {}) if resume_data else {}
    experience = resume_data.get('experience', []) if resume_data else []
    education = resume_data.get('education', []) if resume_data else []
    skills = resume_data.get('skills', []) if resume_data else []
    projects = resume_data.get('projects', []) if resume_data else []
    
    # Ensure all data types are correct
    if personal_info is None:
        personal_info = {}
    if experience is None:
        experience = []
    if education is None:
        education = []
    if skills is None:
        skills = []
    if projects is None:
        projects = []
    
    try:
        education_str = format_education_for_prompt(education)
        experience_str = format_experience_for_prompt(experience)
        skills_str = format_skills_for_prompt(skills)
        projects_str = format_projects_for_prompt(projects)
    except Exception as e:
        education_str = "No education data available"
        experience_str = "No experience data available"
        skills_str = "No skills data available"
        projects_str = "No projects data available"
    
    prompt = f"""
You are a professional career counselor helping a job candidate write an outstanding cover letter.

CRITICAL INSTRUCTION: You must ONLY use factual information provided in the candidate's resume below. DO NOT invent, fabricate, or assume any experiences, projects, achievements, metrics, or accomplishments that are not explicitly listed.

CANDIDATE PROFILE:
- Professional qualifications and background as detailed below
- Personal contact information will be added automatically to the header

EDUCATIONAL BACKGROUND:
{education_str}

PROFESSIONAL EXPERIENCE:
{experience_str}

TECHNICAL SKILLS & COMPETENCIES:
{skills_str}

KEY PROJECTS:
{projects_str}

TARGET POSITION:
- Job Title: {internship_data.get('job_title', 'Position')}
- Company: {internship_data.get('company_name', 'Company')}
- Job Description: {(internship_data.get('job_description') or '')[:1000]}

ADDITIONAL REQUIREMENTS/INFO:
{additional_info.strip() if additional_info and additional_info.strip() else 'None provided - focus on job description and candidate qualifications'}

TASK:
Write a compelling, professional cover letter with the following structure:

**HEADER:**
- Skip the header - it will be added automatically
- Start directly with the date and hiring manager address

**OPENING PARAGRAPH:**
- State the specific position you're applying for
- Briefly mention your most relevant qualification
- Show enthusiasm for the company/role

**BODY PARAGRAPH 1 - Experience & Skills:**
- Highlight 2-3 most relevant work experiences
- Include specific achievements with metrics when possible
- Connect experience directly to job requirements

**BODY PARAGRAPH 2 - Technical Skills & Projects:**
- Showcase relevant technical skills
- Mention key projects that demonstrate capabilities
- Explain how these align with the role

**CLOSING PARAGRAPH:**
- Reaffirm interest and qualifications
- Request interview/next steps
- End with "Sincerely," only - name will be added automatically

CRITICAL REQUIREMENTS:
- ONLY use factual information explicitly provided in the candidate's resume above
- DO NOT fabricate, invent, or assume any experiences, projects, achievements, or statistics
- DO NOT create fictional work examples, metrics, or accomplishments
- If candidate lacks specific experience for the role, focus on:
  * Relevant coursework and academic projects (if listed in education)
  * Transferable skills from actual experiences
  * Enthusiasm and ability to learn
  * General technical competencies that are actually listed
- Keep cover letter to 3-4 paragraphs (400-500 words)
- Use formal business letter format
- Maintain professional tone throughout
- Stay truthful to the candidate's actual background
- When uncertain about details, be more general rather than inventing specifics
- Focus on potential and learning ability rather than false expertise
- Include specific examples and achievements
- Avoid generic statements
- DO NOT include personal contact information - this will be added automatically
- Start with the date and company address, skip personal header
- End with "Sincerely," only
- NEVER use generic project names like "Project A", "Project B", "Project C", "Project D", etc.
- When referring to projects, use natural language such as "in one of my projects", "through a recent project", "during my academic work", or use the actual project name if provided
- Completely avoid alphabetical or numerical project labeling (A, B, C, D, 1, 2, 3, etc.)
- If multiple projects exist, refer to them as "various projects", "several projects", or "my project work"

Generate the cover letter now:
"""
    return prompt

def append_contact_info_to_email(ai_content: str, resume_data: dict) -> str:
    """
    Append personal contact information to AI-generated email
    
    Args:
        ai_content: AI-generated email content
        resume_data: User's resume information
        
    Returns:
        Email with contact information appended
    """
    if not resume_data:
        return ai_content
    
    personal_info = resume_data.get('personal_information', {})
    if not personal_info:
        return ai_content
    
    name = personal_info.get('name', '[Your Name]')
    email = personal_info.get('email', '[Your Email]')
    phone = personal_info.get('phone', '[Your Phone]')
    
    # Add contact information after "Best regards,"
    if "Best regards," in ai_content:
        contact_signature = f"\n{name}\n{email}\n{phone}"
        return ai_content + contact_signature
    else:
        # If "Best regards," not found, append at the end
        contact_signature = f"\n\nBest regards,\n{name}\n{email}\n{phone}"
        return ai_content + contact_signature

def append_contact_info_to_cover_letter(ai_content: str, resume_data: dict, internship_data: dict) -> str:
    """
    Append personal contact information to AI-generated cover letter
    
    Args:
        ai_content: AI-generated cover letter content
        resume_data: User's resume information
        internship_data: Job/internship details
        
    Returns:
        Cover letter with contact information appended
    """
    if not resume_data:
        return ai_content
    
    personal_info = resume_data.get('personal_information', {})
    if not personal_info:
        return ai_content
    
    name = personal_info.get('name', '[Your Name]')
    email = personal_info.get('email', '[Your Email]')
    phone = personal_info.get('phone', '[Your Phone]')
    address = personal_info.get('address', '[Your Address]')
    
    # Create header with contact information
    header = f"""{name}
{address}
{email} | {phone}

{datetime.now().strftime('%B %d, %Y')}

"""
    
    # Add name after "Sincerely,"
    if "Sincerely," in ai_content:
        final_content = header + ai_content + f"\n{name}"
    else:
        # If "Sincerely," not found, append at the end
        final_content = header + ai_content + f"\n\nSincerely,\n{name}"
    
    return final_content

def call_groq_api(prompt: str, max_tokens: int = 1000) -> Tuple[bool, str]:
    """
    Call Groq API to generate content based on prompt
    
    Args:
        prompt: The prompt to send to the AI
        max_tokens: Maximum tokens in response
        
    Returns:
        Tuple of (success: bool, content: str)
    """
    
    api_key = get_api_key()
    if not api_key:
        return False, "Error: Groq API key not configured. Please set GROQ_API_KEY in secrets.toml or environment variable."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-oss-20b",  # Groq's fast Llama model
        "messages": [
            {
                "role": "system",
                "content": "You are a professional career counselor and expert writer specializing in job applications. Generate high-quality, tailored content that helps candidates stand out. CRITICAL RULES: 1) Only use factual information provided in the prompt. Never fabricate experiences, projects, achievements, or statistics. 2) NEVER use generic project names like 'Project A', 'Project B', 'Project C', etc. Instead use natural language like 'in one of my projects', 'through my project work', or the actual project name if provided. 3) If insufficient information is provided, focus on transferable skills, enthusiasm to learn, and general qualifications."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if content:
            return True, content.strip()
        else:
            return False, "Error: Empty response from Groq API"
            
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"API Request Error: {str(e)}"
    except json.JSONDecodeError as e:
        return False, f"JSON Decode Error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected Error: {str(e)}"

def generate_email_content(resume_data: dict, internship_data: dict, additional_info: str = "") -> Tuple[bool, str]:
    """
    Generate professional email content using AI
    
    Args:
        resume_data: User's resume information
        internship_data: Job/internship details
        additional_info: Additional job requirements (optional)
        
    Returns:
        Tuple of (success: bool, email_content: str)
    """
    
    # Clean additional info
    additional_info = additional_info.strip() if additional_info else ""
    
    # Validate resume data quality
    if not has_sufficient_resume_data(resume_data):
        return False, "Please add more details to your resume (education, skills, experience, or projects) for better AI generation quality."
    
    try:
        prompt = get_email_prompt(resume_data, internship_data, additional_info)
        
        # Add extra validation reminder
        prompt += "\n\nIMPORTANT REMINDER: Only use factual information from the candidate's resume above. Do not fabricate any experiences, projects, or achievements."
        
        success, ai_content = call_groq_api(prompt, max_tokens=800)
        
        if success:
            # Append personal contact information after AI generation
            final_content = append_contact_info_to_email(ai_content, resume_data)
            return True, final_content
        else:
            return False, ai_content
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return False, f"Error generating email prompt: {str(e)}\n\nFull error:\n{error_details}"

def generate_cover_letter_content(resume_data: dict, internship_data: dict, additional_info: str = "") -> Tuple[bool, str]:
    """
    Generate professional cover letter content using AI
    
    Args:
        resume_data: User's resume information
        internship_data: Job/internship details
        additional_info: Additional job requirements (optional)
        
    Returns:
        Tuple of (success: bool, cover_letter_content: str)
    """
    
    # Clean additional info
    additional_info = additional_info.strip() if additional_info else ""
    
    # Validate resume data quality
    if not has_sufficient_resume_data(resume_data):
        return False, "Please add more details to your resume (education, skills, experience, or projects) for better AI generation quality."
    
    try:
        prompt = get_cover_letter_prompt(resume_data, internship_data, additional_info)
        
        # Add extra validation reminder
        prompt += "\n\nCRITICAL REMINDER: Only use factual information from the candidate's resume above. Do not invent any experiences, projects, achievements, or statistics."
        
        success, ai_content = call_groq_api(prompt, max_tokens=1200)
        
        if success:
            # Append personal contact information after AI generation
            final_content = append_contact_info_to_cover_letter(ai_content, resume_data, internship_data)
            return True, final_content
        else:
            return False, ai_content
            
    except Exception as e:
        return False, f"Error generating cover letter prompt: {str(e)}"

def create_fallback_email(resume_data: dict, internship_data: dict, additional_info: str = "") -> str:
    """
    Create a fallback email template when AI is unavailable
    """
    # Handle None or missing resume data
    if not resume_data:
        resume_data = {}
    
    # Handle None internship data
    if not internship_data:
        internship_data = {}
    
    personal_info = resume_data.get('personal_information', {})
    skills = resume_data.get('skills', [])
    experience = resume_data.get('experience', [])
    
    job_title = internship_data.get('job_title', 'Position')
    company_name = internship_data.get('company_name', 'Company')
    
    return f"""THIS IS A FALLBACK TEMPLATE !!!
Subject: Application for {job_title} Position at {company_name}

Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With my background in {skills[0] if skills else 'relevant field'} and experience in {experience[0].get('role', experience[0].get('job_title', 'professional roles')) if experience else 'various projects'}, I am excited about the opportunity to contribute to your team.

Key qualifications I bring:
• {skills[0] if len(skills) > 0 else 'Relevant technical skills'}
• {skills[1] if len(skills) > 1 else 'Strong problem-solving abilities'}
• {skills[2] if len(skills) > 2 else 'Excellent communication skills'}

{f"In my recent role as {experience[0].get('role', experience[0].get('job_title', ''))}, I {experience[0].get('achievements', experience[0].get('description', ['gained valuable experience']))[0] if experience and (experience[0].get('achievements') or experience[0].get('description')) else 'developed relevant skills'}." if experience else "Through my academic and project experience, I have developed strong foundational skills relevant to this position."}

{f"The additional requirements you mentioned - {additional_info} - align well with my experience and interests." if additional_info else "I am particularly drawn to this role because of the opportunity to apply my skills in a dynamic environment."}

I would welcome the opportunity to discuss how my background and enthusiasm can contribute to {company_name}'s success. Thank you for considering my application.

Best regards,
{personal_info.get('name', '[Your Name]')}
{personal_info.get('phone', '[Your Phone]')}
{personal_info.get('email', '[Your Email]')}"""

def create_fallback_cover_letter(resume_data: dict, internship_data: dict, additional_info: str = "") -> str:
    """
    Create a fallback cover letter template when AI is unavailable
    """
    # Handle None or missing resume data
    if not resume_data:
        resume_data = {}
    
    # Handle None internship data
    if not internship_data:
        internship_data = {}
    
    personal_info = resume_data.get('personal_information', {})
    education = resume_data.get('education', [])
    experience = resume_data.get('experience', [])
    skills = resume_data.get('skills', [])
    
    return f"""THIS IS A FALLBACK TEMPLATE !!!

{personal_info.get('name', '[Your Name]')}
{personal_info.get('address', '[Your Address]')}
{personal_info.get('email', '[Email]')} | {personal_info.get('phone', '[Phone]')}

{datetime.now().strftime('%B %d, %Y')}

Hiring Manager
{internship_data.get('company_name', 'Company')}
[Company Address]

Dear Hiring Manager,

I am writing to express my sincere interest in the {internship_data.get('job_title', 'Position')} position at {internship_data.get('company_name', 'Company')}. As a {education[0].get('degree', 'qualified professional') if education else 'dedicated professional'} with expertise in {skills[0] if skills else 'relevant technologies'}, I am excited about the opportunity to contribute to your team's continued success.

RELEVANT EXPERIENCE:
{f"In my previous role as {experience[0].get('role', experience[0].get('job_title', ''))}, I successfully:" if experience else "Throughout my professional development, I have:"}
{f"• {experience[0].get('achievements', experience[0].get('description', ['Developed relevant skills']))[0]}" if experience and (experience[0].get('achievements') or experience[0].get('description')) else "• Developed strong technical and analytical skills"}
{f"• {experience[0].get('achievements', experience[0].get('description', ['', 'Collaborated effectively with teams']))[1] if len(experience[0].get('achievements', experience[0].get('description', []))) > 1 else 'Collaborated effectively with cross-functional teams'}" if experience and (experience[0].get('achievements') or experience[0].get('description')) else "• Demonstrated ability to work effectively in team environments"}

TECHNICAL SKILLS:
My technical expertise includes: {', '.join(skills[:5]) if skills else 'Various relevant technologies and methodologies'}

{f"ADDITIONAL QUALIFICATIONS: {additional_info}" if additional_info else ""}

I am particularly drawn to {internship_data.get('company_name', 'Company')} because of your reputation for innovation and excellence. The {internship_data.get('job_title', 'Position')} role represents an ideal opportunity for me to apply my skills while contributing to meaningful projects.

I would welcome the opportunity to discuss how my background, skills, and enthusiasm align with your team's needs. Thank you for your time and consideration.

Sincerely,
{personal_info.get('name', '[Your Name]')}"""