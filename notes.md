
### todo -- 

* package to run daily, grab the last several days and set it up to start running incrementally
    * fix sorting
    * dockerize
        


* cheaper way to extract/enrich with the other meta data rather than give it all to the llm
* still doesn't get things from the human recruiters like lauren at gartner

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
* file changes to get appending to work more smoothly
* remove timestamps
* getting 0, 1,2, etc as headers
* same filters in api and gmail ui don't yield the same results, but seems like can't fix this and still gets the relevant results
* not classified centraprise email as a listing
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

Dynamic sorting: If you need to sort the data dynamically as new values are added, you can use the SORT function in conjunction with cell references instead of hardcoding the range.