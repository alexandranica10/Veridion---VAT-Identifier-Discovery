import csv
import requests
import re
from bs4 import BeautifulSoup
from thefuzz import fuzz


def is_valid_vat_checksum(vat_str):
    vat_str = re.sub(r'[^0-9]', '', vat_str)
    if len(vat_str) != 9: return False
    weights = [8, 7, 6, 5, 4, 3, 2]
    total = sum(int(vat_str[i]) * weights[i] for i in range(7))
    while total > 0: total -= 97
    return abs(total) == int(vat_str[7:9])

def extract_vat_from_website(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ')
        
        pattern = r'(?:GB|VAT\s*No\.?:?|VAT)\s*([0-9]{3}\s*[0-9]{4}\s*[0-9]{2})'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        valid_vats = []
        for match in matches:
            clean_match = re.sub(r'\s+', '', match)
            if is_valid_vat_checksum(clean_match):
                valid_vats.append(clean_match)
        return list(set(valid_vats))
    except Exception as e:
        return []

def check_hmrc_api(vat_number):
    url = f"https://api.service.hmrc.gov.uk/organisations/vat/check-vat-number/lookup/{vat_number}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get('target', {}).get('name', '')
        return None
    except:
        return None

print("Starting the VAT Discovery...\n")

with open("business_sample.csv", mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        target_name = row['Name']
        url = row['Website_URL']
        
        print(f"Testing: {target_name}")
        print(f"Scraping: {url}")
        
        found_vats = extract_vat_from_website(url)
        
        if not found_vats:
            print("Result: No valid VAT pattern found on website.\n")
            continue
        print(f"Found mathematically valid numbers: {found_vats}")

            
        match_found = False
        for vat in found_vats:
            hmrc_name = check_hmrc_api(vat)
            
            if hmrc_name:
                similarity = fuzz.token_sort_ratio(target_name.lower(), hmrc_name.lower())
                
                if similarity > 70:
                    print(f" SUCCESS: Found {vat}. HMRC confirmed it belongs to {hmrc_name}.")
                    match_found = True
                    break 
                else:
                    print(f" FALSE POSITIVE: Found {vat}, but HMRC says it belongs to '{hmrc_name}', not '{target_name}'.")
        
        if not match_found:
            print(" Result: Numbers found, but none matched the target company.\n")
        else:
            print("") 
