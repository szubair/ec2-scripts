import pandas as pd
from flask import Flask, render_template, request
import os

app = Flask(__name__)

# Configure a temporary folder to store uploaded files
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Define the specific columns to display and their new names
RENAME_MAPPING = {
    "TerminalId": "Terminal ID",
    "Retailer Name": "Merchant Name",
    "TerminalClass": "Standard Merchant",
    "City": "City Name",
    "Within/Outside City": "Within Outside City",
    "Ticket Type": "Call Type Detail"
}

# Create a list of the required columns based on the dictionary keys, plus the date columns
REQUIRED_COLUMNS = list(RENAME_MAPPING.keys()) + ["Last Update Date", "Last Response Date"]

# Define the final output column order and names
OUTPUT_COLUMNS = [
    "Terminal ID",
    "Merchant Name",
    "Standard Merchant",
    "City Name",
    "Within Outside City",
    "Call Type Detail",
    "Ticket Open Date",
    "Ticket Open Time",
    "Ticket Close Date",
    "Ticket Close Time"
]

@app.route('/')
def index():
    """Renders the file upload and filter form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload, filters rows, selects columns, and renames headers."""

    if 'excel_file' not in request.files:
        return 'No file part'

    file = request.files['excel_file']
    ticket_type = request.form.get('ticket_type')

    if file.filename == '':
        return 'No selected file'

    if file and ticket_type:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        try:
            # Read the Excel file, specifying the header on the 15th row (index 14)
            df = pd.read_excel(file_path, header=16)

            # Check for missing columns before processing
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                return f"Error: The following required columns are missing from the Excel sheet: {', '.join(missing_cols)}"

            # Convert 'TerminalId' column to integer to remove '.0'
            df['TerminalId'] = df['TerminalId'].astype('Int64')

            # Filter the DataFrame based on a partial string match
            filtered_df = df[df['Ticket Type'].str.contains(ticket_type, case=False, na=False)]
            
            if filtered_df.empty:
                return f"""
                    <h1>No Records Found</h1>
                    <p>No records were found for the selected ticket type: '{ticket_type}'.</p>
                    <br><a href="/">Back to Home</a>
                """

            # Select and rename columns as before
            selected_df = filtered_df[REQUIRED_COLUMNS]

            selected_df['Last Update Date'] = pd.to_datetime(selected_df['Last Update Date'])
            selected_df['Last Response Date'] = pd.to_datetime(selected_df['Last Response Date'])

            selected_df['Ticket Open Date'] = selected_df['Last Update Date'].dt.date
            selected_df['Ticket Open Time'] = selected_df['Last Update Date'].dt.time
            selected_df['Ticket Close Date'] = selected_df['Last Response Date'].dt.date
            selected_df['Ticket Close Time'] = selected_df['Last Response Date'].dt.time
            
            final_df = selected_df.drop(columns=["Last Update Date", "Last Response Date"])
            final_df = final_df.rename(columns=RENAME_MAPPING)
            final_df = final_df[OUTPUT_COLUMNS]

            # Convert the final DataFrame to HTML
            final_html = final_df.head(100).to_html(classes='table table-striped')

            return f"""
                <h1>Filtered Results for '{ticket_type}'</h1>
                <p>Showing the first 100 matching rows with selected and renamed columns.</p>
                {final_html}
                <br><a href="/">Back to Home</a>
            """

        except Exception as e:
            return f"An error occurred: {e}"

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == '__main__':
    app.run(debug=True)
