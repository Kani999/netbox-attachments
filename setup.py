from setuptools import find_packages, setup

setup(
    name = 'netbox-attachments',
    version='0.0.1',
    description = 'Netbox plugin to manage attachments for any model',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
