from setuptools import setup, find_packages
setup(
    name='kwenta_sdk',
    version='1.0.0',
    description='Python SDK for Kwenta',
    long_description='Python SDK for Kwenta',
    author='Kwenta Development Team',
    packages=['kwenta_sdk'],
    install_requires=[
        "numpy",
        "pandas",
        "requests",
        "web3>=6.0.0",
    ],
    classifiers=[
        'Development Status :: 2 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires=">=3.8",
    package_data={"kwenta_sdk":["json/*"]},
    include_package_data=True,
)
# Local Install
# python .\setup.py sdist bdist_wheel
# pip install .