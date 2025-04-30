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

    # Sort by date and prepare filtered DataFrame
    df_filtered = df.sort_values('date')
    df_filtered['date'] = df_filtered['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_to_save = df_filtered[['date'] + selected_vars]  # Include date as first column

    # Save filtered data
    df_to_save.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'filtered_data.csv'), index=False)

    # Save negative variables as plain text file
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'negative_variables.txt'), 'w') as f:
        for var in negative_vars:
            f.write(f"{var}\n")

    # Process to complete missing data
    complete_data, missing_dates = complete_missing_data(df_filtered, selected_vars)

    # Save complete data and missing dates
    complete_data.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'complete_data.csv'), index=False)
    missing_dates.to_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'missing_dates.csv'), index=False)

    return render_template('results.html',
                           selected_vars=selected_vars,
                           negative_vars=negative_vars,
                           start=df['date'].min().strftime('%Y-%m-%d %H:%M:%S'),
                           end=df['date'].max().strftime('%Y-%m-%d %H:%M:%S'))


def complete_missing_data(df_filtered, selected_vars):
    """
    Completes missing data in the df_filtered DataFrame by interpolating between
    previous and next valid values for measurement columns.
    """

    # Get date column
    date_column = 'date'

    # Identify measurement columns (all except the date column)
    measurement_columns = selected_vars

    # Create a DataFrame with all expected dates
    start_date = df_filtered[date_column].min()
    end_date = df_filtered[date_column].max()

    # Get time intervals
    intervals = df_filtered[date_column].diff().dropna()

    # Determine the most frequent interval
    most_frequent_interval = intervals.value_counts().idxmax()

    # Identify large intervals (greater than 5 minutes)
    minute_intervals = intervals.dt.total_seconds() / 60
    large_intervals = minute_intervals[minute_intervals > 5]

    # Create missing date ranges
    date_ranges = []
    current_date = start_date

    for idx in large_intervals.index:
        start = df_filtered[date_column].iloc[idx - 1]
        end = df_filtered[date_column].iloc[idx]
        if current_date < start:
            range_end = min(start, end_date)
            date_ranges.append(pd.date_range(start=current_date, end=range_end, freq=most_frequent_interval))
        current_date = end

    if current_date < end_date:
        date_ranges.append(pd.date_range(start=current_date, end=end_date, freq=most_frequent_interval))

    # Merge date ranges
    date_range = pd.concat([pd.Series(range) for range in date_ranges])

    # Create complete DataFrame
    complete_df = pd.DataFrame({date_column: date_range})

    # Merge original DataFrame with expected dates
    merged_df = pd.merge(complete_df, df_filtered, on=date_column, how="left")

    # Function to complete missing data by interpolating
    previous_df = pd.DataFrame()
    next_df = pd.DataFrame()

    for col in measurement_columns:
        previous_df[f'{col}_previous'] = merged_df[col].ffill()
        next_df[f'{col}_next'] = merged_df[col].bfill()

    # Calculate time intervals
    intervals = pd.DataFrame({
        'previous_interval': merged_df[date_column].diff().dt.total_seconds() / 60,
        'next_interval': merged_df[date_column].diff(-1).dt.total_seconds().abs() / 60
    })

    # Combine dataframes
    temp_df = pd.concat([merged_df, previous_df, next_df, intervals], axis=1)

    # Complete only if intervals are smaller than 5 minutes
    complete_mask = (temp_df['previous_interval'] < 5) & (temp_df['next_interval'] < 5)

    # Apply interpolation for each measurement column
    for col in measurement_columns:
        factor = temp_df['previous_interval'] / (temp_df['previous_interval'] + temp_df['next_interval'])
        variation = temp_df[f'{col}_next'] - temp_df[f'{col}_previous']
        interpolated_value = temp_df[f'{col}_previous'] + (variation * factor)
        complete_df.loc[complete_mask & complete_df[col].isna(), col] = interpolated_value

    # Prepare missing dates
    missing_rows = merged_df[measurement_columns].isna().any(axis=1)
    missing_dates = complete_df.loc[missing_rows, date_column]

    missing_dates_df = pd.DataFrame({"date": missing_dates})
    missing_dates_df["date"] = missing_dates_df["date"].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Return completed data and missing dates
    complete_df[date_column] = complete_df[date_column].dt.strftime('%Y-%m-%d %H:%M:%S')
    return complete_df, missing_dates_df


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

