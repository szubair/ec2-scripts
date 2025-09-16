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
    "Ticket Close Time",
    "Fulfilment Time"
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
            df = pd.read_excel(file_path, header=14)

            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                return f"Error: The following required columns are missing from the Excel sheet: {', '.join(missing_cols)}"

            df['TerminalId'] = df['TerminalId'].astype('Int64')

            filtered_df = df[df['Ticket Type'].str.contains(ticket_type, case=False, na=False)]
            
            if filtered_df.empty:
                return f"""
                    <h1>No Records Found</h1>
                    <p>No records were found for the selected ticket type: '{ticket_type}'.</p>
                    <br><a href="/">Back to Home</a>
                """

            selected_df = filtered_df[REQUIRED_COLUMNS]

            # Convert date columns to datetime objects and round them to the nearest second
            selected_df['Last Update Date'] = pd.to_datetime(selected_df['Last Update Date']).dt.round('S')
            selected_df['Last Response Date'] = pd.to_datetime(selected_df['Last Response Date']).dt.round('S')

            # Split 'Last Update Date' into 'Ticket Open Date' and 'Ticket Open Time'
            selected_df['Ticket Open Date'] = selected_df['Last Update Date'].dt.date
            selected_df['Ticket Open Time'] = selected_df['Last Update Date'].dt.time

            # Split 'Last Response Date' into 'Ticket Close Date' and 'Ticket Close Time'
            selected_df['Ticket Close Date'] = selected_df['Last Response Date'].dt.date
            selected_df['Ticket Close Time'] = selected_df['Last Response Date'].dt.time
            
            # Calculate Fulfillment Time and round it to the nearest second
            selected_df['Fulfilment Time'] = selected_df['Last Response Date'] - selected_df['Last Update Date']
            
            final_df = selected_df.drop(columns=["Last Update Date", "Last Response Date"])
            final_df = final_df.rename(columns=RENAME_MAPPING)
            
            final_df = final_df[OUTPUT_COLUMNS]

            # Convert the final DataFrame to HTML
            final_html = final_df.head(100).to_html(classes='table table-striped')

            styled_html = f"""
                <style>
                    .table-striped th {{
                        text-align: center;
                    }}
                </style>
                <h1>Filtered Results for '{ticket_type}'</h1>
                <p>Showing the first 100 matching rows with selected and renamed columns.</p>
                {final_html}
                <br><a href="/">Back to Home</a>
            """

            return styled_html

        except Exception as e:
            return f"An error occurred: {e}"

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == '__main__':
    app.run(debug=True)
