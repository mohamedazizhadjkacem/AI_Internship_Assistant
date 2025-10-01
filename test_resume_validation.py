#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced resume template validation.
"""

import json
import sys
import os

# Add the project directory to the path so we can import the resume view
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from views.resume_view import validate_json_format, get_required_template

def test_valid_resume():
    """Test with a valid resume that matches the template."""
    print("🧪 **Test 1: Valid Resume**")
    print("=" * 50)
    
    valid_resume = {
        "personal_information": {
            "name": "John Doe",
            "phone": "+1-234-567-8900",
            "email": "john.doe@email.com",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe"
        },
        "education": [
            {
                "degree": "Computer Science Bachelor",
                "institution": "Tech University",
                "years": "2020-2024"
            }
        ],
        "skills": ["Python", "JavaScript", "React"],
        "languages": ["English", "French"],
        "certifications": ["AWS Certified Developer"],
        "professional_experience": [
            {
                "role": "Software Developer Intern",
                "organization": "Tech Corp",
                "duration": "Summer 2023",
                "achievements": ["Built a web application", "Improved performance by 30%"]
            }
        ],
        "projects": [
            {
                "title": "Personal Portfolio",
                "technologies": ["React", "Node.js"],
                "description": "A responsive portfolio website"
            }
        ],
        "extracurricular_activities": ["Programming Club Member", "Hackathon Participant"]
    }
    
    json_text = json.dumps(valid_resume, indent=2)
    is_valid, errors = validate_json_format(json_text)
    
    print(f"📋 Resume JSON:")
    print(json_text[:200] + "..." if len(json_text) > 200 else json_text)
    print(f"\\n✅ **Result:** {'Valid' if is_valid else 'Invalid'}")
    
    if not is_valid:
        print("❌ **Errors found:**")
        for error in errors:
            print(f"  • {error}")
    else:
        print("🎉 **Perfect!** Resume matches the required template!")

def test_missing_fields():
    """Test with a resume missing required fields."""
    print("\\n\\n🧪 **Test 2: Missing Required Fields**")
    print("=" * 50)
    
    incomplete_resume = {
        "personal_information": {
            "name": "Jane Smith",
            "email": "jane@email.com"
            # Missing phone, linkedin, github
        },
        "skills": ["Python", "Java"],
        # Missing education, languages, certifications, professional_experience, projects, extracurricular_activities
    }
    
    json_text = json.dumps(incomplete_resume, indent=2)
    is_valid, errors = validate_json_format(json_text)
    
    print(f"📋 Incomplete Resume JSON:")
    print(json_text)
    print(f"\\n❌ **Result:** {'Valid' if is_valid else 'Invalid'}")
    
    if not is_valid:
        print("❌ **Validation Errors:**")
        for error in errors:
            print(f"  • {error}")

def test_wrong_data_types():
    """Test with wrong data types."""
    print("\\n\\n🧪 **Test 3: Wrong Data Types**")
    print("=" * 50)
    
    wrong_types_resume = {
        "personal_information": {
            "name": "Bob Wilson",
            "phone": 1234567890,  # Should be string, not number
            "email": "bob@email.com",
            "linkedin": "https://linkedin.com/in/bobwilson",
            "github": "https://github.com/bobwilson"
        },
        "education": "Computer Science Degree",  # Should be array, not string
        "skills": ["Python", "JavaScript"],
        "languages": ["English"],
        "certifications": ["Some Cert"],
        "professional_experience": [
            {
                "role": "Developer",
                "organization": "Company",
                "duration": "2023",
                "achievements": "Built something"  # Should be array, not string
            }
        ],
        "projects": [
            {
                "title": "Project",
                "technologies": "React, Node.js",  # Should be array, not string
                "description": "A project"
            }
        ],
        "extracurricular_activities": ["Club Member"]
    }
    
    json_text = json.dumps(wrong_types_resume, indent=2)
    is_valid, errors = validate_json_format(json_text)
    
    print(f"📋 Wrong Types Resume JSON:")
    print(json_text)
    print(f"\\n❌ **Result:** {'Valid' if is_valid else 'Invalid'}")
    
    if not is_valid:
        print("❌ **Type Validation Errors:**")
        for error in errors:
            print(f"  • {error}")

def test_extra_fields():
    """Test with extra fields not in template."""
    print("\\n\\n🧪 **Test 4: Extra Fields Not in Template**")
    print("=" * 50)
    
    extra_fields_resume = {
        "personal_information": {
            "name": "Alice Johnson",
            "phone": "+1-234-567-8900",
            "email": "alice@email.com",
            "linkedin": "https://linkedin.com/in/alicejohnson",
            "github": "https://github.com/alicejohnson",
            "age": 25,  # Extra field
            "address": "123 Main St"  # Extra field
        },
        "education": [
            {
                "degree": "Computer Science",
                "institution": "University",
                "years": "2020-2024",
                "gpa": 3.8  # Extra field
            }
        ],
        "skills": ["Python", "Java"],
        "languages": ["English"],
        "certifications": ["Cert"],
        "professional_experience": [
            {
                "role": "Developer",
                "organization": "Company",
                "duration": "2023",
                "achievements": ["Built app"],
                "salary": 50000  # Extra field
            }
        ],
        "projects": [
            {
                "title": "Project",
                "technologies": ["React"],
                "description": "Description"
            }
        ],
        "extracurricular_activities": ["Club"],
        "hobbies": ["Reading", "Gaming"]  # Extra field
    }
    
    json_text = json.dumps(extra_fields_resume, indent=2)
    is_valid, errors = validate_json_format(json_text)
    
    print(f"📋 Extra Fields Resume JSON (first 300 chars):")
    print(json_text[:300] + "...")
    print(f"\\n⚠️ **Result:** {'Valid' if is_valid else 'Invalid'}")
    
    if not is_valid:
        print("⚠️ **Extra Field Warnings:**")
        for error in errors:
            print(f"  • {error}")

def show_required_template():
    """Show the required template structure."""
    print("\\n\\n📋 **Required Template Structure**")
    print("=" * 50)
    
    template = get_required_template()
    print("This is the EXACT structure your resume must follow:")
    print(json.dumps(template, indent=2))

if __name__ == "__main__":
    print("🚀 **Resume Template Validation Tests**")
    print("\\nThis script demonstrates how the enhanced resume validation works.")
    
    # Show the required template first
    show_required_template()
    
    # Run all tests
    test_valid_resume()
    test_missing_fields()
    test_wrong_data_types()
    test_extra_fields()
    
    print("\\n\\n🎯 **Summary:**")
    print("✅ **Valid resumes** must match the exact template structure")
    print("❌ **Invalid resumes** will show detailed error messages")
    print("⚠️ **Extra fields** not in the template are not allowed")
    print("🔍 **Data types** must match exactly (strings, arrays, objects)")
    print("\\n💡 **In the app:** Use 'Validate JSON' button to check your resume!")