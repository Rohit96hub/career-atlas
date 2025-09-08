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

print("--- Loading Masterclass Agent Backend v6.2 (Scope Fix) ---")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Career Navigator (Final)"

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

# --- LLM and Tools ---
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

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

# --- RESUME WRITING ROOM (SUB-GRAPH) ---
def create_resume_writing_team():
    """Creates the 'Resume Assembly Line' sub-graph."""
    
    # CORRECTED: Pydantic models needed by the sub-graph are defined INSIDE its scope.
    class ParsedExperience(BaseModel):
        title: str
        company: str
        description: str

    class ParsedProfile(BaseModel):
        full_name: str
        email: str
        phone: str
        education: str
        raw_experiences: List[ParsedExperience]
        raw_skills: List[str]

    class ResumeTeamState(TypedDict):
        student_profile: str
        chosen_career: str
        market_analysis: SkillAnalysis
        parsed_profile: ParsedProfile
        rewritten_summary: str
        rewritten_experiences: List[JobExperience]
        optimized_skills: List[str]
        final_resume_content: TailoredResumeContent

    # --- Micro-Agent Definitions ---
    profile_parser_agent = llm.with_structured_output(ParsedProfile)
    summary_writer_agent = ChatPromptTemplate.from_template(
        "You are a professional resume writer. Write a compelling 3-4 sentence professional summary for a {chosen_career}, based on this user's profile: {student_profile}"
    ) | llm
    experience_rewriter_agent = ChatPromptTemplate.from_template(
        "You are an expert resume writer. Rewrite this single job experience to be achievement-oriented, using keywords from the skill analysis. "
        "Use the STAR method and quantify results. Output only the rewritten description as a list of 3-4 bullet points.\n\n"
        "Required Skills: {skills}\n"
        "Original Experience:\nTitle: {title}\nCompany: {company}\nDescription: {description}"
    ) | llm
    skills_optimizer_agent = ChatPromptTemplate.from_template(
        "You are a skills analyst. From the following list of raw skills, select the top 10 most relevant skills for a {chosen_career}, informed by the market analysis.\n\n"
        "Required Market Skills: {market_skills}\nRaw Skills List: {raw_skills}"
    ) | llm

    # --- Sub-Graph Node Functions ---
    def parser_node(state: ResumeTeamState):
        print("    > Assembly Line: Parsing raw profile...")
        prompt = ChatPromptTemplate.from_template("Parse the user's profile into a structured format. Extract their name, contact info, education, and list of raw experiences and skills.")
        chain = prompt | profile_parser_agent
        parsed_profile = chain.invoke({"input": state["student_profile"]})
        return {"parsed_profile": parsed_profile}
    def summary_node(state: ResumeTeamState):
        print("    > Assembly Line: Writing summary...")
        result = summary_writer_agent.invoke(state)
        return {"rewritten_summary": result.content}
    def experience_node(state: ResumeTeamState):
        print("    > Assembly Line: Rewriting experiences...")
        rewritten_jobs = []
        for exp in state["parsed_profile"].raw_experiences:
            rewritten_desc_str = experience_rewriter_agent.invoke({
                "chosen_career": state["chosen_career"],
                "skills": state["market_analysis"].technical_skills,
                "title": exp.title, "company": exp.company, "description": exp.description
            }).content
            rewritten_desc_list = [line.strip().lstrip('-* ') for line in rewritten_desc_str.split('\n') if line.strip()]
            rewritten_jobs.append(JobExperience(title=exp.title, company=exp.company, dates="Present", description=rewritten_desc_list))
        return {"rewritten_experiences": rewritten_jobs}
    def skills_node(state: ResumeTeamState):
        print("    > Assembly Line: Optimizing skills...")
        result = skills_optimizer_agent.invoke({
            "chosen_career": state["chosen_career"],
            "market_skills": state["market_analysis"].technical_skills,
            "raw_skills": state["parsed_profile"].raw_skills
        })
        optimized_list = [skill.strip() for skill in result.content.split(',')]
        return {"optimized_skills": optimized_list}
    def compile_resume_node(state: ResumeTeamState):
        print("    > Assembly Line: Compiling final resume...")
        final_resume = TailoredResumeContent(
            full_name=state["parsed_profile"].full_name, email=state["parsed_profile"].email,
            phone=state["parsed_profile"].phone, education=state["parsed_profile"].education,
            summary=state["rewritten_summary"], experiences=state["rewritten_experiences"],
            skills=state["optimized_skills"]
        )
        return {"final_resume_content": final_resume}

    builder = StateGraph(ResumeTeamState)
    builder.add_node("parse_profile", parser_node)
    builder.add_node("write_summary", summary_node)
    builder.add_node("rewrite_experience", experience_node)
    builder.add_node("optimize_skills", skills_node)
    builder.add_node("compile_resume", compile_resume_node)
    builder.set_entry_point("parse_profile")
    builder.add_edge("parse_profile", "write_summary")
    builder.add_edge("parse_profile", "rewrite_experience")
    builder.add_edge("parse_profile", "optimize_skills")
    builder.add_edge("write_summary", "compile_resume")
    builder.add_edge("rewrite_experience", "compile_resume")
    builder.add_edge("optimize_skills", "compile_resume")
    builder.add_edge("compile_resume", END)
    return builder.compile()

