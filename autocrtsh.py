import argparse
import requests
import bs4

def skipped(d):
    with open("skipped.txt", "a+") as f:
        f.write(d)
        f.write("\n")

def remove_duplicates(filename):
    print(f"[+] Removing duplicats from {filename}")
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
        print(f"[+] Saving {len(domains)} domain names in file {filename} and adding to {filename_all}")
        with open (filename, 'w') as file:
            for domain in domains:
                file.write(domain + "\n")
        with open(filename_all, 'a+') as file:
            for domain in domains:
                file.write(domain + "\n")
    else:
        print(f"[+] Adding {len(domains)} domain names in file {filename_all}")
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
        print(f"[-][-] Error ocured {error} , skipping {domain} ")
        skipped(domain)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--domain", dest="domain", help="Give domain name to find subdomain from https://crt.sh")
    parser.add_argument("-r", "--recursive", dest="recursive", action="store_true", help="Look for subdomain recursively")
    options = parser.parse_args()
    domain_name = options.domain
    recursive = options.recursive

    if not domain_name:
        print("Please provide a domain name to subdomain lookup")
        exit(0)

    print(f"[+] Fetching data from https://crt.sh for the domain {domain_name}")
    filename_all = "all_domains.txt"
    html_page = crtsh(domain_name)
    print("[+] Parsing domain names")
    raw_domains = url_parse(html_page)
    domains = domain_parse(raw_domains)
    # converting to python set datatype to remove duplicates
    domains = set(domains)
    data_save(domains, domain_name, filename_all)
    print("[+] Collecting data recursively ===================================================")

    if recursive:
        # Getting domain level to enumerate recursively
        dom_level = -(len(domain_name.split(".")) + 1)
        sub_root = sub_domain_root(domains, dom_level)
        for sub_domain_name in sub_root:
            print(f"[+] Getting subdomains for {sub_domain_name}")
            try:
                sub_html_page = crtsh(sub_domain_name)
                sub_raw_domains = url_parse(sub_html_page)
                sub_domains = domain_parse(sub_raw_domains)
                sub_domains = set(sub_domains)
                data_save(sub_domains, sub_domain_name, filename_all)
            except KeyboardInterrupt:
                print("[-] User interuption detected, Shutting down programe")
                exit(0)
            except:
                pass
         # removing duplicates from all domains files
        remove_duplicates(filename_all)