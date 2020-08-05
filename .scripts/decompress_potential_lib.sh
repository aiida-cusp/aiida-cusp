#!/bin/sh

#
# VASP Potential Library Decompressor Tool
#

# Searches the present working directory (PWD) recursively for archive files
# of type '.tar.gz' and '.tgz'. Contents of the files will be extracted to
# their own (new) directories located in the top level directory from where
# this script is run (i.e. the PWD). Additionally, uncompress is run on all
# folders containing files of type POTCAR.Z

ARCHIVES="$(find $PWD -type f -regex ".*\.tar\.gz" -or -regex ".*\.tgz")"
for archive in $ARCHIVES; do
	full_path="$(realpath $archive)"
	# nested basename to remove either '.tar.gz' **and** '.tgz' suffixes
	archive_name="$(basename $(basename $archive '.tar.gz') '.tgz')"
	extract_folder="$PWD/$archive_name"
	# create dir and extract
	mkdir -p $extract_folder && tar -C $extract_folder -zxvf $full_path
	# check for possible LZW compressed potentials (Why VASP ... Why????)
	z_archives="$(find $extract_folder -type f -name 'POTCAR.Z')"
	if [[ ! -z "$z_archives" ]]; then
		echo "running uncompress on files in $extract_folder"
		uncompress -r $extract_folder
	fi
	# change file permissions
	echo "changing file permissions on folder $extract_folder to 755"
	chmod 755 -R $extract_folder
done
