"""
RAG-Powered LinkedIn Search Module
Uses resume context to intelligently search and filter LinkedIn opportunities
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional
import json
import re
from smart_matching_engine import SmartMatchingEngine
from web_scraper import scrape_linkedin
from supabase_db import SupabaseDB

class RAGLinkedInSearcher:
    """
    Retrieval-Augmented Generation powered LinkedIn search that uses resume context
    to intelligently find and rank relevant opportunities
    """
    
    def __init__(self):
        self.matching_engine = SmartMatchingEngine()
        self.db = SupabaseDB()
    
    def generate_smart_search_queries(self, resume_data: dict) -> List[Dict[str, str]]:
        """
        Generate intelligent search queries based on resume analysis
        
        Args:
            resume_data: User's resume information
            
        Returns:
            List of search query dictionaries with query and reasoning
        """
        
        if not resume_data:
            return [{"query": "software intern", "location": "", "reasoning": "Default broad search"}]
        
        resume_analysis = self.matching_engine.analyze_resume(resume_data)
        
        search_queries = []
        
        # 1. Skills-based searches
        if resume_analysis['programming_languages']:
            for lang in list(resume_analysis['programming_languages'])[:3]:  # Top 3 languages
                if len(lang) > 2:  # Avoid single letters
                    search_queries.append({
                        "query": f"{lang} developer intern",
                        "location": "",
                        "reasoning": f"Based on your {lang} programming skills"
                    })
        
        # 2. Technical category searches
        category_mapping = {
            'web_frameworks': 'web development intern',
            'data_science': 'data science intern',
            'cloud_platforms': 'cloud engineer intern',
            'databases': 'database developer intern'
            
        }
        
        for category in resume_analysis['technical_categories']:
            if category in category_mapping:
                search_queries.append({
                    "query": category_mapping[category],
                    "location": "",
                    "reasoning": f"Matches your {category.replace('_', ' ')} background"
                })
        
        # 3. Experience level appropriate searches
        experience_queries = {
            'entry_level': [
                "software engineer intern",
                "junior developer intern",
                "entry level software intern"
            ],
            'mid_level': [
                "software engineer intern",
                "development intern",
                "technical intern"
            ],
            'senior_level': [
                "senior software intern",
                "lead developer intern",
                "engineering intern"
            ]
        }
        
        exp_level = resume_analysis['experience_level']
        for query in experience_queries.get(exp_level, experience_queries['entry_level'])[:2]:
            search_queries.append({
                "query": query,
                "location": "",
                "reasoning": f"Appropriate for your {exp_level.replace('_', ' ')} experience"
            })
        
        # 4. Education-based searches
        if resume_analysis['education_level'] != 'none':
            education_queries = {
                'bachelor': ["computer science intern", "engineering intern"],
                'master': ["graduate software intern", "masters level intern"],
                'phd': ["research intern", "phd intern"]
            }
            
            for query in education_queries.get(resume_analysis['education_level'], [])[:1]:
                search_queries.append({
                    "query": query,
                    "location": "",
                    "reasoning": f"Matches your {resume_analysis['education_level']} education level"
                })
        
        # 5. Broad fallback searches if few specific skills found
        if len(search_queries) < 3:
            fallback_queries = [
                {"query": "software intern", "location": "", "reasoning": "Broad software internship search"},
                {"query": "technology intern", "location": "", "reasoning": "General technology internship search"},
                {"query": "computer science intern", "location": "", "reasoning": "CS field internship search"}
            ]
            
            for fallback in fallback_queries:
                if len(search_queries) < 5:
                    search_queries.append(fallback)
        
        # Remove duplicates while preserving order
        seen_queries = set()
        unique_queries = []
        for query_info in search_queries:
            query_key = query_info["query"]
            if query_key not in seen_queries:
                seen_queries.add(query_key)
                unique_queries.append(query_info)
        
        return unique_queries[:5]  # Limit to 5 queries to avoid overwhelming
    
    def perform_rag_search(self, resume_data: dict, user_id: str, max_results_per_query: int = 20, custom_queries: List[dict] = None) -> Dict:
        """
        Perform RAG-powered search across multiple intelligent queries
        
        Args:
            resume_data: User's resume information
            user_id: User identifier for saving results
            max_results_per_query: Maximum results per individual search
            custom_queries: Optional list of custom search queries to use instead of AI-generated ones
            
        Returns:
            Dictionary with search results and metadata
        """
        
        # Use custom queries if provided, otherwise generate intelligent search queries
        if custom_queries:
            search_queries = custom_queries
        else:
            search_queries = self.generate_smart_search_queries(resume_data)
        
        results = {
            'search_queries_used': search_queries,
            'raw_results': [],
            'analyzed_results': [],
            'summary': {
                'total_found': 0,
                'high_match_count': 0,
                'medium_match_count': 0,
                'low_match_count': 0,
                'average_compatibility': 0,
                'top_recommendations': []
            }
        }
        
        all_scraped_results = []
        
        # Execute each search query
        for i, query_info in enumerate(search_queries):
            st.write(f"🔍 **Search {i+1}/{len(search_queries)}:** {query_info['query']}")
            st.write(f"*{query_info['reasoning']}*")
            
            with st.spinner(f"Searching LinkedIn for: {query_info['query']}..."):
                # Perform the actual LinkedIn search
                try:
                    search_results = scrape_linkedin(
                        job_title=query_info['query'],
                        location=query_info['location'],
                        max_results=max_results_per_query
                    )
                    
                    # Check if scraping returned an error
                    if isinstance(search_results, dict) and 'error' in search_results:
                        st.error(f"❌ Error in search: {search_results['error']}")
                        continue
                    
                    if search_results and len(search_results) > 0:
                        st.success(f"✅ Found {len(search_results)} opportunities")
                        
                        # Add query context to each result
                        for result in search_results:
                            if isinstance(result, dict):  # Ensure result is a dictionary
                                result['search_context'] = query_info
                                all_scraped_results.append(result)
                    else:
                        st.warning(f"⚠️ No results found for this search")
                        
                except Exception as e:
                    st.error(f"❌ Error in search: {str(e)}")
                    
                # Small delay between searches to be respectful
                import time
                time.sleep(2)
        
        results['raw_results'] = all_scraped_results
        results['summary']['total_found'] = len(all_scraped_results)
        
        # Analyze and score all results
        st.write("🧠 **Analyzing compatibility scores...**")
        analyzed_results = self.analyze_and_score_results(all_scraped_results, resume_data)
        
        results['analyzed_results'] = analyzed_results
        results['summary'] = self._generate_summary_stats(analyzed_results)
        
        return results
    
    def analyze_and_score_results(self, scraped_results: List[dict], resume_data: dict) -> List[dict]:
        """
        Analyze and score each job posting for compatibility
        
        Args:
            scraped_results: Raw scraped job postings
            resume_data: User's resume information
            
        Returns:
            List of job postings with compatibility scores and analysis
        """
        
        resume_analysis = self.matching_engine.analyze_resume(resume_data)
        analyzed_results = []
        
        progress_bar = st.progress(0)
        
        for i, job in enumerate(scraped_results):
            # Extract job requirements
            job_requirements = self.matching_engine.extract_job_requirements(
                job_description=job.get('job_description', ''),
                job_title=job.get('job_title', '')
            )
            
            # Calculate compatibility score
            compatibility_scores = self.matching_engine.calculate_compatibility_score(
                resume_analysis, job_requirements
            )
            
            # Calculate acceptance probability
            additional_factors = {
                'competition_level': self._estimate_competition_level(job),
                'application_timing': 'normal'  # Could be enhanced with posting date analysis
            }
            
            acceptance_analysis = self.matching_engine.calculate_acceptance_probability(
                compatibility_scores, additional_factors
            )
            
            # Combine all analysis
            analyzed_job = {
                **job,  # Original job data
                'resume_analysis': resume_analysis,
                'job_requirements': job_requirements,
                'compatibility_scores': compatibility_scores,
                'acceptance_analysis': acceptance_analysis,
                'match_category': self._categorize_match(compatibility_scores['overall_compatibility']),
                'recommendation_priority': self._calculate_priority(compatibility_scores, acceptance_analysis)
            }
            
            analyzed_results.append(analyzed_job)
            
            # Update progress
            progress_bar.progress((i + 1) / len(scraped_results))
        
        # Sort by recommendation priority (highest first)
        analyzed_results.sort(key=lambda x: x['recommendation_priority'], reverse=True)
        
        return analyzed_results
    
    def _estimate_competition_level(self, job: dict) -> str:
        """
        Estimate competition level based on job characteristics
        """
        title = job.get('job_title', '').lower()
        company = job.get('company_name', '').lower()
        description = job.get('job_description', '').lower()
        
        # High competition indicators
        high_competition_indicators = [
            'google', 'apple', 'microsoft', 'amazon', 'meta', 'netflix', 'tesla',
            'senior', 'lead', 'principal', 'architect',
            'machine learning', 'artificial intelligence', 'ai'
        ]
        
        # Low competition indicators
        low_competition_indicators = [
            'intern', 'entry', 'junior', 'new grad', 'trainee',
            'startup', 'small company'
        ]
        
        high_score = sum(1 for indicator in high_competition_indicators 
                        if indicator in title + company + description)
        low_score = sum(1 for indicator in low_competition_indicators 
                       if indicator in title + company + description)
        
        if high_score > low_score:
            return 'high'
        elif low_score > high_score:
            return 'low'
        else:
            return 'medium'
    

    
    def _categorize_match(self, compatibility_score: float) -> str:
        """Categorize match quality based on compatibility score"""
        if compatibility_score >= 80:
            return 'High Match'
        elif compatibility_score >= 60:
            return 'Medium Match'
        else:
            return 'Low Match'
    
    def _calculate_priority(self, compatibility_scores: dict, acceptance_analysis: dict) -> float:
        """
        Calculate recommendation priority combining compatibility and acceptance probability
        """
        compatibility = compatibility_scores['overall_compatibility']
        acceptance_prob = acceptance_analysis['acceptance_probability']
        
        # Weighted combination: 60% compatibility, 40% acceptance probability
        priority = (compatibility * 0.6) + (acceptance_prob * 0.4)
        
        return round(priority, 1)
    
    def _generate_summary_stats(self, analyzed_results: List[dict]) -> dict:
        """Generate summary statistics for the search results"""
        if not analyzed_results:
            return {
                'total_found': 0,
                'high_match_count': 0,
                'medium_match_count': 0,
                'low_match_count': 0,
                'average_compatibility': 0,
                'average_acceptance_probability': 0,
                'top_recommendations': []
            }
        
        # Count matches by category
        high_match_count = sum(1 for job in analyzed_results if job['match_category'] == 'High Match')
        medium_match_count = sum(1 for job in analyzed_results if job['match_category'] == 'Medium Match')
        low_match_count = sum(1 for job in analyzed_results if job['match_category'] == 'Low Match')
        
        # Calculate averages
        avg_compatibility = sum(job['compatibility_scores']['overall_compatibility'] 
                               for job in analyzed_results) / len(analyzed_results)
        
        avg_acceptance = sum(job['acceptance_analysis']['acceptance_probability'] 
                            for job in analyzed_results) / len(analyzed_results)
        
        # Get top recommendations
        top_recommendations = analyzed_results[:5]  # Top 5 by priority
        
        return {
            'total_found': len(analyzed_results),
            'high_match_count': high_match_count,
            'medium_match_count': medium_match_count,
            'low_match_count': low_match_count,
            'average_compatibility': round(avg_compatibility, 1),
            'average_acceptance_probability': round(avg_acceptance, 1),
            'top_recommendations': top_recommendations
        }
    
    def save_smart_search_results(self, search_results: dict, user_id: str) -> bool:
        """
        Save the analyzed search results to database
        
        Args:
            search_results: Complete search results with analysis
            user_id: User identifier
            
        Returns:
            Boolean indicating success
        """
        try:
            saved_count = 0
            
            for job in search_results['analyzed_results']:
                # Prepare job data for database (only fields that exist in schema)
                job_data = {
                    'job_title': job.get('job_title', ''),
                    'company_name': job.get('company_name', ''),
                    'application_link': job.get('application_link', ''),
                    'status': 'new'
                    # Note: Smart Search metadata (compatibility scores, acceptance probability, etc.) 
                    # is stored in session state and displayed during the search session
                    # job_description is not saved to avoid schema errors
                }
                
                # Save to database
                result = self.db.add_internship(user_id, job_data)
                if result.get('success'):
                    saved_count += 1
            
            return saved_count > 0
            
        except Exception as e:
            st.error(f"Error saving results: {str(e)}")
            return False