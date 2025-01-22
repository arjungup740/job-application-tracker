
### todo -- 

* tweak llm prompt & output
    * prompt strat
        * could go through and get all the emails that relate to an application, then a second call classifies them into confirmation, rejection, other
        * or just in one shot classify correctly
    * add thread id? sender email?

* not gettting full set off messages
* missing 3 jellyfish emails for example

* not being written in order of date received


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
* write it to the sheet
* decide on a reasonable output format
* decide what the sheet should have
run gmail search, then have llm discren what emails are relevant and what aren't based on snippets
a loop to feed in emails ids and collect the relevant data in an easy to use format
able to get the ids of the last n emails
able to access the data given each of those ids
dealing with auth stuff