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

    # Interpolación y detección de fechas faltantes solo sobre las variables seleccionadas
    complete_data, missing_dates = complete_missing_data(df_to_save, selected_vars)

    complete_data['date'] = pd.to_datetime(complete_data['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
    complete_data.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'complete_data.csv'), index=False)

    # Guardar fechas faltantes como TXT
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'missing_dates.txt'), 'w') as f:
        for date in missing_dates:
            f.write(f"{date}\n")

    return render_template('results.html',
                           selected_vars=selected_vars,
                           negative_vars=negative_vars,
                           start=df['date'].min().strftime('%Y-%m-%d %H:%M:%S'),
                           end=df['date'].max().strftime('%Y-%m-%d %H:%M:%S'))

def complete_missing_data(df_filtered, measurement_columns):
    df_filtered = df_filtered.copy()

    date_column = 'date'
    df_filtered[date_column] = pd.to_datetime(df_filtered[date_column])

    # Inferir la frecuencia temporal (o asumir 10 segundos)
    inferred_freq = pd.infer_freq(df_filtered[date_column])
    if inferred_freq is None:
        inferred_freq = '10s'  # minúscula para evitar FutureWarning

    date_range = pd.date_range(start=df_filtered[date_column].min(), 
                               end=df_filtered[date_column].max(), 
                               freq=inferred_freq)

    complete_dates_df = pd.DataFrame({date_column: date_range})
    merged_df = pd.merge(complete_dates_df, df_filtered, how='left', on=date_column)

    complete_df = merged_df.copy()

    for col in measurement_columns:
        if col not in complete_df.columns:
            raise ValueError(f"La columna '{col}' no se encuentra en los datos. Revisa tu selección.")

    missing_dates = []

    for idx in range(1, len(merged_df) - 1):  # Avoid the first and last index
        if pd.isna(merged_df.iloc[idx][measurement_columns]).any():
            # Find the previous and next rows to calculate the average
            prev_row = merged_df.iloc[idx - 1]
            next_row = merged_df.iloc[idx + 1]
            
            for col in measurement_columns:
                if pd.isna(merged_df.at[idx, col]):
                    # Calculate the average between the previous and next valid values
                    avg_value = (prev_row[col] + next_row[col]) / 2
                    merged_df.at[idx, col] = avg_value
                    missing_dates.append(merged_df.at[idx, date_column].strftime('%Y-%m-%d %H:%M:%S'))

    return merged_df[[date_column] + measurement_columns], missing_dates

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
