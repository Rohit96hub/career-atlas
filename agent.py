# agent.py

import os
from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
# ... (rest of imports are the same)

print("--- Loading Advanced Agent Backend v3.2 (Enhanced Prompts) ---")

# --- (API Keys and Pydantic Models are the same) ---
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# ... (rest of setup)
# --- Pydantic Models ---
class SkillAnalysis(BaseModel):
    technical_skills: List[str]
    soft_skills: List[str]
class ProfileFeedback(BaseModel):
    resume_strengths: List[str]
    resume_gaps: List[str]
    linkedin_suggestions: List[str]
class JobExperience(BaseModel):
    title: str
    company: str
    dates: str
    description: List[str]
class TailoredResumeContent(BaseModel):
    full_name: str
    email: str
    phone: str
    summary: str
    experiences: List[JobExperience]
    education: str
    skills: List[str]
class CareerActionPlan(BaseModel):
    chosen_career: str
    career_overview: str
    skill_analysis: SkillAnalysis
    profile_feedback: ProfileFeedback
    learning_roadmap: str
    portfolio_plan: str
# --- Agent State ---
class TeamState(TypedDict):
    student_profile: str
    role_choice: str
    chosen_career: Optional[str]
    market_analysis: Optional[SkillAnalysis]
    profile_analysis: Optional[ProfileFeedback]
    tailored_resume: Optional[TailoredResumeContent]
    final_plan: Optional[CareerActionPlan]
# --- (Tools, role_suggester, job_market_analyst, profile_reviewer agents are the same) ---
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0) # Using faster model

@tool
def scrape_web_content(url: str) -> str:
    """Scrapes text content from a given URL."""
    # ... (function is the same)
    pass

def role_suggester_agent(state: TeamState):
    # ... (function is the same)
    pass
def job_market_analyst_agent(state: TeamState):
    # ... (function is the same)
    pass
def profile_reviewer_agent(state: TeamState):
    # ... (function is the same)
    pass


# NEW UPGRADED AGENT: Resume Tailor with Few-Shot Prompting
def resume_tailor_agent(state: TeamState):
    print("--- ✍️ Agent: AI Resume Tailor (Upgraded) ---")
    structured_llm = llm.with_structured_output(TailoredResumeContent, method="function_calling")
    
    # This is the new, much more detailed prompt with examples
    few_shot_prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are an elite resume writer for the tech industry. Your task is to transform a student's raw profile into a professional, ATS-friendly, and highly attractive resume for their target role. "
         "You MUST extract personal info, write a compelling summary, and rewrite experience bullet points to be achievement-oriented, using keywords from the provided skill analysis. "
         "Follow the examples provided closely."),
        ("human", 
         "### EXAMPLE ###\n"
         "Target Role: Data Analyst\n"
         "Required Skills: Python, Pandas, SQL, Tableau, Communication\n"
         "User's Raw Profile:\n"
         "- Name: Jane Doe\n"
         "- Experience: Intern at BizCorp. I was responsible for making weekly reports.\n"
         "- Education: CS Degree at State U.\n"
         "- Skills: Python\n\n"
         "### GOOD OUTPUT FROM YOU ###\n"
         "{\n"
         "  \"full_name\": \"Jane Doe\",\n"
         "  \"email\": \"jane.doe@email.com\",\n"
         "  \"phone\": \"123-456-7890\",\n"
         "  \"summary\": \"Aspiring Data Analyst with a strong foundation in Python and data structures from my Computer Science studies. Eager to apply my skills in data manipulation and visualization to drive business insights.\",\n"
         "  \"experiences\": [\n"
         "    {\n"
         "      \"title\": \"Data Analyst Intern\",\n"
         "      \"company\": \"BizCorp\",\n"
         "      \"dates\": \"Summer 2024\",\n"
         "      \"description\": [\n"
         "        \"Developed and automated weekly performance reports using Python and Pandas, reducing manual effort by 80%.\",\n"
         "        \"Queried SQL databases to extract and analyze sales data, identifying key trends that informed marketing strategy.\",\n"
         "        \"Presented findings to team members, demonstrating strong communication skills.\"\n"
         "      ]\n"
         "    }\n"
         "  ],\n"
         "  \"education\": \"Bachelor of Science in Computer Science, State University\",\n"
         "  \"skills\": [\"Python\", \"Pandas\", \"NumPy\", \"SQL\", \"Tableau\", \"Microsoft Excel\", \"Communication\"]\n"
         "}\n"
         "### END EXAMPLE ###\n\n"
         "--- NOW, DO THE SAME FOR THIS USER ---\n\n"
         "Target Role: {career}\n\n"
         "Required Skills: {skills}\n\n"
         "User's Raw Profile:\n{profile}"
        )
    ])
    
    chain = few_shot_prompt | structured_llm
    resume_content = chain.invoke({
        "career": state["chosen_career"],
        "skills": state["market_analysis"].dict(),
        "profile": state["student_profile"]
    })
    return {"tailored_resume": resume_content}

def lead_agent_node(state: TeamState):
    # ... (function is the same)
    pass

def route_initial_choice(state: TeamState):
    # ... (function is the same)
    pass

# --- (Graph Definition is the same, but we add the new tailor agent) ---
graph_builder = StateGraph(TeamState)
graph_builder.add_node("suggest_role", role_suggester_agent)
graph_builder.add_node("analyze_market", job_market_analyst_agent)
graph_builder.add_node("review_profile", profile_reviewer_agent)
graph_builder.add_node("tailor_resume", resume_tailor_agent)
graph_builder.add_node("create_final_plan", lead_agent_node)

graph_builder.set_conditional_entry_point(route_initial_choice, {"suggest_role": "suggest_role", "analyze_market": "analyze_market"})
graph_builder.add_edge("suggest_role", "analyze_market")
# The profile review and resume tailoring now run in parallel
graph_builder.add_edge("analyze_market", "review_profile")
graph_builder.add_edge("analyze_market", "tailor_resume")
# The lead agent waits for both to finish before creating the final plan
graph_builder.add_edge("review_profile", "create_final_plan")
graph_builder.add_edge("tailor_resume", "create_final_plan")
graph_builder.add_edge("create_final_plan", END)
navigator_agent = graph_builder.compile()

def run_agent(student_profile, role_choice):
    # ... (function is the same)
    pass
def run_chat(user_message, history, plan_context):
    # ... (function is the same)
    pass
