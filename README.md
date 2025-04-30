# 🛠️ Web Platform for Filtering, Completing, and Correcting Mining Equipment Data

This web application allows you to upload `.csv` sensor datasets, select variables, fill missing timestamps, detect outliers, and automatically correct common issues like negative or inconsistent values.

---

## 🚀 Features

1. **CSV File Upload**
   - Must contain a `date` column.
   - Variables should be numeric.

2. **Variable Selection**
   - Select which variables to analyze.
   - Mark those that **can have negative values**.

3. **Data Filtering & Cleaning**
   - Removes invalid or corrupted records.
   - Saves cleaned data as `filtered_data.csv`.

4. **Missing Data Completion**
   - Automatically detects time frequency (e.g., every 10 seconds).
   - Inserts missing timestamps.
   - Imputes missing values using the average of temporal neighbors.
   - Results saved as `complete_data.csv` and `missing_dates.txt`.

5. **Automatic Fault Detection & Correction**
   - Detects sudden abnormal jumps (greater than 5× the average variation).
   - Corrects negative values (if not allowed).
   - Flags inconsistencies in correlated variables.
   - Final results saved in `corrected_data.csv` and `detected_failures.csv`.

---

## 🧪 Generated Files

| File Name | Description |
|-----------|-------------|
| `filtered_data.csv` | Cleaned data based on selected variables |
| `complete_data.csv` | Data with completed timestamps and imputed values |
| `missing_dates.txt` | List of detected missing timestamps |
| `corrected_data.csv` | Data after applying automatic corrections |
| `detected_failures.csv` | Detailed list of detected failures and anomalies |

---

## 🧰 Requirements

- Python 3.8+
- Flask
- Pandas
- Numpy

To install dependencies:

```bash
pip install -r requirements.txt
