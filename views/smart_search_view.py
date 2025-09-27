"""
Smart Search View
Implements intelligent, resume-tailored job search with RAG and compatibility scoring
"""

import streamlit as st
import json
from typing import Dict, List
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from rag_linkedin_searcher import RAGLinkedInSearcher
from smart_matching_engine import SmartMatchingEngine
import time

def show_smart_search_page():
    """Main Smart Search page with RAG-powered LinkedIn search and compatibility analysis"""
    
    st.title("🧠 Smart Search - AI-Powered Job Matching")
    st.markdown("""
    **Intelligent job search that analyzes your resume to find the best opportunities with acceptance probability scores.**
    
    This advanced system:
    - 🎯 Generates targeted searches based on your resume
    - 📊 Calculates compatibility scores for each opportunity  
    - 🎲 Estimates acceptance probability using our proprietary formula
    - 🚀 Provides actionable improvement suggestions
    """)
    
    # Check if user has resume
    if 'resume' not in st.session_state or not st.session_state.resume:
        st.warning("⚠️ **Resume Required**: Please add your resume in the Resume Manager first for personalized job matching.")
        st.info("� **Tip**: Go to the Resume Manager tab in the sidebar to upload and manage your resume information.")
        return
    
    # Initialize searcher
    searcher = RAGLinkedInSearcher()
    matching_engine = SmartMatchingEngine()
    
    # Display Resume Analysis Summary
    with st.expander("📋 Your Resume Analysis", expanded=False):
        show_resume_analysis_summary(st.session_state.resume, matching_engine)
    
    st.markdown("---")
    
    # Smart Search Section
    st.markdown("## 🔍 Intelligent Job Search")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Search Configuration")
        
        # Search options
        st.markdown("**Search Mode:** 🎯 Custom Queries Only")
        st.info("💡 **Tip**: Add your own targeted search queries below to find specific opportunities.")
        search_mode = "🎯 Custom Query"  # Fixed to custom only
        
        max_results_per_query = st.slider(
            "Max results per search query:",
            min_value=10,
            max_value=50,
            value=25,
            help="Higher values give more comprehensive results but take longer"
        )
        
    # Query Management section (moved above Add New Search Query)
    st.markdown("---")
    st.markdown("## 📋 Query Management")
    
    # Display current queries
    if 'custom_queries' not in st.session_state:
        st.session_state.custom_queries = []
    if 'modify_query_index' not in st.session_state:
        st.session_state.modify_query_index = None
    
    if st.session_state.custom_queries:
        # Clear all queries button at the top
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 📋 Current Search Queries:")
        with col2:
            if st.button("🗑️ Clear All Queries", help="Remove all search queries", key="clear_all_top"):
                st.session_state.custom_queries = []
                st.success("All queries cleared!")
                st.rerun()
        
        for i, query_info in enumerate(st.session_state.custom_queries):
            # Highlight the query being modified
            is_being_modified = st.session_state.get('modify_query_index') == i
            
            if is_being_modified:
                st.info("✏️ **This query is being modified below**")
            
            col_query, col_actions = st.columns([3, 1])
            
            with col_query:
                query_prefix = "🔧" if is_being_modified else f"**{i+1}.**"
                st.write(f"{query_prefix} `{query_info['query']}`")
                if query_info.get('location'):
                    st.write(f"📍 *Location: {query_info['location']}*")
            
            with col_actions:
                # Remove button for each query
                if st.button("🗑️", key=f"remove_{i}", help="Remove this query"):
                    if st.session_state.modify_query_index == i:
                        st.session_state.modify_query_index = None  # Clear modify mode if deleting
                    st.session_state.custom_queries.pop(i)
                    # Adjust modify index if needed
                    if st.session_state.modify_query_index is not None and st.session_state.modify_query_index > i:
                        st.session_state.modify_query_index -= 1
                    st.rerun()
                
                # Modify button for each query
                modify_label = "📝" if is_being_modified else "✏️"
                modify_help = "Currently modifying" if is_being_modified else "Modify this query"
                if st.button(modify_label, key=f"modify_{i}", help=modify_help, disabled=is_being_modified):
                    st.session_state.modify_query_index = i
                    st.rerun()
    else:
        st.info("No search queries added yet. Add some below!")
        
        # Quick start templates
        st.markdown("**🚀 Quick Start Templates:**")
        template_queries = [
            {"query": "Software Engineer Intern", "location": ""},
            {"query": "Data Science Intern", "location": ""},
            {"query": "Frontend Developer Intern", "location": ""},
            {"query": "Machine Learning Intern", "location": ""},
            {"query": "Backend Developer Intern", "location": ""}
        ]
        
        cols = st.columns(len(template_queries))
        for i, template in enumerate(template_queries):
            with cols[i]:
                if st.button(f"➕ {template['query']}", key=f"template_{i}", help="Add this template query"):
                    template["reasoning"] = "User-selected template search"
                    st.session_state.custom_queries.append(template)
                    st.success(f"✅ Added: {template['query']}")
                    st.rerun()
    

    
    # Query modification section (appears when modify button is clicked)
    if st.session_state.get('modify_query_index') is not None and st.session_state.custom_queries:
        modify_idx = st.session_state.modify_query_index
        
        # Check if the index is still valid
        if 0 <= modify_idx < len(st.session_state.custom_queries):
            current_query = st.session_state.custom_queries[modify_idx]
            
            st.markdown(f"### ✏️ Modify Query #{modify_idx + 1}")
            
            with st.form("modify_query_form"):
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    modified_title = st.text_input(
                        "Job Title/Keywords",
                        value=current_query['query'],
                        key="modify_title"
                    )
                
                with col2:
                    modified_location = st.text_input(
                        "Location",
                        value=current_query.get('location', ''),
                        key="modify_location"
                    )
                
                with col3:
                    st.write("")
                    update_query = st.form_submit_button("💾 Update", use_container_width=True)
                
                with col4:
                    st.write("")
                    cancel_modify = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if update_query:
                    if modified_title:
                        st.session_state.custom_queries[modify_idx] = {
                            "query": modified_title,
                            "location": modified_location,
                            "reasoning": "User-defined custom search"
                        }
                        st.success(f"✅ Updated query: {modified_title}")
                        st.session_state.modify_query_index = None  # Clear modify mode
                        st.rerun()
                    else:
                        st.error("Please enter a job title/keywords")
                
                if cancel_modify:
                    st.session_state.modify_query_index = None  # Clear modify mode
                    st.rerun()
        else:
            # Invalid index, clear modify mode
            st.session_state.modify_query_index = None
            st.rerun()
    
    # Custom query section (moved below modify section)
    st.markdown("### ➕ Add New Search Query")
    
    # Show examples
    with st.expander("💡 **Search Query Examples**", expanded=False):
        st.markdown("""
        **Effective search queries:**
        - `Machine Learning Engineer Intern` - Specific role
        - `Frontend Developer Intern React` - Technology-specific
        - `Software Engineer Intern Google` - Target company
        - `Data Science Intern Remote` - Work arrangement
        - `DevOps Engineer Intern` - Specialized field
        - `Full Stack Developer Intern Startup` - Company type
        """)
    
    with st.form("custom_queries_form"):
        st.markdown("Add your own targeted search terms:")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            custom_job_title = st.text_input("Job Title/Keywords", placeholder="e.g., Machine Learning Engineer Intern")
        with col2:
            custom_location = st.text_input("Location (optional)", placeholder="e.g., San Francisco, CA")
        with col3:
            st.write("")
            add_query = st.form_submit_button("➕ Add Query", use_container_width=True)
        
        if add_query:
            if custom_job_title:
                new_query = {
                    "query": custom_job_title,
                    "location": custom_location,
                    "reasoning": "User-defined custom search"
                }
                st.session_state.custom_queries.append(new_query)
                st.success(f"✅ Added: {custom_job_title}")
                st.rerun()
            else:
                st.error("Please enter a job title/keywords")
    
    # Main search button
    st.markdown("---")
    
    # Clear queries button
    if st.session_state.custom_queries:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("�️ Clear All Queries", help="Remove all search queries"):
                st.session_state.custom_queries = []
                st.success("All queries cleared!")
                st.rerun()
    
    # Main search button
    if st.button("🚀 Start Smart Search", type="primary", use_container_width=True):
        if not st.session_state.get('user_id'):
            st.error("Please log in to perform searches")
            return
        
        if not st.session_state.custom_queries:
            st.error("Please add at least one search query before starting the search")
            return
            
        perform_smart_search(searcher, search_mode, st.session_state.custom_queries, max_results_per_query)
    
    # Display previous search results if available
    if 'smart_search_results' in st.session_state:
        st.markdown("---")
        display_search_results(st.session_state.smart_search_results)

