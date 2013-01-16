#!/bin/sh
rpmbuild -bb kernel.spec --with rhel5 --without dracut --define="_sourcedir `pwd`" --define="_builddir `pwd`" --define="_rpmdir `pwd`/rpm"
