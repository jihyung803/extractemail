"""
Enhanced email extraction from websites
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
import time
import json


class EmailExtractor:
    """Enhanced email extractor that finds emails in various formats and locations"""
    
    def __init__(self, timeout: int = 10, max_pages: int = 5):
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
        
        # Enhanced email regex patterns
        self.email_patterns = [
            # Standard email pattern
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
            # Email with spaces around @
            re.compile(r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),
            # Obfuscated emails: email[at]domain[dot]com
            re.compile(r'\b[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Z|a-z]{2,}\b', re.IGNORECASE),
            # Obfuscated emails: email(at)domain(dot)com
            re.compile(r'\b[A-Za-z0-9._%+-]+\s*\(at\)\s*[A-Za-z0-9.-]+\s*\(dot\)\s*[A-Z|a-z]{2,}\b', re.IGNORECASE),
            # Obfuscated emails: email AT domain DOT com
            re.compile(r'\b[A-Za-z0-9._%+-]+\s+AT\s+[A-Za-z0-9.-]+\s+DOT\s+[A-Z|a-z]{2,}\b', re.IGNORECASE),
        ]
        
        # Common email-related page paths to check (expanded)
        self.email_paths = [
            '',  # main page
            '/contact',
            '/contact-us',
            '/contactus',
            '/about',
            '/about-us',
            '/aboutus',
            '/support',
            '/help',
            '/info',
            '/inquiry',
            '/customer-service',
            '/customer-support',
            '/get-in-touch',
            '/reach-us',
            '/feedback',
            '/questions'
        ]
    
    def extract_emails_from_website(self, website_url: str) -> List[str]:
        """
        Extract email addresses from a website using enhanced methods
        
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
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"Error crawling {url}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error processing website {website_url}: {e}")
        
        # Filter out invalid emails and apply length restrictions
        filtered_emails = self._filter_and_clean_emails(list(emails), base_domain)
        return filtered_emails
    
    def _extract_emails_from_page(self, url: str, base_domain: str) -> Set[str]:
        """
        Extract emails from a single page using multiple methods
        
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
            raw_html = response.text
            
            # Method 1: Extract from text content
            emails.update(self._extract_from_text(soup))
            
            # Method 2: Extract from mailto links
            emails.update(self._extract_from_mailto_links(soup))
            
            # Method 3: Extract from form actions
            emails.update(self._extract_from_forms(soup))
            
            # Method 4: Extract from JavaScript code
            emails.update(self._extract_from_javascript(raw_html))
            
            # Method 5: Extract from hidden inputs and data attributes
            emails.update(self._extract_from_hidden_elements(soup))
            
            # Method 6: Extract from comments
            emails.update(self._extract_from_comments(raw_html))
        
        except requests.exceptions.RequestException as e:
            print(f"Request error for {url}: {e}")
        except Exception as e:
            print(f"Parsing error for {url}: {e}")
        
        return emails
    
    def _extract_from_text(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from visible text content"""
        emails = set()
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Apply all email patterns
        for pattern in self.email_patterns:
            found_emails = pattern.findall(text)
            for email in found_emails:
                cleaned_email = self._clean_obfuscated_email(email)
                if cleaned_email:
                    emails.add(cleaned_email.lower())
        
        return emails
    
    def _extract_from_mailto_links(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from mailto links"""
        emails = set()
        
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.IGNORECASE))
        for link in mailto_links:
            href = link.get('href', '')
            if href.lower().startswith('mailto:'):
                email = href[7:].split('?')[0].split('&')[0]  # Remove query params
                cleaned_email = self._clean_obfuscated_email(email)
                if cleaned_email and self._is_basic_email_valid(cleaned_email):
                    emails.add(cleaned_email.lower())
        
        return emails
    
    def _extract_from_forms(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from form actions and hidden inputs"""
        emails = set()
        
        # Check form actions
        forms = soup.find_all('form')
        for form in forms:
            action = form.get('action', '')
            if action:
                # Look for emails in form action URLs
                for pattern in self.email_patterns:
                    found_emails = pattern.findall(action)
                    for email in found_emails:
                        cleaned_email = self._clean_obfuscated_email(email)
                        if cleaned_email:
                            emails.add(cleaned_email.lower())
        
        return emails
    
    def _extract_from_javascript(self, html_content: str) -> Set[str]:
        """Extract emails from JavaScript code"""
        emails = set()
        
        # Find script tags and extract their content
        script_pattern = re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
        scripts = script_pattern.findall(html_content)
        
        for script in scripts:
            # Apply email patterns to JavaScript content
            for pattern in self.email_patterns:
                found_emails = pattern.findall(script)
                for email in found_emails:
                    cleaned_email = self._clean_obfuscated_email(email)
                    if cleaned_email:
                        emails.add(cleaned_email.lower())
            
            # Look for string concatenation patterns (common obfuscation)
            # Example: "contact" + "@" + "domain.com"
            concat_pattern = re.compile(r'["\']([a-zA-Z0-9._%+-]+)["\']\s*\+\s*["\']@["\']\s*\+\s*["\']([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', re.IGNORECASE)
            concat_matches = concat_pattern.findall(script)
            for local, domain in concat_matches:
                email = f"{local}@{domain}"
                if self._is_basic_email_valid(email):
                    emails.add(email.lower())
        
        return emails
    
    def _extract_from_hidden_elements(self, soup: BeautifulSoup) -> Set[str]:
        """Extract emails from hidden inputs and data attributes"""
        emails = set()
        
        # Check hidden input values
        hidden_inputs = soup.find_all('input', type='hidden')
        for input_elem in hidden_inputs:
            value = input_elem.get('value', '')
            if value:
                for pattern in self.email_patterns:
                    found_emails = pattern.findall(value)
                    for email in found_emails:
                        cleaned_email = self._clean_obfuscated_email(email)
                        if cleaned_email:
                            emails.add(cleaned_email.lower())
        
        # Check data attributes (fixed error handling)
        try:
            elements_with_data = soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()) if x else False)
            for elem in elements_with_data:
                if hasattr(elem, 'attrs') and elem.attrs:
                    for attr_name, attr_value in elem.attrs.items():
                        if attr_name.startswith('data-') and isinstance(attr_value, str):
                            for pattern in self.email_patterns:
                                found_emails = pattern.findall(attr_value)
                                for email in found_emails:
                                    cleaned_email = self._clean_obfuscated_email(email)
                                    if cleaned_email:
                                        emails.add(cleaned_email.lower())
        except Exception as e:
            # Silently ignore data attribute parsing errors
            pass
        
        return emails
    
    def _extract_from_comments(self, html_content: str) -> Set[str]:
        """Extract emails from HTML comments"""
        emails = set()
        
        # Find HTML comments
        comment_pattern = re.compile(r'<!--(.*?)-->', re.DOTALL)
        comments = comment_pattern.findall(html_content)
        
        for comment in comments:
            for pattern in self.email_patterns:
                found_emails = pattern.findall(comment)
                for email in found_emails:
                    cleaned_email = self._clean_obfuscated_email(email)
                    if cleaned_email:
                        emails.add(cleaned_email.lower())
        
        return emails
    
    def _clean_obfuscated_email(self, email: str) -> Optional[str]:
        """
        Clean and deobfuscate email addresses
        
        Args:
            email (str): Raw email that might be obfuscated
            
        Returns:
            Optional[str]: Cleaned email or None if invalid
        """
        if not email:
            return None
        
        # Remove extra spaces
        email = re.sub(r'\s+', '', email)
        
        # Replace obfuscation patterns
        replacements = [
            (r'\[at\]', '@'),
            (r'\(at\)', '@'),
            (r'\s+AT\s+', '@'),
            (r'\[dot\]', '.'),
            (r'\(dot\)', '.'),
            (r'\s+DOT\s+', '.'),
        ]
        
        for pattern, replacement in replacements:
            email = re.sub(pattern, replacement, email, flags=re.IGNORECASE)
        
        # Final cleanup
        email = email.strip().lower()
        
        # Basic validation
        if self._is_basic_email_valid(email):
            return email
        
        return None
    
    def _is_basic_email_valid(self, email: str) -> bool:
        """Basic email validation"""
        if not email or '@' not in email or '.' not in email:
            return False
        
        # Check email length (exclude emails longer than 30 characters as requested)
        if len(email) > 30:
            return False
        
        # Check for valid email pattern
        pattern = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', re.IGNORECASE)
        return bool(pattern.match(email))
    
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
    
    def _filter_and_clean_emails(self, emails: List[str], base_domain: str) -> List[str]:
        """
        Filter and clean email list with enhanced validation
        
        Args:
            emails (List[str]): Raw email list
            base_domain (str): Base domain of the website
            
        Returns:
            List[str]: Filtered and cleaned email list
        """
        if not emails:
            return []
        
        filtered_emails = []
        
        for email in emails:
            email = email.lower().strip()
            
            # Skip if not basic valid
            if not self._is_basic_email_valid(email):
                continue
            
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
                'user@user',
                'email@email',
                'info@info',
                'contact@contact',
                'sample@sample',
                'demo@demo'
            ]
            
            if any(pattern in email for pattern in invalid_patterns):
                continue
            
            # Skip test emails pattern
            local_part, domain_part = email.split('@')
            if local_part == domain_part.split('.')[0]:  # Skip emails like test@test.com
                continue
            
            # Skip very short or suspicious emails
            if len(email) < 6:  # Minimum reasonable email length
                continue
            
            # Skip emails with too many numbers (likely generated/fake)
            local_part = email.split('@')[0]
            if len(re.findall(r'\d', local_part)) / len(local_part) > 0.7:
                continue
            
            filtered_emails.append(email)
        
        # Remove duplicates and sort by relevance
        unique_emails = list(set(filtered_emails))
        
        # Sort by domain relevance and email quality
        def email_priority(email):
            domain = email.split('@')[1].lower()
            local = email.split('@')[0].lower()
            
            score = 0
            
            # Prefer emails from the same domain
            if base_domain and domain in base_domain:
                score += 100
            
            # Prefer common business email patterns
            business_keywords = ['contact', 'info', 'support', 'hello', 'mail', 'office']
            if any(keyword in local for keyword in business_keywords):
                score += 50
            
            # Prefer common business domains
            business_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'naver.com', 'daum.net']
            if domain in business_domains:
                score += 30
            
            # Prefer shorter, cleaner emails
            score += max(0, 30 - len(email))
            
            return score
        
        unique_emails.sort(key=email_priority, reverse=True)
        
        return unique_emails[:10]  # Limit to top 10 emails per website 