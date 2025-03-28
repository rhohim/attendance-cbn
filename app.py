from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import datetime
import io

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        return redirect(request.url)

    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
        # Read the files into DataFrames
        df_file1 = pd.read_excel(file1, header=1)
        df_file2 = pd.read_excel(file2, header=1)
        
        # Process the DataFrames
        df_final = pd.DataFrame(columns=['Name', 'Record date', 'Time in', 'Time out', 'Late Time'])
        date = datetime.date(1, 1, 1)
        check_in = datetime.time(8, 30, 0)
        check_out = datetime.time(18, 0, 0)

        df_date = df_file1['Record Date'].unique()
        for i in range(len(df_file2['First Name'])):
            for j in range(len(df_date)):
                df_result = df_file1[(df_file1['First Name'] == df_file2['First Name'][i]) & (df_file1['Record Date'] == df_date[j])]
                if df_result.empty:
                    Name = df_file2['First Name'][i]
                    Date = df_date[j]
                    timein = ""
                    timeout = ""
                    status = "no tapping"
                else:
                    time_in = df_result['Earliest Time'].loc[df_result.index[0]].split(":")
                    time_out = df_result['Latest Time'].loc[df_result.index[0]].split(":")
                    person_in = datetime.time(int(time_in[0]), int(time_in[1]), int(time_in[2]))
                    person_out = datetime.time(int(time_out[0]), int(time_out[1]), int(time_out[2]))

                    if person_in <= check_in:
                        status = ""
                    else:
                        datetime1 = datetime.datetime.combine(date, check_in)
                        datetime2 = datetime.datetime.combine(date, person_in)
                        status = str(datetime2 - datetime1)

                    Name = df_file2['First Name'][i]
                    Date = df_result['Record Date'].loc[df_result.index[0]]
                    timein = df_result['Earliest Time'].loc[df_result.index[0]]
                    timeout = df_result['Latest Time'].loc[df_result.index[0]]

                new_row = {'Name': Name, 'Record date': Date, 'Time in': timein, 'Time out': timeout, 'Late Time': status}
                new_df = pd.DataFrame([new_row])
                df_final = pd.concat([df_final, new_df], ignore_index=True)

        # Save the final DataFrame to a CSV file in memory
        output_file = io.StringIO()
        df_final.to_csv(output_file, encoding='utf-8-sig', index=False)
        output_file.seek(0)

        # Return the CSV file as an attachment
        return send_file(io.BytesIO(output_file.getvalue().encode()), 
                         download_name='Attendance-Cvox.csv', 
                         as_attachment=True, 
                         mimetype='text/csv')

    return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True)