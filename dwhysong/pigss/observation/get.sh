cd /home/obs/dwhysong
scp dwhysong@aster:pigss/$1 .
rm -f pigss.targets
ln -s $1 pigss.targets
echo "To: karto@hcro.org, dwhysong@gmail.com" > tmp
echo "Subject: $1 is ready" >> tmp
echo "obs@strato ~/dwhysong % cat $1" >> tmp
cat $1 >> tmp
mail karto@hcro.org dwhysong@gmail.com < tmp
