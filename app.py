import re
import pandas as pd
import numpy as np
import sqlite3
import matplotlib
matplotlib.use('agg') # add this so we can use GUI matlib outside main thread macOS using non-interactive
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import os

# Import for flask
from flask import Flask, jsonify
from flask import request
from flasgger import Swagger, LazyJSONEncoder
from flasgger import swag_from


app = Flask(__name__)

# Set Flask's JSON encoder to LazyJSONEncoder
app.json_encoder = LazyJSONEncoder

# Swagger template with standard strings
swagger_template = {
    "info": {
        "title": "Api Documentation for Data Processing and Modeling For Hatespeech on Tweets",
        "version": "1.0.0",
        "description": "Dokumentasi Api untuk Data Processing dan Modeling Pada Tweets",
    },
    "host": "127.0.0.1:5000",  # You can set the host directly here
}
# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "docs",
            "route": "/docs.json",
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/",
}
# Initialize Swagger
swagger = Swagger(app, template=swagger_template, config=swagger_config)

# Import assets data to df
df_abusive = pd.read_csv('assets/abusive.csv')
df_kamlay = pd.read_csv('assets/new_kamusalay.csv', encoding='latin-1', header=None)
df_kamlay.columns=["tidak baku", "baku"]


# List endpoint apis
@swag_from("docs/hello_world.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def hello_world():
    json_response = {
        'status_code' : 200,
        'description' : "Hi, Welcome to this Gold Challenge Project",
        'data' : 'Hello World'
    }

    response_data = jsonify(json_response)
    return response_data


@swag_from("docs/processing_file.yml", methods=['POST'])
@app.route('/text-processing-file', methods=['POST'])
def text_processing_file():
    global file_df
    files_data = request.files
    input_file = files_data.get('file')    
    # Add data input file to file_df, with spesific setting and rows default:100
    file_df = pd.read_csv(input_file, encoding='latin-1', nrows=100)

    # ================= Cleansing Part =================
    # Use only tweet columns and remove duplicate
    file_df = file_df[['Tweet']]
    file_df.drop_duplicates(inplace=True)
    # Create new column num of char and words from based tweet
    file_df['num_of_char'] = file_df['Tweet'].apply(len)
    file_df['num_of_words'] = file_df['Tweet'].apply(lambda x: len(x.split()))
    # Create function data cleansing with that replace all 
    # beside numbers words and space, to empty string. 
    # and using strip() function remove more spaces on first and end of tweet
    def data_cleansing(x):
        tweet = x
        cleaned_tweet = re.sub(r'[^a-zA-Z0-9 ]', '', tweet).strip()
        return cleaned_tweet
    # Create function to count abusive words that appears per tweet
    def data_abusive_cnt(x):
        matched_list = []
        for i in range(len(df_abusive)):
            for j in x.split():
                word = df_abusive['ABUSIVE'].iloc[i]
                if word==j.lower():
                    matched_list.append(word)
        return len(matched_list)

    # Create new column based on cleanse tweet that using function data cleansing and count data abusive
    file_df['cleaned_tweet'] = file_df['Tweet'].apply(lambda x: data_cleansing(x))
    file_df['num_of_char_clean'] = file_df['cleaned_tweet'].apply(len)
    file_df['num_of_words_clean'] = file_df['cleaned_tweet'].apply(lambda x: len(x.split()))
    file_df['num_of_abusive_words'] = file_df['cleaned_tweet'].apply(lambda x: data_abusive_cnt(x))


    # ================= Sqlite3 Part, Create and insert db and table =================
    # Check if the 'attachments' directory exists, and create it if it doesn't
    if not os.path.exists('attachments'):
        os.makedirs('attachments')        
    
    # Create or connect new db gold_ch_project and create new table file_df if not exists
    conn = sqlite3.connect('attachments/gold_ch_project.db')
    q_create_table = """
    CREATE TABLE IF NOT EXISTS file_df (Tweet varchar(255), num_of_char int, num_of_words int, cleaned_tweet varchar(255), num_of_char_clean int, num_of_words_clean int);
    """
    conn.execute(q_create_table)
    conn.commit()

    # Check if there's data already stored in table 
    cursor = conn.execute("SELECT COUNT(*) FROM file_df")
    num_rows = cursor.fetchall()
    num_rows = num_rows[0][0]    

    # Insert data into the 'file_df' table with same name column
    # if file_df is not None:
    #     file_df.to_sql('file_df', conn, if_exists='append', index=False)
    # conn.close()    
    #  Loop only if there's no data in num rows
    if num_rows == 0:
        for i in range(len(file_df)):
            tweet = file_df['Tweet'].iloc[i]
            num_of_char = int(file_df['num_of_char'].iloc[i])
            num_of_words = int(file_df['num_of_words'].iloc[i])
            cleaned_tweet = file_df['cleaned_tweet'].iloc[i]
            num_of_char_clean = int(file_df['num_of_char_clean'].iloc[i])
            num_of_words_clean = int(file_df['num_of_words_clean'].iloc[i])
    
            q_insertion = "INSERT INTO file_df (Tweet, num_of_char, num_of_words, cleaned_tweet, num_of_char_clean, num_of_words_clean) values (?,?,?,?,?,?)"
            conn.execute(q_insertion,(tweet,num_of_char,num_of_words,cleaned_tweet,num_of_char_clean,num_of_words_clean))
            conn.commit()   
    conn.close()    

    # ================= Data Visualization =================
    
    # Visualize numbers of abused words with barplot
    plt.figure(figsize=(10, 7))
    countplot = sns.countplot(data=file_df, x="num_of_abusive_words")
    for p in countplot.patches:
        countplot.annotate(format(p.get_height(), '.0f'), (p.get_x() + p.get_width() / 2., p.get_height()), ha='center',
                        va='center', xytext=(0, 10), textcoords='offset points')
    warnings.filterwarnings('ignore', category=FutureWarning)
    plt.title('Count of Estimated Number of Abusive Words')
    plt.xlabel('Estimated Number of Abusive Words')
    plt.savefig('attachments/new_countplot.jpeg')

    # Visualize num of cleanse words using boxplot
    plt.figure(figsize=(20,4))
    boxplot = sns.boxplot(data=file_df, x="num_of_words_clean")
    print()
    warnings.filterwarnings('ignore', category=FutureWarning)
    plt.title('Number of Words Boxplot (after tweet cleansing)')
    plt.xlabel('')
    plt.savefig('attachments/new_boxplot.jpeg')    


    # Export to new csv after data cleansing
    file_df.to_csv("attachments/data_cleanse.csv", index=False)  # Set index=False to exclude the index column

        
    # Print json response with data cleaned tweet
    json_response = {
        'status_code' : 200,
        'description' : 'File processing',
        'data' : list(file_df['cleaned_tweet'])
    }
    response_data = jsonify(json_response)
    return response_data


if __name__ == '__main__':
    app.run(debug = True)