import requests
import yaml
import os
import re
import json
from flask import Flask, url_for  # , abort
from datetime import datetime
app = Flask(__name__)

'''
    Note:
    My first of this sort of framework based web app / micro service thingys.
    I am sure to be "doing it wrong"(tm).

    This should sit on the web somewhere and you send it a string
    and it lets you know if it has found it registered somewhere.

    That is: yes/no.

    As such you do not even need to transmit pages
    ('cept humans will want them)

    http head requests and the returned status codes is enough.

    so that is where we will are. next we start pileing on the request forms
    and beautiful search results ...
    hopefully never aproaching the 1Meg page just to say "nope" a source does.

'''


def fetch_regurl():
    '''
        Reads in the local list of urls to ping
    '''
    # if not hasattr(session, 'regurl'):
    if os.path.isfile('registry_url.yaml'):
        with open('registry_url.yaml', 'r') as fh:
            regurl = yaml.load(fh)
    else:
        print("halp. halp. I've fallen and can't get up")
    return regurl


# maybe put in a different package and import?
regurl = fetch_regurl()


# just c&p from notebook likely needs to be less chatty
def fetch_go():
    '''
        Fetches  goc yaml if there is none yet for the
        current application context.
    '''
    gocurl = 'http://current.geneontology.org/metadata/db-xrefs.yaml'
    gocprefixfile = 'gocprefix.yaml'
    gocprefix = []
    # Tue, 01 Aug 2017 14:14:26 GMT   note see http://strftime.org/
    fmt = '%a, %d %b %Y %H:%M:%S GMT'
    response = requests.get(gocurl)
    if response.status_code == requests.codes.ok:
        gocxref = yaml.load(response.text)
        remote_last_modified = response.headers['Last-Modified']
        remote_datetime = datetime.strptime(remote_last_modified, fmt)
        gocprefix.append('# ' + str(remote_datetime))
        for db in gocxref:
            gocprefix.append(db['database'])
        # renew local cache
        with open(gocprefixfile, 'w') as fh:
            yaml.dump(gocprefix, fh)
    else:
        print(
            'ERROR ' + response.url + ' returned ' + str(response.status_code))
        print('Trying local cache')
        remote_datetime = None
        if os.path.isfile(gocprefixfile):
            with open(gocprefixfile, 'r') as fh:
                gocprefix = yaml.load(fh)
            local_datetime = gocprefix[0]
            print('Found local cache from: ', local_datetime)
        else:
            print('Error no local cache of ' + gocprefixfile + ' available')
            local_datetime = None

    return [word.lower() for word in gocprefix]


def fetch_cdlebi():
    cdlebi_url = 'https://n2t.net/e/cdl_ebi_prefixes.yaml'
    cdlebipfx = []
    # Last modified: 2017.08.01_08.28.20
    # fmt = '# Last modified: %Y.%m.%d_%H.%M.%S'
    cdlebi_file = 'cdl_ebi_prefixes.yaml'
    response = requests.get(cdlebi_url)
    if response.status_code == requests.codes.ok:
        cdlebiraw = response.text
        cdlebireg = yaml.load(cdlebiraw)
        # first_line = cdlebiraw[0:cdlebiraw.index('\n')]
        # remote_datetime = datetime.strptime(first_line, fmt)
    else:
        print(
            'ERROR ' + response.url + ' returned ' + str(response.status_code))
        print('Trying local cache')
        # remote_datetime = None
        if os.path.isfile(cdlebi_file):
            with open(cdlebi_file, 'r') as fh:
                cdlebireg = yaml.load(fh)
                # print('Found local cache from: ',local_datestamp)
        else:
            print('Error no local cache of ' + cdlebi_file + ' available')
            # local_datetime = None
    for reg in cdlebireg:
        cdlebipfx.append(reg['namespace'])
        if 'alias' in reg:  # TODO should I be including these?
            cdlebipfx.append(reg['alias'])

    return cdlebipfx


gocprefix = fetch_go()
cdlebiprefix = fetch_cdlebi()
# prefixes = union(gocprefix[1:], cdlebiprefix[1:])

# blurb to return when the string does not parse
howto = 'letter followed by one or more letters, digits, or dash(dot)'

dot_whinge = '''
    prefix accepted with prejudice.
    dot is best left delimiting trailing version numbers.
    please consider replacing dot with dash.
    Thanks,  The Management
'''


def sanitize(tainted):
    '''
        a letter followed a handful of alphanums, hyphen
        not including underscore or colon
        as they are expected to delimit the local id
        dots should be for trailing versions on the local id (but are not)
        spaces should get you shot.
        need at least two chars (would prefer more)
        limiting to 16 chars (would prefer less)

        :return: safer string or None
    '''
    penultimat = 32
    match = re.match(
        r'[a-zA-Z][0-9a-zA-Z.-]{1,' + str(penultimat) + '}', tainted)
    if not match:
        pfx = None
    else:  # limit to first acceptable part
        pfx = match.group(0)
    return pfx


@app.route('/')
def hello_world():
    route_path = url_for('ping', qrystr='XYZ')
    return '<h2>Prefix Ping!</h2><br>Usage: http://<host>%s<br>' % route_path


@app.route('/prefix/<string:qrystr>', methods=['GET'])
def ping(qrystr):
    pfx = sanitize(qrystr).lower()
    result = {'user_query': qrystr, 'hits': 0, 'miss': 0}
    if pfx is not None:
        result['accepted_prefix'] = pfx
        result['sources'] = {}
        if len(pfx) == len(qrystr):
            if re.search(r'\.', pfx) is not None:
                result['status'] = dot_whinge
            else:
                result['status'] = 'prefix accepted'

            result['sources']['GO'] = {
                'uri': 'http://current.geneontology.org/metadata/db-xrefs.yaml',
                'url': 'http://amigo2.berkeleybop.org/xrefs#'
            }
            if pfx in gocprefix:
                result['sources']['GO']['registered'] = True
                result['hits'] += 1
            else:
                result['sources']['GO']['registered'] = False
                result['miss'] += 1
            result['sources']['N2T'] = {
                'uri':  'https://n2t.net/e/cdl_ebi_prefixes.yaml',
                'url':  'http://identifiers.org/'}
            if pfx in cdlebiprefix:
                result['sources']['N2T']['registered'] = True
                result['hits'] += 1
            else:
                result['sources']['N2T']['registered'] = False
                result['miss'] += 1
            # hit the remote sites
            for reg in regurl:
                response = requests.head(regurl[reg] + pfx)
                result['sources'][reg] = {'url': regurl[reg]}
                if response.status_code == requests.codes.ok:
                    result['sources'][reg]['registered'] = True
                    result['hits'] += 1
                else:
                    result['sources'][reg]['registered'] = False
                    result['miss'] += 1

        else:
            # only accepting part of the beginning of the prefix to check
            result['status'] = 'prefix only partialy accepted'
            result['comment'] = howto
    else:
        # something very wrong with the input
        result['status'] = 'NOPE! query prefix NOT accepted'
        result['comment'] = howto

    return json.dumps(result)


@app.route('/refresh/', methods=['GET'])
def refresh():
    '''
    after I figure out where flask persist stuff
    (hint it is not flask.g nor flask.session)
    this will be made to make more sense
    '''
    # relying on side effects
    gocprefix = fetch_go()
    cdlebiprefix = fetch_cdlebi()

    return  # union(gocprefix[1:], cdlebiprefix[1:])