def show_resume_analysis_summary(resume_data: dict, matching_engine: SmartMatchingEngine):
    """Display a summary of the user's resume analysis"""
    
    analysis = matching_engine.analyze_resume(resume_data)
    
    # Create metrics display
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Experience Level",
            analysis['experience_level'].replace('_', ' ').title(),
            f"{analysis['years_experience']} years"
        )
    
    with col2:
        st.metric(
            "Technical Skills",
            len(analysis['skills']),
            f"{len(analysis['programming_languages'])} languages"
        )
    
    with col3:
        st.metric(
            "Education Level",
            analysis['education_level'].title(),
            "✅ Degree" if analysis['has_degree'] else "❌ No Degree"
        )
    
    with col4:
        st.metric(
            "Projects & Certs",
            analysis['relevant_projects'],
            f"{analysis.get('certifications_count', 0)} certifications"
        )
    
    # Technical categories breakdown
    if analysis['technical_categories']:
        st.markdown("**🛠️ Technical Categories:**")
        categories_text = " • ".join([cat.replace('_', ' ').title() 
                                     for cat in analysis['technical_categories']])
        st.write(categories_text)
    
    # Top skills and languages
    col1, col2 = st.columns(2)
    
    with col1:
        if analysis['skills']:
            st.markdown("**💡 Key Skills:**")
            skills_list = list(analysis['skills'])[:8]  # Show top 8
            st.write(" • ".join(skills_list))
    
    with col2:
        if analysis.get('languages'):
            st.markdown("**🌍 Languages:**")
            languages_list = list(analysis['languages'])
            st.write(" • ".join(languages_list))

