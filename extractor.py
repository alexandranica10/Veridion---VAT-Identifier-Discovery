import csv
import random

input_file = "companies_data.csv" 
output_file = "business_sample.csv"

sampled_companies = []

print("Opening the file... ")

with open(input_file, mode='r', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    
    headers = reader.fieldnames
    number_col = next((col for col in headers if "CompanyNumber" in col.replace(" ", "")), None)
    sic_col = next((col for col in headers if "SICCode.SicText_1" in col.replace(" ", "")), None)

    for row in reader:
        status = row.get('CompanyStatus', '')
        sic_text = row.get(sic_col, '') if sic_col else ''
        
        if status == 'Active' and any(keyword in sic_text for keyword in ['Retail', 'software', 'manufacturing', 'trade']): # only look at Active companies in industries likely to have websites

            if random.random() < 0.01:
                sampled_companies.append({
                    'Name': row.get('CompanyName', ''),
                    'Number': row.get(number_col, ''),
                    'Website_URL': '' # blank for manual entry
                })
                
        if len(sampled_companies) >= 100: 
            break

print(f"Successfully grabbed {len(sampled_companies)} real businesses. Saving...")

with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=['Name', 'Number', 'Website_URL'])
    writer.writeheader()
    writer.writerows(sampled_companies)

print("Done! Open 'business_sample.csv' and find their websites on Google.")
