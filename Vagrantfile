# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<SCRIPT

apt-get install -y python-setuptools

SCRIPT

Vagrant.configure("2") do |config|

    config.vm.box = "hashicorp/precise64"
    config.vm.network "private_network", ip: "172.20.20.248"
    config.vm.provision "shell", inline: $script

end