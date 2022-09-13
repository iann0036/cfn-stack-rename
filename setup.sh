#!/bin/bash

root_check() {
  current_user=$(id -un)
  if [ "${current_user}" == "root" ]; then
    echo -e "\n\n${current_user}, "
    echo -e "please dont run me using sudo or as root\n\n"
    exit
  fi
  echo -e "\n\nHi ${current_user}, configuring everything for you now."
}

root_check
rm -rfv build/ dist/ *.egg-info
/usr/bin/env python3 -m venv --system-site-packages env
source env/bin/activate
pip3 install -U pip
pip3 install -r requirements.txt
pip3 install .
rm -rfv build/ dist/ *.egg-info

echo -e "\n\n*****************************************************************************************************"
echo -e "\t\tcfn-stack-rename has been installed in virtual env"
echo -e "\t\t************************************************\n"
echo -e "stack_rename has been installed inside the python virtual env folder env\nin this current working directory"
echo -e "\nTo activate please run:\n\tsource env/bin/activate\n\nThis will drop you into virtual env to de-activate please run:\n\tdeactivate"
echo -e "\nPlease run:\n\tstack_migration --help\n\nThis will display all available options."
echo -e "\nOnce finished running, please remember to run deactivate to deactivate the python venv"
echo -e "Please refer to the included README.md for for further usage instructions.\n"
echo -e "******************************************************************************************************\n\n"
