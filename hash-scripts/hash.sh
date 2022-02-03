#!/bin/bash

password=$1
secret=$(echo $1|base64)
echo $secret
