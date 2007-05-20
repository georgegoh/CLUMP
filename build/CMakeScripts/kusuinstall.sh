#!${BASH}
KUSU_MODULE="${KUSU_MODULE}"
if [ $KUSU_MODULE == "ON" ]
then
  if [ -d ${SETUPPY_PATH}/installdir/lib64 ] ; 
  then mkdir -p ${SETUPPY_PATH}/installdir/lib64/python/kusu ;
        if [ -d ${SETUPPY_PATH}/installdir/lib64/python${PYTHON_VERSION}/site-packages ];
        then
          cp -rf ${SETUPPY_PATH}/installdir/lib64/python${PYTHON_VERSION}/site-packages/* ${SETUPPY_PATH}/installdir/lib64/python/kusu/. ;
          rm -rf ${SETUPPY_PATH}/installdir/lib64/python${PYTHON_VERSION} ;
        fi
  else
        mkdir -p ${SETUPPY_PATH}/installdir/lib/python/kusu ;
        if [ -d ${SETUPPY_PATH}/installdir/lib/python${PYTHON_VERSION}/site-packages ];
        then
          cp -rf ${SETUPPY_PATH}/installdir/lib/python${PYTHON_VERSION}/site-packages/* ${SETUPPY_PATH}/installdir/lib/python/kusu/.
          rm -rf ${SETUPPY_PATH}/installdir/lib/python${PYTHON_VERSION} ;
        fi
  fi
else
  if [ -d ${SETUPPY_PATH}/installdir/lib64 ] ; 
  then mkdir -p ${SETUPPY_PATH}/installdir/lib64/python ;
        if [ -d ${SETUPPY_PATH}/installdir/lib64/python${PYTHON_VERSION}/site-packages ];
        then
          cp -rf ${SETUPPY_PATH}/installdir/lib64/python${PYTHON_VERSION}/site-packages/* ${SETUPPY_PATH}/installdir/lib64/python/. ;
          rm -rf ${SETUPPY_PATH}/installdir/lib64/python${PYTHON_VERSION} ;
        fi
  else
        mkdir -p ${SETUPPY_PATH}/installdir/lib/python ;
        if [ -d ${SETUPPY_PATH}/installdir/lib/python${PYTHON_VERSION}/site-packages ];
        then
          cp -rf ${SETUPPY_PATH}/installdir/lib/python${PYTHON_VERSION}/site-packages/* ${SETUPPY_PATH}/installdir/lib/python/. ;
          rm -rf ${SETUPPY_PATH}/installdir/lib/python${PYTHON_VERSION} ;
        fi
  fi
fi

mkdir -p ${SETUPPY_PATH}/installdir/doc
mv ${SETUPPY_PATH}/installdir/share/doc ${SETUPPY_PATH}/installdir/doc/${PROJECT_NAME}-${VERSION_STR}
mv ${SETUPPY_PATH}/installdir/doc ${SETUPPY_PATH}/installdir/share/.
if [ -d ${SETUPPY_PATH}/installdir/share/etc ] ;
then
  mv ${SETUPPY_PATH}/installdir/share/etc ${SETUPPY_PATH}/installdir/.
fi
cp -rf ${SETUPPY_PATH}/installdir/* ${KUSU_ROOT}/. ;
rm -rf ${SETUPPY_PATH}/installdir ;