from flask import Flask, request, jsonify, render_template, make_response
import google.generativeai as genai
import logging
import json
from weasyprint import HTML, CSS
from jinja2 import Template
import io

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

API_KEY = "AIzaSyDEFSNW6dJZ2xyFUXaAhsrU1K53-3eYA80"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route('/')
def index():
    return render_template('index.html')

def create_prompt(data):
    """Create a structured prompt for the resume generation."""
    experience_points = []
    for exp in data['experience']:
        exp_details = [
            f"Company: {exp['company']}",
            f"Title: {exp['title']}",
            f"Duration: {exp['startDate']} - {exp['endDate']}",
            f"Responsibilities: {exp['responsibilities']}"
        ]
        experience_points.append("\n".join(exp_details))

    prompt = f"""Generate a professionally formatted ATS-friendly resume with the following details:

CONTACT INFORMATION:
Name: {data['contact_info']['name']}
Email: {data['contact_info']['email']}
Phone: {data['contact_info']['phone']}
Location: {data['contact_info']['location']}

PROFESSIONAL EXPERIENCE:
{chr(10).join(experience_points)}

EDUCATION:
University: {data['education']['university']}
Degree: {data['education']['degree']}
Graduation Year: {data['education']['gradYear']}
{"GPA: " + data['education']['gpa'] if data['education']['gpa'] else ""}

SKILLS:
{', '.join(data['skills'])}

Please format this resume following these guidelines:
1. Create a clean, professional layout optimized for ATS systems
2. Use clear section headings (SUMMARY, EXPERIENCE, EDUCATION, SKILLS)
3. Format the experience section with proper bullet points
4. Include a brief professional summary at the top
5. Ensure all dates and company names are properly aligned
6. Format skills in a clear, scannable way
7. Use appropriate action verbs for experience bullet points
8. Quantify achievements where possible based on the provided information

Format the resume in a way that's both human-readable and ATS-friendly."""

    return prompt

def format_resume_html(content):
    """Convert the resume content to properly formatted HTML."""
    # Split into sections
    sections = content.split('\n\n')
    html_parts = []
    
    for section in sections:
        if not section.strip():
            continue
            
        # Handle contact information
        if 'Contact Information' in section or '@' in section:
            lines = section.split('\n')
            html_parts.append('<div class="contact-section">')
            for line in lines:
                if line.strip():
                    html_parts.append(f'<p>{line}</p>')
            html_parts.append('</div>')
            continue

        # Handle section headers
        if section.isupper() or 'SUMMARY' in section.upper():
            html_parts.append(f'<h2 class="section-header">{section}</h2>')
            continue

        # Handle bullet points
        if '•' in section or '-' in section:
            html_parts.append('<ul>')
            for line in section.split('\n'):
                if line.strip().startswith('•') or line.strip().startswith('-'):
                    point = line.replace('•', '').replace('-', '').strip()
                    html_parts.append(f'<li>{point}</li>')
                elif line.strip():
                    html_parts.append(f'<p>{line}</p>')
            html_parts.append('</ul>')
            continue

        # Regular paragraphs
        html_parts.append(f'<p>{section}</p>')

    return '\n'.join(html_parts)

@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    try:
        data = request.get_json()
        prompt = create_prompt(data)
        
        # Generate resume content
        response = model.generate_content(prompt)
        formatted_content = format_resume_html(response.text)
        
        return jsonify({
            'status': 'success',
            'resume': response.text,
            'formatted_html': formatted_content
        })

    except Exception as e:
        logging.error(f"Error generating resume: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/view_pdf', methods=['POST'])
def view_pdf():
    try:
        data = request.get_json()
        resume_content = data['resume']
        
        # Custom CSS for PDF formatting
        css = CSS(string='''
            @page {
                size: letter;
                margin: 1in;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .contact-section {
                text-align: center;
                margin-bottom: 20px;
            }
            .section-header {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
                margin-top: 20px;
            }
            ul {
                margin-top: 10px;
                margin-bottom: 10px;
                padding-left: 20px;
            }
            li {
                margin-bottom: 5px;
            }
            p {
                margin: 8px 0;
            }
        ''')

        # Format content and create HTML
        formatted_content = format_resume_html(resume_content)
        html_template = Template('''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                {{ content | safe }}
            </body>
            </html>
        ''')
        
        html_content = html_template.render(content=formatted_content)
        
        # Generate PDF
        pdf = HTML(string=html_content).write_pdf(stylesheets=[css])
        
        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline'
        
        return response

    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)