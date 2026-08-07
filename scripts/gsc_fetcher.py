import sys
import subprocess
import os
import argparse
import datetime
import json

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user", "--quiet"])

try:
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
except ImportError:
    print("Installing required Google API packages...")
    install('google-api-python-client')
    install('google-auth-httplib2')
    install('google-auth-oauthlib')
    # Reload
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

def get_service():
    creds = None
    skill_dir = os.path.dirname(os.path.realpath(__file__))
    token_path = os.path.join(skill_dir, 'gsc_token.json')
    creds_path = os.path.join(skill_dir, 'credentials.json')

    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found. Please place the OAuth credentials downloaded from Google Cloud here.")
        sys.exit(1)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    service = build('searchconsole', 'v1', credentials=creds)
    return service

def list_sites():
    service = get_service()
    site_list = service.sites().list().execute()
    sites = site_list.get('siteEntry', [])
    print("Available Properties:")
    for site in sites:
        print(f"- {site['siteUrl']}")

def fetch_top_keywords(site_url, limit=4000):
    service = get_service()
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')

    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query'],
        'rowLimit': limit
    }

    response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
    
    if 'rows' not in response:
        print("No data found.")
        return

    print("Keyword | Clicks | Impressions | CTR | Position")
    print("-" * 60)
    for row in response['rows']:
        query = row['keys'][0]
        print(f"{query} | {row['clicks']} | {row['impressions']} | {row['ctr']:.4f} | {row['position']:.2f}")

def fetch_url_data(site_url, page_url):
    service = get_service()
    end_date = datetime.date.today().strftime('%Y-%m-%d')
    start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime('%Y-%m-%d')

    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query'],
        'dimensionFilterGroups': [{
            'filters': [{
                'dimension': 'page',
                'expression': page_url,
                'operator': 'equals'
            }]
        }],
        'rowLimit': 100
    }

    response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
    
    if 'rows' not in response:
        print(f"No GSC data found for URL: {page_url}")
        return

    print(f"Performance for URL: {page_url}")
    print("Keyword | Clicks | Impressions | Position")
    print("-" * 50)
    for row in response['rows']:
        query = row['keys'][0]
        print(f"{query} | {row['clicks']} | {row['impressions']} | {row['position']:.2f}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Google Search Console Fetcher")
    subparsers = parser.add_subparsers(dest="command")

    parser_list = subparsers.add_parser("list")
    
    parser_top = subparsers.add_parser("fetch_top_keywords")
    parser_top.add_argument("site_url", help="GSC Site URL (e.g., https://example.com/ or sc-domain:example.com)")
    
    parser_url = subparsers.add_parser("fetch_url_data")
    parser_url.add_argument("site_url", help="GSC Site URL")
    parser_url.add_argument("page_url", help="Exact Page URL to analyze")

    args = parser.parse_args()

    if args.command == "list":
        list_sites()
    elif args.command == "fetch_top_keywords":
        fetch_top_keywords(args.site_url)
    elif args.command == "fetch_url_data":
        fetch_url_data(args.site_url, args.page_url)
    else:
        parser.print_help()
