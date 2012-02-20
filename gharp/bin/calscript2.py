
import os
import sys


#check command line parameters
if (len(sys.argv) <= 3):
    print "ERROR: enter 3 file names"
    sys.exit()

print "I'm going to make images"

#read command line parameters
vis=sys.argv[1]
cal1=sys.argv[2]
cal2=sys.argv[3]

#walshcat each file
visd=vis+"_diffwalsh"
viss=vis+"_samewalsh"
cal1d=cal1+"_diffwalsh"
cal1s=cal1+"_samewalsh"
cal2d=cal2+"_diffwalsh"
cal2s=cal2+"_samewalsh"

cmd="rm -r "+visd
os.system(cmd)
cmd="rm -r "+cal1d
os.system(cmd)
cmd="rm -r "+cal2d
os.system(cmd)
cmd="rm -r "+viss
os.system(cmd)
cmd="rm -r "+cal1s
os.system(cmd)
cmd="rm -r "+cal2s
os.system(cmd)

cmd="walshcat "+vis
os.system(cmd)
cmd="walshcat "+cal1
os.system(cmd)
cmd="walshcat "+cal2
os.system(cmd)

#Visprep
visdV=vis+"-dw-VP"
vissV=vis+"-sw-VP"
cal1dV=cal1+"-dw-VP"
cal1sV=cal1+"-sw-VP"
cal2dV=cal2+"-dw-VP"
cal2sV=cal2+"-sw-VP"

cmd="rm -r "+visdV
os.system(cmd)
cmd="rm -r "+cal1dV
os.system(cmd) 
cmd="rm -r "+cal2dV
os.system(cmd)
cmd="rm -r "+vissV
os.system(cmd)
cmd="rm -r "+cal1sV
os.system(cmd) 
cmd="rm -r "+cal2sV
os.system(cmd)

cmd="java jmir.miriad.UVVisPrep vis="+visd+" out="+visdV+" discard=0 flux=0"
os.system(cmd)
cmd="java jmir.miriad.UVVisPrep vis="+viss+" out="+vissV+" discard=0 flux=0"
os.system(cmd)
cmd="java jmir.miriad.UVVisPrep vis="+cal1d+" out="+cal1dV+" discard=10 flux=5"
os.system(cmd)
cmd="java jmir.miriad.UVVisPrep vis="+cal1s+" out="+cal1sV+" discard=10 flux=5"
os.system(cmd)
cmd="java jmir.miriad.UVVisPrep vis="+cal2d+" out="+cal2dV+" discard=10 flux=5"
os.system(cmd)
cmd="java jmir.miriad.UVVisPrep vis="+cal2s+" out="+cal2sV+" discard=10 flux=5"
os.system(cmd)

#average data
cal1dVa=cal1dV+"-av"
cal1sVa=cal1sV+"-av"
cal2dVa=cal2dV+"-av"
cal2sVa=cal2sV+"-av"

cmd="rm -r "+cal1dVa
os.system(cmd)
cmd="rm -r "+cal1sVa
os.system(cmd)
cmd="rm -r "+cal2dVa
os.system(cmd)
cmd="rm -r "+cal2sVa
os.system(cmd)

cmd="uvaver vis="+cal1dV+" interval=30 out="+cal1dVa
os.system(cmd)
cmd="uvaver vis="+cal1sV+" interval=30 out="+cal1sVa
os.system(cmd)
cmd="uvaver vis="+cal2dV+" interval=30 out="+cal2dVa
os.system(cmd)
cmd="uvaver vis="+cal2sV+" interval=30 out="+cal2sVa
os.system(cmd)

#Delay prep
cal1dVaD=cal1dVa+"-DP"
cal1sVaD=cal1sVa+"-DP"
cal2dVaD=cal2dVa+"-DP"
cal2sVaD=cal2sVa+"-DP"

cmd="rm -r "+cal1dVaD
os.system(cmd)
cmd="rm -r "+cal1sVaD
os.system(cmd)
cmd="rm -r "+cal2dVaD
os.system(cmd)
cmd="rm -r "+cal2sVaD
os.system(cmd)


cmd="java jmir.miriad.UVDelayPrep vis="+cal1dVa+" out="+cal1dVaD
os.system(cmd)
cmd="java jmir.miriad.UVDelayPrep vis="+cal1sVa+" out="+cal1sVaD
os.system(cmd)
cmd="java jmir.miriad.UVDelayPrep vis="+cal2dVa+" out="+cal2dVaD
os.system(cmd)
cmd="java jmir.miriad.UVDelayPrep vis="+cal2sVa+" out="+cal2sVaD
os.system(cmd)

#uvcat
calsd=vis+"-cals-dw-mf"
calss=vis+"-cals-sw-mf"

cmd="rm -rf "+calsd
os.system(cmd)
cmd="rm -rf "+calss
os.system(cmd)

cmd="uvcat vis="+cal1dVaD+","+cal2dVaD+" out="+calsd
os.system(cmd)
cmd="uvcat vis="+cal1sVaD+","+cal2sVaD+" out="+calss
os.system(cmd)


#mfcal
cmd="mfcal vis="+calsd+" edge=100 refant=1 interval=60,240,999 select=-auto"
os.system(cmd)
cmd="mfcal vis="+calss+" edge=100 refant=1 interval=60,240,999 select=-auto"
os.system(cmd)


