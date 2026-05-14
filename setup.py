from setuptools import setup, find_packages

setup(
    name="wireless-log-analyzer",
    version="1.0.0",
    description="Automated log analysis and anomaly detection for LTE, 5G NR, and Satellite connectivity",
    author="Wireless Test Automation Team",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "streamlit==1.35.0",
        "pandas==2.2.2",
        "plotly==5.22.0",
    ],
    entry_points={
        "console_scripts": [
            # Run the CLI analyzer
            "wla-analyze=analyzer:main_cli",
            # Generate synthetic logs
            "wla-generate=generate_logs:main_cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)
