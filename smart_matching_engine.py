"""
Smart Job Matching Engine
Analyzes resume and job postings to calculate acceptance probability and compatibility scores
"""

import re
import json
from typing import Dict, List, Tuple, Set
from datetime import datetime
import math
import streamlit as st

class SmartMatchingEngine:
    """
    Engine for calculating job compatibility and acceptance probability
    based on resume analysis and job requirements
    """
    
    def __init__(self):
        # Common tech skills categorized by level
        self.tech_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'solidity'
            ],
            'web_frameworks': [
                'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask',
                'spring', 'laravel', 'rails', 'asp.net', 'fastapi', 'jakarta ee', 'mvc'
            ],
            'databases': [
                'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra', 'dynamodb',
                'sqlite', 'oracle', 'mariadb', 'elasticsearch', 'entity framework'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',
                'kubernetes', 'docker', 'terraform'
            ],
            'data_science': [
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
                'matplotlib', 'seaborn', 'jupyter', 'apache spark', 'opencv', 'power bi',
                'cnn', 'deep learning', 'machine learning', 'computer vision', 'image processing'
            ],
            'devops': [
                'git', 'jenkins', 'travis', 'circleci', 'gitlab', 'github actions',
                'ansible', 'puppet', 'chef', 'github'
            ],
            'blockchain': [
                'ethereum', 'solidity', 'web3', 'blockchain', 'smart contracts'
            ],
            'ai_ml': [
                'llm', 'prompt engineering', 'generative ai', 'artificial intelligence',
                'data mining', 'statistical modeling', 'shap'
            ]
        }
        
        # Experience level indicators
        self.experience_indicators = {
            'entry_level': ['intern', 'entry', 'junior', 'new grad', 'fresh', 'trainee'],
            'mid_level': ['mid', 'intermediate', 'experienced', '2-3 years', '3-5 years'],
            'senior_level': ['senior', 'lead', 'principal', 'architect', '5+ years', 'expert']
        }
        
        # Common requirements patterns
        self.requirement_patterns = {
            'education': r'(bachelor|master|phd|degree|bs|ms|ba|ma|computer science|engineering)',
            'experience_years': r'(\d+)\s*[-+]?\s*years?\s*(of\s*)?(experience|exp)',
            'skills_required': r'(required|must have|essential|mandatory)',
            'skills_preferred': r'(preferred|nice to have|plus|bonus|desired)'
        }
    
    def analyze_resume(self, resume_data: dict) -> dict:
        """
        Analyze resume to extract key matching factors
        
        Args:
            resume_data: User's resume information in the format:
            {
                "personal_information": {...},
                "education": [...],
                "skills": [...],
                "languages": [...],
                "certifications": [...],
                "professional_experience": [...],
                "projects": [...],
                "extracurricular_activities": [...]
            }
            
        Returns:
            Dictionary with analyzed resume factors
        """
        analysis = {
            'skills': set(),
            'experience_level': 'entry_level',
            'years_experience': 0,
            'education_level': 'none',
            'has_degree': False,
            'relevant_projects': 0,
            'programming_languages': set(),
            'technical_categories': set(),
            'certifications_count': 0,
            'languages': set()
        }
        
        if not resume_data:
            return analysis
        
        # Analyze skills
        skills = resume_data.get('skills', [])
        devops_matches = []  # Track DevOps skills separately for stricter detection
        
        if skills:
            for skill in skills:
                skill_lower = skill.lower().strip()
                analysis['skills'].add(skill_lower)
                
                # Categorize technical skills with better matching
                for category, tech_list in self.tech_skills.items():
                    for tech in tech_list:
                        # Check if tech skill is mentioned in the skill description
                        if (tech in skill_lower or 
                            tech.replace(' ', '') in skill_lower.replace(' ', '') or
                            any(tech_variant in skill_lower for tech_variant in [tech, tech.upper(), tech.capitalize()])):
                            
                            # Special handling for DevOps - require more than just Git
                            if category == 'devops':
                                devops_matches.append(tech)
                            else:
                                analysis['technical_categories'].add(category)
                                
                            if category == 'programming_languages':
                                analysis['programming_languages'].add(tech)
                            break  # Found a match, no need to check other techs in this category
            
            # Only add DevOps category if multiple DevOps tools are found (not just Git/GitHub)
            devops_non_git_tools = [tool for tool in devops_matches 
                                   if tool not in ['git', 'github', 'gitlab']]
            if len(devops_non_git_tools) >= 1 or len(devops_matches) >= 3:
                analysis['technical_categories'].add('devops')
        
        # Analyze languages
        languages = resume_data.get('languages', [])
        if languages:
            for lang in languages:
                analysis['languages'].add(lang.lower().strip())
        
        # Analyze education
        education = resume_data.get('education', [])
        if education:
            analysis['has_degree'] = True
            highest_degree = 'bachelor'  # Default assumption
            
            for edu in education:
                degree = edu.get('degree', '').lower()
                # Check for engineering degrees (common for CS)
                if 'engineering' in degree and ('computer' in degree or 'software' in degree):
                    highest_degree = 'bachelor'  # Engineering degree equivalent
                elif 'master' in degree or 'ms' in degree or 'ma' in degree:
                    highest_degree = 'master'
                elif 'phd' in degree or 'doctorate' in degree:
                    highest_degree = 'phd'
                elif 'bachelor' in degree or 'bs' in degree or 'ba' in degree or 'license' in degree:
                    highest_degree = 'bachelor'
                elif 'preparatory' in degree or 'baccalaureate' in degree:
                    # These are pre-university, but still count as some education
                    if highest_degree == 'none':
                        highest_degree = 'high_school'
            
            analysis['education_level'] = highest_degree
        
        # Analyze professional experience
        professional_experience = resume_data.get('professional_experience', [])
        if professional_experience:
            # Calculate total years of experience from duration strings
            total_months = 0
            for exp in professional_experience:
                duration = exp.get('duration', '')
                # Try to parse duration like "2025/07 – 2025/08" or "2024/07 – 2024/08"
                if '–' in duration or '-' in duration:
                    try:
                        parts = duration.replace('–', '-').split('-')
                        if len(parts) == 2:
                            start_str = parts[0].strip()
                            end_str = parts[1].strip()
                            
                            # Parse year/month format
                            if '/' in start_str and '/' in end_str:
                                start_year, start_month = map(int, start_str.split('/'))
                                end_year, end_month = map(int, end_str.split('/'))
                                
                                months = (end_year - start_year) * 12 + (end_month - start_month)
                                total_months += max(1, months)  # At least 1 month
                            else:
                                # Fallback: assume 3 months per experience
                                total_months += 3
                    except:
                        # If parsing fails, assume 3 months
                        total_months += 3
                else:
                    # No clear duration, assume 3 months
                    total_months += 3
            
            analysis['years_experience'] = total_months / 12.0
            
            # Determine experience level
            if analysis['years_experience'] >= 3:
                analysis['experience_level'] = 'mid_level'
            elif analysis['years_experience'] >= 1:
                analysis['experience_level'] = 'entry_level'
            else:
                analysis['experience_level'] = 'entry_level'  # Recent graduate
        
        # Count projects
        projects = resume_data.get('projects', [])
        analysis['relevant_projects'] = len(projects) if projects else 0
        
        # Count certifications
        certifications = resume_data.get('certifications', [])
        analysis['certifications_count'] = len(certifications) if certifications else 0
        
        return analysis
    
    def extract_job_requirements(self, job_description: str, job_title: str) -> dict:
        """
        Extract requirements and preferences from job posting
        
        Args:
            job_description: Job description text
            job_title: Job title
            
        Returns:
            Dictionary with extracted requirements
        """
        requirements = {
            'required_skills': set(),
            'preferred_skills': set(),
            'min_years_experience': 0,
            'education_required': False,
            'degree_level': 'bachelor',
            'experience_level': 'entry_level',
            'technical_categories': set(),
            'is_remote': False,
            'company_size_indicator': 'unknown'
        }
        
        if not job_description:
            return requirements
        
        desc_lower = job_description.lower()
        title_lower = job_title.lower()
        
        # Extract experience requirements
        exp_matches = re.findall(self.requirement_patterns['experience_years'], desc_lower)
        if exp_matches:
            try:
                requirements['min_years_experience'] = int(exp_matches[0][0])
            except:
                pass
        
        # Determine experience level from title and description
        if any(term in title_lower for term in self.experience_indicators['senior_level']):
            requirements['experience_level'] = 'senior_level'
        elif any(term in title_lower for term in self.experience_indicators['mid_level']):
            requirements['experience_level'] = 'mid_level'
        elif any(term in title_lower + desc_lower for term in self.experience_indicators['entry_level']):
            requirements['experience_level'] = 'entry_level'
        
        # Extract education requirements
        if re.search(self.requirement_patterns['education'], desc_lower):
            requirements['education_required'] = True
            if 'master' in desc_lower or 'ms' in desc_lower:
                requirements['degree_level'] = 'master'
            elif 'phd' in desc_lower or 'doctorate' in desc_lower:
                requirements['degree_level'] = 'phd'
        
        # Note: GPA requirements are not processed as user doesn't have GPA
        
        # Extract technical skills with better matching
        for category, tech_list in self.tech_skills.items():
            for tech in tech_list:
                # More flexible matching for technical skills
                if (tech in desc_lower or 
                    tech.replace(' ', '') in desc_lower.replace(' ', '') or
                    any(variant in desc_lower for variant in [tech.upper(), tech.capitalize()])):
                    requirements['technical_categories'].add(category)
                    
                    # Determine if required or preferred
                    tech_context = self._get_skill_context(desc_lower, tech)
                    if re.search(self.requirement_patterns['skills_required'], tech_context):
                        requirements['required_skills'].add(tech)
                    else:
                        requirements['preferred_skills'].add(tech)
        
        # Check for remote work
        requirements['is_remote'] = any(term in desc_lower for term in ['remote', 'work from home', 'distributed'])
        
        return requirements
    
    def _get_skill_context(self, text: str, skill: str, context_window: int = 100) -> str:
        """
        Get surrounding context for a skill mention to determine if it's required or preferred
        """
        skill_pos = text.find(skill)
        if skill_pos == -1:
            return ""
        
        start = max(0, skill_pos - context_window)
        end = min(len(text), skill_pos + len(skill) + context_window)
        
        return text[start:end]
    #Overall Compatibility = (Technical × 40%) + (Experience × 35%) + (Education × 25%)
    def calculate_compatibility_score(self, resume_analysis: dict, job_requirements: dict) -> dict:
        """
        Calculate detailed compatibility score between resume and job
        
        Args:
            resume_analysis: Analyzed resume data
            job_requirements: Extracted job requirements
            
        Returns:
            Dictionary with detailed scoring breakdown
        """
        scores = {
            'technical_skills_score': 0.0,
            'experience_level_score': 0.0,
            'education_score': 0.0,
            'overall_compatibility': 0.0,
            'detailed_breakdown': {}
        }
        
        # Technical Skills Score (40% weight)
        technical_score = self._calculate_technical_score(resume_analysis, job_requirements)
        scores['technical_skills_score'] = technical_score
        
        # Experience Level Score (35% weight)
        experience_score = self._calculate_experience_score(resume_analysis, job_requirements)
        scores['experience_level_score'] = experience_score
        
        # Education Score (25% weight)
        education_score = self._calculate_education_score(resume_analysis, job_requirements)
        scores['education_score'] = education_score
        
        # Calculate weighted overall score
        scores['overall_compatibility'] = (
            technical_score * 0.40 +
            experience_score * 0.35 +
            education_score * 0.25
        )
        
        # Detailed breakdown for transparency
        scores['detailed_breakdown'] = {
            'technical_skills': {
                'score': technical_score,
                'weight': '40%',
                'details': self._get_technical_details(resume_analysis, job_requirements)
            },
            'experience_level': {
                'score': experience_score,
                'weight': '35%',
                'details': self._get_experience_details(resume_analysis, job_requirements)
            },
            'education': {
                'score': education_score,
                'weight': '25%',
                'details': self._get_education_details(resume_analysis, job_requirements)
            }
        }
        
        return scores
    
    def _calculate_technical_score(self, resume: dict, job: dict) -> float:
        """Calculate technical skills compatibility (0-100)"""
        if not job['required_skills'] and not job['preferred_skills']:
            return 85.0  # Benefit of doubt if no specific skills listed
        
        required_match = len(resume['skills'].intersection(job['required_skills']))
        required_total = len(job['required_skills'])
        
        preferred_match = len(resume['skills'].intersection(job['preferred_skills']))
        preferred_total = len(job['preferred_skills'])
        
        # Calculate weighted score
        if required_total > 0:
            required_score = (required_match / required_total) * 100
        else:
            required_score = 100
        
        if preferred_total > 0:
            preferred_score = (preferred_match / preferred_total) * 100
        else:
            preferred_score = 100
        
        # Required skills are 70% weight, preferred are 30%
        technical_score = (required_score * 0.7) + (preferred_score * 0.3)
        
        # Bonus for having programming languages
        if resume['programming_languages'] and job['technical_categories']:
            if 'programming_languages' in job['technical_categories']:
                technical_score = min(100, technical_score + 10)
        
        return round(technical_score, 1)
    
    def _calculate_experience_score(self, resume: dict, job: dict) -> float:
        """Calculate experience level compatibility (0-100)"""
        experience_levels = {'entry_level': 0, 'mid_level': 1, 'senior_level': 2}
        
        resume_level = experience_levels.get(resume['experience_level'], 0)
        required_level = experience_levels.get(job['experience_level'], 0)
        
        # Perfect match
        if resume_level == required_level:
            return 100.0
        
        # Overqualified (can be good or concerning depending on context)
        elif resume_level > required_level:
            if job['experience_level'] == 'entry_level':
                return 85.0  # Slightly lower for overqualification concerns
            else:
                return 95.0
        
        # Underqualified
        else:
            level_gap = required_level - resume_level
            if level_gap == 1:
                return 70.0  # One level below
            else:
                return 40.0  # Two levels below
    
    def _calculate_education_score(self, resume: dict, job: dict) -> float:
        """Calculate education compatibility (0-100)"""
        if not job['education_required']:
            return 95.0  # High score if no education required
        
        if not resume['has_degree']:
            return 30.0  # Low score if degree required but not present
        
        education_levels = {'high_school': 0, 'bachelor': 1, 'master': 2, 'phd': 3}
        
        resume_level = education_levels.get(resume['education_level'], 0)
        required_level = education_levels.get(job['degree_level'], 1)
        
        if resume_level >= required_level:
            return 100.0  # Perfect match
        elif resume_level == required_level - 1:
            return 80.0   # Close match (e.g., bachelor when master preferred)
        else:
            return 60.0  # Has degree but not the required level
    
    def _get_technical_details(self, resume: dict, job: dict) -> dict:
        """Get detailed technical skills breakdown"""
        return {
            'matching_required_skills': list(resume['skills'].intersection(job['required_skills'])),
            'missing_required_skills': list(job['required_skills'] - resume['skills']),
            'matching_preferred_skills': list(resume['skills'].intersection(job['preferred_skills'])),
            'your_technical_categories': list(resume['technical_categories']),
            'job_technical_categories': list(job['technical_categories'])
        }
    
    def _get_experience_details(self, resume: dict, job: dict) -> dict:
        """Get detailed experience breakdown"""
        return {
            'your_experience_level': resume['experience_level'],
            'your_years_experience': resume['years_experience'],
            'required_experience_level': job['experience_level'],
            'min_years_required': job['min_years_experience'],
            'relevant_projects': resume['relevant_projects']
        }
    
    def _get_education_details(self, resume: dict, job: dict) -> dict:
        """Get detailed education breakdown"""
        return {
            'your_education_level': resume['education_level'],
            'required_education': job['degree_level'] if job['education_required'] else 'Not specified',
            'education_required': job['education_required'],
            'certifications_count': resume.get('certifications_count', 0),
            'languages': list(resume.get('languages', set()))
        }
    
    def calculate_acceptance_probability(self, compatibility_scores: dict, additional_factors: dict = None) -> dict:
        """
        Calculate probability of acceptance based on compatibility and market factors
        
        Formula Components:
        1. Base compatibility score (70% weight)
        2. Market competition factor (20% weight) 
        3. Application timing factor (10% weight)
        
        Args:
            compatibility_scores: Output from calculate_compatibility_score
            additional_factors: Market and timing factors
            
        Returns:
            Dictionary with acceptance probability and confidence intervals
        """
        if not additional_factors:
            additional_factors = {}
        
        base_score = compatibility_scores['overall_compatibility']
        
        # Market competition factor (estimated)
        competition_factor = additional_factors.get('competition_level', 'medium')
        competition_multiplier = {
            'low': 1.2,     # 20% boost for low competition
            'medium': 1.0,   # No change
            'high': 0.8      # 20% penalty for high competition
        }.get(competition_factor, 1.0)
        
        # Application timing factor
        timing_factor = additional_factors.get('application_timing', 'normal')
        timing_multiplier = {
            'early': 1.15,   # 15% boost for early applications
            'normal': 1.0,   # No change
            'late': 0.9      # 10% penalty for late applications
        }.get(timing_factor, 1.0)
        
        # Calculate final probability (increased base weight from 60% to 70%)
        raw_probability = (
            base_score * 0.70 * competition_multiplier * timing_multiplier
        )
        
        # Apply realistic constraints (internships typically have lower acceptance rates)
        if raw_probability >= 90:
            final_probability = min(85, raw_probability)  # Cap at 85% for realism
        elif raw_probability >= 80:
            final_probability = raw_probability * 0.95
        elif raw_probability >= 70:
            final_probability = raw_probability * 0.90
        else:
            final_probability = raw_probability * 0.85
        
        # Confidence intervals
        confidence = self._calculate_confidence(compatibility_scores, additional_factors)
        
        return {
            'acceptance_probability': round(final_probability, 1),
            'confidence_level': confidence,
            'probability_range': {
                'low': max(0, round(final_probability - confidence, 1)),
                'high': min(100, round(final_probability + confidence, 1))
            },
            'formula_breakdown': {
                'base_compatibility': f"{base_score}%",
                'competition_adjustment': f"×{competition_multiplier}",
                'timing_adjustment': f"×{timing_multiplier}",
                'final_calculation': f"{raw_probability:.1f}% → {final_probability:.1f}%"
            },
            'improvement_suggestions': self._generate_improvement_suggestions(compatibility_scores, additional_factors)
        }
    
    def _calculate_confidence(self, compatibility_scores: dict, additional_factors: dict) -> float:
        """Calculate confidence level in the probability estimate"""
        base_confidence = 15.0  # Base ±15%
        
        # Higher compatibility = higher confidence
        if compatibility_scores['overall_compatibility'] >= 80:
            base_confidence -= 3
        elif compatibility_scores['overall_compatibility'] <= 40:
            base_confidence += 5
        
        return round(max(5, min(25, base_confidence)), 1)
    
    def _generate_improvement_suggestions(self, compatibility_scores: dict, additional_factors: dict) -> List[str]:
        """Generate actionable suggestions to improve acceptance probability"""
        suggestions = []
        
        breakdown = compatibility_scores['detailed_breakdown']
        
        # Technical skills suggestions
        if breakdown['technical_skills']['score'] < 70:
            technical_details = breakdown['technical_skills']['details']
            missing_skills = technical_details.get('missing_required_skills', [])
            if missing_skills:
                suggestions.append(f"🎯 Learn these required skills: {', '.join(missing_skills[:3])}")
            
            if not technical_details.get('matching_preferred_skills'):
                preferred_skills = technical_details.get('job_technical_categories', [])
                if preferred_skills:
                    suggestions.append(f"📈 Consider learning skills in: {', '.join(preferred_skills[:2])}")
        
        # Experience suggestions
        if breakdown['experience_level']['score'] < 70:
            exp_details = breakdown['experience_level']['details']
            if exp_details['relevant_projects'] < 2:
                suggestions.append("💼 Build 2-3 relevant projects to demonstrate skills")
            
            suggestions.append("🚀 Consider internships or freelance work to gain experience")
        
        # Education suggestions
        if breakdown['education']['score'] < 70:
            edu_details = breakdown['education']['details']
            if edu_details['education_required'] and not edu_details.get('your_education_level'):
                suggestions.append("🎓 Consider pursuing relevant degree or certifications")
        
        # General suggestions
        if not suggestions:
            suggestions.append("✅ Your profile looks strong! Consider applying early to improve chances.")
        
        return suggestions[:4]  # Limit to top 4 suggestions