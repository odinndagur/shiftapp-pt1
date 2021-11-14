from flask import Flask, request, abort, send_from_directory, send_file, render_template, jsonify
import os
import camelot
from flask.helpers import url_for
import numpy as np
import pandas as pd
import json
import requests
import csv

from werkzeug.utils import redirect
from stuff import *

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

outputpath = app.config['UPLOAD_FOLDER'] + '/out/'
ppl = []


def camelprocess(file):
    # filenames = []
    outputpath = app.config["UPLOAD_FOLDER"] + '/out/'
    filepath = app.config['UPLOAD_FOLDER']
    file = filepath + '/' + file
    cellinfo = []
    tables = camelot.read_pdf(file,pages='1-end')
    cellinfo = tablestocellinfo(tables)
    with open(outputpath + 'celldata1.json', 'w') as f:
        json.dump(cellinfo,f)
    with open(outputpath + 'celldata1.json') as f:
        cellinfo = [dict(x) for x in json.load(f)]
    docs = []
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
    return first

@app.route("/")
def index():
    files_in_dir = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'],''))#,'out/'))
    outputfiles = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'],'out/'))
    return render_template("index.html", inputfiles = files_in_dir, outputfiles = outputfiles)

@app.route("/home")
def home():
    files_in_dir = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'],''))#,'out/'))
    outputfiles = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'],'out/'))
    day = request.args.get('day')
    file = request.args.get('file')
    if not file:
        file = '11.12-10.01 Hátíðarplan nöfn leiðrétt.pdf.csv'
        # # filenames = []
        # filepath = app.config['UPLOAD_FOLDER']
        # files_in_dir = os.listdir(outputpath)
        # files_in_dir = [file for file in files_in_dir if '.csv' in file]
        # file = files_in_dir[0]
        # # print(os.path.abspath(file))

    ppl = []
    csv = pd.read_csv(outputpath + file)
    currentperson = -1
    shifts = []
    for p in csv.iloc[:,1]:
        ppl.append(p)
    person = request.args.get('person')
    if not person:
        person = ppl[0]
    if person:
        for i in range(len(csv.iloc[0,:])):
            if person in csv.iloc[i,1]:
                currentperson = i
        tempshifts = csv.iloc[currentperson,:].dropna()
        shifts = []
        for i in range(len(tempshifts)):
            if tempshifts.index[i][0].isdigit():
                shifts.append({'date':tempshifts.index[i],'time':tempshifts[i]})
    days = [str(day).replace('\n', ' ').strip() for day in csv.columns[1:] if day[0].isdigit()]
    data = {}
    if day:
        data['shifts'] = {}
        # day = request.args.get('day')
        day = day.split(' ')[0]
        for i in range(len(csv.columns)):
            col = csv.columns[i]
            if day in col:
                data['date'] = col
                for j in range(len(csv.iloc[:,i])):
                    shift = str(csv.iloc[j,i])
                    if shift[0].isdigit() and len(shift) > 3:
                        # print(shift)
                        name = csv.iloc[j,1]
                        # print(name)
                        shifttime = shift.split('\n')[0]
                        shifttype = shift.split('\n')[1]
                        # print(shifttime, shifttype)
                        # print(name,shift,shifttime,shifttype)
                        if not shifttype in data['shifts']:
                            data['shifts'][shifttype] = []
                        data['shifts'][shifttype].append(" ".join([name,shifttime]))
                        # print(data)
    
    return render_template("home.html", inputfiles = files_in_dir, outputfiles = outputfiles, ppl = ppl, shifts = shifts, person = person,days = days, dayshifts = data)

@app.route("/<file>")
def indexfile(file):
    if file:
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'],file,as_attachment=True)
        except Exception:
            abort(404)
        return file

@app.route('/base')
def base():
    return render_template('basetest.html')

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

# @app.route('/uploader', methods = ['GET', 'POST'])
# def upload_file():
#    if request.method == 'POST':
#         f = request.files['file']
#         filename = f.filename
#         f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
#         return 'Succeeded!'



@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
        f = request.files['file']
        filename = f.filename
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        return redirect(url_for('camelot',file = filename))



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
def camelot():
    file = request.args.get('file')
    if not file:
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


# @app.route("/camelot/<file>", methods=['POST','GET'])
# def camelot(file):
#     files_in_dir = os.listdir(outputpath)
#     tempname = file + '.csv'
#     if not tempname in files_in_dir:
#         plan = camelprocess(file)
#         session['currentfile'] = file
#         # csvout.to_csv(outputpath + 'output.csv')
#         plan.to_csv(outputpath + file + ".csv")
#         csv = plan.to_csv()
#     ppl = []
#     p = pd.read_csv(outputpath + file + ".csv")
#     for person in p.iloc[:,1]:
#         ppl.append(person)
#     return render_template("people.html", file = file,people=ppl)
#     # return render_template(first.to_html())
#     try:
#         return send_from_directory(outputpath,'ALLT.csv',as_attachment=True)
#     except Exception:
#         abort(404)
#     return '1'

