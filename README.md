# Prefix Ping

## Goal

Check a number of life science registeries to see if a string has been claimed as a namespace.

### Specifics

Taking a two (hopefully not three) pronged approach

- Easy  
If a registery implements their service in a way that the question

  _Do you have a page for this __prefix__?_ 

  can be answered with http status codes then the base URL is added to
 the local ```registry_url.txt```

- Okay  
 It the data file the site is generated with is available ise the data directly.  
 Currently this is in the form of yaml files from GO and CDL/EBI
 and covers about 1600 prefixes (have not looked for overlap)

 - Screen scraping  
  Hope to avoid as mych as possible,
  so far only BioSharing falls here and I have an email in to try & rectify 
