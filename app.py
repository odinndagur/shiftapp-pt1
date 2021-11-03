from flask import Flask, request, abort, send_from_directory, send_file, render_template
import os
import camelot
import numpy as np
import pandas as pd
import json
import requests
import csv
from stuff import *

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/write")
def write():
    file = open(app.config["UPLOAD_FOLDER"] + "/text.txt", "w")
    file.write("dadadadada\n")
    file.write("blksdlkslkj fklj asfj klasf jklajsf \n")
    file.write("jlkajflksajlkfasjkljsl\n")
    return "done"

@app.route("/read")
def read():
    file = open(app.config["UPLOAD_FOLDER"] + "/text.txt", "r")
    content = file.read()
    print(content)
    return content

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
        f = request.files['file']
        filename = f.filename
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        return 'Succeeded!'

@app.route('/get', methods=['POST','GET'])
def uploadimages():
    file_names=[]
    curr_path=os.getcwd()
    inputpath = app.config['UPLOAD_FOLDER']
    files_in_dir=os.listdir(inputpath)
    # for file in file_names:
    #     if file.split('.')[-1] is in ['jpeg','png','jpg','pdf']:
    #         os.remove(file)
    # uploaded_files=request.files.getlist("files") 
    # for file in uploaded_files:  
    #     if file.filename.split('.')[-1] is in ['jpeg','png','jpg']:
    #         file.save(file.filename)
    # imagetopdf_obj=imagetopdf.Imagetopdf()
    # imagetopdf.convert()
    try:
        return send_from_directory(inputpath,files_in_dir[0],
                                             as_attachment=True)
    except Exception:
        abort(404)             

@app.route("/camelot", methods=['POST','GET'])
def c():
    # filenames = []
    outputpath = app.config["UPLOAD_FOLDER"] + '/out/'
    filepath = app.config['UPLOAD_FOLDER']
    files_in_dir = os.listdir(filepath)
    files_in_dir = [file for file in files_in_dir if '.pdf' in file]
    file = files_in_dir[0]
    # print(os.path.abspath(file))
    file = filepath + '/' + file
    cellinfo = []

    tables = camelot.read_pdf(file,pages='1-end')
    cellinfo = tablestocellinfo(tables)
    with open(outputpath + 'celldata1.json', 'w') as f:
        json.dump(cellinfo,f)

    with open(outputpath + 'celldata1.json') as f:
        cellinfo = [dict(x) for x in json.load(f)]
    # return cellinfo[0]
    docs = []

    # tables[0].col = tables[0].df.col + 1
    # tables[0].row = tables[0].df.row + 2

    # tables[1].col = tables[1].df.col + 1
    # tables[1].row = tables[1].df.row + 1
    csvout = cleanuptables(tables,docs)

    csvout.to_csv(outputpath + 'output.csv')
    temp_pdf = open(file, 'rb')
    files = {'pdffile': temp_pdf.read(),
            'jsonfile': open(outputpath + 'celldata1.json','rb')
            }
    r = requests.post('http://127.0.0.1:5001/uploader', files = files)
    print(r)

    if r.ok:
        cellinfo = r.json()['shifts']
    docs = []

    for cell in cellinfo:
        tables[cell['table']].df.iloc[cell['row']][cell['col']] = cell['text'] + cell['shifttype']
    #     return r.json()
    #     # return [dict(x) for x in r.json()]
    # else:
    #     return "Error uploading file!"
    # try:
    #     return send_from_directory(filepath + '/out/','output.csv',as_attachment=True)
    # except Exception:
    #     abort(404)
    for i in range(0,tables.n, 2):
        df = tables[i].df #even
        df2 = tables[i+1].df #odd

        df2 = df2.iloc[:,1:]
        df2.iloc[0,0] = "Starfsmaður"
        headers = df2.iloc[0]
        # headers.to_csv(out + "headers" + str(i+1) + ".csv")

        df = df.iloc[2: , 1:]
        df2 = df2.iloc[1: , :]

        df.index = df.index - 1

        df.columns = headers
        df2.columns = headers

        # df.dropna(how='all',axis=1)
        # df2.dropna(how='all',axis=1)

        total = df.append(df2, ignore_index = True)
        # total.to_csv(out + "vaktaplan" + str(int(i/2)) + ".csv")
        docs.append(total)

    first = docs[0]
    for i in range(len(docs)):
        if(i != 0):
            temp = docs[i].iloc[:,1:]
            first = pd.concat([first, temp], axis=1)

    csvout.to_csv(outputpath + 'output.csv')
    first.to_csv(outputpath + "ALLT.csv")
    try:
        return send_from_directory(outputpath,'ALLT.csv',as_attachment=True)
    except Exception:
        abort(404)
    return '1'


if __name__ == '__main__':     
    app.run(debug=True)