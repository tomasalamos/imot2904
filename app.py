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
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    selected_vars = request.form.getlist('variables')
    negative_vars = request.form.getlist('negative_variables')
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    mode_frequency = df['date'].diff().dt.total_seconds().mode().iloc[0]
    min_available_date = df['date'].min() + pd.Timedelta(seconds=mode_frequency)

    start_date_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
    end_date_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')

    if start_date_dt < min_available_date or end_date_dt > df['date'].max() or end_date_dt < start_date_dt:
        return "Invalid date range selected."

    start_date_idx = df[df['date'] == start_date_dt].index[0]
    end_date_idx = df[df['date'] == end_date_dt].index[0]

    if start_date_idx > 0 and (df['date'].iloc[start_date_idx] - df['date'].iloc[start_date_idx - 1]).total_seconds() == mode_frequency:
        start_idx = start_date_idx - 1
    else:
        start_idx = start_date_idx

    filtered_df = df.iloc[start_idx:end_date_idx + 1][['date'] + selected_vars]
    filtered_df['date'] = filtered_df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")

    output_csv = os.path.join(app.config['UPLOAD_FOLDER'], 'filtered_data.csv')
    output_txt = os.path.join(app.config['UPLOAD_FOLDER'], 'negative_variables.txt')
    filtered_df.to_csv(output_csv, index=False)

    with open(output_txt, 'w') as f:
        for var in negative_vars:
            f.write(f"{var}\n")

    return render_template('results.html',
                           csv_file='filtered_data.csv',
                           txt_file='negative_variables.txt',
                           record_count=len(filtered_df),
                           selected_vars=selected_vars,
                           negative_vars=negative_vars,
                           start_date=start_date_dt,
                           end_date=end_date_dt)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
