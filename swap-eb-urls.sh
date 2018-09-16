#!/bin/bash

#primary
p_id='e-xxxxxx'
p_cname='webapp.xxxxxxx.us-east-2.elasticbeanstalk.com'
p_ebenv=`echo $p_cname | cut -d. -f1`
echo "pri eb ename=$p_ebenv"
#seconday
s_id='e-xxxxx'


res_cname=`aws elasticbeanstalk describe-environments --environment-ids $p_id --output json | jq -r .'Environments[].CNAME'`
eb_pri_cname=`echo $res_cname | cut -d. -f1`
if [ $eb_pri_cname = $p_ebenv ]; then
   #swap the urls
   aws elasticbeanstalk swap-environment-cnames --source-environment-id $p_id --destination-environment-id $s_id
   res=`echo $?`
   if [ $res -eq 0 ]; then
      sleep 2
      echo "EB Env swap command successed!"
   fi
else
   echo "EB Env $res_cname is not correct(primary), deployment cannot continue..."
fi

