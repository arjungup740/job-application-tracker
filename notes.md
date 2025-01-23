
### todo -- 

* cheaper way to extract/enrich with the other meta data rather than give it all to the llm 


* not gettting full set of messages -- missing 3 jellyfish emails for example
* not getting centraprise email classified as a listing


* the appends are in weird format, writes the header each time as well
* getting 0, 1,2, etc as headers
* package to run daily


### reference

https://stackoverflow.com/questions/75454425/access-blocked-project-has-not-completed-the-google-verification-process

### latest applications
goodparty rejection
captions rejection
better up
artemis
biorender
captions again
southgeeks
daydream
jellyfish
roomprice genie
electric mind
point
developers
adthena


### Done
* anytime we have something like "data scientist, product" we get "product" as a separate column. Those need to stay together
* could go through and get all the emails that relate to an application, then a second call classifies them into confirmation, rejection, other. This might lead to better classifications
* add thread id? sender email? the general From field?
* prompt strat
    * or just in one shot classify correctly
* write it to the sheet
* decide on a reasonable output format
* decide what the sheet should have
run gmail search, then have llm discren what emails are relevant and what aren't based on snippets
a loop to feed in emails ids and collect the relevant data in an easy to use format
able to get the ids of the last n emails
able to access the data given each of those ids
dealing with auth stuff