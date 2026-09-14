from flask import Flask, request, render_template, redirect
from .test_explorer import TestExplorer
from .update_script import sync_database
import logging

app = Flask(__name__)

sql_helper = TestExplorer()
sql_helper.define_classes()

logging.basicConfig(
    filename=r"W:\durant\github\engineer\snd\sql\app.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

@app.route('/hello/<username>')
def hello_user(username):
    return f'Hello {username}'

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        name = request.form['username']
        return f'Hello {name}, POST request received'
    return render_template('name.html')

@app.route('/lazy',methods=['GET','POST'])
def lazy():
    if request.method == 'POST':
        url = request.form['url']
        split = url.split('/')
        sn1 = split[-3].replace('%20',' ')
        sn2 = split[-2].replace('%20',' ')
        rev = split[-1][0]

        return redirect(f'/{sn1}/{sn2}/{rev}', 301)

@app.route('/',methods=['GET','POST'])
def homepage():
    if request.method == 'POST':
        sn1 = request.form['serial_number']
        sn2 = request.form['serial_number_2']
        rev = request.form['revision']
        comparisons = int(request.form['num_comparisons'])
        matchsubtype_string = request.form['match_subtype']
        lowdrive_string = request.form['low_drive']

        if matchsubtype_string == "True":
            matchsubtype=True
        else:
            matchsubtype=False

        if lowdrive_string == "True":
            lowdrive=True
        else:
            lowdrive=False

        plot_array = sql_helper.generate_approval_plots(\
            sn1, \
            sn2, \
            rev, \
            matchsubtype, \
            lowdrive, \
            comparisons)

        my_band,my_type,my_arch,my_subtype = sql_helper.get_attributes_from_sn(sn1, sn2)

        html_plots = [plot.to_html(full_html=False,auto_play=False) for plot in plot_array]

        return render_template('plots.html',sn1=sn1, sn2=sn2, rev=rev, html_plots=html_plots,\
            band=my_band,\
            type=my_type,\
            arch=my_arch,\
            subtype=my_subtype)


    return render_template('home.html',\
     test_count = sql_helper.get_test_count(),\
     table_data=sql_helper.get_newest_testsets())

@app.route('/reload')
def reload():
    sync_database(sql_helper)
    return redirect('/')

@app.route('/<sn1>/<sn2>/<rev>')
def getdata_simple(sn1,sn2,rev):
    plot_array = sql_helper.generate_approval_plots(\
    sn1, \
    sn2, \
    rev, \
    True, \
    True, \
    5)

    my_band,my_type,my_arch,my_subtype = sql_helper.get_attributes_from_sn(sn1, sn2)

    available_revs = sql_helper.get_revs_from_sn(sn1, sn2)

    html_plots = [plot.to_html(full_html=False,auto_play=False) for plot in plot_array]

    return render_template('plots.html',sn1=sn1, sn2=sn2, rev=rev, html_plots=html_plots,\
        band=my_band,\
        type=my_type,\
        arch=my_arch,\
        subtype=my_subtype,\
        available_revs = available_revs)

@app.route('/getdata',methods=['GET','POST'])
def getdata():
    if request.method == 'POST':
        sn = request.form['serial_number']
        sn2 = request.form['serial_number_2']
        rev = request.form['revision']
        comparisons = int(request.form['num_comparisons'])
        matchsubtype_string = request.form['match_subtype']
        lowdrive_string = request.form['low_drive']

        if matchsubtype_string == "True":
            matchsubtype=True
        else:
            matchsubtype=False

        if lowdrive_string == "True":
            lowdrive=True
        else:
            lowdrive=False

        plot_array = sql_helper.generate_approval_plots(\
            sn, \
            sn2, \
            rev, \
            matchsubtype, \
            lowdrive, \
            comparisons)

        my_band,my_type,my_arch,my_subtype = sql_helper.get_attributes_from_sn(sn, sn2)

        html_plots = [plot.to_html(full_html=False,auto_play=False) for plot in plot_array]

        return render_template('plots.html',html_plots=html_plots,\
            band=my_band,\
            type=my_type,\
            arch=my_arch,\
            subtype=my_subtype)

    return render_template('input.html')