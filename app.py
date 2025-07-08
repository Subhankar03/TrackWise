from typing import List

import streamlit as st
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from pypdf import PdfReader


# Configure page
st.set_page_config(
	page_title="TrackWise - ATS Resume Analyzer",
	page_icon="🎯",
	layout="wide",
	initial_sidebar_state="collapsed"
)

# Check for API key
if "GEMINI_API_KEY" not in st.secrets:
	st.error("🚨 Gemini API key not found! Please add it to your `.streamlit/secrets.toml` file.")
	st.stop()

st.html('style.css')


class ATSAnalysis(BaseModel):
	match_score: int = Field(description="integer between 0-100")
	summary: str = Field(description="brief 2-3 sentence summary of the candidate's fit")
	strengths: List[str] = Field(description="list of strengths")
	weaknesses: List[str] = Field(description="list of weaknesses")
	missing_keywords: List[str] = Field(description="list of missing keywords")
	improvement_suggestions: List[str] = Field(description="list of specific actionable suggestions")
	technical_skills_match: str = Field(description="percentage match for technical skills")
	experience_relevance: str = Field(description="assessment of experience relevance")
	education_match: str = Field(description="assessment of educational background match")
	recommendations: str = Field(description="specific recommendations for the candidate")


def extract_text_from_pdf(pdf_file) -> str:
	"""Extract text from the uploaded PDF file"""
	try:
		pdf_reader = PdfReader(pdf_file)
		text = ""
		for page in pdf_reader.pages:
			text += page.extract_text() + "\n"
		return text.strip()
	except Exception as e:
		st.error(f"Error extracting text from PDF: {str(e)}")
		return ""


def analyze_resume(job_role: str, job_description: str, resume_text: str) -> ATSAnalysis | None:
	"""Analyze resume using LangChain and Google Gemini"""
	try:
		# Set up the parser
		parser = JsonOutputParser(pydantic_object=ATSAnalysis)
		
		# Create the prompt template
		prompt_template = ChatPromptTemplate.from_template(
			template="""
			You are an expert ATS (Applicant Tracking System) analyzer and HR professional.
			Analyze the following resume against the job description and provide a comprehensive assessment.

			**Job Role:**
			{job_role}

			**Job Description:**
			{job_description}

			**Resume Content:**
			{resume_text}

			{format_instructions}
			""",
			partial_variables={"format_instructions": parser.get_format_instructions()}
		)
		
		# Initialize the model
		model = ChatGoogleGenerativeAI(
			model="gemini-2.5-flash",
			google_api_key=st.secrets["GEMINI_API_KEY"],
			temperature=0, thinking_budget=0
		)
		
		# Create the chain
		chain = prompt_template | model | parser
		
		# Invoke the chain
		response = chain.invoke({
			"job_role": job_role,
			"job_description": job_description,
			"resume_text": resume_text
		})
		
		return ATSAnalysis(**response)
	
	except Exception as e:
		st.error(f"Error analyzing resume: {e}")
		return None


def display_results(analysis: ATSAnalysis):
	"""Display analysis results with enhanced UI"""
	
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
		for strength in analysis.strengths:
			st.markdown(f"• {strength}")
	
	with col2:
		st.markdown("### ⚠️ Areas for Improvement")
		for weakness in analysis.weaknesses:
			st.markdown(f"• {weakness}")
	
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


# Header
st.html("""
<div class="main-header">
	<h1>🎯 TrackWise</h1>
	<p>Advanced ATS Resume Analyzer &nbsp;•&nbsp; Optimize Your Resume for Success</p>
</div>
""")

# Input fields
col1, col2 = st.columns([1, 1])

with col1:
	job_role = st.text_input("🎯 Job Role", placeholder="e.g., Data Analyst, Software Engineer")
	uploaded_file = st.file_uploader("📄 Upload Resume", type=['pdf'], help="Upload your resume in PDF format")

with col2:
	job_description = st.text_area(
		"📝 Job Description",
		placeholder="Paste the complete job description here...",
		height=300
	)

# Analysis button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
	analyze_button = st.button("Analyze Resume", icon=':material/readiness_score:', use_container_width=True)

# Process analysis
if analyze_button:
	if not job_role.strip():
		st.error("⚠️ Please enter the job role")
	elif not job_description.strip():
		st.error("⚠️ Please enter the job description")
	elif not uploaded_file:
		st.error("⚠️ Please upload your resume")
	else:
		# Show loading animation
		with st.spinner("Analyzing your resume... This may take a few moments"):
			
			# Extract text from PDF
			resume_text = extract_text_from_pdf(uploaded_file)
			
			if resume_text:
				# Analyze with LangChain
				analysis = analyze_resume(job_role, job_description, resume_text)
				
				if analysis:
					st.html('<br>')
					display_results(analysis)
			else:
				st.error("❌ Failed to extract text from PDF. Please ensure the file is readable.")

# Footer
st.divider()
st.html("""
<div style="text-align: center; color: #666;">
	<p style="font-size: 0.95rem;">Built by <a href="https://subhankar-dutta.streamlit.app" target="_blank"><b>Subhankar Dutta</b></a> | Powered by <span class="gemini-text"><b>Gemini</b></span></p>
	<p style="font-size: 0.8rem;">Upload your resume and get instant ATS optimization insights</p>
</div>
""")