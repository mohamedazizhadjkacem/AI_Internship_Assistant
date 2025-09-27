"""
Test script to verify the Smart Matching Engine works with the new resume format
"""

from smart_matching_engine import SmartMatchingEngine

def test_resume_analysis():
    """Test the updated analyze_resume method with the new format"""
    
    # Your exact resume format
    resume_data = {
        "personal_information": {
            "name": "m",
            "phone": "",
            "email": "",
            "linkedin": "",
            "github": ""
        },
        "education": [
            {
                "degree": "Engineering Degree in Computer Science (Software Engineering & Information Systems)",
                "institution": "Higher Institute of Computer Science and Multimedia of Gabès",
                "years": "2023 – 2026 (Currently)"
            },
            {
                "degree": "Preparatory Mathematics, Physics and Computer Science",
                "institution": "Higher Institute of Computer Science and Multimedia of Gabès",
                "years": "2021 – 2023"
            },
            {
                "degree": "Baccalaureate in Mathematics",
                "institution": "Taieb Mhiri High School Sfax, Tunisia",
                "years": "2021"
            }
        ],
        "skills": [
            "Python",
            "Solidity",
            "PostgreSQL",
            "Git / Github",
            "Deep Learning (PyTorch/TensorFlow, CNN)",
            "Database Systems (SQL, NoSQL)",
            "Computer Vision (OpenCV, Image Segmentation)",
            "Prompt Engineering",
            "Data Mining & Statistical Modeling (Scikit-learn, Pandas)",
            "Machine Learning",
            "Object-Oriented Design (Java/C#, Design Patterns)",
            "Data Visualization (Matplotlib, Seaborn, Power BI)",
            "Matlab",
            "Image processing",
            "LLM APIs",
            "NumPy"
        ],
        "languages": [
            "Arabic",
            "French",
            "English"
        ],
        "certifications": [
            "Deep Learning with TensorFlow 2.0 – 365 Careers",
            "ChatGPT Prompt Engineering for Developers – DeepLearning.AI",
            "Generative AI with Diffusion Models - Nvidia",
            "Python 101 for Data Science - Cognitive Class",
            "Scrum Fundamentals Certified (SFC) - SCRUMstudy",
            "National Student Entrepreneur Status - The Student Entrepreneur Hub"
        ],
        "professional_experience": [
            {
                "role": "Summer Internship – Sales Forecasting AI Assistant",
                "organization": "COGNIRA",
                "duration": "2025/07 – 2025/08",
                "achievements": [
                    "Developed an end-to-end retail sales prediction system combining ML, time-series forecasting, and chatbot.",
                    "Built and explained forecasting models with SHAP.",
                    "Researched and compared LLMs for retail sales prediction and interactive analysis.",
                    "Created interactive Streamlit dashboard with LLM query, scenario analysis, and real-time simulation."
                ]
            },
            {
                "role": "End of year project - AI-Powered Breast Cancer Imaging Platform",
                "organization": "Digital Research Center of Sfax",
                "duration": "2025/02 – 2025/05",
                "achievements": [
                    "Developed complete platform for patient management and automatic segmentation of breast tumors.",
                    "Built end-to-end system for annotation, segmentation, and diagnosis using U-Net.",
                    "Enhanced mammogram quality and accelerated diagnosis with visualization and annotation tools."
                ]
            },
            {
                "role": "Summer Internship – ERP System Developer",
                "organization": "Engineering and Machining Precision",
                "duration": "2024/07 – 2024/08",
                "achievements": [
                    "Designed and implemented C# .NET ERP system with stock management and project management modules.",
                    "Automated inventory tracking, reducing manual errors.",
                    "Streamlined task allocation and dashboards.",
                    "Demonstrated full-cycle development from requirements to deployment."
                ]
            }
        ],
        "projects": [
            {
                "title": "E-Commerce Platform",
                "technologies": [
                    "ASP.NET Core",
                    "Entity Framework"
                ],
                "description": "Developed full-stack e-commerce site with product catalog, cart system, and authentication. Adapted database schema for AI product recommendations."
            },
            {
                "title": "Hotel Management System",
                "technologies": [
                    "Jakarta EE",
                    "MVC",
                    "JSTL"
                ],
                "description": "Built role-based web app with dynamic hotel search filters, applying MVC best practices."
            },
            {
                "title": "Sales Forecasting Model",
                "technologies": [
                    "Python"
                ],
                "description": "Optimized Walmart sales forecasting models with preprocessing, visualizations, and evaluation metrics."
            },
            {
                "title": "PharmaChain: Supply Chain Integrity dApp",
                "technologies": [
                    "Ethereum",
                    "Solidity",
                    "Web3.js"
                ],
                "description": "Built decentralized app for drug supply chain integrity, enabling secure and transparent tracking."
            },
            {
                "title": "MediScan (Student Entrepreneur Program)",
                "technologies": [
                    "Blockchain",
                    "QR codes"
                ],
                "description": "Digital health platform for instant patient data access, blockchain-secured records, and SaaS financial modeling."
            }
        ],
        "extracurricular_activities": [
            "Active member of Student Entrepreneur Hub & IoT Club",
            "Deputy Head of HR & Corporate Relations Manager - Higher Institute of Computer Science and Multimedia of Gabès",
            "Organizer of XDays & JPO events"
        ]
    }

    # Initialize the engine
    engine = SmartMatchingEngine()
    
    # Test the analysis
    print("Testing resume analysis...")
    analysis = engine.analyze_resume(resume_data)
    
    # Print results
    print("\n=== RESUME ANALYSIS RESULTS ===")
    print(f"Skills found: {len(analysis['skills'])}")
    print(f"Programming languages: {analysis['programming_languages']}")
    print(f"Technical categories: {analysis['technical_categories']}")
    print(f"Experience level: {analysis['experience_level']}")
    print(f"Years of experience: {analysis['years_experience']:.1f}")
    print(f"Education level: {analysis['education_level']}")
    print(f"Has degree: {analysis['has_degree']}")
    print(f"Relevant projects: {analysis['relevant_projects']}")
    print(f"Certifications count: {analysis['certifications_count']}")
    print(f"Languages: {analysis['languages']}")
    
    # Test sample skills
    print(f"\nSample skills detected: {list(analysis['skills'])[:10]}")
    
    return analysis

