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

print("--- Loading Advanced Agent Backend ---")

# Set API keys from environment variables
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Flask Career Navigator v2"

# --- Pydantic Models for More Structured Data ---
class SkillAnalysis(BaseModel):
    technical_skills: List[str] = Field(description="List of top 5 technical skills.")
    soft_skills: List[str] = Field(description="List of top 3 soft skills.")

class ProfileFeedback(BaseModel):
    resume_strengths: List[str] = Field(description="Strengths of the resume.")
    resume_gaps: List[str] = Field(description="Gaps in the resume.")
    linkedin_suggestions: List[str] = Field(description="Actionable suggestions to enhance the LinkedIn profile.")

class CareerActionPlan(BaseModel):
    chosen_career: str = Field(description="The final chosen career path for the user.")
    career_overview: str = Field(description="Overview of the chosen career.")
    skill_analysis: SkillAnalysis
    profile_feedback: ProfileFeedback
    learning_roadmap: str = Field(description="Markdown-formatted learning plan.")
    portfolio_plan: str = Field(description="Markdown-formatted portfolio project plan.")

# --- Agent State ---
class TeamState(TypedDict):
    student_profile: str
    role_choice: str # The user's initial selection
    chosen_career: Optional[str]
    market_analysis: Optional[SkillAnalysis]
    profile_analysis: Optional[ProfileFeedback]
    final_plan: Optional[CareerActionPlan]

# --- Tools ---
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

# --- Specialist Agents ---
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

def role_suggester_agent(state: TeamState):
    print("--- 🧑‍🏫 Agent: Role Suggester ---")
    if state["role_choice"] == "resume_based":
        prompt_text = "You are a career counselor. Analyze the user's profile and suggest the single most suitable job role for them. Output only the job title. Profile: {profile}"
    else: # market_demand
        prompt_text = "You are a job market analyst. Based on current tech trends, suggest a single, high-demand job role for a college student. Output only the job title. Current Trends Info: {profile}" # Use profile as a placeholder for market data if needed
    
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    suggested_role = chain.invoke({"profile": state["student_profile"]}).content.strip()
    print(f"    > Suggested Role: {suggested_role}")
    return {"chosen_career": suggested_role}

def job_market_analyst_agent(state: TeamState):
    print("--- 🕵️ Agent: Job Market Analyst ---")
    structured_llm = llm.with_structured_output(SkillAnalysis)
    prompt = ChatPromptTemplate.from_template(
        "You are an expert job market analyst. Based on the career of '{career}', identify the top 5 technical skills and top 3 soft skills required."
    )
    chain = prompt | structured_llm
    analysis = chain.invoke({"career": state['chosen_career']})
    return {"market_analysis": analysis}

def profile_reviewer_agent(state: TeamState):
    print("--- 📝 Agent: Profile Reviewer & LinkedIn Enhancer ---")
    structured_llm = llm.with_structured_output(ProfileFeedback)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert career coach. Analyze the user's professional profile (from resume and LinkedIn). "
                   "1. Compare it to the required skills and identify strengths and gaps. "
                   "2. Provide 3-5 specific, actionable suggestions to improve their LinkedIn profile (e.g., headline, summary, project descriptions)."),
        ("human", "User's Professional Profile:\n{profile}\n\nRequired Skills Analysis:\n{skill_analysis}")
    ])
    chain = prompt | structured_llm
    feedback = chain.invoke({
        "profile": state["student_profile"],
        "skill_analysis": state["market_analysis"].dict()
    })
    return {"profile_analysis": feedback}

def lead_agent_node(state: TeamState):
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
    """The main router directing the workflow based on user's role choice."""
    print("--- 🚦 Main Router ---")
    if state["role_choice"] in ["resume_based", "market_demand"]:
        print(f"    > Routing to: Suggest Role ({state['role_choice']})")
        return "suggest_role"
    else:
        print(f"    > Routing to: Analyze Market (User-defined role)")
        return "analyze_market"

# --- Graph Definition ---
graph_builder = StateGraph(TeamState)
graph_builder.add_node("suggest_role", role_suggester_agent)
graph_builder.add_node("analyze_market", job_market_analyst_agent)
graph_builder.add_node("review_profile", profile_reviewer_agent)
graph_builder.add_node("create_final_plan", lead_agent_node)

graph_builder.set_conditional_entry_point(
    route_initial_choice,
    {
        "suggest_role": "suggest_role",
        "analyze_market": "analyze_market"
    }
)
graph_builder.add_edge("suggest_role", "analyze_market")
graph_builder.add_edge("analyze_market", "review_profile")
graph_builder.add_edge("review_profile", "create_final_plan")
graph_builder.add_edge("create_final_plan", END)
navigator_agent = graph_builder.compile()

print("--- Advanced LangGraph Agent Backend is ready. ---")

def run_agent(student_profile, role_choice):
    """Main function to run the agent graph."""
    initial_state = {
        "student_profile": student_profile,
        "role_choice": role_choice,
        "chosen_career": role_choice if role_choice not in ["resume_based", "market_demand"] else None
    }
    final_state = navigator_agent.invoke(initial_state)
    return final_state['final_plan']

def run_chat(user_message, history, plan_context):
    """Main function to handle chat follow-ups."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful career coach. The user has just received the following career action plan. Answer their follow-up questions based ONLY on this plan.\n\n--- CAREER PLAN ---\n{plan_text}"),
        ("user", "{user_question}")
    ])
    chat_chain = prompt | llm
    response = chat_chain.invoke({"plan_text": str(plan_context), "user_question": user_message})
    return response.content