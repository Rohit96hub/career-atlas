# app.py

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from pypdf import PdfReader
import os
import secrets
import uuid
from agent import run_agent, scrape_web_content, run_chat
from resume_generator import create_resume_pdf, CareerActionPlan # Import CareerActionPlan for type hint

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = '/tmp/career_navigator'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    resume_file = request.files.get('resume')
    profile_pic_file = request.files.get('profile_picture')
    linkedin_url = request.form.get('linkedin_url', '').strip()
    role_choice = request.form.get('career_choice')
    custom_role = request.form.get('custom_role', '').strip()

    if role_choice == 'Other' and custom_role:
        final_role_choice = custom_role
    else:
        final_role_choice = role_choice

    if not resume_file or resume_file.filename == '':
        return "A PDF resume is required to proceed."

    unique_id = str(uuid.uuid4())
    resume_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_resume.pdf")
    resume_file.save(resume_filepath)
    
    image_filepath = None
    if profile_pic_file and profile_pic_file.filename != '':
        image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_pic.png")
        profile_pic_file.save(image_filepath)

    try:
        reader = PdfReader(resume_filepath)
        resume_text = "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"Error reading PDF: {e}"

    linkedin_text = ""
    if linkedin_url:
        linkedin_text = scrape_web_content.invoke({"url": linkedin_url})
    
    student_profile_text = f"--- RESUME ---\n{resume_text}\n\n--- LINKEDIN PROFILE ---\n{linkedin_text}"

    agent_result = run_agent(student_profile_text, final_role_choice)
    final_plan = agent_result['final_plan']
    tailored_resume_content = agent_result['tailored_resume']
    
    resume_pdf_filename = f"{unique_id}_generated_resume.pdf"
    resume_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_pdf_filename)
    
    # CORRECTED LINE: Pass the chosen_career to the PDF generator
    create_resume_pdf(tailored_resume_content, image_filepath, resume_pdf_path, final_plan.chosen_career)

    session['plan'] = final_plan.dict()
    
    return render_template('result.html', plan=final_plan, resume_pdf_filename=resume_pdf_filename)

@app.route('/preview/<filename>')
def preview_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download/<filename>')
def download_resume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    history = request.json.get('history')
    plan_context = session.get('plan', {})
    if not plan_context:
        return jsonify({"response": "I'm sorry, I've lost context. Please start over."})
    ai_response = run_chat(user_message, history, plan_context)
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(debug=True)
