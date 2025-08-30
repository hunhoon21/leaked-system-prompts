#!/usr/bin/env python3
"""
Analysis script to show how files would be processed by the migration script.
Shows sample processing without actually moving files.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Big Tech companies that get separate directories
BIG_TECH_COMPANIES = {
    'openai': 'OpenAI',
    'anthropic': 'Anthropic', 
    'google': 'Google',
    'microsoft': 'Microsoft',
    'xai': 'xAI'
}

def extract_company_and_model(filename: str) -> Tuple[str, str]:
    """Extract company name and model from filename."""
    base_name = filename.replace('.md', '')
    
    # Handle special cases first
    if base_name.startswith('xAI-'):
        # xAI files: xAI-grok3_20250509.md -> xai, grok3
        match = re.match(r'^xAI-(.+)_(\d{8})$', base_name)
        if match:
            return 'xai', match.group(1)
    
    # Standard pattern: company-model_date
    match = re.match(r'^([^-]+)-(.+)_(\d{8})$', base_name)
    if match:
        company = match.group(1).lower()
        model = match.group(2)
        return company, model
    
    # Pattern without model: company_date
    match = re.match(r'^([^_]+)_(\d{8})$', base_name)
    if match:
        company = match.group(1).lower()
        return company, ""
    
    # Files with just company prefix
    for company in BIG_TECH_COMPANIES:
        if base_name.lower().startswith(company):
            remaining = base_name[len(company):].lstrip('-_')
            return company, remaining
    
    # Default: no specific company identified
    return "", base_name

def extract_date_from_filename(filename: str) -> Optional[str]:
    """Extract date from filename in format YYYYMMDD."""
    match = re.search(r'_(\d{8})', filename)
    if match:
        date_str = match.group(1)
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

def create_title_from_filename(filename: str, company: str, model: str) -> str:
    """Create a human-readable title from filename components."""
    base_name = filename.replace('.md', '')
    
    # Extract date for display
    date_match = re.search(r'_(\d{8})', base_name)
    date_part = ""
    if date_match:
        date_str = date_match.group(1)
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            date_part = f" ({date_obj.strftime('%Y.%m.%d')})"
        except ValueError:
            pass
    
    # Create title based on available information
    if company and model:
        # Clean up model name
        model_clean = model.replace('-', '-').replace('_', ' ')
        # Handle version numbers and special formatting
        if re.match(r'^[\d.]+$', model_clean):
            # Just version numbers
            model_title = model_clean
        else:
            # Capitalize appropriately
            parts = model_clean.split('-')
            model_title = '-'.join([
                part.upper() if part.lower() in ['ai', 'gpt', 'api', 'cli', 'ios', 'ide'] 
                else part.capitalize() 
                for part in parts
            ])
        
        return f"{model_title}{date_part}"
    elif model:
        # Just model, no company
        return f"{model.replace('_', ' ').title()}{date_part}"
    else:
        # Fallback
        return base_name.replace('_', ' ').replace('-', ' ').title()

def analyze_files():
    """Analyze how files would be processed."""
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent
    
    print(f"Analyzing markdown files in: {parent_dir}")
    
    # Find all markdown files
    md_files = list(parent_dir.glob("*.md"))
    print(f"Found {len(md_files)} markdown files")
    
    # Categorize files
    big_tech_files = defaultdict(list)
    ai_service_files = []
    korean_files = []
    system_files = []
    
    sample_processing = []
    
    for file_path in sorted(md_files):
        filename = file_path.name
        
        # Skip Korean translations
        if filename.endswith('_KR.md'):
            korean_files.append(filename)
            continue
        
        # Skip system files
        if filename.lower() in ['readme.md']:
            system_files.append(filename)
            continue
        
        # Extract info
        company, model = extract_company_and_model(filename)
        date = extract_date_from_filename(filename)
        title = create_title_from_filename(filename, company, model)
        
        # Determine category
        if company.lower() in BIG_TECH_COMPANIES:
            target_dir = f"docs/big-tech/{company.lower()}"
            big_tech_files[company.lower()].append({
                'filename': filename,
                'model': model,
                'title': title,
                'date': date,
                'target_dir': target_dir
            })
        else:
            target_dir = "docs/ai-services"
            ai_service_files.append({
                'filename': filename,
                'company': company or 'other',
                'model': model,
                'title': title,
                'date': date,
                'target_dir': target_dir
            })
        
        # Add to sample for first 10 files
        if len(sample_processing) < 10:
            sample_processing.append({
                'filename': filename,
                'company': company or 'other',
                'model': model,
                'title': title,
                'date': date,
                'target_dir': target_dir
            })
    
    # Print analysis results
    print(f"\n=== File Categorization ===")
    print(f"Korean translations (will be skipped): {len(korean_files)}")
    print(f"System files (will be skipped): {len(system_files)}")
    print(f"Big Tech files: {sum(len(files) for files in big_tech_files.values())}")
    print(f"AI Service files: {len(ai_service_files)}")
    
    print(f"\n=== Big Tech Breakdown ===")
    for company, files in sorted(big_tech_files.items()):
        print(f"{BIG_TECH_COMPANIES[company]}: {len(files)} files")
        # Show a few examples
        for i, file_info in enumerate(files[:3]):
            print(f"  • {file_info['filename']} → {file_info['title']}")
        if len(files) > 3:
            print(f"  ... and {len(files) - 3} more")
        print()
    
    print(f"=== AI Services Sample ===")
    ai_companies = defaultdict(int)
    for file_info in ai_service_files:
        ai_companies[file_info['company']] += 1
    
    for company, count in sorted(ai_companies.items()):
        print(f"{company}: {count} files")
    
    print(f"\n=== Sample File Processing ===")
    for i, file_info in enumerate(sample_processing):
        print(f"{i+1}. {file_info['filename']}")
        print(f"   → Title: \"{file_info['title']}\"")
        print(f"   → Date: {file_info['date']}")
        print(f"   → Target: {file_info['target_dir']}")
        print(f"   → Company: {file_info['company']}")
        print()
    
    print(f"=== Files that would be skipped ===")
    if korean_files:
        print(f"Korean translations ({len(korean_files)}):")
        for filename in korean_files[:5]:
            print(f"  • {filename}")
        if len(korean_files) > 5:
            print(f"  ... and {len(korean_files) - 5} more")
        print()
    
    if system_files:
        print(f"System files ({len(system_files)}):")
        for filename in system_files:
            print(f"  • {filename}")
        print()

if __name__ == "__main__":
    analyze_files()
