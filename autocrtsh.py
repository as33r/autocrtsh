import argparse
import requests
from termcolor import colored
import os
import json
from threading import *

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
    domains = set(domains)
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

def domain_parse(json_response):
    if json_response:
        resp = json.loads(json_response)
        return set([domain["name_value"] for domain in resp])

def crtsh(domain):
    url = "https://crt.sh/?Identity=%."
    query = url + domain + "&output=json"
    try:
        req = requests.get(query)
        return req.text
    except Exception as error:
        print(colored(f"[-][-] Error ocured {error} , skipping {domain} ", "red"))
        skipped(domain)

def sub_domains(domain_name, domains, filename_all):
    # Getting domain level to enumerate recursively
    screen_lock = Semaphore(value=1)
    dom_level = -(len(domain_name.split(".")) + 1)
    sub_root = sub_domain_root(domains, dom_level)
    for sub_domain_name in sub_root:
        print(colored(f"[+] Getting subdomains for {sub_domain_name}", "green"))
        try:
            sub_json_response = crtsh(sub_domain_name)
            sub_raw_domains = domain_parse(sub_json_response)
            sub_domains = extract_emails(sub_raw_domains)
            data_save(sub_domains, sub_domain_name, filename_all)
        except KeyboardInterrupt:
            print(colored("[-] User interuption detected, Shutting down programe", "red"))
            exit(0)
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", dest="domain", help="Give domain name to find subdomain from https://crt.sh")
    parser.add_argument("-r", "--recursive", dest="recursive", action="store_true", help="Look for subdomain recursively")
    parser.add_argument("-o", "--output-dir", dest="output", default="autocrtsh",
                        help="Output directory to save output")
    options = parser.parse_args()
    domain_name = options.domain
    recursive = options.recursive
    output_dir = options.output

    if not domain_name:
        print(colored("Please provide a domain name to subdomain lookup", "red"))
        exit(0)

    print(colored(f"[+] Fetching data from https://crt.sh for the domain {domain_name}", "green"))
    # creating a directory to save data
    cwd = os.getcwd()
    dir = domain_name.split(".")[-2]
    path = os.path.join(cwd, dir, output_dir)
    if os.path.exists(path):
        print(colored(f"[*] {dir}  directory already exists", "yellow"))
        os.chdir(path)
    else:
        print(colored(f"[*] Creating {dir} direcoty to save data", "yellow"))
        try:
            os.mkdir(dir)
        except:
            pass
        os.mkdir(os.path.join(dir, output_dir))
        os.chdir(path)

    filename_all = "all_domains.txt"
    resp_json = crtsh(domain_name)
    print(colored("[+] Parsing domain names", "green"))
    raw_domains = domain_parse(resp_json)
    domains = extract_emails(raw_domains)
    data_save(domains, domain_name, filename_all)

    if recursive:
        print(
            colored("[*]  ======================   Collecting data recursively   =============================",
                    "yellow"))
        sub_domains(domain_name, domains, filename_all)
        threads = Thread(target=sub_domains, args=(domain_name, domains, filename_all))
        threads.start()
         # removing duplicates from all domains files
        remove_duplicates(filename_all)
    print(colored("[*] Extracted emails are saved in emails.txt file", "yellow"))