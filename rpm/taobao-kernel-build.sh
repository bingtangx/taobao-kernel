#!/bin/bash
## prepare necessary packages for building
sudo yum -b current install asciidoc -y
sudo yum install xmlto rng-utils m4 python-devel perl-TimeDate binutils-devel zlib-devel elfutils-libelf-devel -y

## try to restart rngd to generate random number for building
sudo pkill -9 rngd
sudo rngd -r /dev/urandom

## prepare building
cd $1
echo Starting "$BUILD_NUMBER"th Taobao-kernel build.
python ./scripts/package.py --buildid $BUILD_NUMBER

## build
cd taobao-kernel-build
rpmbuild -bb  --rmsource *.spec --define="_rpmdir $1/rpm" --define="_builddir `pwd`" --define="_sourcedir $1/taobao-kernel-build" --define="_tmppath $1/rpm"

cd $1/rpm
find . -name "*.rpm"  -exec mv {} . \;
for mypk in `ls *.rpm`
do
	t_pk_l=${mypk//-/ }
	t_pk_array=($t_pk_l)
	ac=${#t_pk_array[*]}
	version=${t_pk_array[$ac-2]}
	echo $version > $1/rpm/$2-VER.txt
	buildnumber=${t_pk_array[$ac-1]}
        sf=`echo $buildnumber|awk -F'.' '{print "."$(NF-2)"."$(NF-1)"."$NF}'`
        buildnumber=${buildnumber/$sf/}
        echo $buildnumber >  $1/rpm/BUILDNO.txt
	break
done

