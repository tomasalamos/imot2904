import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pandas as pd
from datetime import datetime

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
    min_date = df['date'].min().strftime('%Y-%m-%dT%H:%M:%S')
    max_date = df['date'].max().strftime('%Y-%m-%dT%H:%M:%S')

    return render_template('form.html', variables=numeric_columns, min_date=min_date, max_date=max_date)

@app.route('/process', methods=['POST'])
def process():
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'data.csv')
    df = pd.read_csv(filepath)
    
    # Manejo robusto de fechas
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])  # Filtra filas con fechas inválidas

    # Rango real del archivo
    real_min = df['date'].min()
    real_max = df['date'].max()

    # Captura fechas del formulario
    start_str = request.form.get('start_date')
    end_str = request.form.get('end_date')
    selected_vars = request.form.getlist('variables')
    negative_vars = request.form.getlist('negative_vars')

    # Convierte fechas del formulario
    try:
        start_date = pd.to_datetime(start_str, errors='coerce')
        if pd.isna(start_date) or start_date < real_min:
            start_date = real_min
    except:
        start_date = real_min

    try:
        end_date = pd.to_datetime(end_str, errors='coerce')
        if pd.isna(end_date) or end_date > real_max:
            end_date = real_max
    except:
        end_date = real_max

    # Asegura que el rango tenga sentido
    if start_date >= end_date:
        start_date = real_min
        end_date = real_max

    # Filtrado final
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    # Guardar outputs
    filtered_path = os.path.join(app.config['UPLOAD_FOLDER'], 'filtered_data.csv')
    filtered_vars_path = os.path.join(app.config['UPLOAD_FOLDER'], 'negative_variables.txt')

    df_filtered.to_csv(filtered_path, index=False)
    with open(filtered_vars_path, 'w') as f:
        f.write('\n'.join(negative_vars))

    return render_template('result.html', 
                           filtered_data='filtered_data.csv',
                           negative_vars='negative_variables.txt',
                           selected_vars=selected_vars,
                           date_range=f"{start_date} to {end_date}")

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
