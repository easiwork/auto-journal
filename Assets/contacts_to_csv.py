import csv
import re

def vcf_to_csv(vcf_file, csv_file):
    with open(vcf_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    contacts = []
    current_contact = {}

    for line in lines:
        line = line.strip()
        
        if line.startswith('FN:'):
            current_contact['Name'] = line[3:]
            print(f"current_contact", current_contact)

        elif 'TEL' in line:
            phone = re.sub(r'\D', '', line.split(':')[-1])
            current_contact['Phone Number/Email'] = f"+{phone}"
            contacts.append(current_contact.copy())
            print(f"current_contact", current_contact)

        elif 'EMAIL' in line:
            email = line.split(':')[-1]
            current_contact['Phone Number/Email'] = f"{email}"
            contacts.append(current_contact.copy())
            print(f"current_contact", current_contact)

        elif line == 'END:VCARD':
            current_contact = {}

    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Phone Number/Email', 'Name'])
        writer.writeheader()
        writer.writerows(contacts)

# use like this:
if __name__ == "__main__":
    vcf_to_csv('contacts.vcf', 'contacts_reformatted.csv')

