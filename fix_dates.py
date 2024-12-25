import pandas as pd
import re
from datetime import datetime
import traceback

def update_dates_in_dataframe(df):
    date_patterns = [
        r"(?:DATE\s*:\s*)?(?P<day>\d{1,2})(?:[\s/\\\-])?(?P<month>[A-Za-z]{3,5})(?:[.,]?\s*)?(?P<year>(?:202[2-9]|20[3-9][0-9]|[2-9][0-9]))",
        r"(?:DATE\s*:\s*)?(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>(?:202[2-9]|20[3-9][0-9]|[2-9][0-9]))"
    ]
    replacements = {
        'APPR': 'APR',
        'návie': 'naive',
        'MAP': 'MAR',
        'MAF': 'MAR',
        'CCT': 'OCT',
        'OCCT': 'OCT',
        'OOCT': 'OCT',
        'OCTT': 'OCT',
        'COT': 'OCT',
        'FEED': 'FEB',
        'Feo': 'FEB',
        'FEU': 'FEB',
        'FLB': 'FEB',
        'FEP': 'FEB',
        'FFB': 'FEB',
        'Febo': 'FEB',
        'FEFE': 'FEB',
        'FED': 'FEB',
        'MARP': 'MAR',
        'JULN': 'JUL',
        'JUIN': 'JUN',
        'JULY': 'JUL',
        'UJLY': 'JUL',
        'UJY': 'JUL',
        'April': 'APR',
        'May': 'MAY',
        'June': 'JUN',
        'July': 'JUL',
        'Aug': 'AUG',
        'Sep': 'SEP',
        'Oct': 'OCT',
        'Nov': 'NOV',
        'Dec': 'DEC',
    }

    def extract_and_normalize_dates(row):
        # First try full_text
        text = str(row['full_text'])
        for old, new in replacements.items():
            text = text.replace(old, new)
        text += f" {row['file_path']}"
            
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                day = match.group('day')
                month = match.group('month')
                year = match.group('year')
                try:
                    if len(year) == 4:
                        # Parse 4-digit year
                        if month.isdigit():
                            # Parse month as a number
                            date_obj = datetime.strptime(f'{day} {month} {year}', '%d %m %Y')
                        else:
                            # Parse month as an abbreviated name
                            date_obj = datetime.strptime(f'{day} {month} {year}', '%d %b %Y')
                    elif len(month) > 2:
                        # Parse 2-digit year with month name
                        date_obj = datetime.strptime(f'{day} {month} {year}', '%d %b %y')
                    else:
                        # Parse 2-digit year with month number
                        date_obj = datetime.strptime(f'{month}/{day}/{year}', '%m/%d/%y')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    # print full traceback
                    print(f"Error parsing date: {day} {month} {year}")
                    # print(traceback.format_exc())
                    continue
        
        return None
    
    def extract_ear_tag(row):
        text = str(row['full_text'])
        ear_tag_match = re.search(r'\b[56]\d{3}\b', text)
        ear_tag = ear_tag_match.group(0) if ear_tag_match else ''
        return ear_tag
    
    # Apply the function to each row in the DataFrame
    df['date'] = df.apply(extract_and_normalize_dates, axis=1)
    df['ear_tag'] = df.apply(extract_ear_tag, axis=1)

    return df

if __name__ == "__main__":
    input_file = 'image_results.csv'
    output_file = 'image_results.csv'
    
    # Load the CSV file
    df = pd.read_csv(input_file)
    
    # Apply the date updating function
    updated_df = update_dates_in_dataframe(df)
    
    # Save the updated DataFrame back to CSV
    updated_df.to_csv(output_file, index=False)
    
    print(f"Processed {len(df)} rows and saved to '{output_file}'")


