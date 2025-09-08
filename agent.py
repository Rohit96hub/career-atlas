# agent.py

import os
from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
import requests
from bs4 import BeautifulSoup

print("--- Loading Advanced Agent Backend v3 ---")

# API Keys and Tracing Setup
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Flask Career Navigator v3 (Resume Gen)"

# --- Pydantic Models ---
class SkillAnalysis(BaseModel):
    technical_skills: List[str]
    soft_skills: List[str]

class ProfileFeedback(BaseModel):
    resume_strengths: List[str]
    resume_gaps: List[str]
    linkedin_suggestions: List[str]

# New models for the resume content
class JobExperience(BaseModel):
    title: str
    company: str
    dates: str
    description: List[str] = Field(description="3-4 bullet points describing achievements, optimized with keywords.")

class TailoredResumeContent(BaseModel):
    full_name: str = Field(description="Extracted full name of the user.")
    email: str = Field(description="Extracted email of the user.")
    phone: str = Field(description="Extracted phone number of the user.")
    summary: str = Field(description="A 2-3 sentence professional summary tailored for the target role.")
    experiences: List[JobExperience]
    education: str = Field(description="A summary of the user's education.")
    skills: List[str] = Field(description="A list of key technical and soft skills.")

class CareerActionPlan(BaseModel):
    # ... (no changes here from before)
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
    tailored_resume: Optional[TailoredResumeContent] # New state for resume
    final_plan: Optional[CareerActionPlan]

# --- Tools and Agents ---
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# ... (role_suggester_agent, job_market_analyst_agent, profile_reviewer_agent are unchanged) ...
def role_suggester_agent(state: TeamState):
    print("--- 🧑‍🏫 Agent: Role Suggester ---")
    if state["role_choice"] == "resume_based":
        prompt_text = "You are a career counselor. Analyze the user's profile and suggest the single most suitable job role for them. Output only the job title. Profile: {profile}"
    else:
        prompt_text = "You are a job market analyst. Based on current tech trends, suggest a single, high-demand job role for a college student. Output only the job title."
    
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    suggested_role = chain.invoke({"profile": state["student_profile"]}).content.strip()
    print(f"    > Suggested Role: {suggested_role}")
    return {"chosen_career": suggested_role}

def job_market_analyst_agent(state: TeamState):
    print("--- 🕵️ Agent: Job Market Analyst ---")
    structured_llm = llm.with_structured_output(SkillAnalysis)
    prompt = ChatPromptTemplate.from_template( "You are an expert job market analyst. Based on the career of '{career}', identify the top 5 technical skills and top 3 soft skills required.")
    chain = prompt | structured_llm
    analysis = chain.invoke({"career": state['chosen_career']})
    return {"market_analysis": analysis}

def profile_reviewer_agent(state: TeamState):
    print("--- 📝 Agent: Profile Reviewer & LinkedIn Enhancer ---")
    structured_llm = llm.with_structured_output(ProfileFeedback)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert career coach. Analyze the user's professional profile. 1. Compare it to the required skills and identify strengths and gaps. 2. Provide 3-5 specific, actionable suggestions to improve their LinkedIn profile."),
        ("human", "User's Profile:\n{profile}\n\nRequired Skills:\n{skill_analysis}")
    ])
    chain = prompt | structured_llm
    feedback = chain.invoke({"profile": state["student_profile"], "skill_analysis": state["market_analysis"].dict()})
    return {"profile_analysis": feedback}

# NEW AGENT: Resume Tailor
def resume_tailor_agent(state: TeamState):
    print("--- ✍️ Agent: AI Resume Tailor ---")
    structured_llm = llm.with_structured_output(TailoredResumeContent)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert resume writer. Your task is to completely rewrite and tailor the user's provided profile into a professional, ATS-friendly resume for their target role. Extract personal info, write a compelling summary, and rephrase experience bullet points to include keywords from the skill analysis."),
        ("human", "Target Role: {career}\n\nRequired Skills: {skills}\n\nUser's Raw Profile:\n{profile}")
    ])
    chain = prompt | structured_llm
    resume_content = chain.invoke({
        "career": state["chosen_career"],
        "skills": state["market_analysis"].dict(),
        "profile": state["student_profile"]
    })
    return {"tailored_resume": resume_content}

def lead_agent_node(state: TeamState):
    # ... (no changes here from before) ...
    print("--- 👑 Agent: Lead Agent (Synthesizing & Planning) ---")
    structured_llm = llm.with_structured_output(CareerActionPlan)
    prompt = ChatPromptTemplate.from_template(
        "You are the lead career strategist. Synthesize all information into a comprehensive Career Action Plan. "
        "Create a detailed 8-week learning roadmap and suggest 3 portfolio projects.\n\n"
        "Chosen Career: {career}\n"
        "Required Skills: {skills}\n"
        "Profile Feedback: {profile_feedback}"
    )
    chain = prompt | structured_llm
    final_plan = chain.invoke({
        "career": state["chosen_career"],
        "skills": state["market_analysis"].dict(),
        "profile_feedback": state["profile_analysis"].dict()
    })
    return {"final_plan": final_plan}
    
# --- Conditional Router ---
def route_initial_choice(state: TeamState):
    # ... (no changes here from before) ...
    print("--- 🚦 Main Router ---")
    if state["role_choice"] in ["resume_based", "market_demand"]:
        return "suggest_role"
    else:
        return "analyze_market"

# --- Graph Definition ---
graph_builder = StateGraph(TeamState)
graph_builder.add_node("suggest_role", role_suggester_agent)
graph_builder.add_node("analyze_market", job_market_analyst_agent)
graph_builder.add_node("review_profile", profile_reviewer_agent)
graph_builder.add_node("tailor_resume", resume_tailor_agent) # Add new node
graph_builder.add_node("create_final_plan", lead_agent_node)

graph_builder.set_conditional_entry_point(route_initial_choice, {"suggest_role": "suggest_role", "analyze_market": "analyze_market"})
graph_builder.add_edge("suggest_role", "analyze_market")
# After market analysis, review profile and tailor resume can happen in parallel
graph_builder.add_edge("analyze_market", "review_profile")
graph_builder.add_edge("analyze_market", "tailor_resume")
# The lead agent waits for both to finish
graph_builder.add_edge("review_profile", "create_final_plan")
graph_builder.add_edge("tailor_resume", "create_final_plan")
graph_builder.add_edge("create_final_plan", END)
navigator_agent = graph_builder.compile()

print("--- Advanced LangGraph Agent Backend with Resume Generation is ready. ---")

def run_agent(student_profile, role_choice):
    """Main function to run the agent graph."""
    initial_state = {
        "student_profile": student_profile,
        "role_choice": role_choice,
        "chosen_career": role_choice if role_choice not in ["resume_based", "market_demand"] else None
    }
    # The agent now returns the full final state, which includes the tailored resume content
    final_state = navigator_agent.invoke(initial_state)
    return final_state

def run_chat(user_message, history, plan_context):
    # ... (no changes here from before) ...
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful career coach. The user has just received the following career action plan. Answer their follow-up questions based ONLY on this plan.\n\n--- CAREER PLAN ---\n{plan_text}"),
        ("user", "{user_question}")
    ])
    chat_chain = prompt | llm
    response = chat_chain.invoke({"plan_text": str(plan_context), "user_question": user_message})
    return response.content
