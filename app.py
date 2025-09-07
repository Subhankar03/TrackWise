import streamlit as st
from backend import (
	ATSAnalysis,
	AnalysisError,
	FileProcessingError,
	analyze_resume,
	create_qna_pdf,
	extract_text_from_file
)

# Configure page
st.set_page_config(
	page_title="TrackWise - ATS Resume Analyzer",
	page_icon="app/static/target.png",
	layout="wide",
)

# Check for API key
if "GEMINI_API_KEY" not in st.secrets:
	st.error("🚨 Gemini API key not found! Please add it to your `.streamlit/secrets.toml` file.")
	st.stop()

st.html('style.css')


def display_results(analysis: ATSAnalysis, mode: str):
	"""Display analysis results with enhanced UI"""
	
	if mode == 'analysis':
		# Score Display
		st.html(f"""
		<div class="score-container">
			<div class="score-number">{analysis.match_score}%</div>
			<div class="score-label">ATS Match Score</div>
		</div>
		""")
		
		# Summary
		st.markdown("### 📋 Executive Summary")
		st.info(analysis.summary)
		
		# Create two columns for strengths and weaknesses
		col1, col2 = st.columns(2)
		
		with col1:
			st.markdown("### ✅ Strengths")
			strengths_list = ''.join([f'<li class="strength-item">{strength}</li>' for strength in analysis.strengths])
			st.html(f'<ul class="styled-list">{strengths_list}</ul>')
		
		with col2:
			st.markdown("### ⚠️ Areas for Improvement")
			weaknesses_list = ''.join([f'<li class="weakness-item">{weakness}</li>' for weakness in analysis.weaknesses])
			st.html(f'<ul class="styled-list">{weaknesses_list}</ul>')
		
		# Missing Keywords
		if analysis.missing_keywords:
			st.markdown("### 🔍 Missing Keywords")
			keywords_str = ", ".join(analysis.missing_keywords)
			st.warning(f"Consider adding these keywords: **{keywords_str}**")
		
		# Detailed Analysis
		st.markdown("### 📊 Detailed Analysis")
		
		col3, col4, col5 = st.columns(3)
		with col3:
			st.write(f'**Technical Skills Match:** \n\n {analysis.technical_skills_match}')
		with col4:
			st.write(f'**Experience Relevance:** \n\n {analysis.experience_relevance}')
		with col5:
			st.write(f'**Education Match:** \n\n {analysis.education_match}')
		
		# Improvement Suggestions
		st.html(f"""
		<div class="improvement-section">
			<h3>🚀 Improvement Suggestions</h3>
			{''.join([f"<p>{i}. {suggestion}</p>" for i, suggestion in enumerate(analysis.improvement_suggestions, 1)])}
		</div>
		""")
		
		# Recommendations
		if analysis.recommendations:
			st.html(f"""
			<div class="recommendation-section">
				<h3>💡 Professional Recommendations</h3>
				<p>{analysis.recommendations}</p>
			</div>
			""")
	
	elif mode == 'interview':
		# Interview Questions
		if analysis.interview_questions:
			st.markdown("### 🎯 Prepare for Your Interview")
			st.markdown("Here are some potential interview questions based on your resume.")
			
			col1, col2 = st.columns(2)
			
			for index, qa in enumerate(analysis.interview_questions):
				col = col1 if index % 2 == 0 else col2
				with col:
					st.html(f"""
						<div class="qa-card">
							<p class="question">{qa['question']}</p>
							<p style="color: #333333;">{qa['answer']}</p>
						</div>
					""")
			
			# Add download button
			pdf_bytes = create_qna_pdf(analysis.interview_questions)
			st.download_button(
				label="Save as PDF",
				icon=":material/file_save:",
				data=pdf_bytes,
				file_name="interview_qna.pdf",
				type="primary",
				on_click="ignore"
			)


# Header
st.html("""
<div class="main-header">
    <img src="app/static/target.png">
    <h1>TrackWise</h1>
    <p>Advanced ATS Resume Analyzer &nbsp;•&nbsp; Optimize Your Resume for Success</p>
</div>
""")

# Input fields
col1, col2 = st.columns([1, 1])

with col1:
	job_role = st.text_input("🎯 Job Role", placeholder="e.g., Data Analyst, Software Engineer")
	uploaded_file = st.file_uploader("📄 Upload Resume", type=['pdf', 'docx'],
									 help="Upload your resume in PDF or DOCX format")

with col2:
	job_description = st.text_area(
		"📝 Job Description",
		placeholder="Paste the complete job description here...",
		height=300
	)

# Action buttons
_, col1, col2, _ = st.columns([1, 2, 2, 1], gap="medium")
with col1:
	analyze_button = st.button("Analyze Resume", use_container_width=True)
with col2:
	interview_button = st.button("Prepare for Interview", use_container_width=True)

if 'analysis_result' not in st.session_state:
	st.session_state.analysis_result = None


def run_analysis(mode: str):
	try:
		if not job_role.strip():
			st.error("⚠️ Please enter the job role")
		elif not job_description.strip():
			st.error("⚠️ Please enter the job description")
		elif not uploaded_file:
			st.error("⚠️ Please upload your resume")
		else:
			spinner_text = "Analyzing your resume..." if mode == 'analysis' else "Preparing interview questions..."
			with st.spinner(spinner_text):
				resume_text = extract_text_from_file(uploaded_file)
				st.session_state.analysis_result = analyze_resume(job_role, job_description, resume_text)

	except (FileProcessingError, AnalysisError) as e:
		st.error(f"❌ {e}")
		st.session_state.analysis_result = None


if analyze_button:
	run_analysis('analysis')

if interview_button:
	run_analysis('interview')

if st.session_state.analysis_result:
	mode = 'interview' if interview_button else 'analysis'
	display_results(st.session_state.analysis_result, mode)

# Footer
st.divider()
st.html("""
<div style="text-align: center; color: #666;">
	<p style="font-size: 0.95rem;">Built by <a href="https://subhankar-dutta.streamlit.app" target="_blank"><b>Subhankar Dutta</b></a>
	 | Powered by <span class="gemini-text"><b>Gemini</b></span></p>
	<p style="font-size: 0.8rem;">Upload your resume and get instant ATS optimization insights</p>
</div>
""")