#!/bin/bash

FILE=trigger.txt   
if [ -f $FILE ]
then 
    #Do what you want if file exists
    echo found
else
    checking2.sh | at now + 1 minute
fi

