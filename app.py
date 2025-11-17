import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from src.database import TechRadarDB
from src.analyzer import TechAnalyzer
from src.visualizer import RadarVisualizer

load_dotenv()

# Page config
st.set_page_config(
    page_title="CX Tech Radar",
    page_icon="👥",
    layout="wide"
)

# Initialize components
@st.cache_resource
def init_components():
    db = TechRadarDB()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("⚠️ ANTHROPIC_API_KEY not found in .env file")
        st.stop()
    analyzer = TechAnalyzer(api_key)
    visualizer = RadarVisualizer()
    return db, analyzer, visualizer

db, analyzer, visualizer = init_components()

# Sidebar
st.sidebar.title("👥 CX Tech Radar")
st.sidebar.caption("Customer Experience Team")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "➕ Add Tool", "🔍 Search", "📊 Radar View"]
)

# Home Page
if page == "🏠 Home":
    st.title("👥 CX Tech Radar")
    st.caption("Tools For Humanity - Customer Experience Team")
    st.markdown("""
    Welcome to the **CX Tech Radar**! This tool helps the Customer Experience team 
    discover, evaluate, and track technologies that improve how we serve our customers.
    
    **What is this?**  
    A living catalog of CX tools, with AI-powered analysis to help us make better 
    technology decisions.
    """)
    
    # Stats (cached for 60 seconds)
    @st.cache_data(ttl=60)
    def get_cached_stats():
        return db.get_stats()
    
    stats = get_cached_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tools", stats['total_tools'])
    with col2:
        st.metric("Adopt", stats['by_position'].get('Adopt', 0))
    with col3:
        st.metric("Trial", stats['by_position'].get('Trial', 0))
    with col4:
        st.metric("Assess", stats['by_position'].get('Assess', 0))
    
    # Recent tools
    st.subheader("Recently Added Tools")
    
    @st.cache_data(ttl=60)
    def get_cached_tools():
        return db.get_all_tools()
    
    df = get_cached_tools()
    if not df.empty:
        df_sorted = df.sort_values('added_date', ascending=False).head(5)
        for _, tool in df_sorted.iterrows():
            with st.expander(f"**{tool['name']}** - {tool['category']}"):
                st.write(f"**Position:** {tool['radar_position']}")
                st.write(f"**Scores:** CX: {tool['cx_relevance_score']}/10, Integration: {tool['integration_score']}/10")
                st.write(tool['description'])
        
        # CSV Export button
        st.markdown("---")
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download All Tools as CSV",
            data=csv,
            file_name="cx_tech_radar_tools.csv",
            mime="text/csv"
        )
    else:
        st.info("No tools yet. Add your first tool using the '➕ Add Tool' page!")

# Add Tool Page
elif page == "➕ Add Tool":
    st.title("Add New Tool")
    
    st.subheader("AI-Powered Analysis")
    st.markdown("Paste information about a tool and let AI analyze it.")
    
    tool_info = st.text_area(
        "Tool Information",
        placeholder="Paste a product description, press release, or website content...",
        height=200
    )
    
    source_url = st.text_input("Source URL (optional)")
    
    # Store analysis in session state
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🤖 Analyze with AI", use_container_width=True):
            if tool_info:
                with st.spinner("Analyzing..."):
                    try:
                        analysis = analyzer.analyze_tool(tool_info, source_url)
                        st.session_state.current_analysis = analysis
                        st.session_state.source_url = source_url
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error analyzing tool: {e}")
                        st.error("If this persists, check that your API key is correct in the .env file")
            else:
                st.warning("Please enter tool information")
    
    with col2:
        if st.session_state.current_analysis:
            if st.button("💾 Save to Radar", type="primary", use_container_width=True):
                tool_data = st.session_state.current_analysis.dict()
                tool_data['source_url'] = st.session_state.source_url
                result = db.add_tool(tool_data)
                
                if result > 0:
                    st.success(f"✅ Saved {st.session_state.current_analysis.name}!")
                    st.balloons()
                    # Clear the analysis
                    st.session_state.current_analysis = None
                    st.rerun()
                elif result == -1:
                    st.warning("⚠️ Tool already exists in database")
                else:
                    st.error("Error saving tool")
    
    # Display analysis results if available
    if st.session_state.current_analysis:
        st.markdown("---")
        analysis = st.session_state.current_analysis
        
        st.success("✅ Analysis complete!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {analysis.name}")
            st.write(analysis.description)
            st.markdown(f"**Category:** {analysis.category}")
            st.markdown(f"**Radar Position:** {analysis.radar_position}")
        
        with col2:
            st.metric("CX Relevance", f"{analysis.cx_relevance_score}/10")
            st.metric("Integration", f"{analysis.integration_score}/10")
            st.metric("Overall", f"{analysis.overall_score:.1f}/10")
            st.markdown(f"**Cost:** {analysis.cost_rating}")
        
        st.markdown("**Key Features:**")
        for feature in analysis.key_features:
            st.markdown(f"- {feature}")
        
        st.markdown("**Use Cases:**")
        for use_case in analysis.use_cases:
            st.markdown(f"- {use_case}")
        
        st.markdown("**Reasoning:**")
        st.info(analysis.reasoning)

