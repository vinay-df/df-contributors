from setuptools import setup, find_packages

setup(
    name='decafluence_social_package',
    version='0.1',
    packages=find_packages(),
    install_requires=['requests', 'firebase-admin'],
    description='Social media management package for Decafluence Corp',
    author='Decafluence Dev Team',
)
