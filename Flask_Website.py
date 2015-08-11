''' Program behind the website '''
#### FLASK RELATED LIBRARIES
import os
from flask import Flask,render_template,request,redirect,url_for,make_response,send_file, response
from functools import wraps
from pandas import read_csv
global download_filename,precision_dict_cat,precision_dict_subcat,unique_category,unique_subcategory,results
from preset_dictionaries import precision_dict_cat,precision_dict_subcat 
from featureextraction import*  ## Library to extract features from text data 
from Categories import*  ## Library to categorize data
from uniqueCategories import unique_category, unique_subcategory # Library with the list of unique catergories and subcategories
from upload_models import* 
from PrepareDisplay import generate_displayresults

### Upload the models and features
models, features, models_sub, features_sub = upload_modelsFeatures()

##
results={}
data=read_csv("Category_predicted.csv")
print "Allready loaded files: Starting server"


#############################

download_filename='Results.csv'
ALLOWED_EXTENSIONS = set(['csv'])
UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

##########PWD PART of the website #########

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'pebble'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


##############Other part of the website###############
@app.route('/')
#@app.route('/index')

@requires_auth
def index():
  return render_template("input_thefile.html")

## Categorization Page
@app.route('/categorize')
@requires_auth
def categorize():
  global unique_category,unique_subcategory  
  return render_template("input_textbox.html",unique_category=unique_category,unique_subcategory=unique_subcategory)
  
@app.route('/categorize',methods=['POST'])
def read_text():
    global results
    if request.form['btn']=='Send':
        description = request.form['Description']
        preset=request.form['Preset']
        results={}
        results['most_c'],results['second_c'],results['subcategory'],results['precision_most'],results['precision_second'],results['precision_sub']=compute_categories(description,preset)  
        return render_template("outputfromtextinput.html",description=description,preset=preset,results=results)

    elif request.form['btn']=='Find':
        category_select=request.form['category_select']
        subcategory_select=request.form['subcategory_select']
        display_results=generate_displayresults(data,category_select,subcategory_select) 
        return render_template("find_related_apps2.html",name='Crappy',display_results=display_results)
        
    elif request.form['btn']=='Find related apps':
        category_select=results['most_c']
        subcategory_select=results['subcategory']
        display_results=generate_displayresults(data,category_select,subcategory_select) 
        return render_template("find_related_apps2.html",name='Crappy',display_results=display_results)
  
#### Part of the page to upload a file with app description and dowload the categorized file

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
  #pull 'ID' from input field and store it
  if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = "results.csv"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
        
        else: 
            return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    data=read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    results = []
    if data.shape[1]>=3:
        for i in range(data.shape[0]):
            results.append(dict(idx=str(i+1).decode('iso-8859-1'), title=(str(data.ix[i,0])).decode('iso-8859-1'), preset=(str(data.ix[i,1])).decode('iso-8859-1'),
            desc=(str(data.ix[i,2])).decode('iso-8859-1'),categ=(str("car")).decode('iso-8859-1'),secondCateg=str("bicycle").decode('iso-8859-1')))
    else: 
        results.append(dict(idx=(str("no data")).decode('iso-8859-1'), title=(str("no data")).decode('iso-8859-1'), preset=(str("no data")).decode('iso-8859-1'),
      desc=(str("no data")).decode('iso-8859-1'),categ=(str("no data")).decode('iso-8859-1'),secondCateg=(str("no data")).decode('iso-8859-1')))
    with open("result", 'wb') as f:
        pickle.dump(results, f)
        f.close()
    return redirect(url_for('output2',filename="result"))

@app.route('/download')
def download():
    global download_filename
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], download_filename),as_attachment=True)
    
@app.route('/<filename>')    
def output2(filename):
    with open(filename, 'rb') as f:
        results = pickle.load(f)
    return render_template("try_inputwithoutput3.html", results = results)
    #return redirect(url_for('download',results=results))

app.run()    