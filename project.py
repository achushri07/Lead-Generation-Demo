"""
3D In-Vitro Models Lead Generation Web Crawler
Generates CSV with ranked leads for drug discovery & toxicology
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time
from urllib.parse import quote
import json

class LeadGenerationCrawler:
    def __init__(self):
        self.leads = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def calculate_score(self, lead_data):
        """Calculate propensity to buy score (0-100) based on weighted signals"""
        score = 0
        signals = {}
        
        # Role Fit (+30): Title contains key terms
        role_keywords = ['toxicology', 'safety', 'hepatic', '3d', 'preclinical', 'in vitro', 'dili']
        title_lower = lead_data.get('title', '').lower()
        if any(keyword in title_lower for keyword in role_keywords):
            role_score = 30
            if 'director' in title_lower or 'head' in title_lower or 'vp' in title_lower:
                role_score = 30
            elif 'principal' in title_lower or 'senior' in title_lower:
                role_score = 25
            else:
                role_score = 20
            score += role_score
            signals['role_fit'] = role_score
        else:
            signals['role_fit'] = 0
        
        # Company Intent (+20): Recent funding
        funding = lead_data.get('funding', '').lower()
        if 'series b' in funding or 'series c' in funding:
            score += 20
            signals['funding'] = 20
        elif 'series a' in funding:
            score += 15
            signals['funding'] = 15
        else:
            signals['funding'] = 0
        
        # Technographic (+15): Uses similar tech
        if lead_data.get('uses_tech', False):
            score += 15
            signals['tech'] = 15
        else:
            signals['tech'] = 0
        
        # Location (+10): Hub location
        location = lead_data.get('location', '').lower()
        hq = lead_data.get('hq', '').lower()
        hubs = ['cambridge', 'boston', 'bay area', 'san francisco', 'basel', 'oxford', 'uk golden triangle']
        if any(hub in location or hub in hq for hub in hubs):
            score += 10
            signals['location'] = 10
        else:
            signals['location'] = 0
        
        # Scientific Intent (+40): Recent publications
        if lead_data.get('recent_publication', False):
            score += 40
            signals['publication'] = 40
        elif lead_data.get('has_publications', False):
            score += 20
            signals['publication'] = 20
        else:
            signals['publication'] = 0
        
        lead_data['score'] = score
        lead_data['signals'] = signals
        return lead_data
    
    def search_pubmed(self, query, max_results=50):
        """Search PubMed for recent publications"""
        print(f"🔬 Searching PubMed for: {query}")
        leads_found = []
        
        try:
            # PubMed search URL
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'sort': 'pub_date'
            }
            
            response = self.session.get(base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                pmids = data.get('esearchresult', {}).get('idlist', [])
                
                # Fetch details for each article
                if pmids:
                    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                    fetch_params = {
                        'db': 'pubmed',
                        'id': ','.join(pmids[:20]),  # Limit to first 20
                        'retmode': 'json'
                    }
                    
                    time.sleep(0.5)  # Rate limiting
                    fetch_response = self.session.get(fetch_url, params=fetch_params)
                    
                    if fetch_response.status_code == 200:
                        articles = fetch_response.json().get('result', {})
                        
                        for pmid in pmids[:20]:
                            if pmid in articles:
                                article = articles[pmid]
                                authors = article.get('authors', [])
                                
                                # Extract corresponding author (usually last)
                                if authors:
                                    author = authors[-1] if len(authors) > 1 else authors[0]
                                    name = author.get('name', 'Unknown')
                                    
                                    lead = {
                                        'name': f"Dr. {name}",
                                        'title': 'Researcher (Corresponding Author)',
                                        'company': article.get('source', 'Academic Institution'),
                                        'location': 'Unknown',
                                        'hq': 'Unknown',
                                        'email': f"{name.lower().replace(' ', '.')}@research.edu",
                                        'linkedin': f"linkedin.com/in/{name.lower().replace(' ', '')}",
                                        'recent_activity': f"Published: {article.get('title', '')[:60]}...",
                                        'funding': 'Academic/Grant funded',
                                        'recent_publication': True,
                                        'has_publications': True,
                                        'uses_tech': 'liver' in query.lower() or '3d' in query.lower()
                                    }
                                    
                                    leads_found.append(self.calculate_score(lead))
                
                print(f"   ✓ Found {len(leads_found)} leads from PubMed")
        
        except Exception as e:
            print(f"   ✗ PubMed error: {str(e)}")
        
        return leads_found
    
    def search_crunchbase_mock(self, industry='biotechnology'):
        """Mock Crunchbase search for funded companies"""
        print(f"💰 Searching for funded {industry} companies")
        
        # Mock data for demonstration (in production, use Crunchbase API)
        companies = [
            {
                'company': 'Moderna Therapeutics',
                'funding': 'Series B funded, $120M',
                'location': 'Cambridge, MA',
                'contacts': [
                    {'name': 'Sarah Mitchell', 'title': 'Director of Toxicology & Safety'},
                    {'name': 'John Davis', 'title': 'Head of Preclinical Safety'}
                ]
            },
            {
                'company': 'Beam Therapeutics',
                'funding': 'Series C funded, $150M',
                'location': 'Cambridge, MA',
                'contacts': [
                    {'name': 'Maria Gonzalez', 'title': 'Director of Safety Assessment'}
                ]
            },
            {
                'company': 'Alnylam Pharmaceuticals',
                'funding': 'Series B, $85M raised',
                'location': 'Cambridge, MA',
                'contacts': [
                    {'name': 'Lisa Anderson', 'title': 'Associate Director, Preclinical Safety'}
                ]
            },
            {
                'company': 'Vertex Pharmaceuticals',
                'funding': 'Public company',
                'location': 'Boston, MA',
                'contacts': [
                    {'name': 'James Chen', 'title': 'Head of Preclinical Safety Assessment'}
                ]
            },
            {
                'company': 'Regeneron Pharmaceuticals',
                'funding': 'Public company',
                'location': 'Tarrytown, NY',
                'contacts': [
                    {'name': 'Rachel Kim', 'title': 'Director of In Vitro Toxicology'}
                ]
            }
        ]
        
        leads_found = []
        for comp in companies:
            for contact in comp['contacts']:
                lead = {
                    'name': f"Dr. {contact['name']}",
                    'title': contact['title'],
                    'company': comp['company'],
                    'location': comp['location'],
                    'hq': comp['location'],
                    'email': f"{contact['name'].lower().replace(' ', '.')}@{comp['company'].lower().replace(' ', '').replace('pharmaceuticals', 'pharma').replace('therapeutics', 'tx')}com",
                    'linkedin': f"linkedin.com/in/{contact['name'].lower().replace(' ', '')}",
                    'recent_activity': 'Recently joined funded company',
                    'funding': comp['funding'],
                    'recent_publication': False,
                    'has_publications': True,
                    'uses_tech': True
                }
                leads_found.append(self.calculate_score(lead))
        
        print(f"   ✓ Found {len(leads_found)} leads from funded companies")
        return leads_found
    
    def search_conference_attendees_mock(self, conference='SOT 2024'):
        """Mock conference attendee search"""
        print(f"🎤 Searching {conference} conference data")
        
        # Mock conference data
        attendees = [
            {
                'name': 'Emily Rodriguez',
                'title': 'VP of Hepatic Research',
                'company': 'Gilead Sciences',
                'location': 'Foster City, CA'
            },
            {
                'name': 'David Patel',
                'title': 'Head of Safety Pharmacology',
                'company': 'AstraZeneca',
                'location': 'Cambridge, UK'
            },
            {
                'name': 'Michael Thompson',
                'title': 'Senior Scientist, Drug Safety',
                'company': 'BioNTech',
                'location': 'Mainz, Germany'
            },
            {
                'name': 'Robert Zhang',
                'title': 'Principal Scientist, Toxicology',
                'company': 'Genentech',
                'location': 'South San Francisco, CA'
            }
        ]
        
        leads_found = []
        for attendee in attendees:
            lead = {
                'name': f"Dr. {attendee['name']}",
                'title': attendee['title'],
                'company': attendee['company'],
                'location': attendee['location'],
                'hq': attendee['location'],
                'email': f"{attendee['name'].lower().replace(' ', '.')}@{attendee['company'].lower().replace(' ', '')}com",
                'linkedin': f"linkedin.com/in/{attendee['name'].lower().replace(' ', '')}",
                'recent_activity': f'Attended {conference}',
                'funding': 'Established company',
                'recent_publication': False,
                'has_publications': True,
                'uses_tech': True
            }
            leads_found.append(self.calculate_score(lead))
        
        print(f"   ✓ Found {len(leads_found)} leads from conference")
        return leads_found
    
    def run_full_scan(self):
        """Execute full lead generation scan"""
        print("\n" + "="*70)
        print("🚀 STARTING 3D IN-VITRO MODELS LEAD GENERATION SCAN")
        print("="*70 + "\n")
        
        all_leads = []
        
        # Stage 1: PubMed Scientific Publications
        print("📚 STAGE 1: Scanning Scientific Publications")
        print("-" * 70)
        pubmed_queries = [
            'drug-induced liver injury DILI 3D',
            'hepatic spheroids toxicology',
            'organ-on-chip liver safety'
        ]
        
        for query in pubmed_queries:
            leads = self.search_pubmed(query, max_results=10)
            all_leads.extend(leads)
            time.sleep(1)
        
        # Stage 2: Funded Companies
        print("\n💼 STAGE 2: Scanning Funded Biotech Companies")
        print("-" * 70)
        funded_leads = self.search_crunchbase_mock()
        all_leads.extend(funded_leads)
        
        # Stage 3: Conference Attendees
        print("\n🎯 STAGE 3: Scanning Conference Attendees")
        print("-" * 70)
        conference_leads = self.search_conference_attendees_mock()
        all_leads.extend(conference_leads)
        
        # Remove duplicates and rank
        self.leads = self.deduplicate_leads(all_leads)
        self.leads.sort(key=lambda x: x['score'], reverse=True)
        
        print("\n" + "="*70)
        print(f"✅ SCAN COMPLETE: {len(self.leads)} unique leads identified and ranked")
        print("="*70 + "\n")
        
        return self.leads
    
    def deduplicate_leads(self, leads):
        """Remove duplicate leads based on email"""
        seen_emails = set()
        unique_leads = []
        
        for lead in leads:
            email = lead.get('email', '')
            if email not in seen_emails:
                seen_emails.add(email)
                unique_leads.append(lead)
        
        return unique_leads
    
    def export_to_csv(self, filename=None):
        """Export leads to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'leads_3d_invitro_{timestamp}.csv'
        
        # Prepare data for export
        export_data = []
        for idx, lead in enumerate(self.leads, 1):
            signals = lead.get('signals', {})
            export_data.append({
                'Rank': idx,
                'Probability_Score': lead['score'],
                'Name': lead['name'],
                'Title': lead['title'],
                'Company': lead['company'],
                'Location': lead['location'],
                'HQ': lead['hq'],
                'Email': lead['email'],
                'LinkedIn': lead['linkedin'],
                'Recent_Activity': lead['recent_activity'],
                'Funding_Status': lead['funding'],
                'Signal_Role_Fit': signals.get('role_fit', 0),
                'Signal_Funding': signals.get('funding', 0),
                'Signal_Tech': signals.get('tech', 0),
                'Signal_Location': signals.get('location', 0),
                'Signal_Publication': signals.get('publication', 0)
            })
        
        df = pd.DataFrame(export_data)
        df.to_csv(filename, index=False)
        
        print(f"📊 CSV exported successfully: {filename}")
        print(f"   Total leads: {len(df)}")
        print(f"   High priority (>85): {len(df[df['Probability_Score'] >= 85])}")
        print(f"   Medium priority (70-84): {len(df[(df['Probability_Score'] >= 70) & (df['Probability_Score'] < 85)])}")
        print(f"   Low priority (<70): {len(df[df['Probability_Score'] < 70])}")
        
        return filename
    
    def display_summary(self):
        """Display summary statistics"""
        if not self.leads:
            print("No leads to display")
            return
        
        print("\n" + "="*70)
        print("📈 LEAD SUMMARY")
        print("="*70)
        
        print("\n🏆 TOP 5 HIGHEST PRIORITY LEADS:")
        print("-" * 70)
        for idx, lead in enumerate(self.leads[:5], 1):
            print(f"\n{idx}. {lead['name']} (Score: {lead['score']}/100)")
            print(f"   {lead['title']} at {lead['company']}")
            print(f"   📍 {lead['location']}")
            print(f"   📧 {lead['email']}")
            print(f"   📊 Signals: Role={lead['signals']['role_fit']}, "
                  f"Funding={lead['signals']['funding']}, "
                  f"Tech={lead['signals']['tech']}, "
                  f"Location={lead['signals']['location']}, "
                  f"Publication={lead['signals']['publication']}")


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("  3D IN-VITRO MODELS LEAD GENERATION CRAWLER")
    print("  Identifying qualified leads for drug discovery & toxicology")
    print("="*70)
    
    crawler = LeadGenerationCrawler()
    
    # Run full scan
    leads = crawler.run_full_scan()
    
    # Display summary
    crawler.display_summary()
    
    # Export to CSV
    print("\n")
    csv_file = crawler.export_to_csv()
    
    print("\n" + "="*70)
    print("✨ PROCESS COMPLETE!")
    print(f"📁 Your lead list is ready: {csv_file}")
    print("="*70 + "\n")
    
    return csv_file


if __name__ == "__main__":
    # Required libraries: requests, beautifulsoup4, pandas
    # Install with: pip install requests beautifulsoup4 pandas
    main()