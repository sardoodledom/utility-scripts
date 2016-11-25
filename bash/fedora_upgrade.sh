#!/usr/bin/env bash

let fedora_version="$(grep -i version_id /etc/os-release | cut -d"=" -f2)+1"
sudo dnf -y upgrade --refresh
sudo dnf -y install dnf-plugin-system-upgrade
sudo dnf -y system-upgrade download --releasever=$fedora_version
while true; do
  read -p 'Do you want to reboot and complete the upgrade?' yn
  case $yn in
    [Yy]* ) sudo dnf -y system-upgrade reboot;
    [Nn]* ) exit;;
    * ) echo 'Please answer yes or no.';;
  esac
done