def perform_smart_search(searcher: RAGLinkedInSearcher, search_mode: str, custom_queries: List[dict], max_results: int):
    """Execute the smart search process"""
    
    search_start_time = time.time()
    
    with st.container():
        st.markdown("## 🔄 Search in Progress...")
        
        # Initialize progress tracking
        total_steps = 4  # Query generation, searching, analysis, saving
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Prepare search queries
            status_text.text("Step 1/4: Preparing intelligent search queries...")
            progress_bar.progress(0.25)
            
            all_queries = custom_queries.copy()  # Use only custom queries
            
            st.write(f"📋 **Generated {len(all_queries)} search queries**")
            
            # Step 2: Execute searches
            status_text.text("Step 2/4: Executing LinkedIn searches...")
            progress_bar.progress(0.5)
            
            search_results = searcher.perform_rag_search(
                resume_data=st.session_state.resume,
                user_id=st.session_state.user_id,
                max_results_per_query=max_results,
                custom_queries=all_queries
            )
            
            # Step 3: Analysis complete (done in perform_rag_search)
            status_text.text("Step 3/4: Analysis completed...")
            progress_bar.progress(0.75)
            
            # Step 4: Save results
            status_text.text("Step 4/4: Saving results...")
            if search_results['analyzed_results']:
                save_success = searcher.save_smart_search_results(
                    search_results, st.session_state.user_id
                )
                if save_success:
                    st.success("✅ Results saved to your internship list!")
            
            progress_bar.progress(1.0)
            status_text.text("✅ Smart search completed!")
            
            # Calculate search time
            search_time = time.time() - search_start_time
            
            # Store results in session state
            st.session_state.smart_search_results = search_results
            st.session_state.smart_search_metadata = {
                'search_time': search_time,
                'timestamp': time.time()
            }
            
            # Display immediate summary
            display_search_summary(search_results, search_time)
            
        except Exception as e:
            st.error(f"❌ Search failed: {str(e)}")
            progress_bar.progress(0)
            status_text.text("Search failed")

