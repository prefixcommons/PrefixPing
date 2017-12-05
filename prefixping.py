import requests
import yaml
import os
import stat
import re
import json
import logging
from flask import Flask, url_for  # , abort
from datetime import datetime
import email.utils as emut

# Tue, 01 Aug 2017 14:14:26 GMT
# note see http://strftime.org/
# fmt = r'%a, %d %b %Y %H:%M:%S GMT'
# using email.utils instead
app = Flask(__name__)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


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
        log.warrning("halp. halp. I've fallen and can't get up")
    return regurl


# maybe put in a different package and import?
regurl = fetch_regurl()


def remote_metadata(head_url):
    remote_date = None
    remote_size = -1
    try:
        response = requests.head(head_url, allow_redirects=True)
    except requests.exceptions.RequestException:
        True

    if response.status_code == requests.codes.ok:
        if 'last-modified' in response.headers:
            date_string = response.headers['last-modified']
            remote_date = datetime(*emut.parsedate(date_string)[:6])
        else:
            log.warning(
                'No "Last-Modified:" header for ' + response.url)
        if 'Content-Length' in response.headers:
            remote_size = response.headers['Content-Length']
        else:
            log.warning(
                'No "Content-Length:" header for ' + response.url)
    else:
        if response.status_code >= 500:
            log.error('Server Error: ' + str(response.status_code))
        else:
            log.error(
                response.url + ' returned ' + str(response.status_code))
    return [remote_date, remote_size]


def local_metadata(pth):
    local_date = None
    local_size = -1
    if os.path.isfile(pth):
        local_date = datetime.fromtimestamp(
            os.stat(pth)[stat.ST_MTIME])
        local_size = os.stat(pth)[stat.ST_SIZE]
    return [local_date, local_size]


def read_yaml_array(fname, arr):
    if os.path.isfile(fname):
        with open(fname, 'r') as fh:
            arr = yaml.load(fh)
        local_datetime = arr[0]
        log.info('Found local cache from: ', local_datetime)
    else:
        log.error("Cannot open " + fname)
    return arr


def fetch_prefix(lcl_file, rmt_url, process_raw):
    '''
    Fetches  yaml
        if the local cache is more than  day old
            check if the remote is newer
            if so use and refresh cache
        otherwise use local cache
    '''

    result_array = []

    # check local cache
    (local_date, local_size) = local_metadata(lcl_file)

    # is cache more than a day old?
    if local_date is None or (datetime.now() - local_date).days > 0:
        (remote_date, remote_size) = remote_metadata(rmt_url)
        # has the remote been updated ?
        if local_date is None or remote_date is not None and remote_date > local_date:
            log.info("Remote newer")
            log.info('Fetching: ' + rmt_url)
            try:
                response = requests.get(rmt_url)
            except requests.exceptions.RequestException:
                True
            #  the happy path
            if response.status_code == requests.codes.ok:
                rawyaml = yaml.load(response.text)
                rmt_pth = rmt_url.split('/')
                rmt_file = rmt_pth[len(rmt_pth)-1]  # last on path
                log.info('renewing local copy of %s', rmt_file) 
                with open(rmt_file, 'w') as fh:
                        yaml.dump(result_array, fh)
                # remote_datetime = datetime.strptime(remote_date, fmt)
                result_array.append('# ' + str(remote_date))
                # source specific
                result_array = process_raw(rawyaml, result_array)
                log.info('renewing local ptrfix cache %s', lcl_file) 
                with open(lcl_file, 'w') as fh:
                        yaml.dump(result_array, fh)
            else:  # fetch remote failed
                log.error(
                    'ERROR ' + response.url + ' returned ' +
                    str(response.status_code))
                log.info('Trying local cache')
                result_array = read_yaml_array(lcl_file, result_array)
        else:
            log.info('Remote is not newer than ' + lcl_file)
            result_array = read_yaml_array(lcl_file, result_array)
    else:  # cache is fresh
        log.info('Cache ' + lcl_file + ' is less than a day old')
        result_array = read_yaml_array(lcl_file, result_array)

    # result_array is a list for go but a dict for cdl ??
     
    return [word.lower() for word in result_array]


# get the GO prefixes refreshing local cache as needed
# specific GO yaml helper f(x)
def go_proc_raw(rawyaml, rstarr):
    for db in rawyaml:
        rstarr.append(db['database'])
    return rstarr

# till geneontology file is fixed
# gocurl = 'http://current.geneontology.org/metadata/db-xrefs.yaml'
gocurl = 'https://raw.githubusercontent.com/geneontology/go-site/master/metadata/db-xrefs.yaml'
gocprefixfile = 'gocprefix.yaml'
gocprefix = fetch_prefix(gocprefixfile, gocurl, go_proc_raw)


