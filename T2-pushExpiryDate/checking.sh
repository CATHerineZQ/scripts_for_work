#!/bin/bash

FILE=/home/czhou/T2-pushExpiryDate/trigger.txt   
if [ -f $FILE ]
then 
    #Do what you want if file exists
    echo found
else
    /home/czhou/T2-pushExpiryDate/checking.sh | at now + 1 minute
fi