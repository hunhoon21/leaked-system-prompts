#!/usr/bin/env python3
"""
Script to migrate markdown files from parent directory to Docusaurus structure.
Categorizes files by company and formats them with proper frontmatter.
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

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
    # Remove .md extension
    base_name = filename.replace('.md', '')
    
    # Try to match pattern: company-model_date
    match = re.match(r'^([^-]+)-(.+)_(\d{8})$', base_name)
    if match:
        company = match.group(1).lower()
        model = match.group(2)
        return company, model
    
    # Try to match pattern: company_date (no model)
    match = re.match(r'^([^_]+)_(\d{8})$', base_name)
    if match:
        company = match.group(1).lower()
        return company, ""
    
    # For files without clear pattern, try to extract company from start
    parts = base_name.split('-')
    if parts:
        potential_company = parts[0].lower()
        if potential_company in BIG_TECH_COMPANIES:
            model = '-'.join(parts[1:]) if len(parts) > 1 else ""
            return potential_company, model
    
    # Default: treat entire filename as model, no specific company
    return "", base_name

def extract_date_from_filename(filename: str) -> Optional[str]:
    """Extract date from filename in format YYYYMMDD."""
    match = re.search(r'_(\d{8})', filename)
    if match:
        date_str = match.group(1)
        try:
            # Parse and reformat date
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None

def create_title_from_filename(filename: str, company: str, model: str) -> str:
    """Create a human-readable title from filename components."""
    base_name = filename.replace('.md', '')
    
    # Extract date
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
        # Format model name nicely
        model_formatted = model.replace('-', '-').replace('_', ' ')
        # Capitalize appropriately
        model_parts = model_formatted.split('-')
        model_title = '-'.join([part.capitalize() if not re.match(r'^\d', part) else part for part in model_parts])
        return f"{model_title}{date_part}"
    elif model:
        # Just model name
        model_formatted = model.replace('-', ' ').replace('_', ' ')
        return f"{model_formatted.title()}{date_part}"
    else:
        # Fallback to filename
        return base_name.replace('_', ' ').replace('-', ' ').title()

def determine_target_directory(company: str) -> str:
    """Determine target directory based on company."""
    if company.lower() in BIG_TECH_COMPANIES:
        return f"docs/big-tech/{company.lower()}"
    else:
        return "docs/ai-services"

def create_frontmatter(title: str, date: Optional[str]) -> str:
    """Create Docusaurus frontmatter for the file."""
    frontmatter = "---\n"
    frontmatter += f"title: \"{title}\"\n"
    if date:
        frontmatter += f"date: {date}\n"
    frontmatter += "---\n\n"
    return frontmatter

def process_file(file_path: Path, target_base: Path) -> Dict:
    """Process a single markdown file."""
    filename = file_path.name
    
    # Skip Korean translations
    if filename.endswith('_KR.md'):
        return {"status": "skipped", "reason": "Korean translation"}
    
    # Skip README and other non-prompt files
    if filename.lower() in ['readme.md']:
        return {"status": "skipped", "reason": "System file"}
    
    try:
        # Extract company and model info
        company, model = extract_company_and_model(filename)
        date = extract_date_from_filename(filename)
        title = create_title_from_filename(filename, company, model)
        
        # Determine target directory
        target_dir = determine_target_directory(company)
        target_path = target_base / target_dir
        
        # Ensure target directory exists
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create new content with frontmatter
        frontmatter = create_frontmatter(title, date)
        new_content = frontmatter + content
        
        # Write to target location
        target_file = target_path / filename
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {
            "status": "success",
            "company": company or "other",
            "model": model,
            "title": title,
            "date": date,
            "target": str(target_file)
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def create_category_files():
    """Create _category_.json files for directories that don't have them."""
    categories = {
        "docs/big-tech/openai": {"label": "OpenAI", "position": 1},
        "docs/big-tech/anthropic": {"label": "Anthropic", "position": 2}, 
        "docs/big-tech/google": {"label": "Google", "position": 3},
        "docs/big-tech/microsoft": {"label": "Microsoft", "position": 4},
        "docs/big-tech/xai": {"label": "xAI", "position": 5}
    }
    
    for dir_path, config in categories.items():
        category_file = Path(dir_path) / "_category_.json"
        if not category_file.exists():
            category_file.parent.mkdir(parents=True, exist_ok=True)
            with open(category_file, 'w') as f:
                f.write(f'{{\n  "label": "{config["label"]}",\n  "position": {config["position"]}\n}}\n')

def main():
    """Main migration function."""
    # Get script directory
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent
    
    print(f"Scanning for markdown files in: {parent_dir}")
    
    # Find all markdown files in parent directory
    md_files = list(parent_dir.glob("*.md"))
    print(f"Found {len(md_files)} markdown files")
    
    # Create category files
    create_category_files()
    
    # Process files
    results = {"success": [], "skipped": [], "errors": []}
    company_counts = {}
    
    for file_path in md_files:
        print(f"Processing: {file_path.name}")
        result = process_file(file_path, script_dir)
        
        if result["status"] == "success":
            results["success"].append(result)
            company = result["company"]
            company_counts[company] = company_counts.get(company, 0) + 1
        elif result["status"] == "skipped":
            results["skipped"].append({"file": file_path.name, "reason": result["reason"]})
        else:
            results["errors"].append({"file": file_path.name, "error": result["error"]})
    
    # Print summary
    print(f"\n=== Migration Summary ===")
    print(f"Successfully processed: {len(results['success'])}")
    print(f"Skipped: {len(results['skipped'])}")
    print(f"Errors: {len(results['errors'])}")
    
    print(f"\n=== Files by Company ===")
    for company, count in sorted(company_counts.items()):
        print(f"{company}: {count} files")
    
    if results["errors"]:
        print(f"\n=== Errors ===")
        for error in results["errors"][:5]:  # Show first 5 errors
            print(f"- {error['file']}: {error['error']}")
    
    print(f"\n=== Sample Processed Files ===")
    for i, result in enumerate(results["success"][:5]):  # Show first 5 successful
        print(f"{i+1}. {result['target']}")
        print(f"   Title: {result['title']}")
        print(f"   Date: {result['date']}")
        print(f"   Company: {result['company']}")
        print()

if __name__ == "__main__":
    main()