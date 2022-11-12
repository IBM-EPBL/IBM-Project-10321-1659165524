import requests
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import flask
from flask import request, render_template,session,redirect,url_for
from flask_cors import CORS
from flask_login import LoginManager, UserMixin
from flask_login import login_user, logout_user, current_user, login_required
from ibm_db import connect
from ibm_db import fetch_assoc
from ibm_db import exec_immediate
from ibm_db import tables
import joblib
import 


response=flask.Response()

# NOTE: you must manually set API_KEY below using information retrieved from your IBM Cloud account.
API_KEY = "bdcHCOVI3tUCe4yhhPmXYDEmizXF0RjYxL38GZGn3v6I"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey": API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]
header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}


app = flask.Flask(__name__, static_url_path='')
CORS(app)
app.secret_key="b'# \x1e\xc7z\xf4\xd9\xe0\xe3!m\xf1'"

##login_manager = LoginManager()
##login_manager.init_app(app)
##login_manager.login_view = 'Login'
    
try:
    print("Connecting")
    conn_string = str(os.get)  
    con=connect(conn_string,"","")
except:
    print("Unable to connect")

def results(command):

    ret = []
    result = fetch_assoc(command)
    while result:
        ret.append(result)
        result = fetch_assoc(command)
    return ret

@app.route('/', methods=['GET'])
def sendHomePage():
    return render_template('index.html')


@app.route('/register',methods=['GET','POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        sql1="select username from user1 where email='"+email+"'"
        try:
            rows = results(exec_immediate(con, sql1))
            if rows:
                return render_template('index.html',msg="Email Already Registered")
            else:
                sql2="insert into user1(username,email,password) values('"+username+"','"+email+"','"+password+"')"
                print("Hello")
                exec_immediate(con,sql2)
                return render_template('login.html')
        except:
            print("Failed")
    return render_template('index.html')


@app.route('/gotologin',methods=['GET','POST'])
def gotologin():
    return render_template('login.html')

@app.route('/login',methods=['GET','POST'])
def login():
    msg = ''
    
    if request.method == 'POST' and  'password' in request.form and 'email' in request.form:
        
        password = request.form['password']
        email = request.form['email']
        sql1="select * from user1 where email='"+email+"' and password='"+password+"'"
        try:
            rows = results(exec_immediate(con, sql1))
            print(rows[0]['USERNAME'])
            if rows:
                ##login_user(rows[0]['UID'])
                session['uid']=email
                session['uname']=str(rows[0]['USERNAME'])
                return redirect('/home')
            
            else:
                return render_template('login.html',msg='Email or Password is Incorrect')
        except:
            print("Failed")
        
        print('uid' in session)
    elif 'uid' not in session:
        return render_template("login.html")
        
    return render_template('login.html')


@app.route('/home')
def home():
    if 'uid' in session:
        return render_template('dataform.html',msg=session['uname'])
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('uid',None)
    print('uid' in session)
    return redirect(url_for('login'))

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.route('/predict', methods=['POST'])
def predictSpecies():
    age = float(request.form['age'])
    gender = float(request.form['gender'])
    tb = float(request.form['tb'])
    db = float(request.form['db'])
    ap = float(request.form['ap'])
    aa1 = float(request.form['aa1'])
    aa2 = float(request.form['aa2'])
    tp = float(request.form['tp'])
    a = float(request.form['a'])
    agr = float(request.form['agr'])
    
    
    
    X = np.array([[float(age),float(gender),float(tb),float(db),float(ap),float(aa1),float(aa2),float(tp),float(a),float(agr)]]);
    mc=joblib.load('mc1.pkl')
    scaled_x=mc.transform(X)
    X=scaled_x.tolist()
    payload_scoring = {"input_data": [{"field": [['age','gender','tb','db','ap','aa1','aa2','tp','a','agr']], "values": X}]}
    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/8216d53f-c157-4b9f-89af-174229f60e03/predictions?version=2022-11-11', json=payload_scoring,headers={'Authorization': 'Bearer ' + mltoken})
    print(response_scoring)
    predictions = response_scoring.json()
    predict = predictions['predictions'][0]['values'][0][0]
    print("Final prediction :",predict)
    
    # showing the prediction results in a UI# showing the prediction results in a UI
    return render_template('predict.html', predict=predict)    

@app.route('/history')
def history():
    if('uid' in session):
        email=session['uid']
        sql1="select * from history where email='"+email+"'"
        try:
            rows = results(exec_immediate(con, sql1))
            
            if rows:
                return render_template('history.html',rows=rows)
            
            else:
                return render_template('history.html')
        except:
            print("Failed")
    return render_template('index.html')
        

if __name__ == '__main__' :
    app.run(debug= False)
