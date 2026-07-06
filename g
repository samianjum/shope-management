#!/usr/bin/env python3
import os
import re

BASE_DIR = os.getcwd()

def backup_file(filepath):
    if os.path.exists(filepath):
        import shutil
        shutil.copy2(filepath, filepath + ".bak")
        print(f"✅ Backup: {filepath}.bak")

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Updated: {filepath}")

def fix_chakki_js():
    """Replace the entire extra_js block in chakki.html with robust version."""
    path = os.path.join(BASE_DIR, "templates", "mobile", "chakki.html")
    backup_file(path)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the {% block extra_js %} ... {% endblock %} block
    # We'll replace everything between {% block extra_js %} and {% endblock %}
    import re
    pattern = r'{% block extra_js %}(.*?){% endblock %}'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("⚠️ Could not find extra_js block in chakki.html. Skipping.")
        return

    old_js_block = match.group(0)
    new_js_block = """{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('transcriptModal');
    const modalBody = document.getElementById('transcriptModalBody');
    const closeBtn = document.getElementById('closeTranscriptModal');
    const printBtn = document.getElementById('printTranscript');

    // ----- Open modal on view transcript button click -----
    document.querySelectorAll('.view-transcript').forEach(btn => {
        btn.addEventListener('click', function() {
            const orderId = this.dataset.orderId;
            if (!orderId) {
                alert('Order ID not found.');
                return;
            }
            // Fetch transcript content
            fetch(`/portal/{{ tenant.schema_name }}/chakki/transcript-modal/${orderId}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.text();
                })
                .then(html => {
                    modalBody.innerHTML = html;
                    modal.classList.add('open');
                })
                .catch(err => {
                    console.error('Fetch error:', err);
                    modalBody.innerHTML = '<div style="padding:20px;text-align:center;color:red;">Error loading transcript. Please try again.</div>';
                    modal.classList.add('open');
                });
        });
    });

    // ----- Close modal -----
    function closeModal() {
        modal.classList.remove('open');
        modalBody.innerHTML = '<div style="text-align:center; padding:20px;">Loading...</div>';
    }
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closeModal();
        });
    }

    // ----- Print -----
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }

    // ----- Download (with format selector) -----
    const downloadBtn = document.getElementById('downloadTranscriptBtn');
    const formatSelect = document.getElementById('downloadFormat');
    if (downloadBtn && formatSelect) {
        downloadBtn.addEventListener('click', function() {
            try {
                const format = formatSelect.value;
                const container = document.querySelector('.transcript-container');
                if (!container) {
                    alert('Transcript content not loaded yet.');
                    return;
                }
                // Check if html2canvas is available
                if (typeof html2canvas === 'undefined') {
                    alert('html2canvas library not loaded. Please check your internet connection.');
                    return;
                }
                html2canvas(container, {
                    scale: 2,
                    useCORS: true,
                    backgroundColor: '#ffffff'
                }).then(canvas => {
                    if (format === 'pdf') {
                        if (typeof window.jspdf === 'undefined') {
                            alert('jsPDF library not loaded. Please check your internet connection.');
                            return;
                        }
                        const imgData = canvas.toDataURL('image/png');
                        const { jsPDF } = window.jspdf;
                        const pdf = new jsPDF('p', 'mm', 'a4');
                        const pdfWidth = pdf.internal.pageSize.getWidth();
                        const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
                        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
                        pdf.save('transcript.pdf');
                    } else {
                        const mimeType = format === 'png' ? 'image/png' : 'image/jpeg';
                        const ext = format === 'png' ? 'png' : 'jpg';
                        const link = document.createElement('a');
                        link.download = `transcript.${ext}`;
                        link.href = canvas.toDataURL(mimeType);
                        link.click();
                    }
                }).catch(err => {
                    console.error('html2canvas error:', err);
                    alert('Failed to generate download: ' + err.message);
                });
            } catch (e) {
                console.error('Download error:', e);
                alert('An error occurred while downloading.');
            }
        });
    }

    // ----- Keyboard shortcut to close -----
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('open')) {
            closeModal();
        }
    });
});
</script>
{% endblock %}"""

    # Replace the block
    new_content = content.replace(old_js_block, new_js_block)
    write_file(path, new_content)

def main():
    print("🔧 Fixing transcript modal issue (robust JS with error handling)...")
    fix_chakki_js()
    print("✅ Done. Refresh the Chakki page and try clicking 'Transcript'.")
    print("   - Modal should now open even if CDN libraries are not loaded.")
    print("   - Check browser console for any errors.")

if __name__ == "__main__":
    main()
