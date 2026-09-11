from flask import Flask, request, render_template
from ..sql.test_explorer import TestExplorer

app = Flask(__name__)

sql_helper = TestExplorer()
sql_helper.define_classes()

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/hello/<username>')
def hello_user(username):
    return f'Hello {username}'

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        name = request.form['username']
        return f'Hello {name}, POST request received'
    return render_template('name.html')

@app.route('/getdata',methods=['GET','POST'])
def get_data():
    if request.method == 'POST':
        sn = request.form['serial_number']
        rev = request.form['revision']
        comparisons = request.form['num_comparisons']
        matchsubtype = request.form['match_subtype']
        lowdrive = request.form['low_drive']
        return f'{sn} {rev} {comparisons} {matchsubtype} {lowdrive}'
    return render_template('input.html')

if __name__ == '__main__':
    app.run()