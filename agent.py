# agent.py

import os
from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

print("--- Loading Masterclass Agent Backend v5.0 (Resume Writing Room) ---")

# --- API Keys and Tracing Setup ---
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Flask Career Navigator v5.0"

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
    # ... (no changes here)
    pass
    
# --- Agent State ---
class TeamState(TypedDict):
    student_profile: str
    role_choice: str
    chosen_career: Optional[str]
    market_analysis: Optional[SkillAnalysis]
    profile_analysis: Optional[ProfileFeedback]
    # This key will now be populated by the sub-graph
    tailored_resume: Optional[TailoredResumeContent]
    final_plan: Optional[CareerActionPlan]

# --- LLM and Tools ---
# Using the powerful model for the highest quality output.
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# --- RESUME WRITING ROOM (SUB-GRAPH) ---

def create_resume_writing_team():
    """Creates a dedicated sub-graph for generating resume content."""
    
    # Define the state for this sub-team
    class ResumeTeamState(TypedDict):
        student_profile: str
        chosen_career: str
        market_analysis: SkillAnalysis
        # Each agent populates a piece of the final resume
        summary: str
        experiences: List[JobExperience]
        skills: List[str]
        final_resume_content: TailoredResumeContent

    # Define the micro-agents for the writing room
    summary_writer_agent = ChatPromptTemplate.from_template(
        "You are a master storyteller. Based on the user's profile and target career, write a compelling 3-4 sentence professional summary. "
        "Target Career: {chosen_career}\nUser Profile: {student_profile}"
    ) | llm

    experience_rewriter_agent = ChatPromptTemplate.from_template(
        "You are an expert resume writer. Rewrite the following work experience to be achievement-oriented, using keywords from the skill analysis. "
        "Focus on the STAR method (Situation, Task, Action, Result) and quantify results. "
        "Target Career: {chosen_career}\nRequired Skills: {skills}\nUser Experience: {student_profile}"
    ) | llm.with_structured_output(JobExperience)

    skills_extractor_agent = ChatPromptTemplate.from_template(
        "You are a skills analyst. Extract and list the most relevant technical and soft skills from the user's profile, cross-referencing with the required market skills. "
        "Required Skills: {skills}\nUser Profile: {student_profile}"
    ) | llm.with_structured_output(TailoredResumeContent)


    # Define the nodes for the sub-graph
    def summary_node(state: ResumeTeamState):
        print("    > Writing Room: Summary Agent...")
        result = summary_writer_agent.invoke(state)
        return {"summary": result.content}

    def experience_node(state: ResumeTeamState):
        print("    > Writing Room: Experience Rewriter Agent...")
        # In a real app, you would map over multiple experiences. Here we simplify for one.
        result = experience_rewriter_agent.invoke({
            "chosen_career": state["chosen_career"],
            "skills": state["market_analysis"].technical_skills,
            "student_profile": state["student_profile"]
        })
        return {"experiences": [result]}

    def skills_node(state: ResumeTeamState):
        print("    > Writing Room: Skills Extractor Agent...")
        # This is a simplified call; a real implementation would be more robust
        result = skills_extractor_agent.invoke({
            "skills": state["market_analysis"].technical_skills,
            "student_profile": state["student_profile"]
        })
        # Extracting multiple fields from a single call for efficiency
        return {
            "skills": result.skills,
            "final_resume_content": result # Assume this agent can also extract name, email, etc.
        }

    # This node compiles the results from the micro-agents
    def compile_resume_node(state: ResumeTeamState):
        print("    > Writing Room: Compiling Resume...")
        # The skills_node already produced a base object, we just fill in the rest
        final_resume = state["final_resume_content"]
        final_resume.summary = state["summary"]
        final_resume.experiences = state["experiences"]
        return {"final_resume_content": final_resume}

    # Build the sub-graph
    builder = StateGraph(ResumeTeamState)
    builder.add_node("summary", summary_node)
    builder.add_node("experience", experience_node)
    builder.add_node("skills_and_extract", skills_node)
    builder.add_node("compile", compile_resume_node)
    
    # Set the workflow: summary, experience, and skills can run in parallel
    builder.set_entry_point("summary")
    builder.add_edge("summary", "compile")
    builder.add_edge("experience", "compile")
    builder.add_edge("skills_and_extract", "compile")
    builder.add_edge("compile", END)
    
    return builder.compile()

# --- MAIN AGENT WORKFLOW ---

# ... (role_suggester_agent and job_market_analyst_agent are unchanged) ...
def role_suggester_agent(state: TeamState):
    # ...
    pass
def job_market_analyst_agent(state: TeamState):
    # ...
    pass
    
def profile_reviewer_agent(state: TeamState):
    # ... (no changes, still provides valuable feedback) ...
    pass

# This is the node that invokes our new "Resume Writing Room" sub-graph
def resume_team_node(state: TeamState):
    print("--- ✍️ Delegating to Resume Writing Room Sub-Graph ---")
    resume_writing_team = create_resume_writing_team()
    
    # We pass only the necessary information to the sub-graph
    sub_graph_input = {
        "student_profile": state["student_profile"],
        "chosen_career": state["chosen_career"],
        "market_analysis": state["market_analysis"]
    }
    
    final_resume_state = resume_writing_team.invoke(sub_graph_input)
    # Return the final compiled resume content to the main graph's state
    return {"tailored_resume": final_resume_state["final_resume_content"]}

def lead_agent_node(state: TeamState):
    # ... (no changes, it just uses the data provided) ...
    pass
    
def route_initial_choice(state: TeamState):
    # ... (no changes) ...
    pass
    
# --- Main Graph Definition ---
graph_builder = StateGraph(TeamState)
graph_builder.add_node("suggest_role", role_suggester_agent)
graph_builder.add_node("analyze_market", job_market_analyst_agent)
graph_builder.add_node("review_profile", profile_reviewer_agent)
# Replace the old tailor agent with our new sub-graph node
graph_builder.add_node("resume_writing_team", resume_team_node)
graph_builder.add_node("create_final_plan", lead_agent_node)

graph_builder.set_conditional_entry_point(route_initial_choice, {"suggest_role": "suggest_role", "analyze_market": "analyze_market"})
graph_builder.add_edge("suggest_role", "analyze_market")
# The workflow is now sequential and robust
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
    # ... (no changes) ...
    pass
