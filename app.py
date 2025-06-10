import os
import tempfile
import shutil
import zipfile
import subprocess

from flask import Flask, request, send_file, render_template

# Initialize Flask app with static and template folders
app = Flask(__name__, static_folder='static', template_folder='templates')
# Limit uploads to 5 MiB
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded = request.files.get('file')
        if not uploaded or not uploaded.filename.lower().endswith('.py'):
            return '🛑 Please upload a .py file.', 400

        # Create a temporary working directory
        workdir = tempfile.mkdtemp()
        try:
            # Save the uploaded file
            src_path = os.path.join(workdir, uploaded.filename)
            uploaded.save(src_path)

            # Prepare output directory
            dist_dir = os.path.join(workdir, 'dist')

            # Run PyArmor obfuscation
            result = subprocess.run(
                ['pyarmor', 'obfuscate', '--output', dist_dir, src_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                app.logger.error('PyArmor error: %s', result.stderr)
                return '💥 PyArmor obfuscation failed.', 500

            # Zip the obfuscated output
            zip_path = os.path.join(workdir, 'obfuscated.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, _, files in os.walk(dist_dir):
                    for file in files:
                        full = os.path.join(root, file)
                        arcname = os.path.relpath(full, dist_dir)
                        z.write(full, arcname)

            # Send the zip file as a download and clean up afterward
            response = send_file(
                zip_path,
                as_attachment=True,
                download_name='obfuscated.zip'
            )
            @response.call_on_close
            def cleanup():
                shutil.rmtree(workdir)
            return response

        except Exception as e:
            app.logger.exception('Processing error')
            shutil.rmtree(workdir, ignore_errors=True)
            return '💥 Internal server error.', 500

    # GET request: render upload form
    return render_template('upload.html')

if __name__ == '__main__':
    # debug=True for development; disable in production
    app.run(host='0.0.0.0', port=5000, debug=True)
  
