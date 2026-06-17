packages = {
    'streamlit': 'streamlit',
    'openai': 'openai',
    'PyMuPDF': 'fitz',
    'pandas': 'pandas',
    'python-dotenv': 'dotenv',
    'plotly': 'plotly',
    'python-docx': 'docx',
    'anthropic': 'anthropic',
    'google-generativeai': 'google.generativeai',
    'scikit-learn': 'sklearn',
    'numpy': 'numpy',
    'requests': 'requests',
}
missing = []
for name, imp in packages.items():
    try:
        __import__(imp)
        print(f'OK   {name}')
    except ImportError:
        print(f'MISSING  {name}')
        missing.append(name)
if missing:
    print(f'\nMISSING PACKAGES: {missing}')
else:
    print('\nALL PACKAGES INSTALLED')
