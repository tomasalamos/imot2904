import os
import pickle
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pandas as pd

app = Flask(__name__)
UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form', methods=['POST'])
def form():
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'data.csv')
    file.save(filepath)

    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()

    return render_template('form.html', variables=numeric_columns)

@app.route('/process', methods=['POST'])
def process():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'data.csv')
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    selected_vars = request.form.getlist('variables')
    negative_vars = request.form.getlist('negatives')

    # Guardar resultados sin filtrar por fecha
    df[selected_vars].to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'filtered_data.csv'), index=False)
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'negative_variables.pkl'), 'wb') as f:
        pickle.dump(negative_vars, f)

    return render_template('results.html', selected_vars=selected_vars,
                           negative_vars=negative_vars,
                           start="No filtrado",
                           end="No filtrado")

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
