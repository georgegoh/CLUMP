#!${BASH_EXE}

wget -m -nH --convert-links --force-html --html-extension --page-requisites http://localhost:8010/
rsync -av --rsh=ssh /data/scratch/buildstatus/* build@ronin:/home/osgdc/www/build/.