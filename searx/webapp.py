#!/usr/bin/env python

'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

(C) 2013- by Adam Tauber, <asciimoo@gmail.com>
'''

if __name__ == "__main__":
    from sys import path
    from os.path import realpath, dirname
    path.append(realpath(dirname(realpath(__file__))+'/../'))

from flask import Flask, request, flash, render_template, url_for, Response, make_response
from searx.engines import search, categories
from searx import settings
import json


app = Flask(__name__)
app.secret_key = settings.secret_key

opensearch_xml = '''<?xml version="1.0" encoding="utf-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
  <ShortName>searx</ShortName>
  <Description>Search searx</Description>
  <InputEncoding>UTF-8</InputEncoding>
  <LongName>searx meta search engine</LongName>
  <Url type="text/html" method="post" template="{host}">
    <Param name="q" value="{{searchTerms}}" />
  </Url>
</OpenSearchDescription>
'''

def render(template_name, **kwargs):
    global categories
    kwargs['categories'] = sorted(categories.keys())
    if not 'selected_categories' in kwargs:
        kwargs['selected_categories'] = []
        cookie_categories = request.cookies.get('categories', '').split(',')
        for ccateg in cookie_categories:
            if ccateg in categories:
                kwargs['selected_categories'].append(ccateg)
        if not len(kwargs['selected_categories']):
            kwargs['selected_categories'] = ['general']
    return render_template(template_name, **kwargs)

@app.route('/', methods=['GET', 'POST'])
def index():
    global categories
    if request.method=='POST':
        if not request.form.get('q'):
            flash('Wrong post data')
            return render('index.html')
        selected_engines = []
        selected_categories = []
        for pd_name,pd in request.form.items():
            if pd_name.startswith('category_'):
                category = pd_name[9:]
                if not category in categories:
                    continue
                selected_categories.append(category)
                selected_engines.extend(x.name for x in categories[category])
        if not len(selected_engines):
            cookie_categories = request.cookies.get('categories', '').split(',')
            for ccateg in cookie_categories:
                if ccateg in categories:
                    selected_categories.append(ccateg)
                    selected_engines.extend(x.name for x in categories[ccateg])
        query = request.form['q'].encode('utf-8')
        results = search(query, request, selected_engines)
        remember_categs = True if 'save' in request.form else False
        if request.form.get('format') == 'json':
            # TODO HTTP headers
            return json.dumps({'query': query, 'results': results})
        template = render('results.html', results=results, q=query.decode('utf-8'), selected_categories=selected_categories)
        resp = make_response(template)
        if remember_categs:
            resp.set_cookie('categories', ','.join(selected_categories))
        return resp
    return render('index.html')

@app.route('/favicon.ico', methods=['GET'])
def fav():
    return ''

@app.route('/opensearch.xml', methods=['GET'])
def opensearch():
    global opensearch_xml
    ret = opensearch_xml.format(host=url_for('index', _external=True))
    resp = Response(response=ret,
                status=200,
                mimetype="application/xml")
    return resp

if __name__ == "__main__":
    from gevent import monkey
    monkey.patch_all()

    app.run(debug        = settings.debug
           ,use_debugger = settings.debug
           ,port         = settings.port
           )
