import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pandas as pd
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
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
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    selected_vars = request.form.getlist('variables')
    negative_vars = request.form.getlist('negative_variables')

    df_filtered = df.sort_values('date')
    df_to_save = df_filtered[['date'] + selected_vars]

    # Save filtered data as CSV with formatted date
    df_to_save_copy = df_to_save.copy()
    df_to_save_copy['date'] = df_to_save_copy['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_to_save_copy.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'filtered_data.csv'), index=False)

    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'negative_variables.txt'), 'w') as f:
        for var in negative_vars:
            f.write(f"{var}\n")

    complete_data, missing_dates = complete_missing_data(df_filtered, selected_vars)

    complete_data['date'] = pd.to_datetime(complete_data['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
    missing_dates['date'] = pd.to_datetime(missing_dates['date']).dt.strftime('%Y-%m-%d %H:%M:%S')

    complete_data.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'complete_data.csv'), index=False)
    missing_dates.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'missing_dates.csv'), index=False)

    return render_template('results.html',
                           selected_vars=selected_vars,
                           negative_vars=negative_vars,
                           start=df['date'].min().strftime('%Y-%m-%d %H:%M:%S'),
                           end=df['date'].max().strftime('%Y-%m-%d %H:%M:%S'))

def complete_missing_data(df_filtered, measurement_columns):
    df_filtered = df_filtered.copy()

    date_column = df_filtered.columns[0]  # Se asume que la primera columna es la fecha
    df_filtered[date_column] = pd.to_datetime(df_filtered[date_column])

    # Generar el rango completo de fechas a partir de min y max con la frecuencia más común
    inferred_freq = pd.infer_freq(df_filtered[date_column])
    if inferred_freq is None:
        inferred_freq = '10S'  # Valor por defecto si no se puede inferir

    date_range = pd.date_range(start=df_filtered[date_column].min(), 
                               end=df_filtered[date_column].max(), 
                               freq=inferred_freq)

    # Merge con el rango completo para detectar las fechas faltantes
    complete_dates_df = pd.DataFrame({date_column: date_range})
    merged_df = pd.merge(complete_dates_df, df_filtered, how='left', on=date_column)

    # Crear una copia que será interpolada
    complete_df = merged_df.copy()

    # Verificar si todas las columnas existen antes de procesar
    for col in measurement_columns:
        if col not in complete_df.columns:
            raise ValueError(f"La columna '{col}' no se encuentra en los datos. Revisa tu selección.")

    # Rellenar valores faltantes con interpolación por ventana
    for col in measurement_columns:
        null_mask = merged_df[col].isna()
        for idx in merged_df[null_mask].index:
            window_start = max(0, idx - 3)
            window_end = min(len(merged_df), idx + 4)
            window = merged_df.loc[window_start:window_end, col]
            interpolated_value = window.mean(skipna=True)
            complete_df.at[idx, col] = interpolated_value

    # Detectar fechas faltantes
    missing_dates = merged_df[merged_df[measurement_columns].isna().any(axis=1)][date_column].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

    return complete_df, missing_dates


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
