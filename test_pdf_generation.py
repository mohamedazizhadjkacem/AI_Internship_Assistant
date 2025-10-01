#!/usr/bin/env python3
"""
Test script to verify PDF generation for cover letters.
"""

import sys
import os

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pdf_generation():
    """Test the PDF generation functionality."""
    print("🧪 **Testing Cover Letter PDF Generation**")
    print("=" * 50)
    
    try:
        from pdf_generator import create_cover_letter_pdf, generate_pdf_filename
        print("✅ Successfully imported PDF generation functions")
        
        # Test data
        sample_cover_letter = """Dear Hiring Manager,

I am writing to express my strong interest in the Software Developer Intern position at Tech Company. With my background in computer science and passion for technology, I am excited about the opportunity to contribute to your team.

During my studies, I have developed proficiency in Python, JavaScript, and React, which align perfectly with the requirements mentioned in your job posting. My recent project building a web application using these technologies demonstrates my ability to deliver practical solutions.

I am particularly drawn to Tech Company's commitment to innovation and would welcome the opportunity to contribute to your mission. I am confident that my technical skills, combined with my enthusiasm for learning, make me a strong candidate for this position.

Thank you for considering my application. I look forward to hearing from you.

Sincerely,
John Doe"""
        
        # Test PDF generation
        print("🔄 Generating PDF...")
        pdf_data = create_cover_letter_pdf(
            content=sample_cover_letter,
            applicant_name="John Doe",
            job_title="Software Developer Intern",
            company_name="Tech Company"
        )
        
        print(f"✅ PDF generated successfully! Size: {len(pdf_data)} bytes")
        
        # Test filename generation
        filename = generate_pdf_filename(
            applicant_name="John Doe",
            job_title="Software Developer Intern", 
            company_name="Tech Company"
        )
        
        print(f"✅ Filename generated: {filename}")
        
        # Save test PDF
        with open("test_cover_letter.pdf", "wb") as f:
            f.write(pdf_data)
        
        print("✅ Test PDF saved as 'test_cover_letter.pdf'")
        print("🎉 **All PDF generation tests passed!**")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure reportlab is installed: pip install reportlab")
        return False
        
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        return False

def test_edge_cases():
    """Test PDF generation with edge cases."""
    print("\\n\\n🧪 **Testing Edge Cases**")
    print("=" * 50)
    
    try:
        from pdf_generator import create_cover_letter_pdf, generate_pdf_filename
        
        # Test with empty/minimal data
        print("🔄 Testing with minimal data...")
        pdf_data = create_cover_letter_pdf(
            content="Short cover letter.",
            applicant_name="",
            job_title="",
            company_name=""
        )
        print(f"✅ Minimal data test passed! Size: {len(pdf_data)} bytes")
        
        # Test with special characters
        print("🔄 Testing with special characters...")
        pdf_data = create_cover_letter_pdf(
            content="Dear Sir/Madam, I'm interested in the C# .NET position at A&B Company! My résumé shows 100% dedication.",
            applicant_name="José María",
            job_title="Senior .NET Developer",
            company_name="A&B Tech Solutions"
        )
        print(f"✅ Special characters test passed! Size: {len(pdf_data)} bytes")
        
        # Test with very long content
        print("🔄 Testing with long content...")
        long_content = "This is a very long cover letter. " * 100
        pdf_data = create_cover_letter_pdf(
            content=long_content,
            applicant_name="Very Long Name Here",
            job_title="Very Long Job Title Position Name",
            company_name="Very Long Company Name Corporation Ltd"
        )
        print(f"✅ Long content test passed! Size: {len(pdf_data)} bytes")
        
        print("🎉 **All edge case tests passed!**")
        return True
        
    except Exception as e:
        print(f"❌ Edge case test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 **Cover Letter PDF Generation Tests**")
    print("\\nTesting the PDF generation functionality used in the application...")
    
    success1 = test_pdf_generation()
    success2 = test_edge_cases()
    
    if success1 and success2:
        print("\\n\\n🎯 **SUMMARY: All tests passed!**")
        print("✅ PDF generation is working correctly")
        print("✅ Cover letter download should work in the app")
        print("\\n💡 If you're still having download issues:")
        print("  1. Make sure you've generated a cover letter first")
        print("  2. Check that your resume has personal information")
        print("  3. Try refreshing the page and generating again")
    else:
        print("\\n\\n❌ **SUMMARY: Some tests failed!**")
        print("💡 Check the error messages above to fix the issues")
    
    # Cleanup
    if os.path.exists("test_cover_letter.pdf"):
        os.remove("test_cover_letter.pdf")
        print("\\n🧹 Cleaned up test file")