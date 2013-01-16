#!/bin/sh
rpmbuild -bb kernel.spec --define="_sourcedir `pwd`" --define="_builddir `pwd`" --define="_rpmdir `pwd`/rpm"
