#!/bin/bash
secret=$1
password=$(echo $1|base64 --decode)
echo $password
