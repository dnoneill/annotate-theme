from flask import Flask, jsonify
from flask import request, render_template
from flask_cors import CORS
import json, os, glob, requests
import base64
from settings import *
from bs4 import BeautifulSoup
import yaml
import re
import string, random

app = Flask(__name__)
CORS(app)

annotations = []
@app.route('/create_annotations/', methods=['POST'])
def create_anno():
    response = json.loads(request.data)
    data_object = response['json']
    origin_url = response['origin_url']
    list_file_path = get_list_filepath(data_object)
    lettersAndDigits = string.ascii_letters + string.digits
    annoid = ''.join(random.choice(lettersAndDigits) for i in range(20)).lower()
    data_object['@id'] = annoid
    updatelistdata(list_file_path, data_object, origin_url)
    file_path = os.path.join(filepath, data_object['@id']) + '.json'
    writeannos(file_path, data_object, origin_url)
    return jsonify(data_object), 201

@app.route('/update_annotations/', methods=['POST'])
def update_anno():
    response = json.loads(request.data)
    data_object = response['json']
    file_path = os.path.join(filepath, response['id']) + '.json'
    list_file_path = get_list_filepath(data_object)
    writeannos(file_path, data_object, response['origin_url'])
    newlist = updatelistdata(list_file_path, data_object, response['origin_url'])
    return jsonify(data_object), 201

@app.route('/delete_annotations/', methods=['DELETE', 'POST'])
def delete_anno():
    response = json.loads(request.data)
    id = response['id']
    deletefiles = [os.path.join(filepath, id) + '.json', os.path.join(search_filepath, id) + '.md']
    list_file_path = get_list_filepath(response['listuri'])
    listlength = updatelistdata(list_file_path, {'@id': id, 'delete':  True}, '')
    if listlength <= 0:
        deletefiles.append(list_file_path)
    delete_annos(deletefiles)
    return jsonify({"File Removed": True}), 201

@app.route('/write_annotation/', methods=['POST'])
def write_annotation():
    data = json.loads(request.data)
    json_data = data['json']
    file = filepath if data['type'] == 'annotation' else '_ranges'
    filename = os.path.join(file, data['filename'])
    if 'list' in json_data['@type'].lower() or 'page' in json_data['@type'].lower():
        for anno in json_data['resources']:
            single_filename = os.path.join(file, anno['@id'])
            writeannos(single_filename, anno, '')
    writeannos(filename, json_data, '')
    return request.data

def delete_annos(annolist):
    for anno in annolist:
        if github_repo == "":
            os.remove(anno)
        else:
            existing = github_get_existing(anno)
            data = createdatadict(anno, 'delete', existing['sha'])
            payload = {'ref': github_branch}
            requests.delete("{}/{}".format(github_url, anno), headers={'Authorization': 'token {}'.format(github_token)}, data=json.dumps(data), params=payload)

def get_list_filepath(data_object):
    if type(data_object) == str or type(data_object) == unicode:
        targetid = data_object
    elif 'on' in data_object.keys():
        targetid = data_object['on'][0]['full']
    else:
        targetid = data_object['target']['id']
    numbitems = [item for item in targetid.split('/') if bool(re.match('(?=.*[0-9]$)', item))]
    targetid = '-'.join(numbitems)
    targetid = targetid.split("#xywh")[0]
    listid = targetid.split('/')[-1].replace("_", "-").replace(":", "").replace(".json", "").replace(".", "")
    listfilename = "{}-list.json".format(listid)
    list_file_path = os.path.join(filepath, listfilename)
    return list_file_path

def github_get_existing(filename):
    full_url = github_url + "/{}".format(filename)
    payload = {'ref': github_branch}
    existing = requests.get(full_url, headers={'Authorization': 'token {}'.format(github_token)}, params=payload).json()
    return existing

def get_list_data(filepath):
    if github_repo == "":
        if os.path.exists(filepath):
            filecontents = open(filepath).read()
            jsoncontent = json.loads(filecontents.split("---\n")[-1])
            return jsoncontent
        else:
            return False
    else:
        existing = github_get_existing(filepath)
        if 'content' in existing.keys():
            content = base64.b64decode(existing['content']).split("---\n")[-1]
            jsoncontent = json.loads(content)
            return jsoncontent
        else:
            return False

