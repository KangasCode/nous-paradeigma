"""
CSV Export functionality for checkout data
Saves customer data securely to server-side CSV file
"""
import csv
import os
from datetime import datetime
from pathlib import Path

# CSV file location (secure, server-side only)
# Use persistent volume if available
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
CSV_DIR = DATA_DIR
CSV_FILE = CSV_DIR / "checkout_submissions.csv"

def ensure_csv_exists():
    """Create CSV file with headers if it doesn't exist"""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    
    if not CSV_FILE.exists():
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Aikaleima',
                'Sähköposti',
                'Puhelinnumero',
                'Osoite',
                'Kaupunki',
                'Postinumero',
                'Maa',
                'Valittu Paketti',
                'Email Valmis',
                'Puhelin Valmis',
                'Osoite Valmis',
                'Maksu Aloitettu',
                'Maksu Valmis'
            ])

def save_to_csv(checkout_progress):
    """
    Save checkout progress to CSV file
    
    Args:
        checkout_progress: CheckoutProgress model instance
    """
    ensure_csv_exists()
    
    # Format address
    address = ""
    if checkout_progress.address_line1:
        address = checkout_progress.address_line1
        if checkout_progress.address_line2:
            address += f", {checkout_progress.address_line2}"
    
    # Format timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Prepare row data
    row = [
        timestamp,
        checkout_progress.email or '',
        checkout_progress.phone or '',
        address,
        checkout_progress.city or '',
        checkout_progress.postal_code or '',
        checkout_progress.country or '',
        checkout_progress.selected_plan or '',
        'Kyllä' if checkout_progress.step_email_completed else 'Ei',
        'Kyllä' if checkout_progress.step_phone_completed else 'Ei',
        'Kyllä' if checkout_progress.step_address_completed else 'Ei',
        'Kyllä' if checkout_progress.step_payment_initiated else 'Ei',
        'Kyllä' if checkout_progress.step_payment_completed else 'Ei'
    ]
    
    # Append to CSV
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)
    
    print(f"✅ Tallennettu CSV:hen: {checkout_progress.email}")

def get_csv_path():
    """Return the path to the CSV file"""
    return CSV_FILE

