# app.py

from flask import Flask, render_template, request, jsonify, session
from pypdf import PdfReader
import os
import secrets
# Import the agent logic and tools from agent.py
from agent import run_agent, scrape_web_content, run_chat, CareerActionPlan

app = Flask(__name__)
# A secret key is required for Flask sessions
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Renders the main input page."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """Handles the form submission and runs the agent."""
    resume_file = request.files.get('resume')
    linkedin_url = request.form.get('linkedin_url', '').strip()
    role_choice = request.form.get('career_choice')
    custom_role = request.form.get('custom_role', '').strip()

    if role_choice == 'Other' and custom_role:
        final_role_choice = custom_role
    else:
        final_role_choice = role_choice

    resume_text = ""
    if resume_file and resume_file.filename != '':
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
        resume_file.save(filepath)
        try:
            reader = PdfReader(filepath)
            resume_text = "".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            return f"Error reading PDF: {e}"

    linkedin_text = ""
    if linkedin_url:
        linkedin_text = scrape_web_content.invoke({"url": linkedin_url})
        if "Error scraping" in linkedin_text:
            linkedin_text = f"Could not scrape LinkedIn profile. Proceeding with resume only."
    
    student_profile_text = f"--- RESUME ---\n{resume_text}\n\n--- LINKEDIN PROFILE ---\n{linkedin_text}"

    if not resume_text:
        return "Please upload a resume to begin."

    # Run the LangGraph Agent
    final_plan = run_agent(student_profile_text, final_role_choice)

    # Store the plan in the session for the chat feature
    session['plan'] = final_plan.dict()

    return render_template('result.html', plan=final_plan)

@app.route('/chat', methods=['POST'])
def chat():
    """Handles AJAX requests from the chat interface."""
    user_message = request.json.get('message')
    history = request.json.get('history') # You might use history for more context
    
    # Retrieve the plan from the session
    plan_context = session.get('plan', {})
    if not plan_context:
        return jsonify({"response": "I'm sorry, I've lost the context of your plan. Please start over."})

    # Run the chat logic
    ai_response = run_chat(user_message, history, plan_context)
    
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(debug=True)