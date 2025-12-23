import docx
from fpdf import FPDF
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from pypdf import PdfReader
import streamlit as st


class FileProcessingError(Exception):
	"""Custom exception for file processing errors."""
	pass


class AnalysisError(Exception):
	"""Custom exception for analysis errors."""
	pass


class ATSAnalysis(BaseModel):
	match_score: int = Field(description="integer between 0-100")
	summary: str = Field(description="brief 2-3 sentence summary of the candidate's fit")
	strengths: list[str] = Field(description="list of strengths")
	weaknesses: list[str] = Field(description="list of weaknesses")
	missing_keywords: list[str] = Field(description="list of missing keywords")
	improvement_suggestions: list[str] = Field(description="list of specific actionable suggestions")
	technical_skills_match: str = Field(description="percentage match for technical skills")
	experience_relevance: str = Field(description="assessment of experience relevance")
	education_match: str = Field(description="assessment of educational background match")
	recommendations: str = Field(description="specific recommendations for the candidate")
	interview_questions: list[dict] = Field(description="list of potential interview questions with answers based on resume")


def extract_text_from_file(uploaded_file) -> str:
	"""Extract text from the uploaded PDF or DOCX file"""
	try:
		file_type = uploaded_file.name.split('.')[-1].lower()
		
		if file_type == 'pdf':
			pdf_reader = PdfReader(uploaded_file)
			text = "".join(page.extract_text() + "\n" for page in pdf_reader.pages)
			return text.strip()
		
		elif file_type == 'docx':
			doc = docx.Document(uploaded_file)
			text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
			return text.strip()
		
		else:
			raise FileProcessingError(f"Unsupported file format: {file_type}. Please upload a PDF or DOCX file.")
	
	except Exception as e:
		raise FileProcessingError(f"Error extracting text from file: {e}")


def analyze_resume(job_role: str, job_description: str, resume_text: str) -> ATSAnalysis:
	"""Analyze resume using LangChain and Google Gemini"""
	try:
		parser = JsonOutputParser(pydantic_object=ATSAnalysis)
		
		with open('prompt.md') as f:
			prompt_template = ChatPromptTemplate.from_template(
				template=f.read(),
				partial_variables={"format_instructions": parser.get_format_instructions()}
			)
		
		model = ChatGoogleGenerativeAI(
			model="gemini-3-flash-preview",
			google_api_key=st.secrets["GEMINI_API_KEY"],
			thinking_level="low"
		)
		
		chain = prompt_template | model | parser
		
		response = chain.invoke({
			"job_role": job_role,
			"job_description": job_description,
			"resume_text": resume_text
		})
		
		return ATSAnalysis(**response)
	
	except Exception as e:
		raise AnalysisError(f"Error during analysis: {e}")


def create_qna_pdf(interview_qna: list[dict]) -> bytes:
	"""Create a PDF file for the interview Q&A"""
	pdf = FPDF()
	pdf.add_page()
	pdf.set_font("Arial", 'B', 16)
	pdf.cell(0, 12, 'Interview Questions and Answers', 0, 1, 'C')
	pdf.ln(10)
	
	pdf.set_font("Arial", '', 12)
	for i, qa in enumerate(interview_qna, 1):
		pdf.set_font("Arial", 'B', 12)
		# Encode to latin-1, replacing unsupported characters
		question = f"{i}: {qa['question']}".encode('latin-1', 'replace').decode('latin-1')
		pdf.multi_cell(0, 7, question)
		
		pdf.set_font("Arial", '', 12)
		answer = qa['answer'].encode('latin-1', 'replace').decode('latin-1')
		pdf.multi_cell(0, 7, answer)
		pdf.ln(5)
		
	# The output method of FPDF returns bytes when dest='S', but type hints are incorrect.
	# We encode to latin-1 to match the PDF's internal encoding.
	return pdf.output(dest='S').encode('latin-1')  # type: ignore