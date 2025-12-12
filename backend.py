#backend  

from flask import Flask, jsonify, request, abort #importing the flask framwork tools to build interface 
import os  #to provide operating-system functionality like file presence checks 
import json  #to be able to read and write json data
from urllib.parse import unquote #to decode URL-encoded path parameters 

datafile = "media.json" #the file that stores all media data in JSON format
categories = {"Book", "Film", "Magazine"} #allowed media categories 

app = Flask(__name__) #creating the flask app

#to load stored media data from the JSON file
# if the file does not exist or is invalid, it creates/returns an empty dictionary 
def load_data():
    if not os.path.exists(datafile): #check if file exists
        #create initial empty store  (if file does not exist)
        with open(datafile, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False) #write empty dict
        return {} #empty return of in-memory data store
    #if file exists, attempt to load its contents
    with open(datafile, "r", encoding="utf-8") as f:
        try:
            data = json.load(f) #to parse JSON (examine)
            if not isinstance(data, dict): #ensuring its a dictionary
                return {} #if structure is invalid, return empty dict
            return data #to return loaded data 
        except json.JSONDecodeError:
            return {} #to return empty dict if json is corrupted

#saving the provided data dictionary back to the json file
def save_data(data):
    with open(datafile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False) #ovewrite file with updated data

# loading the initial data into in-memory store
media_store = load_data()

@app.route("/media", methods=["GET"])
def list_all_media(): #returns a list of all available media items that got stored in media_store
    return jsonify(list(media_store.values())), 200  #converting dict values to list and returning as JSON response


@app.route("/media/category/<path:category>", methods=["GET"])
def list_by_category(category): #returns all media items that belong to a specific category (category URL decoded for correct comparison)
    category = unquote(category) # decoding URL-encoded text

    filtered = [m for m in media_store.values() if m.get("category") == category] #filter media items by category requested and matching
    return jsonify(filtered), 200 #returning filtered list as JSON response


@app.route("/media/search", methods=["GET"])
def search_by_name():
    """
    Searches for media items with a specific name (CASE SENSITIVE).

    """
    name = request.args.get("name") #getting the 'name' query parameter from the request URL
    if not name: #if missing name parameter
        return jsonify({"error": "missing 'name' query parameter"}), 400
    item = media_store.get(name)
    if item:
        return jsonify([item]), 200
    else:
        return jsonify([]), 200

@app.route("/media/<path:name>", methods=["GET"])
def get_media(name): #Displaying the metadata of a specific media item

    name = unquote(name) #decoding URL part 
    item = media_store.get(name) #look it up in store
    if not item: #not found
        return jsonify({"error": "not found"}), 404
    return jsonify(item), 200 #return item metadata

@app.route("/media", methods=["POST"])
def create_media(): #creating new media item from json payload

    payload = request.get_json()

#extracting required fields from payload
    name = payload.get("name")
    publication_date = payload.get("publication_date")
    author = payload.get("author")
    category = payload.get("category")

    #ensuring all required fields exist
    if not (name and publication_date and author and category):
        return jsonify({"error": "missing fields; required: name, publication_date, author, category"}), 400

    # validating the date format
    from datetime import datetime
    try:
        datetime.strptime(publication_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "publication_date must be in format YYYY-MM-DD"}), 400

    #Unique key check (name uniqueness)
    if name in media_store:
        return jsonify({"error": "media with that name already exists"}), 400

#building the metadata object
    metadata = {
        "name": name,
        "publication_date": publication_date,
        "author": author,
        "category": category
    }
#storing new item in the in-memory dictionary
    media_store[name] = metadata
    save_data(media_store)  #syncing in-memory store to file
    return jsonify(metadata), 201 #return created item

@app.route("/media/<path:name>", methods=["DELETE"])
def delete_media(name):
    """
delete a specific media item by name
    """
    name = unquote(name) #decoding path 
    deleted = media_store.pop(name) #remove and return item
    save_data(media_store) #sync update to file
    return jsonify({"deleted": deleted}), 200 #respond with deleted item data

if __name__ == "__main__":
    # ensuring data file exists with valid JSON before starting 
    save_data(media_store)
    print("Starting backend on http://127.0.0.1:5000")
    app.run() #start flask app 
