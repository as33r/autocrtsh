import argparse
import requests
import bs4
from termcolor import colored
import os

def extract_emails(domains):
    email_filename = "email.txt"
    domains = list(domains)
    doms = []
    with open(email_filename, "a+")as emails:
        for domain in domains:
            if "@" in domain:
                emails.write(domain + "\n")
            else:
                doms.append(domain)
    return set(doms)


def skipped(d):
    with open("skipped.txt", "a+") as f:
        f.write(d)
        f.write("\n")

def remove_duplicates(filename):
    print(colored(f"[+] Removing duplicats from {filename}", "green"))
    with open(filename, "r+") as f:
        # creating a list of lines of file
        tmp_list = [line for line in f]
        removed_dup = set(tmp_list)
        f.seek(0)
        for line in removed_dup:
            f.write(line)
        f.truncate()

def sub_domain_root(domains, domain_level):
    # Getting domain roots based on domain level. spliting domains with ".", slicing to get last items from list, then joining again with "."
    domain_list = [".".join(domain.split(".")[domain_level:]) for domain in domains]
    return set(domain_list)

def data_save(domains, domain_name, filename_all):
    filename = domain_name + ".txt"
    if len(domains) > 2:
        print(colored(f"[+] Saving {len(domains)} domain names in file {filename} and adding to {filename_all}", "green"))
        with open (filename, 'w') as file:
            for domain in domains:
                file.write(domain + "\n")
        with open(filename_all, 'a+') as file:
            for domain in domains:
                file.write(domain + "\n")
    else:
        print(colored(f"[+] Adding {len(domains)} domain names in file {filename_all}", "green"))
        with open(filename_all, 'a+') as file:
            for domain in domains:
                file.write(domain + "\n")

def domain_parse(domains):
    # removing all occurance of <br/> html tag
    d = [str(domain) for item in domains for domain in item if '<br/>' != str(domain)]
    return d

def url_parse(html_page):
    soup = bs4.BeautifulSoup(html_page, "html.parser")
    # getting second table
    try:
        table = soup.find_all('table')[1]
        # table inside table
        table_row = table.find('table')
        # list to capture all the domains
        domain_data = []
        # iterate through table rows
        for tr in table_row:
            if type(tr) is not bs4.element.NavigableString:
                # getting all the data tags
                td = tr.find_all('td')
                try:
                    domain_data.append(td[4].contents)
                except IndexError:
                    pass
    except IndexError:
        pass
    return domain_data

def crtsh(domain):
    url = "https://crt.sh/?Identity=%."
    query = url + domain
    try:
        req = requests.get(query)
        return req.text
    except Exception as error:
        print(colored(f"[-][-] Error ocured {error} , skipping {domain} ", "red"))
        skipped(domain)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", dest="domain", help="Give domain name to find subdomain from https://crt.sh")
    parser.add_argument("-r", "--recursive", dest="recursive", action="store_true", help="Look for subdomain recursively")
    options = parser.parse_args()
    domain_name = options.domain
    recursive = options.recursive

    if not domain_name:
        print(colored("Please provide a domain name to subdomain lookup", "red"))
        exit(0)

    print(colored(f"[+] Fetching data from https://crt.sh for the domain {domain_name}", "green"))
    # creating a directory to save data
    cwd = os.getcwd()
    dir = domain_name.split(".")[-2]
    path = os.path.join(cwd, dir)
    if os.path.exists(path):
        print(colored(f"[*] {dir} directory already exists", "yellow"))
        os.chdir(path)
    else:
        print(colored(f"[*] Creating {dir} direcoty to save data", "yellow"))
        os.mkdir(dir)
        os.chdir(path)

    filename_all = "all_domains.txt"
    html_page = crtsh(domain_name)
    print(colored("[+] Parsing domain names", "green"))
    raw_domains = url_parse(html_page)
    domains = domain_parse(raw_domains)
    # converting to python set datatype to remove duplicates
    doms = set(domains)
    domains = extract_emails(doms)
    data_save(domains, domain_name, filename_all)

    if recursive:
        print(colored("[*]  ======================   Collecting data recursively   =============================", "yellow"))
        # Getting domain level to enumerate recursively
        dom_level = -(len(domain_name.split(".")) + 1)
        sub_root = sub_domain_root(domains, dom_level)
        for sub_domain_name in sub_root:
            print(colored(f"[+] Getting subdomains for {sub_domain_name}", "green"))
            try:
                sub_html_page = crtsh(sub_domain_name)
                sub_raw_domains = url_parse(sub_html_page)
                sub_domains = domain_parse(sub_raw_domains)
                sub_doms = set(sub_domains)
                sub_domins = extract_emails(sub_doms)
                data_save(sub_domains, sub_domain_name, filename_all)
            except KeyboardInterrupt:
                print(colored("[-] User interuption detected, Shutting down programe", "red"))
                exit(0)
            except:
                pass
         # removing duplicates from all domains files
        remove_duplicates(filename_all)
    print(colored("[*] Extracted emails are saved in emails.txt file", "yellow"))