#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

function doIt() {
	sudo apt install -y zsh sl htop vim;
	trap "sh -c $'\$(wget https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)'" EXIT;
	git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k;
	git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions;
	cd "$(dirname "${BASH_SOURCE}")";
	sh -c "./bootstrap.sh --force";
	/bin/zsh
}

if [ "$1" == "--force" -o "$1" == "-f" ]; then
	doIt;
else
	read -p "This will install a lot of tools, switch you to zsh, and overwrite dotfiles. Are you sure? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt;
	fi;
fi;
unset doIt;
