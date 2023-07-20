from setuptools import setup, find_packages

setup(
    name="kwenta",
    version="1.0.8",
    description="Python SDK for Kwenta",
    long_description="Python SDK for Kwenta",
    author="Kwenta DAO",
    packages=[
        "kwenta",
        "kwenta.alerts",
        "kwenta.cli",
        "kwenta.contracts",
        "kwenta.contracts.json",
        "kwenta.pyth",
        "kwenta.queries",
    ],
    install_requires=["numpy", "pandas", "requests", "web3>=6.0.0", "gql"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    package_data={"kwenta": ["json/*"]},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "kwenta = kwenta.cli.kwenta_cli:kwenta_cli",
        ],
    },
)