# --- MAIN AGENT WORKFLOW ---
def role_suggester_agent(state: TeamState):
    print("--- 🧑‍🏫 Agent: Role Suggester ---")
    if state["role_choice"] == "resume_based":
        prompt_text = "Analyze the user's profile and suggest the single most suitable job role. Output only the job title. Profile: {profile}"
    else:
        prompt_text = "Based on current tech trends, suggest a single, high-demand job role for a college student. Output only the job title."
    prompt = ChatPromptTemplate.from_template(prompt_text)
    chain = prompt | llm
    suggested_role = chain.invoke({"profile": state["student_profile"]}).content.strip()
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

def resume_team_node(state: TeamState):
    print("--- ✍️ Delegating to Resume Assembly Line ---")
    resume_writing_team = create_resume_writing_team()
    sub_graph_input = {
        "student_profile": state["student_profile"],
        "chosen_career": state["chosen_career"],
        "market_analysis": state["market_analysis"]
    }
    final_resume_state = resume_writing_team.invoke(sub_graph_input)
    return {"tailored_resume": final_resume_state["final_resume_content"]}

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
graph_builder.add_node("resume_writing_team", resume_team_node)
graph_builder.add_node("create_final_plan", lead_agent_node)
graph_builder.set_conditional_entry_point(route_initial_choice, {"suggest_role": "suggest_role", "analyze_market": "analyze_market"})
graph_builder.add_edge("suggest_role", "analyze_market")
graph_builder.add_edge("analyze_market", "review_profile")
graph_builder.add_edge("review_profile", "resume_writing_team")
graph_builder.add_edge("resume_writing_team", "create_final_plan")
graph_builder.add_edge("create_final_plan", END)
navigator_agent = graph_builder.compile()

print("--- Masterclass LangGraph Agent is ready. ---")

def run_agent(student_profile, role_choice):
    initial_state = {"student_profile": student_profile, "role_choice": role_choice, "chosen_career": role_choice if role_choice not in ["resume_based", "market_demand"] else None}
    return navigator_agent.invoke(initial_state)

def run_chat(user_message, history, plan_context):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful career coach. The user received the following plan. Answer their follow-up questions based ONLY on this plan.\n\n--- PLAN CONTEXT ---\n{plan_text}"),
        ("user", "{user_question}")
    ])
    chat_chain = prompt | llm
    response = chat_chain.invoke({"plan_text": str(plan_context), "user_question": user_message})
    return response.content
