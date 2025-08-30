#!/usr/bin/env python3
"""
Script to fix MDX compilation issues in Docusaurus markdown files.

This script fixes common MDX parsing errors:
1. URL patterns like <https://example.com> -> proper markdown links
2. Problematic curly braces that interfere with JSX parsing
3. Malformed HTML-like tags that need escaping
4. Other MDX-specific syntax issues
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple


def fix_url_brackets(content: str) -> str:
    """
    Convert <https://url> and <http://url> patterns to proper markdown links.
    """
    # Pattern to match URLs wrapped in angle brackets
    url_pattern = r'<(https?://[^>\s]+)>'
    
    def replace_url(match):
        url = match.group(1)
        return f'[{url}]({url})'
    
    return re.sub(url_pattern, replace_url, content)


def escape_curly_braces_in_text(content: str) -> str:
    """
    Escape curly braces that are not part of JSX expressions or code blocks.
    This is more conservative - only escapes standalone braces that could cause issues.
    """
    lines = content.split('\n')
    result_lines = []
    in_code_block = False
    
    for line in lines:
        # Track if we're in a code block
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue
        
        # Don't process lines inside code blocks
        if in_code_block:
            result_lines.append(line)
            continue
        
        # Don't process lines that look like they contain template variables
        # (common in system prompts)
        if '${' in line and '}' in line:
            result_lines.append(line)
            continue
        
        # Don't process lines that already have escaped braces
        if '\\{' in line or '\\}' in line:
            result_lines.append(line)
            continue
        
        # Only escape isolated curly braces that could cause MDX issues
        # This is a conservative approach to avoid breaking legitimate syntax
        line = re.sub(r'(?<!\$)\{(?![a-zA-Z_$])', r'\\{', line)
        line = re.sub(r'(?<![a-zA-Z_$0-9])\}', r'\\}', line)
        
        result_lines.append(line)
    
    return '\n'.join(result_lines)


def fix_html_tags(content: str) -> str:
    """
    Fix common HTML tag issues that cause MDX problems.
    """
    # Fix unclosed tags or malformed tags
    # Convert <example> and </example> to code blocks or escape them
    content = re.sub(r'^(\s*)<example>\s*$', r'\1```example', content, flags=re.MULTILINE)
    content = re.sub(r'^(\s*)</example>\s*$', r'\1```', content, flags=re.MULTILINE)
    
    # Handle problematic tags by putting them in backticks instead of escaping
    problematic_tags = [
        'user_query', 'resource', 'tool_calling', 'thinking', 'response',
        'system', 'user', 'assistant', 'instructions', 'election_info'
    ]
    
    for tag in problematic_tags:
        # Put problematic tags in backticks to prevent MDX interpretation
        content = re.sub(f'<{tag}>', f'`<{tag}>`', content)
        content = re.sub(f'</{tag}>', f'`</{tag}>`', content)
    
    # Handle other standalone angle brackets that aren't URLs or proper HTML
    # This is conservative - only fixes obvious problematic patterns
    # Don't escape if it's already in backticks, part of a markdown link, or a URL
    content = re.sub(r'(?<!`)(?<!source: \[)(?<!http)(?<!https)<(?!https?://)([\w_-]+)>', r'`<\1>`', content)
    
    return content


def fix_jsx_issues(content: str) -> str:
    """
    Fix JSX-related issues that cause MDX problems.
    """
    lines = content.split('\n')
    result_lines = []
    in_code_block = False
    
    for line in lines:
        # Track if we're in a code block
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue
        
        # Don't process lines inside code blocks
        if in_code_block:
            result_lines.append(line)
            continue
        
        # Fix problematic JSX-like syntax that isn't valid JSX
        # Escape angle brackets that could be interpreted as JSX but aren't
        # Fix issues like <3 (which gets interpreted as starting a JSX element)
        line = re.sub(r'<(\d+)', r'\\<\1', line)  # <3, <4, etc.
        line = re.sub(r'<(\w+)\s+([^>]*?)\\([^>]*?)>', r'\\<\1 \2\\\\\3\\>', line)  # Fix backslashes in attributes
        
        result_lines.append(line)
    
    return '\n'.join(result_lines)


def fix_markdown_escaping(content: str) -> str:
    """
    Fix markdown escaping issues that might interfere with MDX.
    """
    lines = content.split('\n')
    result_lines = []
    in_code_block = False
    
    for line in lines:
        # Track if we're in a code block
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue
        
        # Don't process lines inside code blocks
        if in_code_block:
            result_lines.append(line)
            continue
        
        # Fix any remaining issues with special characters
        # Be very conservative here to avoid breaking valid markdown
        
        result_lines.append(line)
    
    return '\n'.join(result_lines)


def fix_mdx_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Fix MDX issues in a single file.
    
    Returns:
        (bool, List[str]): (whether file was modified, list of changes made)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    content = original_content
    changes = []
    
    # Apply fixes in order
    
    # 1. Fix URL brackets
    new_content = fix_url_brackets(content)
    if new_content != content:
        url_matches = len(re.findall(r'<(https?://[^>\s]+)>', content))
        changes.append(f"Fixed {url_matches} URL bracket patterns")
        content = new_content
    
    # 2. Fix HTML tags
    new_content = fix_html_tags(content)
    if new_content != content:
        changes.append("Fixed HTML tag issues")
        content = new_content
    
    # 3. Fix JSX issues
    new_content = fix_jsx_issues(content)
    if new_content != content:
        changes.append("Fixed JSX syntax issues")
        content = new_content
    
    # 4. Fix curly braces (be very conservative)
    new_content = escape_curly_braces_in_text(content)
    if new_content != content:
        changes.append("Escaped problematic curly braces")
        content = new_content
    
    # 5. Fix markdown escaping
    new_content = fix_markdown_escaping(content)
    if new_content != content:
        changes.append("Fixed markdown escaping")
        content = new_content
    
    # Write back if there were changes
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        except Exception as e:
            return False, [f"Error writing file: {e}"]
    
    return False, []


def process_directory(directory: Path, dry_run: bool = False) -> None:
    """
    Process all .md files in a directory and its subdirectories.
    """
    if not directory.exists():
        print(f"Directory does not exist: {directory}")
        return
    
    md_files = list(directory.rglob("*.md"))
    
    if not md_files:
        print(f"No .md files found in {directory}")
        return
    
    print(f"Found {len(md_files)} markdown files to process")
    
    total_modified = 0
    
    for file_path in md_files:
        if dry_run:
            print(f"\nDRY RUN - Would process: {file_path}")
            # Still run the fixes to see what would change, but don't write
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                content = original_content
                changes = []
                
                # Test all fixes
                new_content = fix_url_brackets(content)
                if new_content != content:
                    url_matches = len(re.findall(r'<(https?://[^>\s]+)>', content))
                    changes.append(f"Would fix {url_matches} URL bracket patterns")
                    content = new_content
                
                new_content = fix_html_tags(content)
                if new_content != content:
                    changes.append("Would fix HTML tag issues")
                    content = new_content
                
                new_content = fix_jsx_issues(content)
                if new_content != content:
                    changes.append("Would fix JSX syntax issues")
                    content = new_content
                
                new_content = escape_curly_braces_in_text(content)
                if new_content != content:
                    changes.append("Would escape problematic curly braces")
                    content = new_content
                
                if changes:
                    print(f"  Changes: {'; '.join(changes)}")
                else:
                    print("  No changes needed")
                    
            except Exception as e:
                print(f"  Error analyzing file: {e}")
        else:
            modified, changes = fix_mdx_file(file_path)
            
            if modified:
                total_modified += 1
                print(f"✓ Modified: {file_path}")
                for change in changes:
                    print(f"  - {change}")
            else:
                if changes:  # There were errors
                    print(f"✗ Error: {file_path}")
                    for change in changes:
                        print(f"  - {change}")
    
    if not dry_run:
        print(f"\n✓ Processing complete. Modified {total_modified} files.")
    else:
        print(f"\n✓ Dry run complete. Analyzed {len(md_files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Fix MDX compilation issues in Docusaurus markdown files"
    )
    parser.add_argument(
        "directories",
        nargs="*",
        help="Directories to process (e.g., docs/big-tech docs/ai-services)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making modifications"
    )
    parser.add_argument(
        "--file",
        help="Process a single file instead of directories"
    )
    
    args = parser.parse_args()
    
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"File does not exist: {file_path}")
            return
        
        if args.dry_run:
            print("DRY RUN mode - no files will be modified")
            # Do dry run analysis
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                content = original_content
                changes = []
                
                # Test all fixes
                new_content = fix_url_brackets(content)
                if new_content != content:
                    url_matches = len(re.findall(r'<(https?://[^>\s]+)>', content))
                    changes.append(f"Would fix {url_matches} URL bracket patterns")
                    content = new_content
                
                new_content = fix_html_tags(content)
                if new_content != content:
                    changes.append("Would fix HTML tag issues")
                    content = new_content
                
                new_content = fix_jsx_issues(content)
                if new_content != content:
                    changes.append("Would fix JSX syntax issues")
                    content = new_content
                
                new_content = escape_curly_braces_in_text(content)
                if new_content != content:
                    changes.append("Would escape problematic curly braces")
                
                if changes:
                    print(f"Changes needed: {'; '.join(changes)}")
                else:
                    print("No changes needed")
                    
            except Exception as e:
                print(f"Error analyzing file: {e}")
        else:
            modified, changes = fix_mdx_file(file_path)
            
            if modified:
                print(f"✓ Modified: {file_path}")
                for change in changes:
                    print(f"  - {change}")
            else:
                if changes:  # There were errors
                    print(f"✗ Error: {file_path}")
                    for change in changes:
                        print(f"  - {change}")
                else:
                    print(f"No changes needed: {file_path}")
    elif args.directories:
        if args.dry_run:
            print("DRY RUN mode - no files will be modified\n")
        
        for directory_str in args.directories:
            directory = Path(directory_str)
            print(f"\nProcessing directory: {directory}")
            process_directory(directory, args.dry_run)
    else:
        print("Please specify either --file or provide directories to process")
        parser.print_help()


if __name__ == "__main__":
    main()