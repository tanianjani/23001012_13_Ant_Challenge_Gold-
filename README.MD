
Gold Challenge For Data Processing and Modeling for hatespeech on Tweets

Folder Structure:
- assets: contains data support for this project
- attachments: when success hit with endpoint text-processing-file. It automatically generate folder and files db and visualization image with .jpeg extension
- docs: file .yml for swagger documentation

List of Endpoint:
- / : root endpoint, just dummy response get
- /text-processing-file : endpoint cleansing data file by uploading a file

Run App : (make sure no app running on port 5000)
python app.py

To access api docs:
http://localhost:5000/docs


nb: 
- default df list row that save to db is 100
can be adjust as needed.
- folder attachments will be excluded on repo.

