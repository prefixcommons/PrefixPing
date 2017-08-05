# Prefix Ping

## Goal

Check a number of life science registries to see if a string has been claimed as a namespace.

### Specifics

Taking a two (hopefully not three) pronged approach

- Easy  
If a registry implements their service in a way that the question

  _Do you have a page for this __prefix__?_ 

  can be answered with http status codes then the base URL is added to
 the local [registry_url.txt](file://registry_url.txt)

    note: A couple of them return a _wrong_ (500 server error) code.  
    We should try to get them fixed.

- Okay  
 It the data file the site is generated with is available use the data directly.  
 Currently this is in the form of yaml files from GO and CDL/EBI
 and covers about 1600 prefixes (have not looked for overlap)
    [db-xrefs.yaml](http://current.geneontology.org/metadata/db-xrefs.yaml)  
    [cdl_ebi_prefixes.yaml](https://n2t.net/e/cdl_ebi_prefixes.yaml)

    Another could be added via a SPARQL query but unless there is a very cheap
way to tell if the remote has been updated it may not be worth it.
      

 - Screen scraping  
  is expensive and a pain hope to avoid as much as possible,
  so far only BioSharing falls here and I have an email in to try & rectify 
