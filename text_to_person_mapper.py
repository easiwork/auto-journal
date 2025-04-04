import csv
import re
import phonenumbers  # pip install phonenumbers
import os
import datetime

def standardize_phone(phone):
    """Standardize phone number to E.164 format and return multiple formats"""
    try:
        # Remove any non-digit characters except +
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Create a list to store all possible formats
        standard_formats = []
        
        # For +15551234567 format, also try matching +5551234567
        if phone.startswith('+1') and len(phone) == 12:
            # Format with country code
            try:
                parsed1 = phonenumbers.parse(phone, None)
                if phonenumbers.is_valid_number(parsed1):
                    e164_1 = phonenumbers.format_number(parsed1, phonenumbers.PhoneNumberFormat.E164)
                    standard_formats.extend([e164_1, e164_1[1:], e164_1[1:].lstrip('1'), phone[1:], phone])
            except:
                pass
                
            # Also try the format without the country code
            phone_without_country = '+' + phone[2:]
            try:
                parsed2 = phonenumbers.parse(phone_without_country, None)
                if phonenumbers.is_valid_number(parsed2):
                    e164_2 = phonenumbers.format_number(parsed2, phonenumbers.PhoneNumberFormat.E164)
                    standard_formats.extend([e164_2, e164_2[1:], e164_2[1:].lstrip('1'), phone_without_country[1:], phone_without_country])
            except:
                pass
                
            # Add original formats
            standard_formats.extend([phone, phone[1:], phone_without_country, phone_without_country[1:]])
            
            # Remove duplicates
            standard_formats = list(set(standard_formats))
            return standard_formats
            
        # If phone starts with +, handle special cases    
        elif phone.startswith('+') and len(phone) == 11:
            phone_with_country = '+1' + phone[1:]
            
            # Add both with and without country code
            try:
                parsed1 = phonenumbers.parse(phone, None)
                if phonenumbers.is_valid_number(parsed1):
                    e164_1 = phonenumbers.format_number(parsed1, phonenumbers.PhoneNumberFormat.E164)
                    standard_formats.extend([e164_1, e164_1[1:], e164_1[1:].lstrip('1'), phone[1:], phone])
            except:
                pass
                
            try:
                parsed2 = phonenumbers.parse(phone_with_country, None)
                if phonenumbers.is_valid_number(parsed2):
                    e164_2 = phonenumbers.format_number(parsed2, phonenumbers.PhoneNumberFormat.E164)
                    standard_formats.extend([e164_2, e164_2[1:], e164_2[1:].lstrip('1'), phone_with_country[1:], phone_with_country])
            except:
                pass
                
            # Add original formats too
            standard_formats.extend([phone, phone[1:]])
            
            # Remove duplicates
            standard_formats = list(set(standard_formats))
            return standard_formats
        
        # If number starts with 1 and is 11 digits, add +
        if phone.startswith('1') and len(phone) == 11:
            phone = '+' + phone
            
        # If number doesn't start with +, try adding it
        if not phone.startswith('+'):
            if len(phone) == 10:
                phone = '+1' + phone
            else:
                phone = '+' + phone.lstrip('0')
        
        # Parse the number
        parsed = phonenumbers.parse(phone, None)
        if phonenumbers.is_valid_number(parsed):
            e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            formats = [
                e164,  # Full international format with +
                e164[1:],  # Without +
                e164[1:].lstrip('1'),  # Without + and country code
                phone.lstrip('+'),  # Original without +
                phone  # Original with +
            ]
            return formats
    except Exception as e:
        pass
    return []

def load_contacts(csv_file):
    phone_map = {}
    email_map = {}
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            contact = row['Phone Number/Email']
            name = row['Name']
            if not name or not contact:
                continue
                
            # Check if it's an email or phone number
            if '@' in contact:
                # It's an email
                email_map[contact.lower()] = name
            else:
                # It's a phone number
                # Get all possible formats for this number
                formats = standardize_phone(contact)
                for fmt in formats:
                    phone_map[fmt] = name
                
                # Also store the original format
                clean_phone = re.sub(r'[^\d+]', '', contact)
                phone_map[clean_phone] = name
                
    return phone_map, email_map

