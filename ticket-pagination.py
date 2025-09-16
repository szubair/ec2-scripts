import pandas as pd
from flask import Flask, render_template, request, session, redirect, url_for
import os
import secrets
import uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configure a temporary folder for uploaded and processed files
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PROCESSED_FOLDER'] = 'processed/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Define constants
RECORDS_PER_PAGE = 25
BUSINESS_HOURS_PER_DAY = 9

# Define the specific columns to display and their new names
RENAME_MAPPING = {
    "TerminalId": "Terminal ID",
    "Retailer Name": "Merchant Name",
    "TerminalClass": "Standard Merchant",
    "City": "City Name",
    "Within/Outside City": "Within Outside City",
    "Ticket Type": "Call Type Detail"
}
REQUIRED_COLUMNS = list(RENAME_MAPPING.keys()) + ["Last Update Date", "Last Response Date"]
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

def format_fulfilment_time(td):
    if pd.isna(td):
        return ""
    total_seconds = int(td.total_seconds())
    days = total_seconds // (24 * 3600)
    remaining_seconds = total_seconds % (24 * 3600)
    
    business_days = days * BUSINESS_HOURS_PER_DAY
    business_hours = business_days + (remaining_seconds // 3600)
    
    minutes = (remaining_seconds % 3600) // 60
    seconds = remaining_seconds % 60
    return f"{business_hours}:{minutes}:{seconds}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'excel_file' not in request.files:
        return 'No file part'
    file = request.files['excel_file']
    ticket_type = request.form.get('ticket_type')
    if file.filename == '':
        return 'No selected file'
    if file and ticket_type:
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(upload_path)
        try:
            df = pd.read_excel(upload_path, header=16)
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
            
            # Use unit='ms' to handle the timestamp format
            selected_df['Last Update Date'] = pd.to_datetime(selected_df['Last Update Date'], unit='ms').dt.round('S')
            selected_df['Last Response Date'] = pd.to_datetime(selected_df['Last Response Date'], unit='ms').dt.round('S')
            selected_df['Ticket Open Date'] = selected_df['Last Update Date'].dt.date
            selected_df['Ticket Open Time'] = selected_df['Last Update Date'].dt.time
            selected_df['Ticket Close Date'] = selected_df['Last Response Date'].dt.date
            selected_df['Ticket Close Time'] = selected_df['Last Response Date'].dt.time
            fulfilment_time_delta = selected_df['Last Response Date'] - selected_df['Last Update Date']
            selected_df['Fulfilment Time'] = fulfilment_time_delta.apply(format_fulfilment_time)
            final_df = selected_df.drop(columns=["Last Update Date", "Last Response Date"])
            final_df = final_df.rename(columns=RENAME_MAPPING)
            final_df = final_df[OUTPUT_COLUMNS]
            
            # Convert date and time columns to string format before saving to JSON
            final_df['Ticket Open Date'] = final_df['Ticket Open Date'].astype(str)
            final_df['Ticket Open Time'] = final_df['Ticket Open Time'].astype(str)
            final_df['Ticket Close Date'] = final_df['Ticket Close Date'].astype(str)
            final_df['Ticket Close Time'] = final_df['Ticket Close Time'].astype(str)

            # Generate a unique filename and save the DataFrame
            session_id = str(uuid.uuid4())
            temp_file_path = os.path.join(app.config['PROCESSED_FOLDER'], f'{session_id}.json')
            final_df.to_json(temp_file_path)
            
            # Store the unique ID and ticket type in the session
            session['session_id'] = session_id
            session['ticket_type'] = ticket_type
            
            return redirect(url_for('display_results', page=1))
        except Exception as e:
            return f"An error occurred: {e}"
        finally:
            if os.path.exists(upload_path):
                os.remove(upload_path)

@app.route('/results')
def display_results():
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    session_id = session.get('session_id')
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], f'{session_id}.json')
    
    if not os.path.exists(processed_path):
        return f"Error: Session data not found. Please re-upload the file."

    page = request.args.get('page', 1, type=int)
    
    # Read the DataFrame from the temporary file
    df = pd.read_json(processed_path)
    
    total_records = len(df)
    total_pages = (total_records + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE
    
    start = (page - 1) * RECORDS_PER_PAGE
    end = start + RECORDS_PER_PAGE
    
    paginated_df = df.iloc[start:end]
    
    table_html = paginated_df.to_html(classes='table table-striped')
    
    return render_template('results.html',
                           table_html=table_html,
                           ticket_type=session.get('ticket_type', 'N/A'),
                           page=page,
                           total_pages=total_pages,
                           total_records=total_records)

if __name__ == '__main__':
    app.run(debug=True)
