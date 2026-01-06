#!/usr/bin/env python3
"""
Test script for process_pdf function
"""

import sys
import os
sys.path.append('.')

from processing import process_pdf
from openai import OpenAI
from config_manager import load_and_validate_config

def main():
    # Test with a small PDF
    pdf_path = 'files/A-study-on-the-behavior-of-eccentrically-compress_2007_Journal-of-Constructi.pdf'

    if not os.path.exists(pdf_path):
        print(f'❌ Test file not found: {pdf_path}')
        return

    try:
        print('✅ Loading configuration...')
        config_path = './config.json'
        config = load_and_validate_config(config_path)

        print('✅ Initializing OpenAI client...')
        api_settings = config.get('api_settings', {})
        client = OpenAI(
            api_key=api_settings.get('api_key'),
            base_url=api_settings.get('base_url')
        )

        print('✅ Loading system prompt...')
        with open('main.py', 'r') as f:
            content = f.read()
            import re
            system_prompt_match = re.search(r'SYSTEM_PROMPT = """(.*?)"""', content, re.DOTALL)
            if system_prompt_match:
                system_prompt = system_prompt_match.group(1)
            else:
                system_prompt = 'You are a helpful assistant.'

        print(f'\n🧪 Testing process_pdf with: {os.path.basename(pdf_path)}')
        print('=' * 60)

        result = process_pdf(pdf_path, client, config, system_prompt)

        print('=' * 60)
        print(f'✅ Success! Result keys: {list(result.keys()) if result else "No result"}')
        if result:
            for group in ['Group_A', 'Group_B', 'Group_C']:
                items = result.get(group, [])
                print(f'  {group}: {len(items)} items')
            is_valid = result.get('is_valid', True)
            reason = result.get('reason', '')
            print(f'  is_valid: {is_valid}')
            if reason:
                print(f'  reason: {reason[:100]}...')

    except Exception as e:
        print(f'❌ Failed: {e}')
        import traceback
        traceback.print_exc(limit=2)

if __name__ == '__main__':
    main()
