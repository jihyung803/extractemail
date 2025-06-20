"""
Email extraction from websites
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
import time


class EmailExtractor:
    """Extract email addresses from websites"""
    
    def __init__(self, timeout: int = 10, max_pages: int = 3):
        """
        Initialize email extractor
        
        Args:
            timeout (int): Request timeout in seconds
            max_pages (int): Maximum number of pages to crawl per website
        """
        self.timeout = timeout
        self.max_pages = max_pages
        self.session = requests.Session()
        
        # Set a user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Email regex pattern
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Common email-related page paths to check
        self.email_paths = [
            '',  # main page
            '/contact',
            '/contact-us',
            '/about',
            '/about-us',
            '/support',
            '/help',
            '/info'
        ]
    
    def extract_emails_from_website(self, website_url: str) -> List[str]:
        """
        Extract email addresses from a website
        
        Args:
            website_url (str): Website URL to crawl
            
        Returns:
            List[str]: List of unique email addresses found
        """
        if not website_url or not self._is_valid_url(website_url):
            return []
        
        emails = set()
        pages_crawled = 0
        
        try:
            # Normalize URL
            if not website_url.startswith(('http://', 'https://')):
                website_url = 'https://' + website_url
            
            base_domain = self._get_base_domain(website_url)
            
            # Try different pages that might contain contact information
            for path in self.email_paths:
                if pages_crawled >= self.max_pages:
                    break
                
                try:
                    url = urljoin(website_url, path)
                    page_emails = self._extract_emails_from_page(url, base_domain)
                    emails.update(page_emails)
                    pages_crawled += 1
                    
                    # Small delay between requests
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error crawling {url}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error processing website {website_url}: {e}")
        
        # Filter out common false positives and suspicious emails
        filtered_emails = self._filter_emails(list(emails))
        return filtered_emails
    
    def _extract_emails_from_page(self, url: str, base_domain: str) -> Set[str]:
        """
        Extract emails from a single page
        
        Args:
            url (str): Page URL
            base_domain (str): Base domain to validate emails
            
        Returns:
            Set[str]: Set of email addresses found on the page
        """
        emails = set()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Find emails in text
            found_emails = self.email_pattern.findall(text)
            
            # Also check mailto links
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                href = link.get('href', '')
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').split('?')[0]  # Remove query params
                    if self.email_pattern.match(email):
                        found_emails.append(email)
            
            # Add valid emails
            for email in found_emails:
                email = email.lower().strip()
                if self._is_valid_email(email, base_domain):
                    emails.add(email)
        
        except requests.exceptions.RequestException as e:
            print(f"Request error for {url}: {e}")
        except Exception as e:
            print(f"Parsing error for {url}: {e}")
        
        return emails
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            if not url:
                return False
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            return bool(parsed.netloc) and bool(parsed.scheme)
        except:
            return False
    
    def _get_base_domain(self, url: str) -> str:
        """Get base domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _is_valid_email(self, email: str, base_domain: str) -> bool:
        """
        Validate email address
        
        Args:
            email (str): Email address to validate
            base_domain (str): Base domain of the website
            
        Returns:
            bool: True if email is valid
        """
        if not email or '@' not in email:
            return False
        
        # Skip obviously invalid emails
        invalid_patterns = [
            'example.com',
            'test.com',
            'dummy.com',
            'placeholder',
            'noreply',
            'no-reply',
            'donotreply',
            'admin@admin',
            'test@test',
            'user@user'
        ]
        
        email_lower = email.lower()
        for pattern in invalid_patterns:
            if pattern in email_lower:
                return False
        
        # Prefer emails from the same domain or common business domains
        email_domain = email.split('@')[1].lower()
        
        # Check if it's from the same domain
        if base_domain and email_domain in base_domain:
            return True
        
        # Allow common business email domains
        business_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'naver.com', 'daum.net', 'hanmail.net', 'kakao.com'
        ]
        
        if email_domain in business_domains:
            return True
        
        # If it's a different domain, it should be related to the base domain
        if base_domain:
            base_parts = base_domain.split('.')
            email_parts = email_domain.split('.')
            
            # Check if they share common parts
            if len(base_parts) >= 2 and len(email_parts) >= 2:
                if base_parts[-2] in email_parts:  # Same company name
                    return True
        
        # Default: accept if it passed the basic regex
        return True
    
    def _filter_emails(self, emails: List[str]) -> List[str]:
        """
        Filter and clean email list
        
        Args:
            emails (List[str]): Raw email list
            
        Returns:
            List[str]: Filtered and cleaned email list
        """
        if not emails:
            return []
        
        # Remove duplicates and sort
        unique_emails = list(set(email.lower().strip() for email in emails))
        
        # Sort by relevance (business domains first, then others)
        business_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        
        def email_priority(email):
            domain = email.split('@')[1].lower()
            if any(bd in domain for bd in business_domains):
                return 1  # Business email
            return 0  # Other domain
        
        unique_emails.sort(key=email_priority, reverse=True)
        
        return unique_emails[:5]  # Limit to top 5 emails per website 