# Search Page
elif page == "🔍 Search":
    st.title("Search Tools")
    
    search_query = st.text_input("🔍 Search", placeholder="Enter tool name, category, or keyword...")
    
    if search_query and search_query.strip():
        @st.cache_data(ttl=30)
        def cached_search(q):
            return db.search_tools(q.strip())
        
        results = cached_search(search_query)
        
        if not results.empty:
            st.success(f"Found {len(results)} tools")
            
            for _, tool in results.iterrows():
                with st.expander(f"**{tool['name']}** - {tool['category']} ({tool['radar_position']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(tool['description'])
                        st.markdown(f"**Position:** {tool['radar_position']}")
                        if tool['source_url']:
                            st.markdown(f"[Learn more]({tool['source_url']})")
                    
                    with col2:
                        st.metric("CX Relevance", f"{tool['cx_relevance_score']}/10")
                        st.metric("Integration", f"{tool['integration_score']}/10")
            
            # CSV Export button
            st.markdown("---")
            csv = results.to_csv(index=False)
            # Sanitize filename
            import re
            safe_query = re.sub(r'[^\w\s-]', '', search_query[:20]).strip()
            safe_query = re.sub(r'[-\s]+', '-', safe_query) or "search"
            
            st.download_button(
                label="📥 Download Search Results as CSV",
                data=csv,
                file_name=f"cx_tech_radar_search_{safe_query}.csv",
                mime="text/csv"
            )
        else:
            st.info("No tools found matching your search")
    else:
        st.info("Enter a search term to find tools")

# Radar View Page
elif page == "📊 Radar View":
    st.title("Tech Radar Visualization")
    
    # Filters sidebar
    with st.sidebar.expander("🔍 Filters", expanded=False):
        # Get all tools once for categories list
        @st.cache_data(ttl=60)
        def get_categories():
            df = db.get_all_tools()
            if df.empty:
                return []
            return df['category'].dropna().unique().tolist()
        
        categories = get_categories()
        positions = ['Adopt', 'Trial', 'Assess', 'Hold']
        
        filter_category = st.selectbox("Category", options=["All"] + sorted(categories), index=0)
        filter_position = st.selectbox("Position", options=["All"] + positions, index=0)
        
        st.markdown("**Score Filters**")
        col1, col2 = st.columns(2)
        with col1:
            min_cx = st.slider("Min CX Score", 0, 10, 0, key="min_cx")
            max_cx = st.slider("Max CX Score", 0, 10, 10, key="max_cx")
        with col2:
            min_int = st.slider("Min Integration Score", 0, 10, 0, key="min_int")
            max_int = st.slider("Max Integration Score", 0, 10, 10, key="max_int")
        
        show_labels = st.checkbox("Show Labels", value=True)
    
    # Build filters dict
    filters = {}
    if filter_category != "All":
        filters['category'] = filter_category
    if filter_position != "All":
        filters['position'] = filter_position
    if min_cx > 0:
        filters['min_cx_score'] = min_cx
    if max_cx < 10:
        filters['max_cx_score'] = max_cx
    if min_int > 0:
        filters['min_integration_score'] = min_int
    if max_int < 10:
        filters['max_integration_score'] = max_int
    
    df = db.get_all_tools(filters=filters if filters else None)
    
    if not df.empty:
        # Create visualization
        fig = visualizer.create_radar_chart(df, show_labels=show_labels)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"Showing {len(df)} tool(s)")
        
        # Legend explanation
        with st.expander("📖 How to read this radar"):
            st.markdown("""
            **Rings (from center outward):**
            - **Adopt** (Green): Ready to use, proven, recommended
            - **Trial** (Blue): Worth testing, promising
            - **Assess** (Yellow): Monitor, not ready yet
            - **Hold** (Red): Avoid or phase out
            
            **Segments:** Different technology categories (CRM, Support, etc.)
            
            Hover over dots for detailed information!
            """)
    else:
        st.info("No tools match the selected filters. Try adjusting your filters or add some tools!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**CX Tech Radar**  
Tools For Humanity  
Customer Experience Team

Built with Streamlit + Claude  
Data stored locally in SQLite
""")