def replace_numbers_with_names(text_file, phone_map, email_map):
    with open(text_file, 'r') as f:
        content = f.read()
    
    # Pattern to match phone numbers in the specific iMessage format
    phone_patterns = [
        r'\+1\d{10}\b',  # Explicitly matches +15551234567 format
        r'\+\d{11,}',  # Matches +14084766548 format
        r'\+\d{10}',   # Matches +4084766548 format
        r'\b\d{10}\b',  # Matches 10 digit numbers
        r'\(\d{3}\)\s*\d{3}[-\s]?\d{4}'  # Matches (408) 476-6548 format
    ]
    
    # Pattern to match email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    def replace_phone_match(match):
        phone = match.group(0)
        
        # Try all possible formats
        formats = standardize_phone(phone)
        
        for fmt in formats:
            if fmt in phone_map:
                return phone_map[fmt]
        
        # Try the original format
        clean_phone = re.sub(r'[^\d+]', '', phone)
        if clean_phone in phone_map:
            return phone_map[clean_phone]
        
        # If no match found, return original
        return phone
    
    def replace_email_match(match):
        email = match.group(0).lower()  # Convert to lowercase for matching
        if email not in email_map:
            print(f"Warning: Email address '{email}' not found in contacts")
        return email_map.get(email, match.group(0))
    
    # Apply phone number patterns
    new_content = content
    for pattern in phone_patterns:
        new_content = re.sub(pattern, replace_phone_match, new_content)
    
    # Apply email pattern
    new_content = re.sub(email_pattern, replace_email_match, new_content)
    
    return new_content

def process_all_files(directory, message_dir=None):
    # Load contacts once
    contacts_file = os.path.join(directory, 'contacts_reformatted.csv')
    phone_map, email_map = load_contacts(contacts_file)
    
    # Debug: Print all formats in the phone_map
    print("Available phone number formats:")
    for k, v in phone_map.items():
        print(f"'{k}' -> '{v}'")
    
    print("\nAvailable email addresses:")
    for k, v in email_map.items():
        print(f"'{k}' -> '{v}'")
    
    # Determine which directory to process
    if message_dir:
        target_dir = os.path.join(directory, message_dir)
    else:
        target_dir = directory
    
    print(f"\nProcessing files in: {target_dir}")
    
    # Process all .txt files except the output file
    for filename in os.listdir(target_dir):
        if filename.endswith('.txt') and filename != 'converted_messages.txt':
            input_file = os.path.join(target_dir, filename)
            print(f"\nProcessing {filename}...")
            new_content = replace_numbers_with_names(input_file, phone_map, email_map)
            
            # Write to the output file
            output_file = os.path.join(directory, 'converted_messages.txt')
            with open(output_file, 'a') as f:
                f.write(f"\n=== Content from {message_dir}/{filename} ===\n")
                f.write(new_content)
                f.write("\n\n")
    
    print(f"\nConversion complete. Output written to converted_messages.txt")

def main():
    # Get yesterday's date in MM_DD format
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday_dir = yesterday.strftime("%m_%d")  # Format: 04_03
    
    directory = 'Assets'
    message_dir = yesterday_dir  # Use yesterday's directory
    
    # Clear the output file if it exists
    output_file = os.path.join(directory, 'converted_messages.txt')
    open(output_file, 'w').close()
    
    process_all_files(directory, message_dir)

def test_phone_conversion(phone_number, contacts_file='Assets/contacts_reformatted.csv'):
    """Test conversion of a specific phone number using the current logic"""
    phone_map, email_map = load_contacts(contacts_file)
    
    print(f"Testing conversion of: {phone_number}")
    formats = standardize_phone(phone_number)
    print(f"Standardized formats: {formats}")
    
    # Check if any format is in the phone map
    found = False
    for fmt in formats:
        if fmt in phone_map:
            print(f"Match found! '{fmt}' -> '{phone_map[fmt]}'")
            found = True
    
    # Check original format
    clean_phone = re.sub(r'[^\d+]', '', phone_number)
    if clean_phone in phone_map:
        print(f"Original format match found! '{clean_phone}' -> '{phone_map[clean_phone]}'")
        found = True
    
    if not found:
        print(f"No match found for {phone_number} in any format")
        print("Available keys in phone_map:")
        for k in phone_map.keys():
            print(f"  '{k}'")

if __name__ == "__main__":
    # Uncomment one of the following options:
    
    # Option 1: Run tests for specific phone numbers
    # test_numbers = ["+15551234567", "+5551234567"]
    # for num in test_numbers:
    #     test_phone_conversion(num)
    #     print("\n")
    
    # Option 2: Run the main program to process messages
    main()
