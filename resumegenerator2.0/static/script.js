// static/script.js
document.getElementById('resumeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        contact_info: {
            name: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            location: document.getElementById('location').value
        },
        experience: Array.from(document.getElementsByClassName('experience-entry')).map(entry => ({
            company: entry.querySelector('.company-name').value,
            title: entry.querySelector('.job-title').value,
            startDate: entry.querySelector('.start-date').value,
            endDate: entry.querySelector('.end-date').value,
            responsibilities: entry.querySelector('.responsibilities').value
        })),
        education: {
            university: document.getElementById('university').value,
            degree: document.getElementById('degree').value,
            gradYear: document.getElementById('gradYear').value,
            gpa: document.getElementById('gpa').value
        },
        skills: document.getElementById('skills').value.split(',').map(skill => skill.trim())
    };

    try {
        const response = await fetch('/generate_resume', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        if (data.status === 'success') {
            // Display text version
            document.getElementById('resumeContent').innerHTML = data.resume;
            document.getElementById('resumeOutput').style.display = 'block';
            
            // Create PDF viewer
            const pdfViewer = document.getElementById('pdfViewer') || document.createElement('iframe');
            pdfViewer.id = 'pdfViewer';
            pdfViewer.style.width = '100%';
            pdfViewer.style.height = '800px';
            pdfViewer.style.border = 'none';
            
            // Send request to view PDF
            const pdfResponse = await fetch('/view_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ resume: data.resume })
            });
            
            const pdfBlob = await pdfResponse.blob();
            const pdfUrl = URL.createObjectURL(pdfBlob);
            pdfViewer.src = pdfUrl;
            
            // Add PDF viewer to the page
            const viewerContainer = document.getElementById('pdfViewerContainer') || document.createElement('div');
            viewerContainer.id = 'pdfViewerContainer';
            if (!document.getElementById('pdfViewer')) {
                viewerContainer.appendChild(pdfViewer);
                document.getElementById('resumeOutput').appendChild(viewerContainer);
            }
        } else {
            alert('Error generating resume: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error);
    }
});

document.getElementById('addExperience').addEventListener('click', () => {
    const template = document.querySelector('.experience-entry').cloneNode(true);
    template.querySelectorAll('input, textarea').forEach(input => input.value = '');
    document.getElementById('experienceSection').insertBefore(template, document.getElementById('addExperience'));
});