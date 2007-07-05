#${BASH}
SOURCE_PATH=${CMAKE_SOURCE_DIR}
DEVEL_PATH=${CMAKE_BINARY_DIR}
if [ -f ${KUSU_ROOT}/bin/kusudevenv.sh ]; then
  source ${KUSU_ROOT}/bin/kusudevenv.sh
else
  (cd ${CMAKE_BINARY_DIR} && cmake ${CMAKE_SOURCE_DIR} && make && source ${KUSU_ROOT}/bin/kusudevenv.sh)
fi
ec=0
for i in `find $SOURCE_PATH/src/modules -name CMakeLists.txt`; do
  module_dir=`dirname $i | sed "s%$SOURCE_PATH/%%"`; #echo $module_dir
  module_name=`basename $module_dir`; #echo $module_name
  module_author=`svn info $SOURCE_PATH/$module_dir | grep "Last Changed Author"`; #echo $module_author
  test_dir=`find $DEVEL_PATH/$module_dir -type d -name test`; #echo $test_dir
  if [ -d "$test_dir" ]; then
   echo "Kusu Module Name: $module_name"
   svn info $SOURCE_PATH/$module_dir
   for j in `find $test_dir -type f -name "*.py"`; do #echo $j
    echo "running `basename $j` ..."
    #if [ $module_name != "partitiontool" ]; then
     nosetests -v -w $test_dir `basename $j`
     if [ $? -ne 0 ]; then
       $ec=$?
     fi
    #fi
    echo
   done
  fi
done
exit $ec