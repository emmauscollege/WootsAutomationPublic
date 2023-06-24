def print_rule(first='-', last='-'):
    print(first+'-'*77+last)

def print_header(header_text):
    print_rule('\u250c', '\u2510')
    print("|   " + header_text.ljust(74)[:74] + "|")
    print_rule('\u2514', '\u2518')

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_fail(fail_text):
    print(f"{bcolors.FAIL}{fail_text}{bcolors.ENDC}")