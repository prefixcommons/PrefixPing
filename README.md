# Prefix Ping

## Goal

Check a number of life science registries to see if a string has been claimed as a namespace.

### Jupyter notebook
A remnant of initial exploration which can be safely ignored. 

### Specifics  

Taking a two (hopefully not three) pronged approach

- Easy  
If a registry implements their service in a way that the question  

  _Do you have a page for this __prefix__?_

  can be answered with http status codes then the base URL is added to
 the local [registry_url.txt](https://raw.githubusercontent.com/prefixcommons/PrefixPing/master/registry_url.yaml)

    note: A couple of them return a _wrong_ (500 server error) code.
    We should try to get them fixed.  
    _Update_ We have extended the 'short circuit Y/N' approach to return a more comprehensive report
    whether the prefix has been found before or not so return code matter much less now.   

- Okay  
 It the data file the site is generated from is available use that data directly.
 Currently this is in the form of yaml files from GO and CDL/EBI
 and covers about 1,000 prefixes (have not looked for overlap)
    [db-xrefs.yaml](http://current.geneontology.org/metadata/db-xrefs.yaml)
    [cdl_ebi_prefixes.yaml](https://n2t.net/e/cdl_ebi_prefixes.yaml)

    Another could be added via a SPARQL query but unless there is a very cheap
way to tell if the remote has been updated it may not be worth it.


 - Screen scraping  
  It is expensive and a pain; hope to avoid as much as possible,
  so far only one source falls here and I have an email in to try & rectify


# Service

Have a python/flask  ```prefixping.py``` microservice working.

## Start local flask server cli

 - export FLASK_APP=prefixping.py
 - export FLASK_DEBUG=1
 - flask run

should be running on
```http://127.0.0.1:5000/```


### API call is:
```http://<host>/prefix/foo```

returns a json blob with the source registries queried and the result of those query

### Filtering  

We want to promote sane prefixes, so as with xml Qnames
they must begin with a letter and not contain a colon.
Since CURIEs interchange colon with underscore for resolvability
prefixes should not contain underscores either.  

Dots are best left to delimit the version number at the end of a local-ID
but there are legacy identifiers (and schemes) using them within curie prefixes
now so they are grudging allowed.  

In terms of prefix length; one letter is too short, a whole line is too long.
Two letters is still pretty short but we have GO: (Gene Ontology)
looking through the ~600 I have access too, they average 7 or 8 characters
the longest is 33. which is where I am setting the initial size limit.  

Case, mixed case can improve readability and is encouraged but it cannot be
considered when deciding if a prefix is taken or exists. For sources we have
access to or influence with searching over lowercased prefixes will be most efficient.  

TODO: Still need to check/confirm behavior of remote systems we have no access to.
