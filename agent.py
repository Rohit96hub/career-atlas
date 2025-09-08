# agent.py

import os
from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
# ... (rest of imports are the same)
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

print("--- Loading Elite Agent Backend v4.0 (GPT-4o) ---")

# --- (API Keys and Pydantic Models setup remains the same) ---
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
    # ... (state is the same)
    student_profile: str
    role_choice: str
    chosen_career: Optional[str]
    market_analysis: Optional[SkillAnalysis]
    profile_analysis: Optional[ProfileFeedback]
    tailored_resume: Optional[TailoredResumeContent]
    final_plan: Optional[CareerActionPlan]

# --- Tools and Agents ---
# CRITICAL: Using a more powerful model for high-quality content.
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# ... (tool and other agents remain the same) ...

# UPGRADED AGENT: Resume Tailor with an elite prompt
def resume_tailor_agent(state: TeamState):
    print("--- ✍️ Agent: Elite AI Resume Tailor ---")
    structured_llm = llm.with_structured_output(TailoredResumeContent)
    
    elite_prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "You are a top-tier executive resume writer from a leading FAANG company. Your task is to transform a student's raw profile into a powerful, achievement-oriented resume that will pass any ATS. "
         "You must extract personal info, write a powerful 3-4 line professional summary, and rewrite every experience bullet point to follow the STAR (Situation, Task, Action, Result) method. "
         "Start each bullet point with a strong action verb and quantify results with metrics (e.g., 'Increased efficiency by 30%', 'Managed a budget of $5k', 'Reduced server costs by 15%'). "
         "Do not invent information, but creatively rephrase the user's input to highlight achievements."),
        ("human", 
         "Target Role: {career}\n\n"
         "Required Market Skills: {skills}\n\n"
         "User's Raw Profile (from Resume & LinkedIn):\n{profile}"
        )
    ])
    
    chain = elite_prompt | structured_llm
    resume_content = chain.invoke({
        "career": state["chosen_career"],
        "skills": state["market_analysis"].dict(),
        "profile": state["student_profile"]
    })
    return {"tailored_resume": resume_content}

# ... (The rest of the agent.py file, including the graph definition, is the same as the last working version) ...

# The graph definition should remain sequential as it's the most robust.
# The graph definition and run_agent functions from the previous step are correct.
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

def role_suggester_agent(state: TeamState):
    # ... (same as before)
    pass
    
graph_builder = StateGraph(TeamState)
graph_builder.add_node("suggest_role", role_suggester_agent)
graph_builder.add_node("analyze_market", job_market_analyst_agent)
graph_builder.add_node("review_profile", profile_reviewer_agent)
graph_builder.add_node("tailor_resume", resume_tailor_agent)
graph_builder.add_node("create_final_plan", lead_agent_node)

graph_builder.set_conditional_entry_point(route_initial_choice, {"suggest_role": "suggest_role", "analyze_market": "analyze_market"})
graph_builder.add_edge("suggest_role", "analyze_market")
graph_builder.add_edge("analyze_market", "review_profile")
graph_builder.add_edge("review_profile", "tailor_resume")
graph_builder.add_edge("tailor_resume", "create_final_plan")
graph_builder.add_edge("create_final_plan", END)
navigator_agent = graph_builder.compile()

def run_agent(student_profile, role_choice):
    initial_state = {"student_profile": student_profile, "role_choice": role_choice, "chosen_career": role_choice if role_choice not in ["resume_based", "market_demand"] else None}
    return navigator_agent.invoke(initial_state)

def run_chat(user_message, history, plan_context):
    # ... (same as before)
    pass