def updatelistdata(list_file_path, newannotation, origin_url):
    listdata = get_list_data(list_file_path)
    newannoid = newannotation['@id']
    if listdata:
        try:
            listindex = listdata['resources'].index(filter(lambda n: n['@id'] == newannoid, listdata['resources'])[0])
            if 'delete' in newannotation.keys():
                del listdata['resources'][listindex]
            else:
                listdata['resources'][listindex] = newannotation
        except:
            if 'delete' not in newannotation.keys():
                listdata['resources'].append(newannotation)
    elif 'delete' not in newannotation.keys():
        listdata = create_list([newannotation], newannotation['@context'], origin_url, newannoid)
    writeannos(list_file_path, listdata, '')
    return len(listdata['resources'])

def writeannos(file_path, data_object, origin_url):
    if 'list' not in file_path and 'ranges' not in file_path:
        get_search(data_object, file_path, origin_url)
    if github_repo == '':
        writetofile(file_path, data_object)
    else:
        writetogithub(file_path, data_object)

def create_list(annotation, context, origin_url, id):
    if 'w3.org' in context:
        formated_annotation = {"@context":"http://www.w3.org/ns/anno.jsonld",
        "@type": "AnnotationPage", "id": "%s/%s-list.json"% (origin_url, id), "resources": annotation}
    else:
        formated_annotation = {"@context":"http://iiif.io/api/presentation/2/context.json",
            "@type": "sc:AnnotationList", "@id": "%s/%s-list.json"% (origin_url, id), "resources": annotation }
    return formated_annotation

def writetogithub(filename, annotation, yaml=False):
    full_url = github_url + "/{}".format(filename)
    sha = ''
    existing = github_get_existing(filename)
    if 'sha' in existing.keys():
        sha = existing['sha']
    anno_text = annotation if yaml else "---\nlayout: null\n---\n" + json.dumps(annotation)
    data = createdatadict(filename, anno_text, sha)
    response = requests.put(full_url, data=json.dumps(data),  headers={'Authorization': 'token {}'.format(github_token), 'charset': 'utf-8'})

def createdatadict(filename, text, sha):
    writeordelete = "write" if text != 'delete' else "delete"
    message = "{} {}".format(writeordelete, filename)
    data = {"message":message, "content": base64.b64encode(text), "branch": github_branch }
    if sha != '':
        data['sha'] = sha
    return data

def writetofile(filename, annotation, yaml=False):
    anno_text = annotation if yaml else "---\nlayout: null\n---\n" + json.dumps(annotation)
    with open(filename, 'w') as outfile:
        outfile.write(anno_text)

def get_search(anno, filename, origin_url):
    imagescr = '<iiif-annotation annotationurl="{}/{}" styling="image_only:true"></iiif-annotation>'.format(origin_url, filename.replace("_", ""))
    listname = get_list_filepath(anno).split('/')[-1]
    annodata_data = {'tags': [], 'layout': 'searchview', 'listname': listname, 'content': [], 'imagescr': imagescr, 'datecreated':'', 'datemodified': ''}
    if 'oa:annotatedAt' in anno.keys():
        annodata_data['datecreated'] = anno['oa:annotatedAt']
    if 'created' in anno.keys():
        annodata_data['datecreated'] = anno['created']
    if 'oa:serializedAt' in anno.keys():
        annodata_data['datemodified'] = anno['oa:serializedAt']
    if 'modified' in anno.keys():
        annodata_data['datemodified'] = anno['modified']
    annodata_filename = os.path.join(search_filepath, filename.split('/')[-1].replace('.json', '.md'))
    textdata = anno['resource'] if 'resource' in anno.keys() else anno['body']
    textdata = textdata if type(textdata) == list else [textdata]
    for resource in textdata:
        chars = BeautifulSoup(resource['chars'], 'html.parser').get_text() if 'chars' in resource.keys() else ''
        if chars and 'tag' in resource['@type'].lower():
            annodata_data['tags'].append(chars.encode("utf-8"))
        elif 'purpose' in resource.keys() and 'tag' in resource['purpose']:
            tags_data = chars if chars else resource['value']
            annodata_data['tags'].append(tags_data.encode("utf-8"))
        elif chars:
            annodata_data['content'].append(chars.encode("utf-8"))
        elif 'items' in resource.keys():
            field = 'value' if 'value' in resource['items'][0].keys() else 'chars'
            fieldvalues = " ".join([item[field].encode("utf-8") for item in resource['items']])
            annodata_data['content'].append(fieldvalues)
        elif 'value' in resource:
            annodata_data['content'].append(resource['value'])
    content = '\n'.join(annodata_data.pop('content'))
    annodata_yaml = "---\n{}---\n{}".format(yaml.dump(annodata_data), content)
    if github_repo == '':
        writetofile(annodata_filename, annodata_yaml, True)
    else:
        writetogithub(annodata_filename, annodata_yaml, True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
