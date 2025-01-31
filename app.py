from flask import Flask, render_template, request, send_from_directory
import pandas as pd
import os

app = Flask(__name__)

# Configuration
save_folder = "downloaded_pdfs"
metadata_file = "pdf_details.csv"

# Ensure the download folder exists
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# Load metadata from CSV
def load_metadata():
    try:
        return pd.read_csv(metadata_file)
    except FileNotFoundError:
        return pd.DataFrame()

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Search functionality
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    metadata = load_metadata()
    
    if metadata.empty:
        return "No metadata found. Please run the crawler first."
    
    if query:
        # Perform a case-insensitive search across all columns
        results = metadata[metadata.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
    else:
        results = metadata
    
    return render_template('search_results.html', results=results.to_dict('records'), query=query)

# Download PDF
@app.route('/download/<filename>')
def download_pdf(filename):
    return send_from_directory(save_folder, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)