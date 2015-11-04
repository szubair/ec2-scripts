#!/usr/bin/python
import re,sys,os,commands,csv,datetime

def get_elbnames():
  mylist = []
  output = commands.getoutput("aws elb describe-load-balancers --profile dev --query 'LoadBalancerDescriptions[*].[LoadBalancerName,DNSName]'")
  lines = output.splitlines()
  for each in lines:
    elb = []
    #print "Name: %s Dns: %s" % (each.split()[0], each.split()[1])
    elb.append(each.split()[0])
    elb.append(each.split()[1])
    mylist.append(elb)
  return mylist

def testit():
  elbs = get_elbnames()
  for elb,dns in elbs:
    print elb
  return None

def get_elbdetails():
  elbs = get_elbnames()
  elb_list = []
  #elbs = ['FacetServ-ElasticL-1IX15PH3VKRZP','cxp-listn-ElasticL-14GWYVSPC1O5P']
  for name,dns in elbs:
    mylist = []
    mylist.insert(0,name)
    mylist.insert(1,dns)
    #print "elbname: ", elb
    output = commands.getoutput("aws elb describe-load-balancers --profile dev --load-balancer-name %s" % name)
    for elbline in output.splitlines():
      if elbline.startswith('HEALTHCHECK'):
         healthcheck = elbline.split()[3]
         mylist.append(healthcheck)
      if elbline.startswith('INSTANCES'):
         instance = elbline.split()[1]
         mylist.append(instance)
    elb_list.append(mylist)
  return elb_list

def write_csvfile():
  info = get_elbdetails()
  rows = len(info)
  day = datetime.datetime.today()
  today = day.strftime('%Y%m%d')
  report_file = ''.join(['DevElb-', today,'.csv'])
  dir = "/home/ec2-user/sabeerz/cengage/reports"
  filename = os.path.join(dir, report_file)
  if os.path.exists(dir):
    with open(filename, 'wb') as fp:
       csv_writer = csv.writer(fp)
       for row in range(rows):
         cols = len(info[row])
         csv_writer.writerow([ info[row][col] for col in range(cols)])
    fp.close()
  return "Sucessfull"

#print testit()
print write_csvfile()
#print get_elbnames()
#print get_elbdetails()
