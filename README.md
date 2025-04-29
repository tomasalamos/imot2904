# Industrial Measurement Failure Detection and Correction System

A comprehensive system for detecting and correcting anomalies in industrial process measurements using advanced statistical analysis and machine learning techniques.

## System Overview

This system provides a complete solution for industrial data quality management, from data filtering to anomaly detection and correction. It's designed to handle large volumes of time-series data from industrial processes.

## System Architecture

The system is composed of three main modules that work sequentially:

### 1. Data Selection Module (variables.py)
Handles the initial data filtering and configuration.

**Features:**
- Interactive variable selection interface
- Date range specification
- Negative value configuration
- Data filtering and preprocessing

**Input Requirements:**
- `data.parquet`: Raw industrial process data
  - Must contain timestamp column
  - Must contain numeric process variables
  - Should be in Parquet format for optimal performance

**User Interface:**
1. Variable Selection:
   - Displays all available numeric variables
   - Supports multiple selection methods:
     - Individual numbers (e.g., 1,3,5)
     - Ranges (e.g., 1-5)
     - 'all' option for complete selection
   - Real-time validation of selections

2. Negative Value Configuration:
   - Identifies variables that can have negative values
   - Multiple selection options:
     - Individual numbers
     - Ranges
     - 'none' option
   - Critical for proper anomaly detection

3. Date Range Selection:
   - Shows available data range
   - Enforces strict date format (DD/MM/YYYY HH:MM:SS)
   - Validates input against data availability

**Output Files:**
- `data_filtrada.parquet`: Filtered dataset containing only selected variables and date range
- `variables_negativas.pkl`: Configuration file storing variables that allow negative values

### 2. Data Completion Module (data_incompleta.py)
Handles missing data detection and completion.

**Features:**
- Automatic sampling interval detection
- Smart data interpolation
- Missing date identification
- Data quality validation

**Processing Steps:**
1. Interval Analysis:
   - Calculates time differences between measurements
   - Identifies most common sampling interval
   - Validates data consistency

2. Date Range Generation:
   - Creates complete date sequence
   - Respects detected sampling interval
   - Handles timezone considerations

3. Data Interpolation:
   - Implements advanced interpolation methods
   - Considers variable characteristics
   - Maintains data integrity

**Output Files:**
- `data_completa.parquet`: Complete dataset with all missing values filled
- `fechas_faltantes.parquet`: Record of all added dates and interpolated values

### 3. Anomaly Detection Module (falla_mediciones.py)
Implements advanced anomaly detection and correction.

**Features:**
- Multi-method anomaly detection
- Neural network prediction
- Correlation analysis
- Value range validation

**Detection Methodology:**
1. Temporal Analysis:
   - Calculates expected value variations
   - Identifies abnormal changes
   - Considers sampling frequency

2. Correlation Analysis:
   - Identifies strongly correlated variables
   - Uses correlation for validation
   - Implements correlation-based correction

3. Neural Network Prediction:
   - Trains on historical data
   - Predicts expected values
   - Validates measurements

4. Value Range Validation:
   - Enforces variable-specific constraints
   - Handles negative values appropriately
   - Implements value range correction

**Output Files:**
- `fallas_detectadas.parquet`: Detailed record of all detected anomalies
- `data_corregida.parquet`: Final corrected dataset
- `data_corregida.csv`: CSV version of corrected data

## Technical Requirements

### Software Requirements
- Python 3.8 or higher
- Required Python packages:
  ```bash
  pandas>=1.3.0
  numpy>=1.20.0
  scikit-learn>=0.24.0
  tensorflow>=2.6.0
  pyarrow>=3.0.0
  ```

### Hardware Requirements
- Minimum 8GB RAM
- 10GB free disk space
- Multi-core processor recommended

## Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Prepare your data:
   - Ensure `data.parquet` is in the working directory
   - Verify data format and structure

2. Execute the system:
   ```bash
   python variables.py
   python data_incompleta.py
   python falla_mediciones.py
   ```

3. Follow the interactive prompts in `variables.py`

4. Review the generated files:
   - Check `fallas_detectadas.parquet` for detected anomalies
   - Verify corrections in `data_corregida.parquet`
   - Use `data_corregida.csv` for compatibility with other tools

## File Formats

### Parquet Files
- Optimized for large datasets
- Maintains data types
- Efficient storage and retrieval
- View using Parquet Viewer or similar tools

### CSV Files
- Compatible with most tools
- Human-readable format
- Suitable for smaller datasets

### Pickle Files
- Stores Python objects
- Used for configuration
- Not human-readable

## Best Practices

1. Data Preparation:
   - Ensure consistent timestamp format
   - Verify numeric data types
   - Check for obvious data errors

2. Variable Selection:
   - Select related variables together
   - Consider process knowledge
   - Balance between completeness and performance

3. Date Range Selection:
   - Include sufficient historical data
   - Consider process cycles
   - Account for seasonal variations

4. Result Validation:
   - Review detected anomalies
   - Verify corrections
   - Check data consistency

## Troubleshooting

Common issues and solutions:

1. Memory Errors:
   - Reduce selected variables
   - Split date range into smaller chunks
   - Increase system memory

2. Performance Issues:
   - Use fewer variables
   - Reduce date range
   - Optimize system resources

3. Data Format Errors:
   - Verify Parquet file structure
   - Check timestamp format
   - Validate numeric data

## Support

For technical support:
- Email: [support-email]
- Documentation: [documentation-url]
- Issue Tracker: [issue-tracker-url]

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Industrial Process Experts
- Data Science Team
- Open Source Community 