def test_job_requirements():
    """Test job requirements extraction"""
    
    engine = SmartMatchingEngine()
    
    job_description = """
    We are looking for a Python Developer Intern to join our AI team. 
    Required skills: Python, TensorFlow, Machine Learning, SQL
    Preferred: PyTorch, Deep Learning experience, Computer Vision
    Bachelor's degree in Computer Science or Engineering required.
    2+ years of experience preferred but not mandatory for exceptional candidates.
    """
    
    job_title = "Python Developer Intern - AI Team"
    
    print("\n=== TESTING JOB REQUIREMENTS EXTRACTION ===")
    requirements = engine.extract_job_requirements(job_description, job_title)
    
    print(f"Required skills: {requirements['required_skills']}")
    print(f"Preferred skills: {requirements['preferred_skills']}")
    print(f"Education required: {requirements['education_required']}")
    print(f"Degree level: {requirements['degree_level']}")
    print(f"Experience level: {requirements['experience_level']}")
    print(f"Min years experience: {requirements['min_years_experience']}")
    print(f"Technical categories: {requirements['technical_categories']}")
    
    return requirements

def test_compatibility_scoring():
    """Test full compatibility scoring"""
    
    print("\n=== TESTING FULL COMPATIBILITY SCORING ===")
    
    # Get resume analysis
    resume_analysis = test_resume_analysis()
    
    # Get job requirements  
    requirements = test_job_requirements()
    
    # Calculate compatibility
    engine = SmartMatchingEngine()
    compatibility = engine.calculate_compatibility_score(resume_analysis, requirements)
    
    print(f"\nCompatibility Results:")
    print(f"Overall compatibility: {compatibility['overall_compatibility']:.1f}%")
    print(f"Technical skills score: {compatibility['technical_skills_score']:.1f}%")
    print(f"Experience score: {compatibility['experience_level_score']:.1f}%")
    print(f"Education score: {compatibility['education_score']:.1f}%")
    
    # Print detailed breakdown
    breakdown = compatibility['detailed_breakdown']
    for category, details in breakdown.items():
        print(f"\n{category.title()}:")
        print(f"  Score: {details['score']:.1f}% (Weight: {details['weight']})")
        if 'details' in details and isinstance(details['details'], dict):
            for key, value in details['details'].items():
                if value:  # Only show non-empty values
                    print(f"  {key}: {value}")

if __name__ == "__main__":
    print("🧠 Testing Smart Matching Engine with Updated Resume Format")
    print("=" * 60)
    
    try:
        test_compatibility_scoring()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()