def display_search_summary(search_results: dict, search_time: float):
    """Display a quick summary of search results"""
    
    summary = search_results['summary']
    
    st.markdown("## 📊 Search Results Summary")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Opportunities", summary['total_found'])
    
    with col2:
        st.metric("High Match", summary['high_match_count'], "🎯")
    
    with col3:
        st.metric("Avg Compatibility", f"{summary['average_compatibility']}%")
    
    with col4:
        st.metric("Avg Accept Rate", f"{summary['average_acceptance_probability']}%")
    
    # Quick stats
    st.write(f"**⏱️ Search completed in {search_time:.1f} seconds**")
    st.write(f"**📈 Best match: {summary['average_compatibility']}% compatibility**")

def display_search_results(search_results: dict):
    """Display detailed search results with analysis"""
    
    st.markdown("## 🎯 Detailed Results & Analysis")
    
    # Results overview
    summary = search_results['summary']
    analyzed_results = search_results['analyzed_results']
    
    if not analyzed_results:
        st.warning("No results found. Try adjusting your search criteria.")
        return
    
    # Filter and sort options
    st.markdown("### 🔍 Filter & Sort Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        match_filter = st.selectbox(
            "Filter by Match Quality:",
            ["All Matches", "High Match", "Medium Match", "Low Match"]
        )
    
    with col2:
        sort_option = st.selectbox(
            "Sort by:",
            ["Recommendation Priority", "Compatibility Score", "Acceptance Probability", "Company Name"]
        )
    
    with col3:
        min_compatibility = st.slider(
            "Min Compatibility %:",
            min_value=0,
            max_value=100,
            value=50,
            step=5
        )
    
    # Additional row for pagination settings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        results_per_page_options = [5, 10, 15, 20, 25, "Show All"]
        results_per_page_selection = st.selectbox(
            "Results per page:",
            options=results_per_page_options,
            index=0,
            help="Choose how many results to display per page"
        )
    
    # Filter results
    filtered_results = filter_results(analyzed_results, match_filter, min_compatibility)
    
    # Sort results
    filtered_results = sort_results(filtered_results, sort_option)
    
    # Convert "Show All" to actual number
    results_per_page = len(filtered_results) if results_per_page_selection == "Show All" else results_per_page_selection
    
    # Check if filters have changed and reset pagination
    current_filters = f"{match_filter}_{min_compatibility}_{sort_option}_{results_per_page_selection}"
    if 'prev_filters' not in st.session_state:
        st.session_state.prev_filters = current_filters
    elif st.session_state.prev_filters != current_filters:
        st.session_state.current_page = 1  # Reset to first page when filters change
        st.session_state.prev_filters = current_filters
    
    # Pagination setup
    total_results = len(filtered_results)
    
    if total_results > 0:
        # Check if showing all results (no pagination needed)
        show_all = results_per_page_selection == "Show All"
        
        if show_all:
            # Show all results without pagination
            st.info(f"📋 **Showing all {total_results} filtered results**")
            display_results_list(filtered_results, 0)
        else:
            # Calculate pagination
            total_pages = (total_results - 1) // results_per_page + 1
            
            # Initialize current page in session state if not exists or reset if results per page changed
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
            if 'prev_results_per_page' not in st.session_state:
                st.session_state.prev_results_per_page = results_per_page
            
            # Reset current page if results per page changed
            if st.session_state.prev_results_per_page != results_per_page:
                st.session_state.current_page = 1
                st.session_state.prev_results_per_page = results_per_page
            
            # Ensure current page is within bounds
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = total_pages
            elif st.session_state.current_page < 1:
                st.session_state.current_page = 1
            
            # Display pagination info
            start_idx = (st.session_state.current_page - 1) * results_per_page
            end_idx = min(start_idx + results_per_page, total_results)
            
            st.info(f"📋 **Showing results {start_idx + 1}-{end_idx} of {total_results} filtered results** (Page {st.session_state.current_page} of {total_pages})")
            
            # Pagination controls (only show if more than 1 page)
            if total_pages > 1:
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏮️ First", disabled=st.session_state.current_page == 1):
                        st.session_state.current_page = 1
                        st.rerun()
                
                with col2:
                    if st.button("◀️ Prev", disabled=st.session_state.current_page == 1):
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col3:
                    # Page selector
                    new_page = st.selectbox(
                        "Go to page:",
                        options=list(range(1, total_pages + 1)),
                        index=st.session_state.current_page - 1,
                        key="page_selector"
                    )
                    if new_page != st.session_state.current_page:
                        st.session_state.current_page = new_page
                        st.rerun()
                
                with col4:
                    if st.button("Next ▶️", disabled=st.session_state.current_page == total_pages):
                        st.session_state.current_page += 1
                        st.rerun()
                
                with col5:
                    if st.button("Last ⏭️", disabled=st.session_state.current_page == total_pages):
                        st.session_state.current_page = total_pages
                        st.rerun()
            
            # Get paginated results
            paginated_results = filtered_results[start_idx:end_idx]
            
            # Display paginated results
            display_results_list(paginated_results, start_idx)
            
            # Bottom pagination controls (repeat for convenience if more than 1 page)
            if total_pages > 1:
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
                
                with col1:
                    if st.button("⏮️ First ", disabled=st.session_state.current_page == 1, key="first_bottom"):
                        st.session_state.current_page = 1
                        st.rerun()
                
                with col2:
                    if st.button("◀️ Prev ", disabled=st.session_state.current_page == 1, key="prev_bottom"):
                        st.session_state.current_page -= 1
                        st.rerun()
                
                with col3:
                    st.write(f"**Page {st.session_state.current_page} of {total_pages}**")
                
                with col4:
                    if st.button("Next ▶️ ", disabled=st.session_state.current_page == total_pages, key="next_bottom"):
                        st.session_state.current_page += 1
                        st.rerun()
                
                with col5:
                    if st.button("Last ⏭️ ", disabled=st.session_state.current_page == total_pages, key="last_bottom"):
                        st.session_state.current_page = total_pages
                        st.rerun()
    else:
        st.warning("No results match your current filters.")
    
    # Analytics section removed for simplified view

