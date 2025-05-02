# 🛠️ Web Platform for Industrial Process Data Analysis and Correction

This web application provides a comprehensive solution for processing, analyzing, and correcting industrial sensor data. It enables users to upload `.csv` datasets, perform variable selection, complete missing timestamps, detect anomalies, and automatically correct common data inconsistencies.

---

## 🚀 Features

1. **CSV File Upload**
   - Requires a `date` column for temporal analysis
   - Supports numeric variables for processing

2. **Variable Selection**
   - Flexible selection of variables for analysis
   - Configuration of variables that permit negative values

3. **Data Filtering & Cleaning**
   - Systematic removal of invalid or corrupted records
   - Output saved as `filtered_data.csv`

4. **Missing Data Completion**
   - Automatic detection of temporal sampling frequency
   - Intelligent insertion of missing timestamps
   - Missing value imputation using temporal neighborhood averaging
   - Results exported as `complete_data.csv` and `missing_dates.txt`

5. **Anomaly Detection & Data Correction**
   - Detection of significant value deviations (threshold: 5× average variation)
   - Automatic correction of invalid negative values
   - Identification of inconsistencies in correlated variables
   - Final results stored in `corrected_data.csv` and `detected_failures.csv`

---

## 📊 Output Files

| File Name | Description |
|-----------|-------------|
| `filtered_data.csv` | Cleaned dataset containing selected variables |
| `complete_data.csv` | Dataset with completed timestamps and imputed values |
| `missing_dates.txt` | Documented list of identified missing timestamps |
| `corrected_data.csv` | Final dataset after automated corrections |
| `detected_failures.csv` | Comprehensive report of detected anomalies and corrections |

---

## 🧰 Technical Requirements

- Python 3.8 or higher
- Flask
- Pandas
- NumPy

Installation of dependencies:

```bash
pip install -r requirements.txt