@app.route("/days")
def days():
    file = request.args.get('file')
    # days = []
    csv = pd.read_csv(outputpath + file)
    days = [str(day).replace('\n', ' ').strip() for day in csv.columns[1:] if day[0].isdigit()]
    # print(days)
    return render_template("days.html", file = file, days = days)
    # count = len(csv.columns)

    # for i in range(count):
    #     day = csv.columns[i]
    #     shifts = csv.iloc[:,i].dropna()
    #     temp = []
    #     for j in range(len(shifts)):
    #         temp.append({
    #             shifts.iloc[j]                
    #         })
    #     days.append({
    #         'day':day,
    #         'shifts': temp
    #     })
    csv = pd.read_csv(outputpath + currentfile,index_col=1)

    t = csv.iloc[:,6].dropna()

    date = str(csv.columns[6]).replace('\n', ' ').strip()
    #print(date)
    data = {}
    data[date] = {}
    for j in range(1,len(csv)):
        t = csv.iloc[:,j].dropna()
        date = str(csv.columns[j]).replace('\n', ' ').strip()
        for i in range(len(t)):
            name = str(t.index[i]).strip()
            shift = str(t[i]).split('\n')
            shifttime = shift[0].strip()
            shifttype = shift[1].strip()
            if not shifttype in data[date]:
                data[date][shifttype] = []
            data[date][shifttype].append(name + ' ' + shifttime)
        for i in range(len(list(data[date]))):
            key = list(data[date])[i]
            values = list(data[date][key])
            #print(i,key,values)

        tempdata = dict([ (k, pd.Series(v)) for k,v in data[date].items() ])
        tt = [(k,pd.Series(v)) for k,v in data[date].items()]
        #print(dict(tt))
        #for k,v in data[date].items():
            #print(k,pd.Series(v),'\n')
        #for lol in tt:
            #print(lol, '\n')
        df = pd.DataFrame(dict([ (k, pd.Series(v)) for k,v in data[date].items() ]) )
        df.to_csv(outputpath + str(j) +  'testout.csv')
        # return jsonify(temp.to_dict(orient="records"))
    return render_template("days.html", days = df)

@app.route("/day/<day>")
def day(day):
    file = request.args.get('file')
    csv = pd.read_csv(outputpath + file,index_col=1)
    t = csv.iloc[:,6].dropna()
    data = {}
    data['shifts'] = {}
    # day = request.args.get('day')
    day = day.split(' ')[0]
    print(day)
    for i in range(len(csv.columns)):
        col = csv.columns[i]
        if day in col:
            data['date'] = col
            for j in range(len(csv.iloc[:,i])):
                shift = str(csv.iloc[j,i])
                if shift[0].isdigit() and len(shift) > 3:
                    name = csv.index[j]
                    shifttime = shift.split('\n')[0]
                    shifttype = shift.split('\n')[1]
                    # print(name,shift,shifttime,shifttype)
                    if not shifttype in data['shifts']:
                        data['shifts'][shifttype] = []
                    data['shifts'][shifttype].append(name + ' ' + shifttime)
                    # print(data)
    tempdata = dict([ (k, pd.Series(v)) for k,v in data['shifts'].items() ])
    df = pd.DataFrame(tempdata)
    df.to_csv(outputpath + 'testetsetesetsets.csv')
    return render_template("day.html", file = file, shifts = data)

@app.route("/people")
def people():
    file = request.args.get('file')
    person = request.args.get('person')
    ppl = []
    csv = pd.read_csv(outputpath + file)
    currentperson = -1
    shifts = []
    for p in csv.iloc[:,1]:
        ppl.append(p)
    if person:
        for i in range(len(csv.iloc[0,:])):
            if person in csv.iloc[i,1]:
                currentperson = i
        tempshifts = csv.iloc[currentperson,:].dropna()
        shifts = []
        for i in range(len(tempshifts)):
            if tempshifts.index[i][0].isdigit():
                shifts.append({'date':tempshifts.index[i],'time':tempshifts[i]})
        "lol"
    # else:
    #     return person
    return render_template("people.html",person = person,people=ppl,file = file,shifts = shifts)


@app.route("/csv/<file>")
def csv(file):
    # file = os.path.join(app.config['UPLOAD_FOLDER'],'out/',file)
    # return file
    # return redirect('/people?file=' + file)
    return redirect(url_for('people',file=file))

@app.route("/download/<file>")
def download(file):
    dir = ''
    inputfiles = os.listdir(app.config['UPLOAD_FOLDER'])
    outputfiles = os.listdir(outputpath)
    if file in inputfiles:
        dir = app.config['UPLOAD_FOLDER']
    if file in outputfiles:
        dir = outputpath
    try:
        return send_from_directory(dir,file,as_attachment=True)
    except Exception:
        abort(404)


if __name__ == '__main__':     
    app.run(host = "0.0.0.0",debug=True)