# get the CDL prefixes refreshing local cache as needed
# specific CDL yaml helper f(x)
def cdl_proc_raw(rawyaml, rstarr):
    for reg in rawyaml:
        rstarr.append(reg['namespace'])
        if 'alias' in reg:  # TODO should I be including these?
            rstarr.append(reg['alias'])
    return rstarr


cdlebi_url = 'https://n2t.net/e/cdl_ebi_prefixes.yaml'
cdlebi_file = 'cdl_ebi_prefixes.yaml'
cdlebiprefix = fetch_prefix(cdlebi_file, cdlebi_url, cdl_proc_raw)

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
        a letter followed a handful of alphanumerics or hyphen
        not including underscore or colon
        as they are expected to delimit the local id
        dots should be for trailing versions on the local id (but are not)
        spaces should get you shot.
        need at least two chars (would prefer more)
        limiting to 32 chars (would prefer less)

        :return: safer string or None
    '''
    penultimat = 32
    match = re.match(
        r'[a-zA-Z][0-9a-zA-Z.-]{1,' + str(penultimat) + '}', tainted)
    if not match:
        pfx = None
    else:  # limit to first acceptable part
        pfx = match.group(0)
    return pfx.strip()


@app.route('/ping/')
def hello_world():
    route_path = url_for('/ping/prefix/', qrystr='XYZ')
    return '<h2>Prefix Ping!</h2><br>Usage: http://[host]/%s<br>' % route_path


@app.route('/ping/help/')
def help():
    return


@app.route('/ping/prefix/<string:qrystr>', methods=['GET'])
def ping(qrystr):
    qry = sanitize(qrystr)
    pfx = qry.lower()
    result = {'user_query': qrystr, 'hits': 0, 'miss': 0}
    if pfx is not None and pfx is not '':
        result['accepted_prefix'] = pfx
        result['sources'] = {}
        if len(pfx) == len(qrystr):
            if re.search(r'\.', pfx) is not None:
                result['status'] = dot_whinge
            else:
                result['status'] = 'prefix accepted'

            result['sources']['GO'] = {
                'uri': 'http://current.geneontology.org/metadata/db-xrefs.yaml',
                'url': 'http://amigo2.berkeleybop.org/xrefs#'}

            if pfx in gocprefix:
                result['sources']['GO']['registered'] = True
                result['hits'] += 1
                result['sources']['GO']['link'] = \
                    'http://amigo2.berkeleybop.org/xrefs#' + qry
            else:
                result['sources']['GO']['registered'] = False
                result['miss'] += 1

            result['sources']['N2T'] = {
                'uri':  'https://n2t.net/e/cdl_ebi_prefixes.yaml',
                'url':  'http://identifiers.org/'}
            if pfx in cdlebiprefix:
                result['sources']['N2T']['registered'] = True
                result['hits'] += 1
                result['sources']['N2T']['link'] = \
                    'http://identifiers.org/' + qry
            else:
                result['sources']['N2T']['registered'] = False
                result['miss'] += 1

            # hit the remote sites
            for reg in regurl:
                response = None
                try:
                    response = requests.head(
                        regurl[reg] + pfx, allow_redirects=True)
                except requests.exceptions.RequestException:
                    True  # that

                result['sources'][reg] = {
                    'url': regurl[reg]}
                if response.status_code == requests.codes.ok:
                    result['sources'][reg]['registered'] = True
                    result['hits'] += 1
                    result['sources'][reg]['link'] = str(regurl[reg]) + qry
                elif response.status_code > 499 or response.status_code < 400:
                    # non negative response
                    result['sources'][reg]['registered'] = \
                        'ERROR:' + str(response.status_code)
                    result['miss'] += 1
                else:  # non positive response
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


# TODO  this keepalive may not be needed with uwsgi parameter tweaks
@app.route('/ping/pong/', methods=['GET'])
def pong():
    (go_date, go_size) = local_metadata(gocprefixfile)
    (cdl_date, cdl_size) = local_metadata(cdlebi_file)
    # return nonzero if the app's local cache needs refreshing
    age = (datetime.now() - go_date).days | (datetime.now() - cdl_date).days
    return json.dumps({'cachedays': age})


@app.route('/ping/refresh/', methods=['GET'])
def refresh(go=gocprefix, cdl=cdlebiprefix):
    '''
    was an alternative method of refreshing caches but
    fetch_prefix()  now tries to refresh automatically
    and have not rewritten this with new methods
    '''

    return "{'implemented': 'False'}"


#  for local testing
if __name__ == "__main__":
    app.run(host='0.0.0.0')
