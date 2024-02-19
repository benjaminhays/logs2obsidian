import sys
import re
import xml.etree.ElementTree as ET

def usage():
    print(f"""Usage: {sys.argv[0]} [nmap.xml] (--help)""")

def dict_to_markdown_table(dictionary):
    headers = ["Key", "Value"]
    
    # Create the header row
    header_row = "| " + " | ".join(headers) + " |"
    
    # Create the separator row
    separator_row = "| " + "--- |" + "--- |"
    
    # Create the data rows
    data_rows = []
    for key, value in dictionary.items():
        # Replace any pipe characters in the value with a space
        value = str(value).replace('|', ' ')
        # Replace any newline characters with a space
        value = value.replace('\n', ' ')
        data_row = "| " + " | ".join(str(item) for item in [key, value]) + " |"
        data_rows.append(data_row)
    
    # Combine the rows into a single string
    table = "\n".join([header_row, separator_row] + data_rows)
    
    return table

def parse_xml_file(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    host_files = []
    hosts = root.findall('host')
    # Iterate over the <host> elements and print their tags
    for host in hosts:
        # Get the IPv4 Address
        if (host.findall("status")[0].attrib["state"] != "up"):
            continue
        
        addresses = host.findall('address')
        ports = host.findall('ports')[0].findall("port")
        host_details = {}

        for address in addresses:
            if address.attrib["addrtype"] == "ipv4":
                host_details["ipv4"] = address.attrib["addr"]
            elif address.attrib["addrtype"] == "ipv6":
                host_details["ipv6"] = address.attrib["addr"]
            elif address.attrib["addrtype"] == "mac":
                host_details["mac"] = address.attrib["addr"]
        
        host_details["status"] = host.findall("status")[0].attrib["state"]
        if (host.findall("uptime")):
            host_details["uptime"] = "Since " + host.findall("uptime")[0].attrib["lastboot"]

        content = f"""## Host Details:
{dict_to_markdown_table(host_details)}

## Ports\n
"""
        for port in ports:
            if (port.tag != "port"):
                continue

            service = port.findall("service")[0].attrib["name"]
            service_details = {}

            for script in port.findall("script"):
                service_details[script.attrib["id"]] = script.attrib["output"]

            service_details["Reason"] = port.findall("state")[0].attrib["reason"]
            if (port.findall("service")[0].findall("cpe")):
                service_details["CPE"] = port.findall("service")[0].findall("cpe")[0].text
            if (port.findall("service")[0].attrib.get("product")):
                service_details["Product"] = port.findall("service")[0].attrib["product"]
                content += f"""### {port.attrib["protocol"].upper()}/{port.attrib["portid"]} - {service} ({service_details["Product"]}):\n"""
            else:
                content += f"""### {port.attrib["protocol"].upper()}/{port.attrib["portid"]} - {service}:\n#### Port Details:\n"""
            content += f"""{dict_to_markdown_table(service_details)}\n#### Notes: \n\n\n\n-------------------------------------------------------------------------------\n\n"""


        f = open(f"output/{host_details['ipv4']}.md", "w")
        f.write(content)
        f.close()
        host_files.append(host_details['ipv4'])

    cidr_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/[0-9]{1,2}\b'
    match = re.search(cidr_pattern, root.attrib["args"])
    if match:
        CIDR = match.group().replace("/", "-")

    content = "### Hosts\n"
    f = open(f"output/{CIDR}.md", "w")
    for hfile in host_files:
        content += f"* [[{hfile}]]\n"
    f.write(content)
    f.close()

def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)
    
    file_path = sys.argv[1]
    parse_xml_file(file_path)

if __name__ == "__main__":
    main()