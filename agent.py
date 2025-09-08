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

print("--- Loading Advanced Agent Backend v3.1 (Fast Model) ---")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Flask Career Navigator v3.1"

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

# --- Tools and Agents ---
# Use the faster model to prevent timeouts on Vercel
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# The rest of the agent.py file is the same as before...
@tool
def scrape_web_content(url: str) -> str:
    """Scrapes text content from a given URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)[:15000]
    except requests.RequestException as e:
        return f"Error scraping {url}: {e}"
        
def role_suggester_agent(state: TeamState):
    print("--- 🧑‍🏫 Agent: Role Suggester ---")
    if state["role_choice"] == "resume_based":
        prompt_text = "Analyze the user's profile and suggest the single most suitable job role. Output only the job title. Profile: {profile}"
    else:
        prompt_text = "Based on current tech trends, suggest a single, high-demand job role for a college student. Output only the job title."
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    suggested_role = chain.invoke({"profile": state["student_profile"]}).content.strip()
    print(f"    > Suggested Role: {suggested_role}")
    return {"chosen_career": suggested_role}

def job_market_analyst_agent(state: TeamState):
    print("--- 🕵️ Agent: Job Market Analyst ---")
    structured_llm = llm.with_structured_output(SkillAnalysis, method="function_calling")
    prompt = ChatPromptTemplate.from_template("Based on the career of '{career}', identify the top 5 technical skills and top 3 soft skills required.")
    chain = prompt | structured_llm
    analysis = chain.invoke({"career": state['chosen_career']})
    return {"market_analysis": analysis}

def profile_reviewer_agent(state: TeamState):
    print("--- 📝 Agent: Profile Reviewer & LinkedIn Enhancer ---")
    structured_llm = llm.with_structured_output(ProfileFeedback, method="function_calling")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Analyze the user's professional profile. 1. Compare it to required skills, identifying strengths/gaps. 2. Provide 3-5 specific, actionable suggestions to improve their LinkedIn profile."),
        ("human", "User Profile:\n{profile}\n\nRequired Skills:\n{skill_analysis}")
    ])
    chain = prompt | structured_llm
    feedback = chain.invoke({"profile": state["student_profile"], "skill_analysis": state["market_analysis"].dict()})
    return {"profile_analysis": feedback}

def resume_tailor_agent(state: TeamState):
    print("--- ✍️ Agent: AI Resume Tailor ---")
    structured_llm = llm.with_structured_output(TailoredResumeContent, method="function_calling")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert resume writer. Rewrite and tailor the user's profile into a professional, ATS-friendly resume for their target role. Extract personal info, write a compelling summary, and rephrase experience bullet points to include keywords from the skill analysis."),
        ("human", "Target Role: {career}\n\nRequired Skills: {skills}\n\nUser's Raw Profile:\n{profile}")
    ])
    chain = prompt | structured_llm
    resume_content = chain.invoke({"career": state["chosen_career"], "skills": state["market_analysis"].dict(), "profile": state["student_profile"]})
    return {"tailored_resume": resume_content}

def lead_agent_node(state: TeamState):
    print("--- 👑 Agent: Lead Agent (Synthesizing & Planning) ---")
    structured_llm = llm.with_structured_output(CareerActionPlan, method="function_calling")
    prompt = ChatPromptTemplate.from_template(
        "You are the lead career strategist. Synthesize all information into a comprehensive Career Action Plan. Create a detailed 8-week learning roadmap and suggest 3 portfolio projects.\n\n"
        "Chosen Career: {career}\n"
        "Required Skills: {skills}\n"
        "Profile Feedback: {profile_feedback}"
    )
    chain = prompt | structured_llm
    final_plan = chain.invoke({"career": state["chosen_career"], "skills": state["market_analysis"].dict(), "profile_feedback": state["profile_analysis"].dict()})
    return {"final_plan": final_plan}

def route_initial_choice(state: TeamState):
    print("--- 🚦 Main Router ---")
    return "suggest_role" if state["role_choice"] in ["resume_based", "market_demand"] else "analyze_market"

graph_builder = StateGraph(TeamState)
graph_builder.add_node("suggest_role", role_suggester_agent)
graph_builder.add_node("analyze_market", job_market_analyst_agent)
graph_builder.add_node("review_profile", profile_reviewer_agent)
graph_builder.add_node("tailor_resume", resume_tailor_agent)
graph_builder.add_node("create_final_plan", lead_agent_node)
graph_builder.set_conditional_entry_point(route_initial_choice, {"suggest_role": "suggest_role", "analyze_market": "analyze_market"})
graph_builder.add_edge("suggest_role", "analyze_market")
# Run review and tailoring in parallel
graph_builder.add_edge("analyze_market", "review_profile")
graph_builder.add_edge("analyze_market", "tailor_resume")
# The lead agent waits for both to finish
graph_builder.add_edge("review_profile", "create_final_plan")
graph_builder.add_edge("tailor_resume", "create_final_plan")
graph_builder.add_edge("create_final_plan", END)
navigator_agent = graph_builder.compile()

def run_agent(student_profile, role_choice):
    initial_state = {"student_profile": student_profile, "role_choice": role_choice, "chosen_career": role_choice if role_choice not in ["resume_based", "market_demand"] else None}
    return navigator_agent.invoke(initial_state)

def run_chat(user_message, history, plan_context):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful career coach. The user received the following career action plan. Answer their follow-up questions based ONLY on this plan.\n\n--- CAREER PLAN ---\n{plan_text}"),
        ("user", "{user_question}")
    ])
    chat_chain = prompt | llm
    response = chat_chain.invoke({"plan_text": str(plan_context), "user_question": user_message})
    return response.content
