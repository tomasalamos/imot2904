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

def complete_missing_data(df_filtered, selected_vars):
    date_column = 'date'
    measurement_columns = selected_vars

    start_date = df_filtered[date_column].min()
    end_date = df_filtered[date_column].max()

    intervals = df_filtered[date_column].diff().dropna()
    most_frequent_interval = intervals.value_counts().idxmax()

    minute_intervals = intervals.dt.total_seconds() / 60
    large_intervals = minute_intervals[minute_intervals > 5]

    date_ranges = []
    current_date = start_date

    for idx in large_intervals.index:
        if idx == 0 or idx >= len(df_filtered):
            continue
        start = df_filtered[date_column].iloc[idx - 1]
        end = df_filtered[date_column].iloc[idx]
        if current_date < start:
            range_end = min(start, end_date)
            date_ranges.append(pd.date_range(start=current_date, end=range_end, freq=most_frequent_interval))
        current_date = end

    if current_date < end_date:
        date_ranges.append(pd.date_range(start=current_date, end=end_date, freq=most_frequent_interval))

    if not date_ranges:
        return df_filtered, pd.DataFrame(columns=['date'])

    date_range = pd.concat([pd.Series(r) for r in date_ranges])
    complete_df = pd.DataFrame({date_column: date_range})

    merged_df = pd.merge(complete_df, df_filtered, on=date_column, how="left")

    previous_df = pd.DataFrame()
    next_df = pd.DataFrame()

    for col in measurement_columns:
        previous_df[f'{col}_previous'] = merged_df[col].ffill()
        next_df[f'{col}_next'] = merged_df[col].bfill()

    intervals = pd.DataFrame({
        'previous_interval': merged_df[date_column].diff().dt.total_seconds() / 60,
        'next_interval': merged_df[date_column].diff(-1).dt.total_seconds().abs() / 60
    })

    temp_df = pd.concat([merged_df, previous_df, next_df, intervals], axis=1)
    complete_mask = (temp_df['previous_interval'] < 5) & (temp_df['next_interval'] < 5)

    for col in measurement_columns:
        factor = temp_df['previous_interval'] / (temp_df['previous_interval'] + temp_df['next_interval'])
        variation = temp_df[f'{col}_next'] - temp_df[f'{col}_previous']
        interpolated_value = temp_df[f'{col}_previous'] + (variation * factor)
        complete_df.loc[complete_mask & complete_df[col].isna(), col] = interpolated_value

    missing_rows = merged_df[measurement_columns].isna().any(axis=1)
    missing_dates = complete_df.loc[missing_rows, date_column]

    missing_dates_df = pd.DataFrame({"date": missing_dates})

    return complete_df, missing_dates_df

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
