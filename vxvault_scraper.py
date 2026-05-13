import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import os
from urllib.parse import urljoin, urlparse, parse_qs

# Get embedded password from login page HTML
def get_password_from_page():
    """Extract password from HTML comment in login page"""
    try:
        response = requests.get("http://vxvault.net/login.php", verify=False, timeout=5)
        if response.status_code == 200:
            # Password is in HTML comment: File download creds: infected:O3aNDL5z
            if "infected:O3aNDL5z" in response.text:
                return "O3aNDL5z"
            elif "infected" in response.text and ":" in response.text:
                # Try to extract password from comment
                start = response.text.find("File download creds:")
                if start != -1:
                    creds = response.text[start:start+50].split(":")[1].split("\n")[0].strip()
                    return creds.strip()
        return "infected"  # Default fallback
    except:
        return "infected"

def verify_login(session):
    """Verify if login was successful"""
    try:
        response = session.get("http://vxvault.net/ViriList.php", verify=False, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_div = soup.find('div', {'id': 'page'})
        table = page_div.find('table') if page_div else None
        return page_div is not None and table is not None
    except:
        return False

def login_and_get_all_data(max_records=None):
    """Login and get all data from vxvault with pagination"""
    session = requests.Session()

    # Get password
    password = get_password_from_page()
    print(f"[*] Using password: {password}")

    # Login
    login_url = "http://vxvault.net/login.php"
    payload = {'password': password}
    print("[*] Attempting login...")
    response = session.post(login_url, data=payload, verify=False)

    if response.status_code != 200:
        print("❌ Login failed - HTTP error")
        return None

    # Verify login
    if not verify_login(session):
        print("❌ Login verification failed - Password may be incorrect")
        return None

    print("✓ Login successful")

    all_rows = []
    page = 0
    items_per_page = 40  # VX Vault shows 40 items per page
    
    while True:
        start = page * items_per_page
        
        # Construct pagination URL
        url = f"http://vxvault.net/ViriList.php?s={start}&m={items_per_page}"
        print(f"\n[*] Fetching page {page + 1} (offset: {start})...")
        
        response = session.get(url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        page_div = soup.find('div', {'id': 'page'})
        if not page_div:
            print("❌ Page div not found - Login may have expired")
            break
            
        table = page_div.find('table')
        if not table:
            print("✓ No more data available")
            break
        
        rows = []
        all_trs = table.find_all('tr')
        
        # Skip header row
        for tr in all_trs[1:]:
            cells = tr.find_all('td')
            if len(cells) >= 5:
                date = cells[0].get_text(strip=True)
                url_text = cells[1].get_text(strip=True)
                md5 = cells[2].get_text(strip=True)
                ip = cells[3].get_text(strip=True)
                tools = cells[4].get_text(strip=True)
                
                rows.append({
                    'Date': date,
                    'URL': url_text,
                    'MD5': md5,
                    'IP': ip,
                    'Tools': tools
                })
        
        if not rows:
            print("✓ No more data available")
            break
        
        all_rows.extend(rows)
        print(f"  └─ Fetched {len(rows)} records (Total: {len(all_rows)})")
        
        # Check if we've reached the limit
        if max_records and len(all_rows) >= max_records:
            all_rows = all_rows[:max_records]
            print(f"\n✓ Reached limit of {max_records} records")
            break
        
        page += 1
    
    if not all_rows:
        print("❌ No data retrieved")
        return None
    
    return all_rows

def save_to_sqlite(data, db_name="vxvault_data.db"):
    """Save data to SQLite database"""
    print(f"\n[*] Saving to SQLite database: {db_name}...")
    
    # Create connection
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS malware_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            url TEXT,
            md5 TEXT UNIQUE,
            ip TEXT,
            tools TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert data
    inserted = 0
    duplicates = 0
    for row in data:
        try:
            cursor.execute('''
                INSERT INTO malware_urls (date, url, md5, ip, tools)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['Date'], row['URL'], row['MD5'], row['IP'], row['Tools']))
            inserted += 1
        except sqlite3.IntegrityError:
            duplicates += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database saved")
    print(f"  ├─ Inserted: {inserted} records")
    print(f"  └─ Duplicates skipped: {duplicates}")

def main():
    print("="*80)
    print("VX Vault Data Scraper")
    print("="*80)
    
    # Ask user how many records to fetch
    while True:
        try:
            user_input = input("\n[?] How many records to fetch? (or 'all' for all): ").strip().lower()
            if user_input == 'all':
                max_records = None
                print("[*] Will fetch ALL available records")
                break
            elif user_input.isdigit() and int(user_input) > 0:
                max_records = int(user_input)
                print(f"[*] Will fetch {max_records} records")
                break
            else:
                print("❌ Invalid input. Please enter a number or 'all'")
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return
    
    # Fetch data
    data = login_and_get_all_data(max_records)
    
    if not data:
        print("❌ Failed to retrieve data")
        return
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Display table
    print("\n" + "="*180)
    print(df.to_string(index=False))
    print("="*180)
    
    # Save to CSV
    csv_file = 'vxvault_data.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8')
    print(f"\n✓ CSV saved: {csv_file}")
    
    # Save to SQLite
    save_to_sqlite(data, "vxvault_data.db")
    
    print("\n" + "="*80)
    print(f"✓ Total records processed: {len(data)}")
    print("="*80)

if __name__ == "__main__":
    main()