def filter_results(results: List[dict], match_filter: str, min_compatibility: int) -> List[dict]:
    """Filter results based on user criteria"""
    
    filtered = results
    
    # Filter by match quality
    if match_filter != "All Matches":
        filtered = [r for r in filtered if r['match_category'] == match_filter]
    
    # Filter by minimum compatibility
    filtered = [r for r in filtered if r['compatibility_scores']['overall_compatibility'] >= min_compatibility]
    
    return filtered

def sort_results(results: List[dict], sort_option: str) -> List[dict]:
    """Sort results based on user preference"""
    
    sort_keys = {
        "Recommendation Priority": lambda x: x['recommendation_priority'],
        "Compatibility Score": lambda x: x['compatibility_scores']['overall_compatibility'],
        "Acceptance Probability": lambda x: x['acceptance_analysis']['acceptance_probability'],
        "Company Name": lambda x: x.get('company_name', '').lower()
    }
    
    if sort_option in sort_keys:
        reverse_sort = sort_option != "Company Name"  # Company name should be A-Z
        results.sort(key=sort_keys[sort_option], reverse=reverse_sort)
    
    return results

def display_results_list(results: List[dict], start_index: int = 0):
    """Display the filtered and sorted results list"""
    
    for i, job in enumerate(results):
        with st.expander(f"🏢 **{job.get('job_title', 'Unknown Position')}** at **{job.get('company_name', 'Unknown Company')}** - {job['match_category']} ({job['compatibility_scores']['overall_compatibility']:.1f}% compatible)"):
            
            # Top section with key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Compatibility Score",
                    f"{job['compatibility_scores']['overall_compatibility']:.1f}%",
                    help="How well your skills match this role"
                )
            
            with col2:
                st.metric(
                    "Acceptance Probability",
                    f"{job['acceptance_analysis']['acceptance_probability']:.1f}%",
                    help="Estimated chance of getting this position"
                )
            
            with col3:
                st.metric(
                    "Priority Rank",
                    f"#{start_index + i + 1}",
                    f"{job['recommendation_priority']:.1f}/100"
                )
            
            # Detailed analysis
            st.markdown("#### 📈 Detailed Analysis")
            
            # Skills breakdown
            breakdown = job['compatibility_scores']['detailed_breakdown']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**✅ Matching Skills:**")
                technical_details = breakdown['technical_skills']['details']
                matching_skills = technical_details.get('matching_required_skills', []) + \
                                 technical_details.get('matching_preferred_skills', [])
                
                if matching_skills:
                    for skill in matching_skills[:5]:
                        st.write(f"• {skill}")
                else:
                    st.write("• General technical background")
            
            with col2:
                st.markdown("**📚 Areas to Improve:**")
                missing_skills = technical_details.get('missing_required_skills', [])
                if missing_skills:
                    for skill in missing_skills[:5]:
                        st.write(f"• {skill}")
                else:
                    st.write("• No specific gaps identified")
            
            # Job description preview if available
            if job.get('job_description'):
                st.markdown("**📄 Job Description Preview:**")
                description = job['job_description']
                preview = description[:300] + ('...' if len(description) > 300 else '')
                st.markdown(f"> {preview}")
            
            # Short Summary
            st.markdown("**📝 Summary:**")
            compatibility = job['compatibility_scores']['overall_compatibility']
            acceptance = job['acceptance_analysis']['acceptance_probability']
            
            if compatibility >= 80:
                match_quality = "Excellent match"
            elif compatibility >= 60:
                match_quality = "Good match"
            else:
                match_quality = "Moderate match"
                
            summary_text = f"{match_quality} with {compatibility}% compatibility and {acceptance}% estimated acceptance rate."
            st.write(summary_text)
            
            # Apply button only
            if job.get('application_link'):
                st.link_button("🌐 Apply Now", job['application_link'], use_container_width=True)

# Removed detailed analysis function for simplified view

def filter_results(results: List[dict], match_filter: str, min_compatibility: int) -> List[dict]:
    """Filter results based on user criteria"""
    
    filtered = results
    
    # Filter by match quality
    if match_filter != "All Matches":
        filtered = [r for r in filtered if r['match_category'] == match_filter]
    
    # Filter by minimum compatibility
    filtered = [r for r in filtered if r['compatibility_scores']['overall_compatibility'] >= min_compatibility]
    
    return filtered

def sort_results(results: List[dict], sort_option: str) -> List[dict]:
    """Sort results based on user preference"""
    
    sort_keys = {
        "Recommendation Priority": lambda x: x['recommendation_priority'],
        "Compatibility Score": lambda x: x['compatibility_scores']['overall_compatibility'], 
        "Acceptance Probability": lambda x: x['acceptance_analysis']['acceptance_probability'],
        "Company Name": lambda x: x.get('company_name', '')
    }
    
    reverse = sort_option != "Company Name"  # Company name should be ascending
    
    return sorted(results, key=sort_keys[sort_option], reverse=reverse)

# Removed search analytics function for simplified view